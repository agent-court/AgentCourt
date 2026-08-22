from agent import w3, escrow_contract, usdc_contract, CLIENT_ADDR, WORKER_ADDR, PRIVATE_KEY, ESCROW_ADDRESS, get_raw_tx

amount = 1000000
spec = "Write a Python function `calc_discount(price, pct)`"

print("1. Checking allowance and balance...")
bal = usdc_contract.functions.balanceOf(CLIENT_ADDR).call()
allowance = usdc_contract.functions.allowance(CLIENT_ADDR, ESCROW_ADDRESS).call()
print(f"   Balance  : ${bal/10**6:.2f} USDC")
print(f"   Allowance: ${allowance/10**6:.2f} USDC")

print("\n2. Estimating gas dynamically for createTask...")
try:
    est_gas = escrow_contract.functions.createTask(
        WORKER_ADDR,
        amount,
        spec,
        3600
    ).estimate_gas({'from': CLIENT_ADDR})
    print(f"   Estimated Gas Required: {est_gas}")
except Exception as e:
    print(f"   ❌ Gas Estimation Reverted: {e}")
    exit(1)

print("\n3. Building transaction with dynamic gas...")
nonce = w3.eth.get_transaction_count(CLIENT_ADDR, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_priority = w3.to_wei("0.1", "gwei")
max_fee = int(base_fee * 2) + max_priority

tx = escrow_contract.functions.createTask(
    WORKER_ADDR,
    amount,
    spec,
    3600
).build_transaction({
    'from': CLIENT_ADDR,
    'nonce': nonce,
    'gas': int(est_gas * 1.5),
    'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': max_priority,
    'chainId': 84532,
    'type': 2
})

print("4. Broadcasting transaction...")
signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(get_raw_tx(signed))
print(f"   Tx Hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
print(f"   Status : {'✅ SUCCESS (1)' if receipt.status == 1 else '❌ FAILED (0)'}")
print(f"   Gas Used: {receipt.gasUsed} / {tx['gas']}")
