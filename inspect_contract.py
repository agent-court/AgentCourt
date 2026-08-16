from agent import w3, escrow_contract, usdc_contract, ESCROW_ADDRESS

with open("treasury_address.txt") as f:
    treasury = w3.to_checksum_address(f.read().strip())

print(f"Contract Address (active): {ESCROW_ADDRESS}")
print(f"Treasury Address (local) : {treasury}")

# Query contract state
onchain_treasury = escrow_contract.functions.treasury().call()
onchain_fee_bps = escrow_contract.functions.feeBps().call()
task_count = escrow_contract.functions.taskCount().call()
treasury_usdc = usdc_contract.functions.balanceOf(treasury).call()

print("\n--- On-Chain Contract State ---")
print(f"On-Chain Treasury Address : {onchain_treasury}")
print(f"Protocol Fee (Basis Pts) : {onchain_fee_bps} ({onchain_fee_bps / 100}%)")
print(f"Total Tasks on v2        : {task_count}")
print(f"Treasury USDC Balance    : ${treasury_usdc / 10**6:.4f} USDC")
