from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv()

w3 = Web3(Web3.HTTPProvider('https://testnet-rpc.monad.xyz'))
executor_key = os.getenv('EXECUTOR_PRIVATE_KEY')
executor_account = w3.eth.account.from_key(executor_key)
wallet_addr = w3.to_checksum_address('0x29965dc7fc66374d6df1939b7d37d8706621b8c9')
recipient = w3.to_checksum_address('0xaf2F12A3497bc5B74896E943645A8FEFdeD378e3')

# New ABI
abi = [
    {"type":"function","name":"executeETH","inputs":[{"name":"target","type":"address"},{"name":"amount","type":"uint256"},{"name":"data","type":"bytes"}],"outputs":[{"name":"result","type":"bytes"}],"stateMutability":"nonpayable"},
    {"type":"function","name":"getEthBalance","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view"}
]
contract = w3.eth.contract(address=wallet_addr, abi=abi)

print(f"Executor: {executor_account.address}")
print(f"Wallet: {wallet_addr}")
print(f"Balance: {contract.functions.getEthBalance().call()}")

amount_wei = w3.to_wei(0.0001, 'ether')
print(f"Executing with {amount_wei} wei...")

try:
    tx = contract.functions.executeETH(recipient, amount_wei, b"").build_transaction({
        'from': executor_account.address,
        'nonce': w3.eth.get_transaction_count(executor_account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })
    
    # We won't sign yet, just check if it can be simulated
    print("Simulating...")
    w3.eth.call(tx)
    print("SIMULATION SUCCESS!")
except Exception as e:
    print(f"SIMULATION FAILED: {str(e)}")
