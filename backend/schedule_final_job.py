import os
import sys
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

import runtime_service
import runtime_store

# THE TRUTH
WALLET_ADDR = "0x29965dc7fc66374d6df1939b7d37d8706621b8c9"

def schedule_test():
    # 1. Clean data to avoid overlaps
    import shutil
    if os.path.exists(".runtime_data"):
        shutil.rmtree(".runtime_data")
    os.makedirs(".runtime_data")

    # 2. Timing (2 mins from now)
    # We'll use 24h format for the trigger engine
    now_utc = datetime.now(timezone.utc)
    target_time = now_utc + timedelta(minutes=2)
    time_str = target_time.strftime("%H:%M")
    
    print(f"Current UTC: {now_utc.strftime('%H:%M:%S')}")
    print(f"Scheduled Trigger Time (UTC): {time_str}")

    # 3. Spec
    spec = {
        "name": "FINAL SCHEDULED RUN",
        "description": "Sending 0.0001 MON to the target address",
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
                "time": time_str,
                "timezone": "UTC"
            }
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

    id = "LIVE-SCHEDULED-TEST"
    runtime_service.deploy_automation(id, spec, "user-session", "production")
    
    print(f"Automation {id} is now ACTIVE and waiting for trigger at {time_str} UTC.")

if __name__ == "__main__":
    schedule_test()
