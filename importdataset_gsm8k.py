import json
import re
from datasets import load_dataset

def clean_number(n):
    """
    Cleans a string to ensure it can be converted to a float.
    Removes trailing dots (from end of sentences) and commas.
    """
    # Remove trailing non-digit characters like dots or commas. examples: 250, 250.
    cleaned = n.rstrip('.,')
    # Remove commas used as thousands separators. examples: 1,0000 -> 10000
    cleaned = cleaned.replace(',', '')
    return cleaned

def get_max_number(text):
    """ Finds the largest numerical value in a given text string. """
    raw_numbers = re.findall(r'[\d,.]+', text)
    numbers = []
    for n in raw_numbers:
        cleaned = clean_number(n)
        try:
            if cleaned and cleaned.replace('.', '', 1).isdigit():
                numbers.append(float(cleaned))
        except ValueError:
            continue
    return max(numbers) if numbers else 0


def prepare_offline_multi_math_benchmark(output_file="gsm8k_advanced_math_benchmark.json"):
    print("Downloading GSM8K dataset...")
    # 'train' split provides a larger pool of examples (7.5K).
    dataset = load_dataset("openai/gsm8k", "main", split="train")

    number_of_examples = 10
    
    # Storage for candidates before sorting
    candidates = {
        "division": [],
        "multiplication": [],
        "addition": [],
        "subtraction": [],
        "exponent": []
    }

    operations = {
        "division": ["divide", "divided by", "/"],
        "multiplication": ["multiply", "multiplied by", "times", "*"],
        "addition": ["add", "sum", "total", "plus", "+"],
        "subtraction": ["subtract", "minus", "difference", "-"],
        "exponent": ["power of", "square", "cube", "exponent"]
    }

    limit_per_op = 10 
    op_counts = {op: 0 for op in operations}

    print("Filtering for complex math problems...")

    for item in dataset:
        question = item['question']
        answer = item['answer']
        
        found_op = None
        for op, keywords in operations.items():
            if any(key in question.lower() for key in keywords):
                if op_counts[op] < limit_per_op:
                    found_op = op
                    break
        
        if not found_op:
            continue

        # Get the largest number in this specific question to judge its 'complexity'
        max_val = get_max_number(question)
        
        # Only consider 'gigantic' context (e.g., numbers over 5,000)
        if max_val > 5000:
            final_answer_match = re.search(r"####\s?([\d,.]+)", answer)
            final_answer = final_answer_match.group(1).replace(",", "") if final_answer_match else None# Only consider 'gigantic' context (e.g., numbers over 5,000)
        else:
            final_answer = None    
        
        if final_answer:
                candidates[found_op].append({
                    "max_val": max_val, # Used for sorting later
                    "data": {
                        "input": {"question": question},
                        "expected_output": final_answer,
                        "metadata": {
                            "operation_type": found_op,
                            "max_number_detected": max_val,
                            "expected_behavior": {
                                "golden_answer": final_answer,
                                "tone": "professional and precise"
                            }
                        }
                    }
                })

    # FINAL STEP: Sort each category by the 'max_val' and take the top number_of_examples
    final_benchmark = []
    for op in candidates:
        # Sort descending so the largest numbers come first
        top_examples = sorted(candidates[op], key=lambda x: x['max_val'], reverse=True)[:number_of_examples]
        for example in top_examples:
            final_benchmark.append(example['data'])

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_benchmark, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccessfully saved {len(final_benchmark)} gigantic examples to {output_file}")

if __name__ == "__main__":
    prepare_offline_multi_math_benchmark()