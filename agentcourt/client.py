import os
import json
from typing import Dict, Any, Optional
from web3 import Web3
from .arbitrator import arbitrate_task
from .vector_precedents import find_relevant_precedents

class AgentCourtClient:
    """Drop-in SDK for AI agents to evaluate deliverables and arbitrate escrow disputes on Base."""

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        contract_address: str = "0x0233B2B49788204ddd00Fb39508b944aC3904F71"
    ):
        self.rpc_url = rpc_url or os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self.contract_address = contract_address
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, "AgentEscrowV4.json"), "r") as f:
            data = json.load(f)
        self.abi = data["abi"]
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)

    def evaluate(self, task_spec: str, evidence: str) -> Dict[str, Any]:
        """Runs the multi-juror consensus engine using semantic precedents."""
        return arbitrate_task(task_spec, evidence)

    def resolve_onchain(self, job_id: int, task_spec: str, evidence: str) -> str:
        """Evaluates off-chain and executes the basis-point settlement on Base."""
        if not self.private_key:
            raise ValueError("Private key required for on-chain resolution.")
            
        ruling = self.evaluate(task_spec, evidence)
        worker_split_bps = int(ruling.get("worker_share_pct", 50) * 100)
        opinion = ruling.get("court_opinion", "Settled via AgentCourt SDK.")[:500]

        account = self.w3.eth.account.from_key(self.private_key)
        tx = self.contract.functions.evaluateJob(
            job_id,
            worker_split_bps,
            opinion
        ).build_transaction({
            "from": account.address,
            "nonce": self.w3.eth.get_transaction_count(account.address),
            "gasPrice": self.w3.eth.gas_price
        })

        signed = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()
