import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

import runtime_service
import runtime_store

def force_evaluation():
    store = runtime_store.get_store()
    automations = store.list_automations()
    if not automations:
        print("No automations.")
        return
        
    # Get the latest one
    a = automations[-1]
    print(f"Forcing evaluation for {a.id} ({a.name})...")
    
    # Ensure it's active and trigger time is passed
    a.spec_json["trigger"]["params"]["time"] = "10:00am"
    store.update_automation(a.id, {"spec_json": a.spec_json, "status": "active"})
    
    res = runtime_service.evaluate_automation(a.id)
    print(f"Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    force_evaluation()
