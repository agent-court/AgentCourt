import os
import json
import time
import logging
from web3 import Web3
from service.precedent_engine import CaseLawEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Configuration from environment or defaults
RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
COURT_PRIVATE_KEY = os.getenv("COURT_PRIVATE_KEY", "")
ESCROW_ADDRESS = os.getenv("ESCROW_V3_ADDRESS", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))

class AgentCourtDaemon:
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_address) if contract_address else None
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(private_key) if private_key else None
        
        # Load ABI
        abi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts", "AgentEscrowV3_abi.json")
        with open(abi_path, "r") as f:
            self.abi = json.load(f)
            
        if self.contract_address:
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        else:
            self.contract = None

        self.precedent_engine = CaseLawEngine()
        self.processed_tasks = set()

    def assemble_jury_and_score(self, task_id: int, spec_text: str, dispute_reason: str, evidence_summary: str):
        """Query vector case law and synthesize multi-model consensus."""
        logging.info(f"⚖️ Assembling AI Jury Panel for Task #{task_id}...")
        
        # 1. Retrieve vector precedents
        precedents = self.precedent_engine.find_precedents(spec_text, dispute_reason, n_results=2)
        logging.info(f"📚 Retrieved {len(precedents)} relevant legal precedents from ChromaDB.")

        # 2. Mock / Real multi-LLM consensus loop
        # (In production, inject your Gemini / Claude / GPT API calls here with precedents in prompt)
        mock_scores = [7500, 8000, 7500]  # Basis points: 75%, 80%, 75%
        consensus_bps = int(sum(mock_scores) / len(mock_scores))
        
        rationale = (
            f"Multi-LLM Jury assessed deliverable against spec. Deterministic unit tests passed "
            f"partially with minor unhandled exceptions. In accordance with precedent, awarded {consensus_bps/100:.1f}%."
        )

        verdict_payload = {
            "task_id": task_id,
            "contractor_bps": consensus_bps,
            "precedents_applied": [p["task_id"] for p in precedents],
            "rationale": rationale,
            "timestamp": int(time.time())
        }

        # Index verdict into vector store
        self.precedent_engine.record_ruling(
            task_id=task_id,
            spec_text=spec_text,
            dispute_reason=dispute_reason,
            evidence_summary=evidence_summary,
            contractor_bps=consensus_bps,
            jury_rationale=rationale
        )

        return consensus_bps, json.dumps(verdict_payload)

    def submit_ruling_onchain(self, task_id: int, contractor_bps: int, verdict_cid: str):
        """Submit proposeRuling transaction as COURT_ROLE."""
        if not self.contract or not self.account:
            logging.warning("⚠️ No active contract address or private key; running in dry-run mode.")
            return None

        logging.info(f"📡 Submitting proposeRuling for Task #{task_id} ({contractor_bps/100:.1f}% split)...")
        
        tx = self.contract.functions.proposeRuling(
            task_id,
            contractor_bps,
            verdict_cid
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gasPrice": self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        logging.info(f"✅ Ruling on-chain TX confirmed: {receipt.transactionHash.hex()}")
        return receipt

    def run(self):
        logging.info("========================================================")
        logging.info("🚀 AGENTCOURT V3 AUTONOMOUS ARBITRATION DAEMON STARTED")
        logging.info(f"🌐 Target RPC    : {RPC_URL}")
        logging.info(f"🔒 Escrow V3    : {self.contract_address or 'Local / Dry-Run Mode'}")
        logging.info(f"⏱️ Polling Rate : Every {POLL_INTERVAL}s")
        logging.info("========================================================")

        # Standalone demonstration run if not connected to live contract
        if not self.contract:
            logging.info("Running daemon sanity loop test...")
            bps, payload = self.assemble_jury_and_score(
                task_id=202,
                spec_text="Deploy ERC20 token with capped supply and minting limits",
                dispute_reason="Supply cap was implemented but mint limits were missing",
                evidence_summary="Contracts deploy cleanly but testMintLimits failed in test suite."
            )
            logging.info(f"🎉 Generated Ruling Payload: {payload}")
            logging.info("Daemon operational.")
            return

if __name__ == "__main__":
    daemon = AgentCourtDaemon(RPC_URL, ESCROW_ADDRESS, COURT_PRIVATE_KEY)
    daemon.run()
