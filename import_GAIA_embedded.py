import json
import os
import asyncio
import mlflow
import pandas as pd
from datetime import datetime
from datasets import load_dataset
from huggingface_hub import login as hf_login
from google import genai
import chromadb
from chromadb.utils import embedding_functions

# Import the prompts from reference file
from references.agent_prompts_ref import NODE_PROMPTS

# Load environment variables from .env file
import dotenv
dotenv.load_dotenv()

# --- Configuration ---
HF_TOKEN = os.getenv("HF_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OUTPUT_FILE = f'datasets/gaia_node_embedded_benchmark{datetime.now():%Y-%m-%d_%H:%M:%S%z}.json'
GAIA_LEVELS = ["1", "2", "3"]
MAX_EXAMPLES_PER_TOOL_PER_LEVEL = 5

TOOL_DESCRIPTIONS = {
    "direct_answer": "General reasoning, logic, or questions that can be answered using internal knowledge without external data lookup.",
    "sql_trino": "Querying internal databases and structured tables. Use this for any specific data points, records, or facts stored in the organization's datasets via Trino SQL.",
    "calculator": "Mathematical computations, percentages, and statistical analysis on provided or retrieved numbers."
}



# Initialize Google Generative AI embedding function
google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key=(GOOGLE_API_KEY),
    model_name="models/gemini-embedding-001"
)

# Login to HuggingFace and Google Generative AI
hf_login(token=HF_TOKEN)
client = genai.Client(api_key=GOOGLE_API_KEY)

# Creation of ChromaDB client and collection with the Google Generative AI embedding function
chromadb_client = chromadb.Client()
chromacollection = chromadb_client.get_or_create_collection(
    name="gaia_node_embedded_benchmark",
    embedding_function=google_ef
)


for tool_id, tool_description in TOOL_DESCRIPTIONS.items():
    chromacollection.add(
        documents=[tool_description],
        ids=[tool_id]
    )

print("Tools added to ChromaDB collection.")



def get_node_expectations(question):
    context_prompt = f"""
    Analyze the following AI Assistant question and define the expected behavior for these 4 components based on the provided node prompts.
    
    --- SYSTEM NODE PROMPTS ---
    {json.dumps(NODE_PROMPTS, indent=2)}

    --- USER QUESTION ---
    Question: {question}

    Return ONLY a raw JSON object. Do not include any markdown, commentary, or text before/after the JSON.
    Ensure that each component's output serves as the logical basis for the next one 
    (e.g., the 'action' must implement a step defined in the 'plan').
    Expected Keys: "plan", "thought", "action", "observe", "reflect".
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=context_prompt
        )
        
        # IMPROVED EXTRACTION: Find the actual JSON content
        text = response.text.strip()
        first_bracket = text.find('{')
        last_bracket = text.rfind('}')
        
        if first_bracket == -1 or last_bracket == -1:
            print(f"No JSON found in response: {text[:100]}...")
            return None
            
        clean_json = text[first_bracket:last_bracket + 1]
        return json.loads(clean_json)
        
    except Exception as e:
        print(f"Error annotating question: {e}")
        return None

def prepare_annotated_benchmark():
    print("Fetching GAIA dataset...")
    final_benchmark = {level : [] for level in GAIA_LEVELS}
    dataset = load_dataset("gaia-benchmark/GAIA", "2023_all", split="validation")

    # Organize items in the Dataset by GAIA levels
    items_in_dataset_per_level = {level : [] for level in GAIA_LEVELS}
    for item in dataset:
        lvl = str(item['Level'])
        if lvl in items_in_dataset_per_level:
            items_in_dataset_per_level[lvl].append(item)

    # Go over each level and select the top EXAMPLES_PER_LEVEL items, with consideration to maximum number of items per tool
    for level in GAIA_LEVELS:
        print(f"Processing Level {level}...")

        tool_buckets_for_level = {tool: [] for tool in TOOL_DESCRIPTIONS.keys()}

        for item in items_in_dataset_per_level[level]:
            # Skip items that have a file attached
            if item.get('file_name'):
                continue

            # Find the best tool for the current item
            results = chromacollection.query(
                query_texts=[item['Question']],
                n_results=1
            )

            distance = results['distances'][0][0]
            best_tool = results['ids'][0][0]

            tool_buckets_for_level[best_tool].append({
                "item": item,
                "distance": distance,
                "best_tool": best_tool
            })

        # Sort each tool bucket by distance and take the top EXAMPLES_PER_LEVEL items
        for tool in tool_buckets_for_level:
            tool_buckets_for_level[tool].sort(key=lambda x: x['distance'])
            tool_buckets_for_level[tool] = tool_buckets_for_level[tool][:MAX_EXAMPLES_PER_TOOL_PER_LEVEL]

        # Add the top items from each tool bucket to the final benchmark
        for tool, items in tool_buckets_for_level.items():
            print(f"Adding {len(items)} items for tool {tool} to Level {level}")              
            print("-" * 50)
            
            for candidate in items:
                question = candidate['item']['Question']
                node_metadata = get_node_expectations(question)
                
                if node_metadata:
                    final_benchmark[level].append({
                        "input": {"question": question},
                        "expected_output": candidate['item']['Final answer'],
                        "metadata": {
                            "level": level,
                            "node_validation": node_metadata,
                            "expected_behavior": {
                                "golden_answer": candidate['item']['Final answer']
                            }
                        }
                    })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_benchmark, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccess! Saved {len(final_benchmark)} annotated items to {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_annotated_benchmark()