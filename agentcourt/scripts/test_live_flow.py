import os
import json
import time
from web3 import Web3
from eth_account import Account

def run_test():
    print("========================================================")
    print("🚀 RUNNING LIVE END-TO-END TEST ON BASE SEPOLIA")
    print("========================================================")

    rpc_url = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
    contract_address = os.getenv("ESCROW_V3_ADDRESS")
    priv_key = os.getenv("DEPLOYER_PRIVATE_KEY")

    if not contract_address or not priv_key:
        print("❌ Error: Missing ESCROW_V3_ADDRESS or DEPLOYER_PRIVATE_KEY in environment.")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(priv_key)
    contractor_dummy = Account.create().address

    print(f"🌐 Connected to RPC : {rpc_url}")
    print(f"🔑 Client / Court   : {account.address}")
    print(f"👷 Contractor Mock  : {contractor_dummy}")
    print(f"⚖️ Escrow V3 Address : {contract_address}")

    # Load ABI
    artifact_path = "contracts/AgentEscrowV3_abi.json"
    if not os.path.exists(artifact_path):
        artifact_path = "agentcourt/contracts/AgentEscrowV3_abi.json"
    
    with open(artifact_path, "r") as f:
        abi = json.load(f)

    contract = w3.eth.contract(address=contract_address, abi=abi)

    # 1. Create a Task
    print("\n📝 1. Creating on-chain task with 0.0001 ETH escrow...")
    tx = contract.functions.createTask(
        contractor_dummy,
        "ipfs://test-task-spec-summary",
        3600
    ).build_transaction({
        "from": account.address,
        "value": Web3.to_wei(0.0001, "ether"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, priv_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"⏳ Waiting for task creation (TX: {tx_hash.hex()})...")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    task_id = contract.functions.taskCounter().call()
    print(f"✅ Task #{task_id} Created Successfully! (Status: Active)")

    # 2. Raise Dispute with Reason
    print(f"\n⚠️ 2. Raising dispute on Task #{task_id}...")
    dispute_reason = "ipfs://dispute-evidence-deliverable-incomplete"
    tx_disp = contract.functions.raiseDispute(task_id, dispute_reason).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price
    })
    signed_disp = w3.eth.account.sign_transaction(tx_disp, priv_key)
    tx_disp_hash = w3.eth.send_raw_transaction(signed_disp.raw_transaction)
    print(f"⏳ Waiting for dispute transaction (TX: {tx_disp_hash.hex()})...")
    w3.eth.wait_for_transaction_receipt(tx_disp_hash)
    print(f"✅ Task #{task_id} is now in DISPUTED status!")

    # 3. Simulate Court Proposing Ruling (5000 bps Client Split = 50%)
    print(f"\n⚖️ 3. Broadcasting AgentCourt Ruling Proposal (5000 bps to Client / 5000 bps to Contractor)...")
    ruling_bps = 5000
    ruling_uri = "ipfs://bafybeirulingverdicthash5050split"
    
    tx_propose = contract.functions.proposeRuling(
        task_id,
        ruling_bps,
        ruling_uri
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price
    })
    signed_propose = w3.eth.account.sign_transaction(tx_propose, priv_key)
    tx_prop_hash = w3.eth.send_raw_transaction(signed_propose.raw_transaction)
    print(f"⏳ Broadcasting Court Ruling (TX: {tx_prop_hash.hex()})...")
    w3.eth.wait_for_transaction_receipt(tx_prop_hash)

    print(f"\n🎉 Task #{task_id} Ruling Successfully Proposed on Base Sepolia!")
    print(f"🔍 Basescan TX: https://sepolia.basescan.org/tx/{tx_prop_hash.hex()}")
    print(f"📋 Contract on Basescan: https://sepolia.basescan.org/address/{contract_address}")

if __name__ == "__main__":
    run_test()
