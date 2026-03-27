import os
import json
from pathlib import Path
from agent import GenAIAgent

def test_agent():
    print("Testing AEGIS Agent connectivity...")
    
    # Paths
    base_dir = Path(__file__).parent.resolve()
    catalogue_path = base_dir / "catalogue.json"
    action_catalogue_path = base_dir / "action_catalogue.json"
    
    try:
        agent = GenAIAgent(str(catalogue_path), str(action_catalogue_path))
        
        # Test the user's requested automation
        user_req = "Build an automation that checks my wallet balance and notifies me when it goes below 2 MON."
        print(f"Sending test message: '{user_req}'")
        response = agent.chat(user_req, session_id="test-automation-session")
        
        print("\nAgent Response:")
        print(json.dumps(response, indent=2))
        
        if response.get("status") == "chat" or response.get("intent") == "chat":
            print("\nSUCCESS: Agent responded correctly.")
        else:
            print("\nWARNING: Response format might be unexpected, but connectivity is OK.")
            
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
