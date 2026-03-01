import os
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

def download_models():
    # 1. Download the Embeddings Model
    print("Downloading embedding model: mixedbread-ai/mxbai-embed-large-v1...")
    SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")

    # 2. Download the GGUF LLM
    print("Downloading Qwen 2.5 3B GGUF for CPU execution...")
    repo_id = "Qwen/Qwen2.5-3B-Instruct-GGUF"
    filename = "qwen2.5-3b-instruct-q4_k_m.gguf"
    
    # This downloads the single optimized file directly to the Hugging Face cache
    hf_hub_download(repo_id=repo_id, filename=filename)
    
    print("✅ All models successfully downloaded and cached!")

if __name__ == "__main__":
    download_models()