import json
import os
from typing import Dict, Any, Optional
from web3 import Web3

class AgentCourtClient:
    """
    Python SDK for interacting with AgentCourt V2 on Base Mainnet.
    Allows autonomous agents to fund escrows, submit deliverables, and resolve disputes.
    """
    
    BASE_MAINNET_RPC = "https://mainnet.base.org"
    USDC_BASE_MAINNET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

    ERC20_ABI = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"}
    ]

    def __init__(self, private_key: str, escrow_address: str, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or self.BASE_MAINNET_RPC
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        assert self.w3.is_connected(), f"Failed to connect to RPC: {self.rpc_url}"

        self.account = self.w3.eth.account.from_key(private_key)
        self.address = self.account.address
        self.private_key = private_key
        self.escrow_address = self.w3.to_checksum_address(escrow_address)

        abi_path = os.path.join(os.path.dirname(__file__), "..", "escrow_abi.json")
        if os.path.exists(abi_path):
            with open(abi_path, "r") as f:
                self.escrow_abi = json.load(f)
        else:
            self.escrow_abi = []

        self.escrow = self.w3.eth.contract(address=self.escrow_address, abi=self.escrow_abi)
        self.usdc = self.w3.eth.contract(address=self.w3.to_checksum_address(self.USDC_BASE_MAINNET), abi=self.ERC20_ABI)

    def get_usdc_balance(self, address: Optional[str] = None) -> float:
        """Returns USDC balance in units of dollars (e.g. 1.50 USDC)."""
        target = self.w3.to_checksum_address(address) if address else self.address
        raw_bal = self.usdc.functions.balanceOf(target).call()
        return raw_bal / 10**6

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """Fetches on-chain status of a specific task."""
        t = self.escrow.functions.tasks(task_id).call()
        status_map = {0: "Created", 1: "Submitted", 2: "Resolved"}
        return {
            "task_id": t[0],
            "client": t[1],
            "worker": t[2],
            "amount_usdc": t[3] / 10**6,
            "deliverable_spec": t[4],
            "status": status_map.get(t[6], "Unknown")
        }

    def get_total_tasks(self) -> int:
        """Returns total number of tasks created in escrow."""
        return self.escrow.functions.taskCount().call()
