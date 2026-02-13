import json
import os
from datasets import load_dataset
from huggingface_hub import login
from google import genai  

# Import the prompts from reference file
from references.agent_prompts_ref import NODE_PROMPTS

# Load environment variables from .env file
import dotenv
dotenv.load_dotenv()


# --- Configuration ---
HF_TOKEN = os.getenv("HF_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_FILE = "datasets/gaia_node_annotated_benchmark.json"
EXAMPLES_PER_LEVEL = 5 
GAIA_LEVELS = ["1", "2", "3"]

TOOL_KEYWORDS = {
    "sql_trino": ["database", "sql", "table", "query", "record", "data"],
    "calculator": ["average", "ratio", "total", "percentage", "calculate", "math", "divide"]
}

# --- Initialization ---
login(token=HF_TOKEN)

# New SDK Client initialization
client = genai.Client(api_key=GEMINI_API_KEY)

def get_node_expectations(question):
    context_prompt = f"""
    Analyze the following AI Assistant question and define the expected behavior for these 4 components based on the provided node prompts.
    
    --- SYSTEM NODE PROMPTS ---
    {json.dumps(NODE_PROMPTS, indent=2)}

    --- USER QUESTION ---
    Question: {question}

    Return ONLY a raw JSON object. Do not include any markdown, commentary, or text before/after the JSON.
    Expected Keys: "plan", "thought", "action", "observe", "reflect".
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", 
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
    final_benchmark = []
    print("Fetching GAIA dataset...")
    dataset = load_dataset("gaia-benchmark/GAIA", "2023_all", split="validation")

    for level in GAIA_LEVELS:
        print(f"Processing Level {level}...")
        level_count = 0
        level_items = [i for i in dataset if str(i['Level']) == level]
        
        for item in level_items:
            if level_count >= EXAMPLES_PER_LEVEL:
                break
            
            question = item['Question']
            all_keywords = [word for list_in_dict in TOOL_KEYWORDS.values() for word in list_in_dict]
            
            if any(key in question.lower() for key in all_keywords) and not item['file_name']:
                print(f"Generating Golden Trace for Level {level} item {level_count + 1}...")
                node_metadata = get_node_expectations(question)
                
                if node_metadata:
                    final_benchmark.append({
                        "input": {"question": question},
                        "expected_output": item['Final answer'],
                        "metadata": {
                            "level": level,
                            "node_validation": node_metadata,
                            "expected_behavior": {
                                "golden_answer": item['Final answer']
                            }
                        }
                    })
                    level_count += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_benchmark, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccess! Saved {len(final_benchmark)} annotated items to {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_annotated_benchmark()