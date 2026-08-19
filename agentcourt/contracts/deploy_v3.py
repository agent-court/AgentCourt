import json
import os
import sys
from web3 import Web3

RPC_URL = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")
COURT_ADDRESS = os.getenv("COURT_ADDRESS", "")

def deploy():
    if not PRIVATE_KEY:
        print("❌ Error: DEPLOYER_PRIVATE_KEY environment variable is not set.")
        print("Set it using: export DEPLOYER_PRIVATE_KEY='your_private_key'")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"❌ Error: Failed to connect to RPC at {RPC_URL}")
        sys.exit(1)

    account = w3.eth.account.from_key(PRIVATE_KEY)
    admin_address = account.address
    court_address = Web3.to_checksum_address(COURT_ADDRESS) if COURT_ADDRESS else admin_address

    print("========================================================")
    print("🚀 DEPLOYING AGENTESCROW V3 TO BASE")
    print(f"🌐 Target RPC        : {RPC_URL}")
    print(f"🔑 Deployer / Admin  : {admin_address}")
    print(f"⚖️ Court Role        : {court_address}")
    print(f"💰 Balance          : {w3.from_wei(w3.eth.get_balance(admin_address), 'ether')} ETH")
    print("========================================================")

    # Load ABI and Bytecode
    contracts_dir = os.path.dirname(os.path.abspath(__file__))
    abi_path = os.path.join(contracts_dir, "AgentEscrowV3_abi.json")
    bin_path = os.path.join(contracts_dir, "AgentEscrowV3_bytecode.bin")

    if not os.path.exists(abi_path) or not os.path.exists(bin_path):
        print("❌ Error: ABI or Bytecode missing. Run compile_v3.py first.")
        sys.exit(1)

    with open(abi_path, "r") as f:
        abi = json.load(f)
    with open(bin_path, "r") as f:
        bytecode = f.read()

    ContractFactory = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Build constructor transaction
    construct_tx = ContractFactory.constructor(admin_address, court_address).build_transaction({
        "from": admin_address,
        "nonce": w3.eth.get_transaction_count(admin_address),
        "gasPrice": w3.eth.gas_price
    })

    print("📡 Broadcasting deployment transaction...")
    signed_tx = w3.eth.account.sign_transaction(construct_tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"⏳ Waiting for confirmation (TX: {tx_hash.hex()})...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    contract_address = receipt.contractAddress
    print("\n🎉 Deployment Successful!")
    print(f"✅ Contract Address: {contract_address}")
    print(f"⛽ Gas Used        : {receipt.gasUsed}")
    print(f"🔍 Explorer Link   : https://sepolia.basescan.org/address/{contract_address}")

    # Save deployed address locally
    output_info = {
        "network": RPC_URL,
        "contract_address": contract_address,
        "admin": admin_address,
        "court": court_address,
        "tx_hash": tx_hash.hex()
    }
    with open(os.path.join(contracts_dir, "deployed_v3.json"), "w") as f:
        json.dump(output_info, f, indent=2)

if __name__ == "__main__":
    deploy()
