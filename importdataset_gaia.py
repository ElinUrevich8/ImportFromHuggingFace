import json
import os
from datasets import load_dataset
from huggingface_hub import login

def prepare_gaia_for_tools(output_file="gaia_trino_calculator_benchmark.json"):
    print("Downloading GAIA dataset...")
    # Loading validation set as it contains the ground truth answers
    login(token=os.getenv("HF_TOKEN"))
    dataset = load_dataset("gaia-benchmark/GAIA", "2023_all", split="validation")
    
    filtered_items = []
    # Keywords that suggest the need for data retrieval or calculation
    keywords = ["how many", "ratio", "average", "total", "calculate", "percentage", "database"]

    for item in dataset:
        question = item['Question']
        final_answer = item['Final answer']
        level = item['Level']
        
        # Filter: Only text-based questions (no complex files) that match our toolset
        if any(key in question.lower() for key in keywords) and not item['file_name']:
            if len(filtered_items) < 15: # Cherry-pick top 15
                filtered_items.append({
                    "input": {"question": question},
                    "expected_output": final_answer,
                    "metadata": {
                        "difficulty_level": level,
                        "golden_answer": final_answer,
                        "expected_behavior": {
                            "golden_answer": final_answer,
                            "tone": "concise and factual"
                        },
                        "source": f"GAIA-Level-{level}"
                    }
                })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_items, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully saved {len(filtered_items)} GAIA items to {output_file}")

if __name__ == "__main__":
    prepare_gaia_for_tools()