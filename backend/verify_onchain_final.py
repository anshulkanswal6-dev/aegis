import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

import runtime_service
import runtime_store

# THE TRUTH
WALLET_ADDR = "0x657AC464877c534B56CEc17570bC0DC686eFaEeF"

def run_test():
    # 1. Clean Slate
    import shutil
    if os.path.exists(".runtime_data"):
        shutil.rmtree(".runtime_data")
    os.makedirs(".runtime_data")

    # 2. Spec
    spec = {
        "name": "REAL ONCHAIN TEST",
        "chain": {
            "name": "Monad Testnet",
            "rpc": "https://testnet-rpc.monad.xyz"
        },
        "wallet": {
            "address": WALLET_ADDR
        },
        "trigger": {
            "type": "run_once",
            "params": {}
        },
        "actions": [
            {
                "type": "send_native_token",
                "params": {
                    "recipient_address": "0xaf2F12A3497bc5B74896E943645A8FEFdeD378e3",
                    "amount": 0.0001
                }
            }
        ]
    }

    print(f"--- STARTING REAL TEST ---")
    print(f"Target Wallet: {WALLET_ADDR}")
    
    id = "CLEAN-TEST"
    record = runtime_service.deploy_automation(id, spec, "test-session", "final_check")
    
    print(f"Force Evaluating {id}...")
    res = runtime_service.evaluate_automation(id)
    print(f"RESULT: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    run_test()
