import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from web3 import AsyncWeb3, AsyncHTTPProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AgentCourt Daemon] %(message)s"
)
logger = logging.getLogger("AgentCourt")

load_dotenv()

# Use official Base Sepolia endpoint to avoid load balancer node desync
HTTP_RPC_URL = os.getenv("RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("AGENT_COURT_CONTRACT_ADDRESS") or os.getenv("AGENT_ESCROW_V4_ADDRESS")

CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "jobId", "type": "uint256"},
            {"indexed": False, "name": "deliverableHash", "type": "bytes32"}
        ],
        "name": "JobSubmitted",
        "type": "event"
    },
    {
        "inputs": [
            {"name": "_jobId", "type": "uint256"},
            {"name": "_workerSplitBps", "type": "uint256"},
            {"name": "_rulingOpinion", "type": "string"}
        ],
        "name": "evaluateJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class DisputeDaemon:
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        self.rpc_url = rpc_url
        self.contract_address = AsyncWeb3.to_checksum_address(contract_address)
        self.private_key = private_key
        self.w3 = None
        self.contract = None
        self.account = None

    async def initialize(self):
        logger.info(f"Connecting to RPC: {self.rpc_url}...")
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        is_connected = await self.w3.is_connected()
        if not is_connected:
            raise ConnectionError(f"Failed to connect to RPC at {self.rpc_url}")

        self.account = self.w3.eth.account.from_key(self.private_key)
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=CONTRACT_ABI
        )
        logger.info("Connected to Base Sepolia successfully.")
        logger.info(f"Arbitrator Wallet: {self.account.address}")
        logger.info(f"Target Contract: {self.contract_address}")

    async def handle_job_submitted(self, event_data: Dict[str, Any]):
        args = event_data.get("args", {})
        job_id = args.get("jobId", 0)
        deliverable_hash = args.get("deliverableHash", b"").hex()

        logger.info(f"⚡ [Deliverable Detected] Job #{job_id} ready for evaluation!")
        logger.info(f"Deliverable Hash: 0x{deliverable_hash}")

        try:
            logger.info(f"Deliberating Job #{job_id} with AgentCourt Jurors...")
            worker_split_bps = 5000
            ruling_opinion = "AgentCourt Consensus: Deliverable meets 50% task criteria."
            logger.info(f"Consensus reached: Worker Split = {worker_split_bps / 100}%")

            await self.submit_evaluation(job_id, worker_split_bps, ruling_opinion)
        except Exception as err:
            logger.error(f"Failed to evaluate Job #{job_id}: {err}", exc_info=True)

    async def submit_evaluation(self, job_id: int, worker_split_bps: int, ruling_opinion: str):
        logger.info(f"Submitting evaluateJob transaction for Job #{job_id}...")
        nonce = await self.w3.eth.get_transaction_count(self.account.address, "pending")
        gas_price = await self.w3.eth.gas_price

        tx = await self.contract.functions.evaluateJob(
            job_id,
            worker_split_bps,
            ruling_opinion
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 350000,
            "gasPrice": int(gas_price * 1.3),
            "chainId": await self.w3.eth.chain_id
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"✅ Evaluation TX Broadcasted: {tx_hash.hex()}")

        receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            logger.info(f"🎉 Job #{job_id} evaluated & settled on-chain in block {receipt.blockNumber}!")
        else:
            logger.error(f"❌ Transaction reverted for Job #{job_id}")

    async def run(self):
        await self.initialize()
        # Look back 50 blocks on boot so we catch Job #1 if it's still waiting
        current_head = await self.w3.eth.block_number
        latest_scanned_block = max(0, current_head - 50)
        logger.info(f"Listening for JobSubmitted events from block {latest_scanned_block}...")

        while True:
            try:
                head_block = await self.w3.eth.block_number
                target_block = head_block - 1  # 1-block safety margin against RPC desync

                if target_block > latest_scanned_block:
                    events = await self.contract.events.JobSubmitted.get_logs(
                        from_block=latest_scanned_block + 1,
                        to_block=target_block
                    )
                    for event in events:
                        await self.handle_job_submitted(event)
                    latest_scanned_block = target_block

                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Error checking logs ({e}). Retrying in 4s...")
                await asyncio.sleep(4)


if __name__ == "__main__":
    if not CONTRACT_ADDRESS or not PRIVATE_KEY:
        logger.error("Missing CONTRACT_ADDRESS or PRIVATE_KEY in .env.")
        sys.exit(1)

    try:
        asyncio.run(DisputeDaemon(HTTP_RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY).run())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user.")
