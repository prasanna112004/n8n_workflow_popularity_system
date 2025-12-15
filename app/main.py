# app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import json
import os

app = FastAPI(title="n8n Workflow Popularity - Step 1")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "sample_workflows.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=500, detail=f"Data file not found at {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/workflows")
def get_workflows(platform: Optional[str] = Query(None), country: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=100)):
    data = load_data()
    if platform:
        data = [d for d in data if str(d.get("platform","")).lower() == platform.lower()]
    if country:
        data = [d for d in data if str(d.get("country","")).lower() == country.lower()]
    return JSONResponse(content=data[:limit])