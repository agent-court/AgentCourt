from agent import w3, escrow_contract, usdc_contract, CLIENT_ADDR, ESCROW_ADDRESS

eth_bal = w3.eth.get_balance(CLIENT_ADDR)
usdc_bal = usdc_contract.functions.balanceOf(CLIENT_ADDR).call()
allowance = usdc_contract.functions.allowance(CLIENT_ADDR, ESCROW_ADDRESS).call()

print("========================================")
print(f"Client Address      : {CLIENT_ADDR}")
print(f"Client ETH Balance  : {w3.from_wei(eth_bal, 'ether'):.4f} ETH")
print(f"Client USDC Balance : ${usdc_bal / 10**6:.4f} USDC")
print(f"Allowance for Escrow: ${allowance / 10**6:.4f} USDC")
print("========================================")

# Test call simulation
try:
    print("\nSimulating createTask call...")
    escrow_contract.functions.createTask(
        CLIENT_ADDR,
        1000000, # 1 USDC
        "Test spec",
        3600
    ).call({'from': CLIENT_ADDR})
    print("✅ Simulation succeeded with no reverts!")
except Exception as e:
    print(f"❌ Simulation reverted with error: {e}")
