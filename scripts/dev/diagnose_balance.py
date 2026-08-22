from agent import w3, usdc_contract, CLIENT_ADDR

eth_bal = w3.eth.get_balance(CLIENT_ADDR)
usdc_bal = usdc_contract.functions.balanceOf(CLIENT_ADDR).call()

print("========================================")
print(f"Client Address      : {CLIENT_ADDR}")
print(f"Client ETH Balance  : {w3.from_wei(eth_bal, 'ether'):.4f} ETH")
print(f"Client USDC Balance : ${usdc_bal / 10**6:.4f} USDC")
print("========================================")
