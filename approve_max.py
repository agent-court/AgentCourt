from agent import w3, usdc_contract, CLIENT_ADDR, PRIVATE_KEY, ESCROW_ADDRESS, build_tx_params, send_and_wait

print(f"Approving 1,000 USDC for Escrow Contract: {ESCROW_ADDRESS}...")
tx_params = build_tx_params(CLIENT_ADDR, gas_limit=100000)
approve_tx = usdc_contract.functions.approve(
    ESCROW_ADDRESS, 1000 * 10**6
).build_transaction(tx_params)

tx_hash, receipt = send_and_wait(approve_tx, PRIVATE_KEY)
print(f"✅ USDC Approved! Tx: {tx_hash.hex()}")
