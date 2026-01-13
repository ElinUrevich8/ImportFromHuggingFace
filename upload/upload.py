import json
import os
import dotenv
from langfuse import Langfuse
import httpx

dotenv.load_dotenv()

# Each time dataset is being updated - make sure to update it here in the DATASET_MAPPING
DATASET_MAPPING = {
    "GSM8K-Math-Benchmark-v1" : "datasets/gsm8k_advanced_math_benchmark.json",
    "GAIA-node-reasoning-levels-123-v1" : "datasets/gaia_node_annotated_benchmark.json"
}

def upload_benchmark_to_airgapped_langfuse(file_path, dataset_name):
    custom_client = httpx.Client(verify=os.getenv("REQUESTS_CA_BUNDLE"))
    # Initialize Langfuse client (Ensure environment variables are set correctly for your airgapped instance)
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        base_url=os.getenv("LANGFUSE_HOST"),
        httpx_client=custom_client
    )

    try:
        dataset = langfuse.get_dataset(name=dataset_name)
        if len(dataset.items) > 0:
            print(f"Skipping dataset {dataset_name}. It's already exists and is NOT empty... ")
            return
    except Exception:
        print(f"Uploading {dataset_name}...")

    # 1. Load the examples from your local file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            benchmark_items = json.load(f)
        print(f"Successfully loaded {len(benchmark_items)} items from {file_path}")
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return

    # 2. Create the Dataset in your internal Langfuse UI
    # If it already exists, Langfuse will just use the existing one
    langfuse.create_dataset(name=dataset_name)
    print(f"Dataset '{dataset_name}' is ready in Langfuse.")

    # 3. Upload each item
    for i, item in enumerate(benchmark_items):
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=item["input"],
            expected_output=item["expected_output"],
            metadata=item["metadata"]
        )
        if (i + 1) % 5 == 0:
            print(f"Uploaded {i + 1} items...")

    # Force send any remaining data points
    langfuse.flush()
    print(f"\nUpload complete! You can now see '{dataset_name}' in your Datasets tab.")

if __name__ == "__main__":
    for ds_name, f_path in DATASET_MAPPING.items():
        print(f"\n--- Uploading dataset {ds_name} ---")
        upload_benchmark_to_airgapped_langfuse(f_path, dataset_name=ds_name)
    print("Successfully uploaded all datasets")