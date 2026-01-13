# Uploading a Dataset to Langfuse

This guide explains how to configure your environment and install the required dependencies in order to upload datasets to Langfuse.

## Environment Setup

Create a `.env` file in the project root directory and define the following variables:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGFUSE_HOST=https://langfuse.com
REQUESTS_CA_BUNDLE=/path/to/bundle-latest.crt
```

## Installation

Install the required Python modules using pip:

```
python3 -m pip install pydantic httpx packaging python-dotenv requests
```
