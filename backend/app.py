"""FastAPI backend + static frontend.   Run: uvicorn backend.app:app --reload   ->  http://localhost:8000"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .llm import is_mock, list_versions, model_name
from .pipeline import run_part1
from .schemas import Part1Result

app = FastAPI(title="AI Research Assistant: Part 1 (question -> sub-questions)")

class DecomposeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    version: str = "final"

@app.get("/api/health")
def health():
    return {"status": "ok", "model": model_name(), "mock": is_mock(), "has_key": bool(os.getenv("LLM_API_KEY"))}

@app.get("/api/versions")
def versions():
    return {"versions": list_versions(), "default": "final"}

@app.post("/api/decompose", response_model=Part1Result)
def decompose_endpoint(req: DecomposeRequest):
    if req.version not in list_versions():
        raise HTTPException(400, f"Unknown prompt version '{req.version}'")
    try:
        return run_part1(req.question, req.version)
    except ValueError as e:        # decomposition failed validation after retries
        raise HTTPException(422, str(e))
    except RuntimeError as e:      # LLM unavailable / bad key / invalid output
        raise HTTPException(502, str(e))

# Frontend (must be mounted last so it does not shadow /api)
app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "frontend", html=True), name="frontend")
