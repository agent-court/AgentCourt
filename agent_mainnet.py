
import os
try:
    import streamlit as st
    secrets = dict(st.secrets)
except Exception:
    secrets = {}

def get_secret(key, default=None):
    if key in secrets:
        return secrets[key]
    if key in os.environ:
        return os.environ[key]
    try:
        from dotenv import dotenv_values
        env_dict = dotenv_values(".env")
        if key in env_dict:
            return env_dict[key]
    except Exception:
        pass
    return default

import json
import os
from dotenv import dotenv_values
from web3 import Web3

config = dotenv_values(".env.mainnet")

# Resilient Mainnet RPC Pool with fast automatic fallback
RPC_POOL = [
    "https://base-rpc.publicnode.com",
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://1rpc.io/base"
]

w3 = None
for rpc in RPC_POOL:
    try:
        candidate_w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 8}))
        if candidate_w3.is_connected():
            w3 = candidate_w3
            break
    except Exception:
        continue

if not w3 or not w3.is_connected():
    w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

account = w3.eth.account.from_key(get_secret("PRIVATE_KEY"))
CLIENT_ADDR = account.address
PRIVATE_KEY = get_secret("PRIVATE_KEY")

with open("mainnet_escrow_address.txt", "r") as f:
    ESCROW_ADDRESS = w3.to_checksum_address(f.read().strip())

USDC_ADDRESS = w3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

with open("escrow_abi.json", "r") as f:
    ESCROW_ABI = json.load(f)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

escrow_contract = w3.eth.contract(address=ESCROW_ADDRESS, abi=ESCROW_ABI)
usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
