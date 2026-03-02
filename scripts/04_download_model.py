import os
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

def download_models():
    # 1. Download the Embeddings Model
    print("Downloading embedding model: mixedbread-ai/mxbai-embed-large-v1...")
    SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")

    # 2. Download the GGUF LLM (Llama 3.1 8B)
    print("Downloading Llama 3.1 8B GGUF...")
    repo_id = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
    filename = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    
    # Grab the token from the environment variable Docker provides
    hf_token = os.getenv("HF_TOKEN")
    
    hf_hub_download(repo_id=repo_id, filename=filename, token=hf_token)
    
    print("✅ All models successfully downloaded and cached!")

if __name__ == "__main__":
    download_models()