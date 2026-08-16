import json
import solcx
from solcx import compile_source
from agent import w3, CLIENT_ADDR, PRIVATE_KEY, get_raw_tx, build_tx_params

print("📦 Ensuring Solidity compiler v0.8.20 is active...")
solcx.install_solc("0.8.20")
solcx.set_solc_version("0.8.20")

with open("AgentEscrowV2.sol") as f:
    source = f.read()

with open("usdc_address.txt") as f:
    usdc_addr = w3.to_checksum_address(f.read().strip())

with open("treasury_address.txt") as f:
    treasury_addr = w3.to_checksum_address(f.read().strip())

print(f"USDC Token Address : {usdc_addr}")
print(f"Treasury Address   : {treasury_addr}")

# Compile explicitly
compiled = compile_source(source, output_values=["abi", "bin"])
target_key = next((k for k in compiled.keys() if "AgentEscrowV2" in k), None)
assert target_key, "❌ Could not find AgentEscrowV2 in compiled output"

contract_interface = compiled[target_key]
abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

with open("contract_abi.json", "w") as f:
    json.dump(abi, f, indent=2)

print("\n🚀 Deploying AgentEscrow v2 to Base Sepolia...")
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

tx_params = build_tx_params(CLIENT_ADDR)
tx_params["gas"] = 2500000

construct_txn = Contract.constructor(usdc_addr, treasury_addr).build_transaction(tx_params)
signed = w3.eth.account.sign_transaction(construct_txn, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
print(f"Deploy Tx Broadcast: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"Deployment Status  : {'SUCCESS (1)' if receipt.status == 1 else 'FAILED (0)'}")

new_contract_addr = receipt.contractAddress
assert new_contract_addr, "❌ No contract address in receipt"

with open("contract_address.txt", "w") as f:
    f.write(new_contract_addr)

# Verify bytecode is populated on-chain
code = w3.eth.get_code(new_contract_addr)
print(f"On-Chain Bytecode Size : {len(code)} bytes")
assert len(code) > 2, "❌ Deployed contract has no bytecode on-chain"

# Test calling taskCount()
deployed_contract = w3.eth.contract(address=new_contract_addr, abi=abi)
initial_task_count = deployed_contract.functions.taskCount().call()
print(f"Verified initial taskCount(): {initial_task_count}")

print(f"\n🎉 AgentEscrow v2 Verified & Ready!")
print(f"📍 Address: {new_contract_addr}")
print(f"🔗 Explorer: https://sepolia.basescan.org/address/{new_contract_addr}")
