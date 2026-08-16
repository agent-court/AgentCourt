import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import agent
import arbitrator
import precedent_db

app = FastAPI(
    title="AgentCourt Autonomous Dispute Network",
    description="Decentralized escrow and AI-arbitration network for autonomous agent labor on Base.",
    version="2.0.0"
)

class CreateTaskRequest(BaseModel):
    worker_address: str
    task_spec: str
    amount_usd: float = 1.00
    duration_seconds: int = 3600

class SubmitTaskRequest(BaseModel):
    task_id: int
    deliverable: str

class ResolveTaskRequest(BaseModel):
    task_id: int
    task_spec: str
    deliverable: str

class QueryPrecedentRequest(BaseModel):
    task_spec: str
    deliverable: str
    limit: int = 2

@app.get("/")
def root():
    with open("treasury_address.txt") as f:
        treasury_addr = f.read().strip()
    return {
        "network": "Base Sepolia (Chain ID: 84532)",
        "escrow_contract": agent.ESCROW_ADDRESS,
        "treasury": treasury_addr,
        "fee_bps": 150,
        "status": "online"
    }

@app.post("/tasks/create")
def create_task(req: CreateTaskRequest):
    try:
        task_id = agent.create_task_usdc(
            worker_addr=req.worker_address,
            details_hash=req.task_spec,
            amount_usd=req.amount_usd,
            duration_seconds=req.duration_seconds
        )
        return {
            "status": "success",
            "task_id": task_id,
            "escrow_amount_usd": req.amount_usd,
            "worker": req.worker_address
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/submit")
def submit_task(req: SubmitTaskRequest):
    try:
        agent.submit_task(req.task_id, req.deliverable)
        return {
            "status": "success",
            "task_id": req.task_id,
            "message": "Deliverable submitted on-chain by worker"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/resolve")
def resolve_task(req: ResolveTaskRequest):
    try:
        ruling = arbitrator.arbitrate_task(req.task_spec, req.deliverable)
        client_share = ruling["client_share_pct"]
        worker_share = ruling["worker_share_pct"]

        func = agent.escrow_contract.functions.resolveTask(req.task_id, client_share)
        tx = agent.build_tx_with_gas(func, agent.CLIENT_ADDR, fallback_gas=350000)
        tx_hash, receipt = agent.send_and_wait(tx, agent.PRIVATE_KEY)

        precedent_db.store_precedent(
            task_id=req.task_id,
            spec=req.task_spec,
            deliverable=req.deliverable,
            client_share=client_share,
            worker_share=worker_share,
            opinion=ruling["court_opinion"],
            category="api_settlement"
        )

        return {
            "status": "resolved",
            "task_id": req.task_id,
            "tx_hash": tx_hash.hex(),
            "ruling": {
                "spec_adherence": ruling["spec_adherence"],
                "code_quality": ruling["code_quality"],
                "client_share_pct": client_share,
                "worker_share_pct": worker_share,
                "court_opinion": ruling["court_opinion"],
                "provider": ruling["provider"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/precedents/query")
def query_precedents(req: QueryPrecedentRequest):
    try:
        results = precedent_db.query_relevant_precedents(req.task_spec, req.deliverable, n_results=req.limit)
        return {"count": len(results), "precedents": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
