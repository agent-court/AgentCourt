import json
import sys
from dotenv import dotenv_values
from web3 import Web3
from solcx import compile_standard, install_solc

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

assert w3.is_connected(), "❌ Could not connect to Base Mainnet RPC"

account = w3.eth.account.from_key(config["PRIVATE_KEY"])
balance = w3.eth.get_balance(account.address)

USDC_MAINNET = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
with open("treasury_address.txt") as f:
    TREASURY_TARGET = w3.to_checksum_address(f.read().strip())

print("==================================================")
print("🚀 DEPLOYING AGENTCOURT V2 TO BASE MAINNET")
print(f"Deployer : {account.address}")
print(f"USDC     : {USDC_MAINNET}")
print(f"Treasury : {TREASURY_TARGET}")
print(f"Balance  : {w3.from_wei(balance, 'ether')} ETH")
print("==================================================")

install_solc("0.8.20")
with open("AgentEscrowV2.sol", "r") as f:
    contract_source = f.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"AgentEscrowV2.sol": {"content": contract_source}},
        "settings": {
            "evmVersion": "paris",
            "optimizer": {"enabled": True, "runs": 200},
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.20",
)

bytecode = compiled_sol["contracts"]["AgentEscrowV2.sol"]["AgentEscrowV2"]["evm"]["bytecode"]["object"]
abi = json.loads(compiled_sol["contracts"]["AgentEscrowV2.sol"]["AgentEscrowV2"]["metadata"])["output"]["abi"]

with open("escrow_abi.json", "w") as f:
    json.dump(abi, f, indent=2)

EscrowContract = w3.eth.contract(abi=abi, bytecode=bytecode)

nonce = w3.eth.get_transaction_count(account.address)
latest_block = w3.eth.get_block("latest")
base_fee = latest_block.get("baseFeePerGas", w3.to_wei(0.02, "gwei"))
max_priority_fee = w3.to_wei(0.005, "gwei")
max_fee = int(base_fee * 1.5) + max_priority_fee

tx = EscrowContract.constructor(USDC_MAINNET, TREASURY_TARGET).build_transaction({
    "chainId": 8453,
    "from": account.address,
    "nonce": nonce,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": max_priority_fee,
    "gas": 2500000
})

print("Broadcasting deployment transaction to Base Mainnet...")
signed_tx = w3.eth.account.sign_transaction(tx, private_key=config["PRIVATE_KEY"])
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Tx Hash: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status != 1:
    print(f"❌ Deployment Transaction Reverted! Status: {receipt.status}")
    sys.exit(1)

contract_address = receipt.contractAddress
print("\n🎉 MAINNET DEPLOYMENT VERIFIED SUCCESSFUL!")
print(f"📜 Contract Address : {contract_address}")
print(f"🔗 Basescan URL     : https://basescan.org/address/{contract_address}")

with open("mainnet_escrow_address.txt", "w") as f:
    f.write(contract_address)
