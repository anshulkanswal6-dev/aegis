import json
import os
from web3 import Web3
from dotenv import load_dotenv
load_dotenv()

# Monad Testnet
w3 = Web3(Web3.HTTPProvider('https://testnet-rpc.monad.xyz'))
executor_key = os.getenv('EXECUTOR_PRIVATE_KEY')
executor_account = w3.eth.account.from_key(executor_key)

print(f"Deploying with Executor: {executor_account.address}")

# 1. Compile results (assuming we have bytecode ready)
# Usually I'd use solcx, but for speed I will use the established contract layout.
# Let's check walletcontracttemplate.sol again.
