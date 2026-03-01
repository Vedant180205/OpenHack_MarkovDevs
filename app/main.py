from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.engine import engine
from app.verifier import verifier

# This ensures heavy models load ONLY once when the server boots
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting CCPA Compliance Server...")
    try:
        engine.load_resources()
    except Exception as e:
        print(f"❌ Failed to load resources: {e}")
    yield
    print("Shutting down server...")

app = FastAPI(title="CCPA Compliance API", lifespan=lifespan)

@app.get("/health")
def health_check():
    # validate_format.py pings this to know when to start testing
    if engine.is_ready:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Models are still loading")

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_prompt(request: AnalyzeRequest):
    if not engine.is_ready:
        raise HTTPException(status_code=503, detail="Engine not ready")

    try:
        # 1. Run the Graph-RAG Engine
        raw_result = engine.analyze(request.prompt)
        
        # 2. Extract raw data
        harmful = raw_result.get("harmful", False)
        raw_articles = raw_result.get("articles", [])
        
        # 3. Pass through the safety verifier
        safe_articles = verifier.verify(harmful, raw_articles)
        
        # 4. If verifier returns None it means every article the LLM cited was an exemption
        #    section (got filtered out) — the LLM was citing exemptions as evidence, so
        #    this is actually a compliant scenario. Flip harmful to False.
        if safe_articles is None:
            harmful = False
            safe_articles = []

        # 5. Return strictly formatted response
        return AnalyzeResponse(
            harmful=harmful,
            articles=safe_articles
        )

    except Exception as e:
        print(f"❌ Analysis error (returning safe default): {e}")
        # Return a safe default rather than crashing the server
        return AnalyzeResponse(harmful=False, articles=[])