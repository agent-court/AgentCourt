import os
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")
w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))

assert w3.is_connected(), "❌ Could not connect to Base Mainnet RPC"

account = w3.eth.account.from_key(config["PRIVATE_KEY"])
balance_wei = w3.eth.get_balance(account.address)
balance_eth = w3.from_wei(balance_wei, "ether")

print("========================================")
print("🌐 BASE MAINNET STATUS")
print(f"Deployer Address : {account.address}")
print(f"Mainnet ETH Bal  : {balance_eth:.6f} ETH")
print("========================================")

if balance_eth < 0.0005:
    print("⚠️ You will need ~0.001 ETH (~$2-3 USD) on Base Mainnet to deploy the contract.")
else:
    print("✅ Sufficient ETH balance detected for mainnet contract deployment!")
