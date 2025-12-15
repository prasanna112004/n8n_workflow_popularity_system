# server.py - serves raw and scored workflow JSON
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import json, os, uvicorn

app = FastAPI(title="n8n Workflow Popularity - Quick Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(BASE_DIR, "data", "sample_workflows.json")
SCORED_PATH = os.path.join(BASE_DIR, "data", "sample_workflows_scored.json")

def load_json(path):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/")
def root():
    return {"message": "Server is running. Use /health, /workflows, /workflows/raw or /workflows/scored."}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/workflows")
def workflows(platform: Optional[str] = Query(None), country: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=1000)):
    """
    Default: return the scored dataset if available, else fall back to raw.
    Supports optional filtering by platform and country and a limit.
    """
    path = SCORED_PATH if os.path.exists(SCORED_PATH) else RAW_PATH
    data = load_json(path)
    if platform:
        data = [d for d in data if str(d.get("platform","")).lower() == platform.lower()]
    if country:
        data = [d for d in data if (d.get("country") or "").lower() == country.lower()]
    return JSONResponse(content=data[:limit])

@app.get("/workflows/raw")
def workflows_raw(limit: int = Query(100, ge=1, le=1000)):
    data = load_json(RAW_PATH)
    return JSONResponse(content=data[:limit])

@app.get("/workflows/scored")
def workflows_scored(limit: int = Query(100, ge=1, le=1000)):
    if not os.path.exists(SCORED_PATH):
        raise HTTPException(status_code=404, detail="Scored data not found. Run scoring script first.")
    data = load_json(SCORED_PATH)
    return JSONResponse(content=data[:limit])

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)