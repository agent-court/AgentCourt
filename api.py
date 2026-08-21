from content_store import get_spec_by_hash, get_deliverable_by_hash
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from dotenv import load_dotenv

from resolver import save_local_payload, resolve_payload, pin_json_to_ipfs
from jurors import deliberate_job

load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
logger = logging.getLogger("AgentCourt.API")

# Web3 Configuration
RPC_URL = os.getenv("RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("AGENT_COURT_CONTRACT_ADDRESS") or os.getenv("AGENT_ESCROW_V4_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY) if PRIVATE_KEY else None

with open("AgentEscrowV4.json", "r") as f:
    raw_data = json.load(f)
    CONTRACT_ABI = raw_data.get("abi", raw_data)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI) if CONTRACT_ADDRESS else None


# WebSocket Connection Manager for live updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


# Background Task: Blockchain Event Listener
async def blockchain_listener_loop():
    logger.info("Starting background on-chain listener loop...")
    latest_block = w3.eth.block_number
    processed_jobs = set()

    while True:
        try:
            current_block = w3.eth.block_number
            if current_block >= latest_block:
                events = contract.events.JobSubmitted.get_logs(from_block=latest_block, to_block=current_block)
                for event in events:
                    job_id = event.args.jobId
                    deliverable_hash = event.args.deliverableHash.hex()

                    if job_id not in processed_jobs:
                        processed_jobs.add(job_id)
                        logger.info(f"⚡ [Event Detected] Job #{job_id} submitted. Broadcasting...")
                        
                        await manager.broadcast({
                            "type": "JOB_SUBMITTED",
                            "job_id": job_id,
                            "deliverable_hash": f"0x{deliverable_hash}",
                            "block_number": event.blockNumber
                        })

                        # Trigger autonomous deliberation in background
                        asyncio.create_task(run_autonomous_settlement(job_id, f"0x{deliverable_hash}"))

                latest_block = current_block + 1
        except Exception as e:
            # Handle standard Base Sepolia head synchronization race conditions
            if "-32602" in str(e) or "beyond current head" in str(e):
                pass
            else:
                logger.error(f"Listener error: {e}")

        await asyncio.sleep(4)


async def run_autonomous_settlement(job_id: int, deliverable_hash: str):
    try:
        await manager.broadcast({"type": "DELIBERATION_STARTED", "job_id": job_id})
        
        raw_deliv = get_deliverable_by_hash(deliverable_hash)
        try:
            job_data = contract.functions.jobs(job_id).call()
            spec_hex = job_data[7].hex() if hasattr(job_data[7], "hex") else str(job_data[7])
            raw_spec = get_spec_by_hash(spec_hex)
        except Exception:
            raw_spec = None
        
        logging.info(f"[AgentCourt.API] Resolved content for #{job_id} -> Spec: {bool(raw_spec)} | Code: {bool(raw_deliv)}")
        verdict = await deliberate_job(job_id, deliverable_hash, task_spec=raw_spec, deliverable_text=raw_deliv)
        
        await manager.broadcast({
            "type": "CONSENSUS_REACHED",
            "job_id": job_id,
            "verdict": verdict
        })

        # Submit on-chain settlement if arbitrator wallet is available
        if account and contract:
            nonce = w3.eth.get_transaction_count(account.address, "pending")
            gas_price = int(w3.eth.gas_price * 1.3)
            
            tx = contract.functions.evaluateJob(
                job_id,
                verdict["consensus_bps"],
                verdict["opinion"]
            ).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "chainId": w3.eth.chain_id
            })

            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info(f"Settlement TX sent for Job #{job_id}: {tx_hash.hex()}")
            
            await manager.broadcast({
                "type": "SETTLEMENT_BROADCASTED",
                "job_id": job_id,
                "tx_hash": tx_hash.hex()
            })
            
            receipt = await asyncio.to_thread(w3.eth.wait_for_transaction_receipt, tx_hash, timeout=60)
            
            await manager.broadcast({
                "type": "SETTLEMENT_CONFIRMED",
                "job_id": job_id,
                "block_number": receipt.blockNumber,
                "status": receipt.status
            })
            logger.info(f"🎉 Job #{job_id} successfully settled in block {receipt.blockNumber}!")
    except Exception as e:
        logger.error(f"Settlement failed for Job #{job_id}: {e}")
        await manager.broadcast({"type": "SETTLEMENT_ERROR", "job_id": job_id, "error": str(e)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background listener on server startup
    listener_task = asyncio.create_task(blockchain_listener_loop())
    yield
    listener_task.cancel()


# FastAPI Application
app = FastAPI(
    title="AgentCourt API & Oracle Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Schemas
class CreateMetadataRequest(BaseModel):
    task_specification: str
    deliverable_content: str
    criteria: Optional[str] = "Evaluate completeness and adherence to requirements."


class ManualDeliberateRequest(BaseModel):
    job_id: int
    deliverable_hash: str


# REST Endpoints
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "contract": CONTRACT_ADDRESS,
        "arbitrator": account.address if account else None,
        "network": "Base Sepolia"
    }


@app.get("/jobs")
def list_jobs():
    if not contract:
        raise HTTPException(status_code=500, detail="Contract not configured")
    try:
        count = contract.functions.jobCount().call()
        jobs = []
        for i in range(1, count + 1):
            job_data = contract.functions.jobs(i).call()
            jobs.append({
                "job_id": job_data[0],
                "client": job_data[1],
                "provider": job_data[2],
                "evaluator": job_data[3],
                "status": job_data[4],
                "escrow_amount_wei": str(job_data[5]),
                "deliverable_hash": f"0x{job_data[7].hex()}" if len(job_data) > 7 else "N/A"
            })
        return {"total_jobs": count, "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/metadata/store")
async def store_metadata(payload: CreateMetadataRequest):
    data_dict = payload.model_dump()
    raw_content = json.dumps(data_dict, sort_keys=True)
    computed_hash = Web3.keccak(text=raw_content).hex()
    
    # 1. Save local backup cache
    save_local_payload(computed_hash, data_dict)
    
    # 2. Pin to Pinata IPFS
    ipfs_uri = await pin_json_to_ipfs(data_dict, name=f"AgentCourt_Job_{computed_hash[:8]}")
    
    return {
        "deliverable_hash": f"0x{computed_hash}",
        "ipfs_uri": ipfs_uri or "ipfs://local-fallback",
        "payload": data_dict
    }


@app.post("/deliberate")
async def trigger_deliberation(req: ManualDeliberateRequest):
    verdict = await deliberate_job(req.job_id, req.deliverable_hash)
    return verdict


# WebSocket Stream Endpoint
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
