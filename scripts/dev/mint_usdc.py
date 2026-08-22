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
user_addr = account.address
chain_id = 84532

with open("usdc_address.txt") as f:
    usdc_address = w3.to_checksum_address(f.read().strip())

# Explicit ABI including mint, balanceOf, decimals, and approve
ERC20_MINT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

usdc_contract = w3.eth.contract(address=usdc_address, abi=ERC20_MINT_ABI)

# Amount to mint: 1,000 USDC (6 decimals)
amount_to_mint = 1000 * 10**6

print(f"💰 Minting 1,000 MockUSDC to {user_addr} on contract {usdc_address}...")

nonce = w3.eth.get_transaction_count(user_addr, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_priority_fee = w3.to_wei("0.1", "gwei")
max_fee = base_fee * 2 + max_priority_fee

mint_tx = usdc_contract.functions.mint(user_addr, amount_to_mint).build_transaction({
    "from": user_addr,
    "nonce": nonce,
    "chainId": chain_id,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": max_priority_fee,
    "type": 2,
})

signed_tx = w3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed_tx))
print(f"📡 Broadcasted Tx: {tx_hash.hex()} (Waiting for confirmation...)")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
if receipt.status == 1:
    new_bal = usdc_contract.functions.balanceOf(user_addr).call() / 10**6
    print(f"\n✅ Successfully minted!")
    print(f"💵 New USDC Balance: ${new_bal:,.2f} USDC")
else:
    print(f"❌ Mint transaction failed on-chain.")
    