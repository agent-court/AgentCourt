import json
import os
import time
from dotenv import load_dotenv
from web3 import Web3

load_dotenv(override=True)

PRIVATE_KEY = os.getenv("PRIVATE_KEY", "").strip()
RPC_URL = os.getenv("RPC_URL", "https://base-sepolia-rpc.publicnode.com").strip()

if not PRIVATE_KEY:
    print("❌ Error: PRIVATE_KEY missing in .env")
    exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("❌ Failed to connect to Base Sepolia RPC.")
    exit(1)

# Helper for raw tx bytes across web3 versions
def get_raw_tx(signed_tx):
    return getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))

account = w3.eth.account.from_key(PRIVATE_KEY)
deployer_address = account.address
chain_id = 84532

print(f"📡 Connected to: {RPC_URL}")
print(f"🔑 Deployer Address: {deployer_address}")
print(f"💰 Balance: {w3.eth.get_balance(deployer_address) / 10**18:.6f} ETH")

# 1. Load USDC address (constructor arg for AgentCourtEscrow)
with open("usdc_address.txt") as f:
    usdc_address = w3.to_checksum_address(f.read().strip())

# 2. Load Escrow ABI and Bytecode
with open("contract_abi.json") as f:
    escrow_abi = json.load(f)

with open("contract_bytecode.bin") as f:
    escrow_bytecode = f.read().strip()
    if not escrow_bytecode.startswith("0x"):
        escrow_bytecode = "0x" + escrow_bytecode

ContractFactory = w3.eth.contract(abi=escrow_abi, bytecode=escrow_bytecode)

print("\n🚀 Building deployment transaction for AgentCourtEscrow...")

nonce = w3.eth.get_transaction_count(deployer_address, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_priority_fee = w3.to_wei("0.1", "gwei")
max_fee = base_fee * 2 + max_priority_fee

# Constructor takes: (_usdcToken, _protocolFeeRecipient)
construct_tx = ContractFactory.constructor(usdc_address, deployer_address).build_transaction({
    "from": deployer_address,
    "nonce": nonce,
    "chainId": chain_id,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": max_priority_fee,
    "type": 2,
})

signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=PRIVATE_KEY)
raw_tx = get_raw_tx(signed_tx)

print("📡 Broadcasting deployment transaction to Base Sepolia...")
tx_hash = w3.eth.send_raw_transaction(raw_tx)
print(f"⏳ Tx Hash: {tx_hash.hex()} (Waiting for confirmation...)")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

if receipt.status == 1:
    new_contract_addr = receipt.contractAddress
    print(f"\n✅ Contract Deployed Successfully!")
    print(f"🎯 Contract Address: {new_contract_addr}")
    
    with open("contract_address.txt", "w") as f:
        f.write(new_contract_addr)
    print("💾 Saved new address to contract_address.txt!")
else:
    print(f"❌ Deployment failed on-chain! Status: {receipt.status}")