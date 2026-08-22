import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
USDC_SEPOLIA = os.getenv("USDC_SEPOLIA_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e") # Base Sepolia USDC

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def deploy_escrow_v5():
    if not PRIVATE_KEY:
        print("❌ Error: PRIVATE_KEY is missing in .env")
        return

    account = w3.eth.account.from_key(PRIVATE_KEY)
    balance = w3.eth.get_balance(account.address)
    print(f"🔑 Deployer: {account.address}")
    print(f"💰 Balance: {w3.from_wei(balance, 'ether')} ETH")

    if balance == 0:
        print("❌ Cannot deploy with 0 balance. Please fund the wallet with Base Sepolia testnet ETH.")
        return

    # Check for compiled artifact or source
    abi_path = ROOT_DIR / "contracts" / "escrow_abi.json"
    if not abi_path.exists():
        print("❌ Missing contracts/escrow_abi.json")
        return

    with open(abi_path, "r") as f:
        artifact = json.load(f)

    abi = artifact if isinstance(artifact, list) else artifact.get("abi", [])
    bytecode = artifact.get("bytecode", "") if isinstance(artifact, dict) else ""

    if not bytecode:
        print("⚠️ Bytecode not embedded in escrow_abi.json. Checking for compiled artifacts...")
        # Solc or Hardhat artifact fallback can be linked here
        return

    print("🚀 Broadcasting deployment transaction for AgentEscrowV5...")
    Escrow = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Escrow.constructor(USDC_SEPOLIA, account.address).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"⏳ Deployment Tx Sent: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ AgentEscrowV5 Deployed to: {receipt.contractAddress}")
    print(f"🔗 View on BaseScan: https://sepolia.basescan.org/address/{receipt.contractAddress}")

if __name__ == "__main__":
    deploy_escrow_v5()
