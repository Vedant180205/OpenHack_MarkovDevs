import json
import os
import faiss
import re
from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

GRAPH_PATH = "data/ccpa_graph.json"
INDEX_PATH = "data/faiss_index/ccpa.index"
MAPPING_PATH = "data/faiss_index/mapping.json"
EMBED_MODEL_ID = "mixedbread-ai/mxbai-embed-large-v1"

class ComplianceEngine:
    def __init__(self):
        self.is_ready = False
        self.graph = {}
        self.mapping = []
        self.index = None
        self.embedder = None
        self.llm = None

    def load_resources(self):
        with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
        with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        self.index = faiss.read_index(INDEX_PATH)
        self.embedder = SentenceTransformer(EMBED_MODEL_ID)
        
        model_path = hf_hub_download(
            repo_id="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", 
            filename="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        )
        
        self.llm = Llama(model_path=model_path, n_ctx=6144, n_threads=8, n_gpu_layers=-1, verbose=False)
        self.is_ready = True
        print("✅ Engine Fully Loaded on CPU!")

    def retrieve_and_expand(self, query, top_k=4):
        query_vector = self.embedder.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector, top_k)
        
        retrieved_nodes = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.mapping):
                section_id = self.mapping[idx]
                retrieved_nodes.append(section_id)
        
        final_sections = set(retrieved_nodes)
        for node_id in retrieved_nodes:
            node_data = self.graph.get(node_id, {})
            # Expand via exemptions_in AND mentions for richer context
            for ex in node_data.get("exemptions_in", []):
                final_sections.add(ex)
            for mention in node_data.get("mentions", []):
                if mention in self.graph:
                    final_sections.add(mention)

        context = ""
        for sec_id in sorted(final_sections):
            data = self.graph.get(sec_id, {})
            # Use summary for core sections, full content only for exemptions (shorter)
            node_type = data.get('type', '')
            text = data.get('summary', '') or data.get('content', '')[:400]
            context += f"[{sec_id}] ({node_type}) {data.get('title','')}: {text}\n"
        return context

    def analyze(self, prompt: str) -> dict:
        context = self.retrieve_and_expand(prompt)
        
        system_prompt = f"""You are a CCPA Compliance AI. Determine if the business practice violates the law.

LEGAL CONTEXT:
{context}

ANALYSIS STEPS:
1. Identify every Rule/Duty section the practice violates.
2. Check if a VALID Exemption explicitly cancels the violation. (Note: Blocking hackers, fraud, or DDoS attacks counts as the "Security and Integrity" exemption).
3. WARNING: You must strictly IGNORE any exemptions marked as "Expired" or "INOPERATIVE" (such as the Employee/B2B exemption). If the exemption is expired, the practice is a violation.
4. If un-exempted violations remain → harmful=true, list the Rule section IDs.
5. If all violations are cancelled by a VALID exemption → harmful=false, articles=[].

RULES: Only cite Rule/Duty sections (not Exemptions). Output ONLY JSON.

EXAMPLES:
Practice: "We sell user data without opt-out."
→ {{"harmful": true, "articles": ["Section 1798.120"]}}

Practice: "We collect biometric data but don't disclose it in our privacy policy."
→ {{"harmful": true, "articles": ["Section 1798.100"]}}

Practice: "We charge customers who opted out of data selling a higher price for the same service."
→ {{"harmful": true, "articles": ["Section 1798.125"]}}

Practice: "A customer asked us to delete data but we kept purchase history for their active warranty."
→ {{"harmful": false, "articles": []}}

Practice: "A hospital refused to delete patient HIPAA records under CCPA."
→ {{"harmful": false, "articles": []}}
"""
        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\nAnalyze this practice: {prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        output = self.llm(formatted_prompt, max_tokens=512, temperature=0.0, stop=["<|im_end|>"])
        response_text = output['choices'][0]['text'].strip()
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            result = json.loads(json_match.group(0)) if json_match else json.loads(response_text)
            
            # Normalise types
            if isinstance(result.get("harmful"), str):
                result["harmful"] = str(result["harmful"]).lower() == "true"
            if not result.get("harmful"):
                result["articles"] = []
                
            return result
        except (json.JSONDecodeError, AttributeError):
            return {"harmful": False, "articles": []}

engine = ComplianceEngine()