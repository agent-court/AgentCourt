from agent import w3, escrow_contract, usdc_contract, CLIENT_ADDR, WORKER_ADDR, ESCROW_ADDRESS

print(f"Target Escrow Address : {ESCROW_ADDRESS}")
print(f"Client Address        : {CLIENT_ADDR}")

allowance = usdc_contract.functions.allowance(CLIENT_ADDR, ESCROW_ADDRESS).call()
print(f"USDC Allowance for Escrow: ${allowance / 10**6:.4f} USDC")

# Check if allowance is insufficient
if allowance < 1000000:
    print("⚠️ Allowance is LESS than 1.00 USDC! The contract cannot pull the funds.")

print("\nSimulating createTask call directly via RPC...")
try:
    tx_data = escrow_contract.functions.createTask(
        WORKER_ADDR,
        1000000,
        "Test task terms",
        3600
    ).call({'from': CLIENT_ADDR})
    print("✅ eth_call succeeded! Task ID returned:", tx_data)
except Exception as e:
    print("❌ Revert reason:", e)
