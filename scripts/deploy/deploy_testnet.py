import json
import os
import time
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_standard, install_solc

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sepolia.base.org")

assert PRIVATE_KEY, "❌ PRIVATE_KEY missing in .env file"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
assert w3.is_connected(), f"❌ Could not connect to RPC: {RPC_URL}"

account = w3.eth.account.from_key(PRIVATE_KEY)
DEPLOYER_ADDR = account.address
CHAIN_ID = 84532

USDC_ADDRESS = "0x42e1ebC5D826Ac69fA5162eCCA7B1EC32Ec42418"

print(f"Connected to Base Sepolia (Chain ID: {w3.eth.chain_id})")
print(f"Deployer Address: {DEPLOYER_ADDR}")

def build_tx_params(from_addr):
    nonce = w3.eth.get_transaction_count(from_addr, 'pending')
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei('0.01', 'gwei')
    max_fee = base_fee + max_priority_fee
    return {
        'from': from_addr,
        'nonce': nonce,
        'chainId': CHAIN_ID,
        'gas': 1200000,  # Fits comfortably under your 0.000087 ETH balance
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': max_priority_fee,
        'type': 2
    }

def compile_contract():
    print("\n🔨 Compiling contracts/AgentCourtEscrow.sol...")
    install_solc("0.8.20")
    
    with open("contracts/AgentCourtEscrow.sol", "r") as f:
        source_code = f.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"AgentCourtEscrow.sol": {"content": source_code}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]}
                }
            },
        },
        solc_version="0.8.20",
    )

    abi = compiled_sol["contracts"]["AgentCourtEscrow.sol"]["AgentCourtEscrow"]["abi"]
    bytecode = compiled_sol["contracts"]["AgentCourtEscrow.sol"]["AgentCourtEscrow"]["evm"]["bytecode"]["object"]

    with open("contract_abi.json", "w") as f:
        json.dump(abi, f, indent=2)
    with open("contract_bytecode.bin", "w") as f:
        f.write(bytecode)

    print("✅ Compilation complete and contract_abi.json updated!")
    return abi, bytecode

def deploy_contracts():
    balance = w3.eth.get_balance(DEPLOYER_ADDR) / 10**18
    print(f"Deployer Balance: {balance:.6f} ETH")

    escrow_abi, escrow_bytecode = compile_contract()

    print(f"\n1. Using existing Mock USDC at: {USDC_ADDRESS}")

    print("\n2. Deploying AgentCourtEscrow to Base Sepolia...")
    escrow_contract = w3.eth.contract(abi=escrow_abi, bytecode=escrow_bytecode)
    tx_params = build_tx_params(DEPLOYER_ADDR)
    tx = escrow_contract.constructor(USDC_ADDRESS, DEPLOYER_ADDR).build_transaction(tx_params)
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    escrow_address = receipt.contractAddress
    print(f"✅ AgentCourtEscrow Deployed: {escrow_address}")

    with open("usdc_address.txt", "w") as f:
        f.write(USDC_ADDRESS)
    with open("contract_address.txt", "w") as f:
        f.write(escrow_address)
    print("\n🎉 Both contract addresses saved successfully!")

if __name__ == "__main__":
    deploy_contracts()