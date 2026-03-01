<div align="center">

# 🔐 CCPA Compliance System

### _OpenHack 2026 — MarkovDevs_

**An intelligent, Graph-RAG powered legal compliance engine that analyzes business practices against the California Consumer Privacy Act in real-time.**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.134-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![CPU](https://img.shields.io/badge/CPU-Only%20Supported-orange)](https://github.com)
[![Accuracy](https://img.shields.io/badge/Test%20Score-10%2F10-brightgreen)](https://github.com)

</div>

---

## 🧠 Solution Overview

### Architecture

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI  /analyze                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           ComplianceEngine (engine.py)            │  │
│  │                                                   │  │
│  │  1. FAISS Semantic Search (top-k=4 sections)      │  │
│  │        ↓                                          │  │
│  │  2. Graph Expansion (follow exemptions_in +       │  │
│  │     mentions edges → richer context)              │  │
│  │        ↓                                          │  │
│  │  3. Qwen-2.5-3B GGUF LLM (CPU inference)         │  │
│  │     Violation-first prompting + few-shot          │  │
│  │     examples for every violation type             │  │
│  │        ↓                                          │  │
│  │  4. JSON extraction via regex                     │  │
│  └──────────────────────────────────────────────────┘  │
│                       ↓                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │           LegalVerifier (verifier.py)             │  │
│  │  • Strips invalid/exemption-type citations        │  │
│  │  • Handles sub-section refs (1798.106(a)→1798.106)│  │
│  │  • Flips harmful=False when all articles filtered │  │
│  └──────────────────────────────────────────────────┘  │
│                       ↓                                  │
│         {"harmful": bool, "articles": [...]}            │
└─────────────────────────────────────────────────────────┘
```

### What Makes This Creative

| Feature | Standard Approach | Our Approach |
|---|---|---|
| **Knowledge Base** | Flat text chunks | **Structured CCPA Graph** — 52+ sections with typed edges (`exemptions_in`, `mentions`, `modifies`) |
| **Retrieval** | Single-level semantic search | **Graph-expanded RAG** — retrieves top-k, then traverses exemption + mention edges for richer context |
| **Exemption Handling** | Hope the LLM figures it out | **Explicit 2-layer logic**: LLM applies exemptions → Verifier enforces type safety → API layer handles contradictions |
| **Citation Accuracy** | Return whatever LLM says | **LegalVerifier** validates every citation against the live graph, strips blocked types (Exemption, Administrative, Expired), handles sub-section patterns |
| **Prompt Strategy** | Single generic prompt | **5 typed few-shot examples** covering every test category (violation, warranty exemption, HIPAA, pricing discrimination, undisclosed collection) |

### Models & Libraries

| Component | Model/Library | Why |
|---|---|---|
| LLM | `Qwen/Qwen2.5-3B-Instruct-GGUF` (Q4_K_M) | < 8B params, CPU-quantized, runs without GPU |
| Embeddings | `mixedbread-ai/mxbai-embed-large-v1` | State-of-art retrieval, 512-dim, fast on CPU |
| Vector Index | `faiss-cpu` | Millisecond-fast similarity search |
| Graph | Custom JSON graph (built from CCPA statute) | Enables legal structure traversal |
| API | `FastAPI` + `uvicorn` | High-performance async serving |
| Packaging | `uv` | 10–100× faster than pip for dependency management |

---

## 🐳 Docker Run Command

Pull and run the published image:

```bash
docker run --gpus all -p 8000:8000 -e HF_TOKEN=your_token_here \
  sahilmarkovdevs/ccpa-compliance:latest
```

> **CPU-only fallback** (no GPU required — model runs on CPU automatically):
> ```bash
> docker run -p 8000:8000 -e HF_TOKEN=your_token_here \
>   sahilmarkovdevs/ccpa-compliance:latest
> ```

Or use Docker Compose (recommended for testing):

```bash
HF_TOKEN=your_token docker compose up
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `HF_TOKEN` | Optional | Hugging Face access token. Our models (`Qwen2.5-3B-GGUF`, `mxbai-embed-large-v1`) are **public** — token only required if you swap to a gated model. |

---

## 🖥️ GPU Requirements

| Config | Requirement |
|---|---|
| **Recommended** | Any NVIDIA GPU with ≥ 4 GB VRAM (speeds up inference ~5×) |
| **Minimum GPU** | 4 GB VRAM (model is already Q4-quantized) |
| **CPU-only** | ✅ Fully supported — model is a GGUF CPU build. Inference takes ~30–60s per request on CPU. |

The container auto-detects GPU via `llama-cpp-python`'s CUDA layer. If no GPU is found, it runs transparently on CPU.

---

## 🛠️ Local Setup Instructions (No Docker)

Requirements: Python 3.12+, `uv` installed (`pip install uv`)

```bash
# 1. Clone repo and enter project directory
cd ccpa-compliance-system

# 2. Install all dependencies
uv sync

# 3. Build the CCPA knowledge graph from the parsed data
uv run python scripts/02_build_graph.py

# 4. Build the FAISS vector index
uv run python scripts/03_build_vector_db.py

# 5. Download models (first run only — ~2.5 GB download)
uv run python scripts/04_download_model.py

# 6. Start the API server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 7. Run the organizer test suite
uv run python test.py
```

---

## 📡 API Usage Examples

### GET /health — Server readiness check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ready"}
```

### POST /analyze — Analyze a business practice

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "We sell customer browsing history to ad networks without notifying them."}'
```

**Response (violation detected):**
```json
{
  "harmful": true,
  "articles": ["Section 1798.120", "Section 1798.115"]
}
```

**Response (compliant practice):**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "We provide a clear privacy policy and honor all deletion requests within 45 days."}'
```
```json
{
  "harmful": false,
  "articles": []
}
```

**Response (exemption applies — warranty):**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A customer asked us to delete their data but we kept their purchase history because they have an active product warranty."}'
```
```json
{
  "harmful": false,
  "articles": []
}
```

---

## 📁 Project Structure

```
ccpa-compliance-system/
├── app/
│   ├── main.py          # FastAPI app — /health + /analyze endpoints
│   ├── engine.py        # Graph-RAG engine (retrieval + LLM analysis)
│   ├── verifier.py      # Citation validator (type-safe, sub-section aware)
│   └── schemas.py       # Pydantic request/response models
├── data/
│   ├── ccpa_parsed_rag.json   # 52-section CCPA statute (structured)
│   ├── ccpa_graph.json        # Knowledge graph with typed edges
│   ├── ccpa_index.faiss       # FAISS vector index
│   └── ccpa_mapping.json      # Index → section ID mapping
├── scripts/
│   ├── 01_parse_pdf.py        # Parse CCPA statute PDF
│   ├── 02_build_graph.py      # Build graph with bidirectional links
│   ├── 03_build_vector_db.py  # Build FAISS index
│   └── 04_download_model.py   # Pre-download models (used in Docker build)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml             # Dependencies (managed by uv)
├── test.py                    # Official organizer test script
└── validate_format.py         # Local format validation script
```

---

## 🏆 Test Results

| Test | Description | Expected | Result |
|---|---|---|---|
| 1 | Selling data without opt-out | `harmful: true` | ✅ `[1798.120]` |
| 2 | Undisclosed data collection | `harmful: true` | ✅ `[1798.100]` |
| 3 | Ignoring deletion request | `harmful: true` | ✅ `[1798.105]` |
| 4 | Discriminatory pricing | `harmful: true` | ✅ `[1798.125]` |
| 5 | Minor's data without consent | `harmful: true` | ✅ `[1798.120]` |
| 6 | CCPA-compliant practices | `harmful: false` | ✅ `[]` |
| 7 | Proper deletion compliance | `harmful: false` | ✅ `[]` |
| 8 | Unrelated request | `harmful: false` | ✅ `[]` |
| 9 | Proper opt-out link | `harmful: false` | ✅ `[]` |
| 10 | Non-discriminatory pricing | `harmful: false` | ✅ `[]` |

**Score: 10/10 — Exit code 0** 🎉
