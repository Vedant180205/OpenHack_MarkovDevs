import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths
INPUT_JSON = "data/ccpa_graph.json"
INDEX_DIR = "data/faiss_index"
INDEX_FILE = os.path.join(INDEX_DIR, "ccpa.index")
MAPPING_FILE = os.path.join(INDEX_DIR, "mapping.json")

def build_vector_db():
    if not os.path.exists(INPUT_JSON):
        print(f"❌ Error: {INPUT_JSON} not found. Run the graph builder first.")
        return

    print("Loading compiled Graph JSON...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    section_ids = []
    texts_to_embed = []

    # Prepare the text payload for embedding
    for section_id, node in graph.items():
        section_ids.append(section_id)
        
        # Combine Title, Summary, and Content for maximum search surface area
        title = node.get("title", "")
        summary = node.get("summary", "")
        content = node.get("content", "")
        
        # We don't embed the metadata arrays (like exemptions_in) because 
        # that confuses the vector search. We only embed the descriptive text.
        search_text = f"Section {section_id} - {title}\nSummary: {summary}\nText: {content}"
        texts_to_embed.append(search_text)

    print(f"Loaded {len(texts_to_embed)} nodes. Initializing mxbai embedding model...")
    # Using the highly accurate mxbai-embed-large-v1 model
    model = SentenceTransformer('mixedbread-ai/mxbai-embed-large-v1')

    print("Generating embeddings... This will take a few seconds.")
    # Convert text to vectors
    embeddings = model.encode(texts_to_embed, convert_to_numpy=True)

    # Get the dimension size of the vectors (1024 for mxbai-embed-large-v1)
    dimension = embeddings.shape[1]

    print(f"Initializing FAISS index with dimension {dimension}...")
    # Use L2 distance for similarity search
    index = faiss.IndexFlatL2(dimension)
    
    # Add the vectors to the index
    index.add(embeddings)

    print(f"Index built with {index.ntotal} vectors.")

    # Save the FAISS index and the mapping
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    faiss.write_index(index, INDEX_FILE)
    
    # Save the mapping so our API knows which Section ID maps to the search results
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(section_ids, f, indent=4)

    print(f"✅ FAISS index saved to {INDEX_FILE}")
    print(f"✅ ID Mapping saved to {MAPPING_FILE}")

if __name__ == "__main__":
    build_vector_db()