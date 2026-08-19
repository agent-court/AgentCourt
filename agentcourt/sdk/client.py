import json
import os
from web3 import Web3

class AgentCourtClient:
    """Python SDK for interacting with AgentEscrowV3 on Base."""

    def __init__(self, rpc_url: str = "https://mainnet.base.org", contract_address: str = None, private_key: str = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_address) if contract_address else None
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(private_key) if private_key else None

        # Load compiled ABI
        abi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts", "AgentEscrowV3_abi.json")
        if os.path.exists(abi_path):
            with open(abi_path, "r") as f:
                self.abi = json.load(f)
        else:
            self.abi = []

        if self.contract_address and self.abi:
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        else:
            self.contract = None

    def create_task(self, contractor_address: str, amount_eth: float, spec_hash: str, challenge_period_hours: int = 24):
        """Create an escrow task with specifications and a challenge window."""
        if not self.contract or not self.account:
            raise ValueError("Client requires contract address and private key to send transactions.")

        contractor = Web3.to_checksum_address(contractor_address)
        amount_wei = Web3.to_wei(amount_eth, "ether")
        challenge_seconds = int(challenge_period_hours * 3600)

        tx = self.contract.functions.createTask(
            contractor,
            spec_hash,
            challenge_seconds
        ).build_transaction({
            "from": self.account.address,
            "value": amount_wei,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gasPrice": self.w3.eth.gas_price
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def raise_dispute(self, task_id: int, evidence_cid: str):
        """Raise a dispute with an IPFS CID containing logs and test evidence."""
        if not self.contract or not self.account:
            raise ValueError("Client requires contract address and private key to send transactions.")

        tx = self.contract.functions.raiseDispute(
            task_id,
            evidence_cid
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gasPrice": self.w3.eth.gas_price
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()

    def complete_task(self, task_id: int):
        """Client completes task and releases 100% of escrow funds without arbitration."""
        if not self.contract or not self.account:
            raise ValueError("Client requires contract address and private key to send transactions.")

        tx = self.contract.functions.completeTask(task_id).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gasPrice": self.w3.eth.gas_price
        })

        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.transactionHash.hex()
