import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

from agent import GenAIAgent
import runtime_service

def build_and_deploy():
    prompt = "Build an automation to Schedule a transfer of 0.001 MON on Monad Testnet to 0xaf2F12A3497bc5B74896E943645A8FEFdeD378e3 at 10:05am today. Also send an email notification after successfull tx."
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    catalogue_path = os.path.join(BASE_DIR, "catalogue.json")
    action_catalogue_path = os.path.join(BASE_DIR, "action_catalogue.json")
    
    print("Initializing Agent...")
    agent = GenAIAgent(catalogue_path, action_catalogue_path)
    
    # 1. Chat
    print("Sending prompt to AI...")
    # For testing, you can set this in your shell or pass it manually.
    wallet_addr = os.getenv("TEST_AGENT_WALLET", "0x29965dc7fc66374d6df1939b7d37d8706621b8c9")
    resp = agent.chat(prompt, known_fields={"wallet_address": wallet_addr})
    sid = resp["session_id"]
    print(f"Session: {sid}, Stage: {resp['stage']}")
    
    # 2. Add missing fields if any
    if resp["stage"] == "needs_input":
        print("Providing missing fields...")
        # Assume missing fields are address or something the AI knows now. 
        # For simplicity, we'll try to approve anyway or fill known gaps.
        fields = {q["field"]: "anshulkanswal01@gmail.com" if "email" in q["field"] else "0xaf2F12A3497bc5B74896E943645A8FEFdeD378e3" for q in resp.get("structured_questions", [])}
        resp = agent.continue_chat(sid, fields)
        print(f"Stage now: {resp['stage']}")

    # 3. Approve
    if resp["stage"] == "awaiting_approval":
        print("Approving plan...")
        resp = agent.approve_plan(sid, True)
        print(f"Stage now: {resp['stage']}")

    # 4. Deploy
    if resp["stage"] == "complete":
        files = resp["files"]
        config_data = json.loads(files["config.json"])
        
        # Override time to 10:05am today
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        config_data["trigger"]["params"]["date"] = today
        config_data["trigger"]["params"]["time"] = "10:05am"
        config_data["trigger"]["params"]["timezone"] = "IST"
        
        print("Deploying automation...")
        # Reset store first to ensure clean state
        with open(".runtime_data/automations.json", "w") as f:
            f.write("{}")
        with open(".runtime_data/logs.json", "w") as f:
            f.write("{}")

        record = runtime_service.deploy_automation(
            name="Scheduled Transfer Test",
            spec_json=config_data,
            session_id=sid,
            description="Verification for onchain execution fix",
            files=files
        )
        print(f"SUCCESS! Automation {record.id} deployed.")
        return record.id
    else:
        print(f"FAILED to reach complete stage. Final resp: {resp}")

if __name__ == "__main__":
    build_and_deploy()
