import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agentcourt import AgentCourtClient
from vector_precedents import PrecedentEngine

load_dotenv()

app = FastAPI(
    title="AgentCourt API",
    description="REST Gateway for AgentCourt Autonomous On-Chain Dispute Resolution on Base Sepolia",
    version="1.0.0"
)

PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
client = AgentCourtClient(private_key=PRIVATE_KEY) if PRIVATE_KEY else None
precedent_engine = PrecedentEngine()


class CreateTaskRequest(BaseModel):
    worker_address: str
    amount_usdc: int = 0
    spec_text: str


class CompleteTaskRequest(BaseModel):
    deliverable_text: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "network": "Base Sepolia",
        "contract": client.contract_address if client else None,
        "indexed_cases": precedent_engine.collection.count()
    }


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    if not client:
        raise HTTPException(status_code=500, detail="Signer client unconfigured.")
    try:
        return client.get_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/tasks")
def create_task(req: CreateTaskRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Signer client unconfigured.")
    try:
        task_id = client.create_task(req.worker_address, req.amount_usdc, req.spec_text)
        return {"task_id": task_id, "status": "Created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tasks/{task_id}/dispute")
def open_dispute(task_id: int):
    if not client:
        raise HTTPException(status_code=500, detail="Signer client unconfigured.")
    try:
        receipt = client.open_dispute(task_id)
        return {"task_id": task_id, "status": "Disputed", "receipt": receipt}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/precedents")
def search_precedents(query: str, limit: int = 3):
    results = precedent_engine.retrieve_precedents(query, top_k=limit) if hasattr(precedent_engine, "retrieve_precedents") else []
    return {"query": query, "precedents": results}
