from agent import w3, usdc_contract

with open("treasury_address.txt") as f:
    treasury = w3.to_checksum_address(f.read().strip())

raw_bal = usdc_contract.functions.balanceOf(treasury).call()
formatted_bal = raw_bal / 10**6

print("========================================")
print(f"🏦 Protocol Treasury Address : {treasury}")
print(f"💰 Total USDC Fees Accrued   : ${formatted_bal:.4f} USDC")
print("========================================")
