import os
import json
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("AGENT_COURT_CONTRACT_ADDRESS") or os.getenv("AGENT_ESCROW_V4_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("AgentEscrowV4.json", "r") as f:
    raw_data = json.load(f)
    CONTRACT_ABI = raw_data.get("abi", raw_data)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def send_tx(tx_data, desc):
    print(f"{desc} (Nonce: {tx_data['nonce']})...")
    signed = account.sign_transaction(tx_data)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Broadcasted: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if receipt.status != 1:
        raise RuntimeError(f"Transaction reverted on-chain for {desc} (Tx: {tx_hash.hex()})")
    print(f"Confirmed in block {receipt.blockNumber}!")
    return receipt


def main():
    print(f"Using Account: {account.address}")
    
    # 1. Prepare Metadata & Hash
    sample_payload = {
        "task_title": "Production Oracle Dispute",
        "task_specification": "Build a secure Uniswap V3 execution bot with custom MEV protection.",
        "deliverable_content": "def execute_trade():\n    # Integrated private RPC & MEV-Boost\n    return {'status': 'success', 'slippage_bps': 15}",
        "criteria": "Award 9000-10000 bps if private routing is correctly structured."
    }
    
    raw_content = json.dumps(sample_payload, sort_keys=True)
    metadata_hash = Web3.keccak(text=raw_content)

    # Cache locally for resolver
    cache_dir = os.path.join(os.path.dirname(__file__), ".court_metadata_cache")
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, f"{metadata_hash.hex()[2:].lower()}.json"), "w") as f:
        json.dump(sample_payload, f, indent=2)

    escrow_wei = Web3.to_wei(0.0001, "ether")
    gas_price = int(w3.eth.gas_price * 1.3)

    # 2. createJob (Non-payable, value must be 0)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    create_tx = contract.functions.createJob(
        account.address,  # provider
        account.address,  # evaluator / oracle
        escrow_wei,       # amount
        metadata_hash     # metadataHash
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    })
    send_tx(create_tx, "Creating Job")

    # Get newly created Job ID
    job_id = contract.functions.jobCount().call()
    print(f"Created Job #{job_id}")

    # 3. fundJob (Payable with escrow ETH)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    fund_tx = contract.functions.fundJob(job_id).build_transaction({
        "from": account.address,
        "value": escrow_wei,
        "nonce": nonce,
        "gas": 200000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    })
    send_tx(fund_tx, f"Funding Job #{job_id}")

    # 4. submitDeliverable (Triggers JobSubmitted event)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    submit_tx = contract.functions.submitDeliverable(
        job_id,
        metadata_hash
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 250000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id
    })
    send_tx(submit_tx, f"Submitting Deliverable for Job #{job_id}")

    print(f"\n🚀 Job #{job_id} successfully created, funded, and submitted! Monitoring API oracle...")


if __name__ == "__main__":
    main()
