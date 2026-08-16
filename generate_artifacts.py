import json

# 1. Extract AgentCourtEscrow ABI and Bytecode
with open("artifacts/contracts/AgentCourtEscrow.sol/AgentCourtEscrow.json") as f:
    escrow_artifact = json.load(f)

with open("contract_abi.json", "w") as f:
    json.dump(escrow_artifact["abi"], f, indent=2)

with open("contract_bytecode.bin", "w") as f:
    f.write(escrow_artifact["bytecode"])

print("✅ Updated contract_abi.json and contract_bytecode.bin!")

# 2. Extract MockUSDC ABI and Bytecode
with open("artifacts/contracts/MockUSDC.sol/MockUSDC.json") as f:
    usdc_artifact = json.load(f)

with open("usdc_abi.json", "w") as f:
    json.dump(usdc_artifact["abi"], f, indent=2)

with open("usdc_bytecode.bin", "w") as f:
    f.write(usdc_artifact["bytecode"])

print("✅ Updated usdc_abi.json and usdc_bytecode.bin!")
