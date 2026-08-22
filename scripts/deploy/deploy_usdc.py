import json
import os
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
    print("❌ Failed to connect to Base Sepolia.")
    exit(1)

def get_raw_tx(signed_tx):
    return getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))

account = w3.eth.account.from_key(PRIVATE_KEY)
deployer_address = account.address
chain_id = 84532

print(f"📡 Deploying fresh MockUSDC with wallet: {deployer_address}...")

with open("usdc_abi.json") as f:
    usdc_abi = json.load(f)

with open("usdc_bytecode.bin") as f:
    usdc_bytecode = f.read().strip()
    if not usdc_bytecode.startswith("0x"):
        usdc_bytecode = "0x" + usdc_bytecode

USDCFactory = w3.eth.contract(abi=usdc_abi, bytecode=usdc_bytecode)

nonce = w3.eth.get_transaction_count(deployer_address, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_priority_fee = w3.to_wei("0.1", "gwei")
max_fee = base_fee * 2 + max_priority_fee

construct_tx = USDCFactory.constructor().build_transaction({
    "from": deployer_address,
    "nonce": nonce,
    "chainId": chain_id,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": max_priority_fee,
    "type": 2,
})

signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed_tx))
print(f"⏳ Broadcasted Tx: {tx_hash.hex()} (Waiting for confirmation...)")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

if receipt.status == 1:
    new_usdc_addr = receipt.contractAddress
    print(f"\n✅ Fresh MockUSDC Deployed Successfully!")
    print(f"💵 MockUSDC Address: {new_usdc_addr}")
    
    with open("usdc_address.txt", "w") as f:
        f.write(new_usdc_addr)
    print("💾 Saved new MockUSDC address to usdc_address.txt!")
else:
    print(f"❌ Deployment failed on-chain.")
    