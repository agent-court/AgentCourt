import os
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from web3 import Web3
from dotenv import load_dotenv
import solcx

load_dotenv()

RPC_URL = os.getenv("BASE_RPC_URL", "https://base-sepolia-rpc.publicnode.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("ARBITRATOR_PRIVATE_KEY")
USDC_SEPOLIA = os.getenv("USDC_SEPOLIA_ADDRESS", "0x036CbD53842c5426634e7929541eC2318f3dCF7e")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def main():
    account = w3.eth.account.from_key(PRIVATE_KEY)
    print(f"🔑 Deployer: {account.address}")
    print(f"💰 Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

    solc_version = "0.8.20"
    if solc_version not in [str(v) for v in solcx.get_installed_solc_versions()]:
        print(f"⏳ Installing solc {solc_version}...")
        solcx.install_solc(solc_version)

    contract_path = ROOT_DIR / "contracts" / "AgentEscrowV5.sol"
    print(f"🔨 Compiling {contract_path.name}...")

    compiled = solcx.compile_files(
        [str(contract_path)],
        output_values=["abi", "bin"],
        solc_version=solc_version,
        optimize=True,
        optimize_runs=200
    )

    contract_id = f"{contract_path}:AgentEscrowV5"
    if contract_id not in compiled:
        # Fallback to key lookup
        contract_id = [k for k in compiled.keys() if "AgentEscrowV5" in k][0]

    abi = compiled[contract_id]["abi"]
    bytecode = compiled[contract_id]["bin"]

    # Save canonical ABI
    with open(ROOT_DIR / "contracts" / "escrow_abi.json", "w") as f:
        json.dump(abi, f, indent=2)
    print("✅ contracts/escrow_abi.json updated")

    print("🚀 Broadcasting deployment transaction...")
    Escrow = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Estimate gas and construct tx
    construct_txn = Escrow.constructor(USDC_SEPOLIA, account.address).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id
    })

    signed = w3.eth.account.sign_transaction(construct_txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"⏳ Deployment Tx Sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    deployed_address = receipt.contractAddress
    print(f"\n🎉 AgentEscrowV5 Deployed to Base Sepolia: {deployed_address}")
    print(f"🔗 BaseScan: https://sepolia.basescan.org/address/{deployed_address}")

    # Update .env automatically
    env_path = ROOT_DIR / ".env"
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        written = False
        for line in lines:
            if line.startswith("ESCROW_CONTRACT_ADDRESS="):
                f.write(f"ESCROW_CONTRACT_ADDRESS={deployed_address}\n")
                written = True
            else:
                f.write(line)
        if not written:
            f.write(f"ESCROW_CONTRACT_ADDRESS={deployed_address}\n")

    print(f"💾 Updated ESCROW_CONTRACT_ADDRESS in .env to {deployed_address}")

if __name__ == "__main__":
    main()
