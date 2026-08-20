import os
import sys
import json
import time
from dotenv import load_dotenv
from web3 import Web3
from resolver import save_local_payload

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("AGENT_COURT_CONTRACT_ADDRESS") or os.getenv("AGENT_ESCROW_V4_ADDRESS")

if not CONTRACT_ADDRESS or not PRIVATE_KEY:
    print("Error: Missing CONTRACT_ADDRESS or PRIVATE_KEY in .env")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("AgentEscrowV4.json", "r") as f:
    raw_data = json.load(f)
    ABI = raw_data.get("abi", raw_data)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

SAMPLE_SCENARIO = {
    "task_specification": (
        "Build a Python script that connects to Uniswap V3 on Base and executes a token swap. "
        "Must include dynamic slippage calculation and robust error handling."
    ),
    "deliverable_content": (
        "def swap_tokens(token_in, token_out, amount):\n"
        "    # Connects to Uniswap V3 router on Base\n"
        "    router = web3.eth.contract(address=UNISWAP_ROUTER, abi=ROUTER_ABI)\n"
        "    # Hardcoded slippage set to 0.5%\n"
        "    amount_out_min = int(amount * 0.995)\n"
        "    return router.functions.exactInputSingle(...).transact()\n"
    ),
    "criteria": (
        "Full payout (10000 bps) if code runs and meets all requirements. "
        "Deduct 2000-3000 bps if slippage calculation is hardcoded instead of dynamic."
    )
}


def send_tx(tx_dict, desc):
    print(f"{desc} (Nonce: {tx_dict['nonce']})...")
    signed_tx = account.sign_transaction(tx_dict)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Broadcasted: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if receipt.status != 1:
        raise RuntimeError(f"Transaction reverted on-chain for {desc} (Tx: {tx_hash.hex()})")
    print(f"Confirmed in block {receipt.blockNumber}!")
    return receipt


def main():
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    gas_price = int(w3.eth.gas_price * 1.3)
    chain_id = w3.eth.chain_id

    # 1. Create unique deliverable payload & hash
    raw_content = json.dumps(SAMPLE_SCENARIO, sort_keys=True) + str(time.time())
    deliverable_hash = Web3.keccak(text=raw_content)
    hex_hash = deliverable_hash.hex()
    
    # Store locally in cache resolver
    save_local_payload(hex_hash, SAMPLE_SCENARIO)

    # Generate task hash and 7-day expiry
    task_hash = Web3.keccak(text=SAMPLE_SCENARIO["task_specification"])
    expiry = int(time.time()) + 86400 * 7

    # 2. createJob with account.address as provider so this key can submit the deliverable
    create_tx = contract.functions.createJob(
        account.address,
        account.address,
        expiry,
        task_hash
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": gas_price,
        "chainId": chain_id
    })
    send_tx(create_tx, "Creating Job")
    nonce += 1

    job_id = contract.functions.jobCount().call()
    print(f"Created Job #{job_id}")

    # 3. fundJob
    fund_tx = contract.functions.fundJob(job_id).build_transaction({
        "from": account.address,
        "value": Web3.to_wei(0.0001, "ether"),
        "nonce": nonce,
        "gas": 150000,
        "gasPrice": gas_price,
        "chainId": chain_id
    })
    send_tx(fund_tx, f"Funding Job #{job_id}")
    nonce += 1

    # 4. submitDeliverable
    submit_tx = contract.functions.submitDeliverable(job_id, deliverable_hash).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 150000,
        "gasPrice": gas_price,
        "chainId": chain_id
    })
    send_tx(submit_tx, f"Submitting Deliverable for Job #{job_id}")


if __name__ == "__main__":
    main()
