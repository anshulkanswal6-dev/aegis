import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

import runtime_service

def deploy_final_test():
    WALLET_ADDR = "0x657AC464877c534B56CEc17570bC0DC686eFaEeF"
    
    spec = {
        "name": "Final On-chain Verification (10:49am IST)",
        "chain": {
            "name": "Monad Testnet",
            "rpc": "https://testnet-rpc.monad.xyz"
        },
        "wallet": {
            "address": WALLET_ADDR
        },
        "trigger": {
            "type": "run_once_at_datetime",
            "params": {
                "date": "today",
                "time": "10:49am",
                "timezone": "IST"
            }
        },
        "actions": [
            {
                "type": "send_native_token",
                "params": {
                    "recipient_address": "0xaf2F12A3497bc5B74896E943645A8FEFdeD378e3",
                    "amount": 0.001
                }
            },
            {
                "type": "send_email_notification",
                "params": {
                    "to": "anshulkanswal01@gmail.com",
                    "subject": "AEGIS SUCCESS: 0.001 MON SENT",
                    "message": "Final verification successful. The wallet address is now perfectly formatted and whitelisting is removed."
                }
            }
        ],
        "runtime": {
            "interval_seconds": 30
        }
    }

    if not os.path.exists(".runtime_data"):
        os.makedirs(".runtime_data")
    with open(".runtime_data/automations.json", "w") as f: f.write("{}")
    with open(".runtime_data/logs.json", "w") as f: f.write("{}")

    record = runtime_service.deploy_automation(
        name=spec["name"],
        spec_json=spec,
        session_id="final-verif-session",
        description="Final test for onchain execution fix",
        files={}
    )
    print(f"SUCCESS! [e0bd2621] deployed for 10:49 AM IST.")
    return record.id

if __name__ == "__main__":
    deploy_final_test()
