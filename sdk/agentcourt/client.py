import json
import os
from web3 import Web3

DEFAULT_RPC = "https://base-sepolia-rpc.publicnode.com"
DEFAULT_ESCROW = "0x4a1629907Aa583E0f24EA66929f3D38410c66cf2"

class AgentCourtClient:
    def __init__(self, private_key: str, rpc_url: str = DEFAULT_RPC, contract_address: str = DEFAULT_ESCROW):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.contract_address = Web3.to_checksum_address(contract_address)
        
        abi_path = os.path.join(os.path.dirname(__file__), "abi.json")
        if not os.path.exists(abi_path):
            abi_path = "contracts/AgentEscrowV3_abi.json" if os.path.exists("contracts/AgentEscrowV3_abi.json") else "agentcourt/contracts/AgentEscrowV3_abi.json"
        
        with open(abi_path, "r") as f:
            abi = json.load(f)
            
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

    def _send_tx(self, func, value_wei: int = 0):
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = func.build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'value': value_wei,
            'gas': 300000,
            'maxFeePerGas': self.w3.to_wei(1.5, 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei(0.1, 'gwei'),
            'chainId': 84532
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def create_task(self, contractor: str, spec_uri: str, amount_eth: float, challenge_period: int = 3600) -> str:
        """Lock funds into escrow for a specific contractor task."""
        value_wei = self.w3.to_wei(amount_eth, 'ether')
        func = self.contract.functions.createTask(
            Web3.to_checksum_address(contractor),
            spec_uri,
            challenge_period
        )
        return self._send_tx(func, value_wei=value_wei)

    def submit_work(self, task_id: int) -> str:
        """Contractor marks the task as completed/submitted."""
        func = self.contract.functions.submitWork(task_id)
        return self._send_tx(func)

    def raise_dispute(self, task_id: int) -> str:
        """Trigger dispute resolution to convene the autonomous jury."""
        func = self.contract.functions.raiseDispute(task_id)
        return self._send_tx(func)

    def get_task(self, task_id: int) -> dict:
        """Fetch task details and current status from on-chain."""
        t = self.contract.functions.tasks(task_id).call()
        return {
            "id": t[0],
            "client": t[1],
            "contractor": t[2],
            "amount_wei": t[3],
            "amount_eth": float(Web3.from_wei(t[3], 'ether')),
            "spec_uri": t[4],
            "challenge_period": t[5],
            "status": t[6],
            "proposed_bps": t[7],
            "proposed_at": t[8],
            "ruling_uri": t[9]
        }
