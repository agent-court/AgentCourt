import os
import time
from typing import Optional, Dict, Any
from web3 import Web3

DEFAULT_RPC_URL = "https://base-sepolia-rpc.publicnode.com"
DEFAULT_CONTRACT_ADDRESS = "0x541521A9a0eb01e4E395F4c43dd8Fe42d89eB723"

DEFAULT_ABI = [
    {"inputs":[{"internalType":"address","name":"worker","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"specHash","type":"bytes32"}],"name":"createTask","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"taskId","type":"uint256"}],"name":"fundTask","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"taskId","type":"uint256"}],"name":"startTask","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"taskId","type":"uint256"},{"internalType":"bytes32","name":"deliverableHash","type":"bytes32"}],"name":"completeTask","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"taskId","type":"uint256"}],"name":"openDispute","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"taskId","type":"uint256"},{"internalType":"uint256","name":"workerBps","type":"uint256"},{"internalType":"bytes32","name":"verdictHash","type":"bytes32"}],"name":"resolveDispute","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"tasks","outputs":[{"internalType":"uint256","name":"taskId","type":"uint256"},{"internalType":"address","name":"client","type":"address"},{"internalType":"address","name":"worker","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"bytes32","name":"specHash","type":"bytes32"},{"internalType":"bytes32","name":"deliverableHash","type":"bytes32"},{"internalType":"uint8","name":"state","type":"uint8"},{"internalType":"uint256","name":"workerBps","type":"uint256"},{"internalType":"bytes32","name":"verdictHash","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"taskCounter","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

class AgentCourtClient:
    def __init__(
        self,
        private_key: str,
        contract_address: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL", DEFAULT_RPC_URL)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.contract_address = self.w3.to_checksum_address(
            contract_address or os.getenv("ESCROW_CONTRACT_ADDRESS", DEFAULT_CONTRACT_ADDRESS)
        )
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=DEFAULT_ABI)
        self._current_nonce = None

    def _get_nonce(self) -> int:
        onchain_nonce = self.w3.eth.get_transaction_count(self.account.address, "pending")
        if self._current_nonce is None or onchain_nonce > self._current_nonce:
            self._current_nonce = onchain_nonce
        else:
            self._current_nonce += 1
        return self._current_nonce

    def _send_tx(self, fn_call, gas: int = 350000, retries: int = 3) -> Dict[str, Any]:
        for attempt in range(retries):
            try:
                nonce = self._get_nonce()
                tx = fn_call.build_transaction({
                    "from": self.account.address,
                    "nonce": nonce,
                    "gas": gas,
                    "gasPrice": int(self.w3.eth.gas_price * 1.2),
                    "chainId": self.w3.eth.chain_id,
                })
                signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                return {"status": receipt.status, "tx_hash": tx_hash.hex(), "blockNumber": receipt.blockNumber}
            except Exception as e:
                err_msg = str(e).lower()
                if "nonce" in err_msg and attempt < retries - 1:
                    time.sleep(1.5)
                    self._current_nonce = self.w3.eth.get_transaction_count(self.account.address, "latest")
                    continue
                raise e

    def create_task(self, worker_address: str, amount_usdc: int, spec_text: str) -> int:
        spec_hash = Web3.keccak(text=spec_text)
        worker = self.w3.to_checksum_address(worker_address)
        self._send_tx(self.contract.functions.createTask(worker, amount_usdc, spec_hash))
        return self.contract.functions.taskCounter().call()

    def fund_task(self, task_id: int) -> Dict[str, Any]:
        return self._send_tx(self.contract.functions.fundTask(task_id))

    def start_task(self, task_id: int) -> Dict[str, Any]:
        return self._send_tx(self.contract.functions.startTask(task_id))

    def complete_task(self, task_id: int, deliverable_text: str) -> Dict[str, Any]:
        deliv_hash = Web3.keccak(text=deliverable_text)
        return self._send_tx(self.contract.functions.completeTask(task_id, deliv_hash))

    def open_dispute(self, task_id: int) -> Dict[str, Any]:
        return self._send_tx(self.contract.functions.openDispute(task_id))

    def get_task(self, task_id: int) -> Dict[str, Any]:
        t = self.contract.functions.tasks(task_id).call()
        states = ["Created", "Funded", "Started", "Completed", "Disputed", "Settled"]
        return {
            "task_id": t[0],
            "client": t[1],
            "worker": t[2],
            "amount": t[3],
            "spec_hash": "0x" + t[4].hex(),
            "deliverable_hash": "0x" + t[5].hex(),
            "state": states[t[6]] if t[6] < len(states) else "Unknown",
            "worker_bps": t[7],
            "verdict_hash": "0x" + t[8].hex(),
        }
