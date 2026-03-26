import json
import os
import re
import uuid
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

# Load env from current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Verify API key
api_val = os.getenv("GEMINI_API_KEY")
if not api_val:
    print("WARNING: GEMINI_API_KEY not found in environment!")
else:
    print(f"DEBUG: GEMINI_API_KEY found: {api_val[:10]}...")

# =========================================================
# In-memory session tracking
# =========================================================
_sessions: Dict[str, Dict[str, Any]] = {}


class GenAIAgent:
    def __init__(self, catalogue_path: str, action_catalogue_path: str):
        self.catalogue_path = Path(catalogue_path)
        self.action_catalogue_path = Path(action_catalogue_path)

        with open(self.catalogue_path, "r") as f:
            self.catalogue = json.load(f)

        with open(self.action_catalogue_path, "r") as f:
            self.action_catalogue = json.load(f)

        self.triggers: List[Dict[str, Any]] = self.catalogue.get("triggers", [])
        self.actions: List[Dict[str, Any]] = self.action_catalogue.get("actions", [])
        self.field_definitions: Dict[str, Any] = {
            **self.catalogue.get("field_definitions", {}),
            **self.action_catalogue.get("field_definitions", {}),
        }

        self.models: Dict[str, Dict[str, str]] = {
            "gemini_flash": {"provider": "gemini", "model_name": "models/gemini-2.5-flash", "api_key_env": "GEMINI_API_KEY", "label": "Gemini 2.5 Flash"},
            "gemini_pro": {"provider": "gemini", "model_name": "models/gemini-2.5-pro", "api_key_env": "GEMINI_API_KEY", "label": "Gemini 2.5 Pro"},
            "claude_sonnet": {"provider": "claude", "model_name": "claude-3-5-sonnet-latest", "api_key_env": "ANTHROPIC_API_KEY", "label": "Claude Sonnet"},
        }


        # Build the system prompt with catalogue knowledge baked in
        self._system_prompt = self._build_system_prompt()

    # ==========================================================
    # SYSTEM PROMPT BUILDER
    # ==========================================================
    def _build_system_prompt(self) -> str:
        """Build a rich system prompt that includes all triggers and actions from catalogues."""

        # Build trigger descriptions
        trigger_list = []
        for t in self.triggers:
            fields_str = ", ".join(t.get("required_fields", []))
            trigger_list.append(f'  - type: "{t["type"]}" | category: {t.get("category", "n/a")} | description: {t["description"]} | required_fields: [{fields_str}]')
        triggers_text = "\n".join(trigger_list)

        # Build action descriptions
        action_list = []
        for a in self.actions:
            fields_str = ", ".join(a.get("required_fields", []))
            action_list.append(f'  - type: "{a["type"]}" | category: {a.get("category", "n/a")} | description: {a["description"]} | required_fields: [{fields_str}]')
        actions_text = "\n".join(action_list)

        # Build field definitions
        field_list = []
        for fname, fdef in self.field_definitions.items():
            field_list.append(f'  - "{fname}": type={fdef.get("type", "string")}')
        fields_text = "\n".join(field_list)

        return f"""You are AEGIS, a friendly and highly intelligent Web3 automation assistant. You have a warm, conversational personality — like chatting with a knowledgeable friend who's genuinely excited to help.

## YOUR PERSONALITY
- Be warm, natural, and friendly — NOT robotic or corporate
- Use casual language, occasional emojis, and show personality
- Keep responses concise (2-4 sentences for casual chat, more for automation details)
- NEVER say "I couldn't match that to a supported trigger" — that's terrible UX
- If unsure, gently guide the user toward what you can automate

## YOUR CORE PURPOSE
You help users build on-chain automations. You understand the following TRIGGERS and ACTIONS:

### AVAILABLE TRIGGERS (what starts an automation):
{triggers_text}

### AVAILABLE ACTIONS (what happens when triggered):
{actions_text}

### FIELD DEFINITIONS:
{fields_text}

## WALLET MODEL & PRIVACY (CRITICAL)
- Whenever a user refers to "my wallet", "from my wallet", or "send from my wallet", it refers by default to their **Agent Wallet** (a funded smart contract wallet on-chain).
- Your role is to build automations that the platform executor will trigger via the Agent Wallet.
- **NEVER ASK FOR PRIVATE KEYS, SEED PHRASES, OR METAMASK SECRETS.**
- For transfer/payment automations (e.g., `send_native_token`, `send_erc20`), assume the sender is the **Agent Wallet**.
- If the user hasn't provided a `wallet_address`, you can ask for it, but refer to it as the "Agent Wallet address" or "execution wallet". Do NOT ask for the key.

## IMPORTANT: PROTOCOL INTEGRATIONS
We are a platform that generates actual on-chain automation projects. We are NOT directly integrated with every protocol’s backend API yet.
When a user asks for actions like swaps, NFT mints, faucet claims, or marketplace actions, you MUST:
1. Be honest: Tell them you can build the automation node, but they will need to provide specific configuration like contract addresses or router addresses.
2. Ask for missing technical fields: If they haven't provided fields like "router_address", "token_address", "nft_contract", or "faucet_url", ask for them during the conversation to make the generated project more "ready-to-run".
3. NEVER block generation: If a field is unknown, proceed with the plan but mention that there will be a clear "// TODO" placeholder in the generated code for them to fill in later.

## HOW TO RESPOND

You must ALWAYS respond with a valid JSON object. No extra text before or after the JSON.

### CASE 1: Casual chat (greetings, questions about you, small talk, thanks, etc.)
Return:
{{
  "intent": "chat",
  "message": "<your friendly conversational response>"
}}

### CASE 2: User describes an automation they want to build
Analyze their message, identify the best trigger and action(s) from the catalogues above, extract any field values mentioned, and determine what fields are still missing. Use your intelligence to ask for practical fields (e.g., for a swap, ask for the router and token addresses).

Return:
{{
  "intent": "automation",
  "message": "<friendly, honest explanation of what you understood and what you're setting up. Mention if any protocol-specific parts will need manual placeholders.>",
  "trigger": {{
    "type": "<trigger_type from catalogue>",
    "description": "<brief description>"
  }},
  "actions": [
    {{
      "type": "<action_type from catalogue>",
      "description": "<brief description>"
    }}
  ],
  "extracted_fields": {{
    "<field_name>": "<value>"
  }},
  "missing_fields": ["<field1>", "<field2>"],
  "structured_questions": [
    {{
      "field": "<field_name>",
      "question": "<natural, friendly, technical question to ask the user>",
      "input_type": "<text|number|url|address|email|interval|select>",
      "field_type": "<type from field definitions>",
      "required": true,
      "options": null
    }}
  ]
}}

### CASE 3: User provides follow-up field values during an automation flow
If the conversation history shows an active automation being built and the user is providing values for missing fields:

Return:
{{
  "intent": "field_update",
  "message": "<acknowledge values, mention if still missing technical details>",
  "extracted_fields": {{
    "<field_name>": "<value>"
  }},
  "still_missing": ["<remaining fields if any>"],
  "structured_questions": [<questions for remaining fields, same format as above>]
}}

## IMPORTANT RULES:
1. ALWAYS respond with valid JSON only. No markdown, no code fences, no extra text.
2. For automation intents, be smart about mapping and TECHNICAL completeness. For example:
   - "swap ETH to USDC" → ask for the DEX name AND the router address.
   - "mint an NFT" → ask for the contract address AND the mint function signature.
3. Extract as many field values as possible from the user's natural language.
4. For missing fields, generate friendly but technically accurate questions.
5. For "select" type fields with options, include the options array.
6. When a user mentions a token like BNB, ETH, USDC — extract it as both "token" and "asset".
7. Be conversational in your messages, but maintain a high degree of Web3 technical accuracy.
8. NEVER pretend a protocol is "ready to go" if we need a contract address. Be honest about TODO fragments."""

    def list_available_models(self) -> List[Dict[str, Union[str, bool]]]:
        return [{"id": mid, "label": str(cfg["label"]), "active": bool(os.getenv(str(cfg["api_key_env"])))} for mid, cfg in self.models.items()]

    # ==========================================================
    # MAIN CHAT ENTRY POINT
    # ==========================================================
    def chat(self, user_message: str, session_id: Optional[str] = None, known_fields: Optional[Dict[str, Any]] = None, planning_model_id: str = "gemini_flash", codegen_model_id: str = "gemini_flash") -> Dict[str, Any]:
        if not session_id:
            session_id = str(uuid.uuid4())
        if session_id not in _sessions:
            _sessions[session_id] = {
                "id": session_id, "stage": "idle",
                "known_fields": known_fields or {},
                "history": [], "selected_trigger": None,
                "selected_actions": [], "plan_md": "", "files": {},
                "codegen_model_id": codegen_model_id,
            }

        session = _sessions[session_id]
        session["history"].append({"role": "user", "content": user_message})
        session["codegen_model_id"] = codegen_model_id
        if known_fields:
            session["known_fields"].update(known_fields)

        # Send everything to Gemini
        try:
            ai_response = self._ask_gemini(session["history"], planning_model_id)
        except Exception as e:
            print(f"[AEGIS AI Error] {str(e)}")
            traceback.print_exc()
            # Fallback response if AI fails
            return self._response(session_id, "idle", "chat", "greeting",
                "Hey! I'm having a moment connecting to my brain. Could you try again in a sec? 🧠")

        intent = ai_response.get("intent", "chat")
        agent_message = ai_response.get("message", "I'm here to help! What would you like to automate?")

        # --- CASE 1: Casual chat ---
        if intent == "chat":
            session["history"].append({"role": "assistant", "content": agent_message})
            return self._response(session_id, "idle", "chat", "greeting", agent_message)

        # --- CASE 2: Automation intent ---
        if intent == "automation":
            trigger_data = ai_response.get("trigger", {})
            actions_data = ai_response.get("actions", [])
            extracted_fields = ai_response.get("extracted_fields", {})
            missing_fields = ai_response.get("missing_fields", [])
            structured_questions = ai_response.get("structured_questions", [])

            # Merge extracted fields
            session["known_fields"].update(extracted_fields)
            session["selected_trigger"] = trigger_data
            session["selected_actions"] = actions_data

            # If there are missing fields, ask for them
            if missing_fields and structured_questions:
                session["stage"] = "needs_input"
                session["history"].append({"role": "assistant", "content": agent_message})
                return {
                    "session_id": session_id,
                    "stage": "needs_input",
                    "status": "waiting_for_input",
                    "agent_status": "asking",
                    "agent_message": agent_message,
                    "structured_questions": structured_questions,
                    "files": {}
                }

            # All fields present → generate plan
            session["stage"] = "awaiting_approval"
            plan_md = self._generate_plan_md(trigger_data, actions_data, session["known_fields"])
            session["plan_md"] = plan_md
            session["history"].append({"role": "assistant", "content": agent_message})
            return {
                "session_id": session_id,
                "stage": "awaiting_approval",
                "status": "chat",
                "agent_status": "planning",
                "agent_message": agent_message,
                "plan_md": plan_md,
                "files": {"plan.md": plan_md}
            }

        # --- CASE 3: Field update ---
        if intent == "field_update":
            new_fields = ai_response.get("extracted_fields", {})
            still_missing = ai_response.get("still_missing", [])
            structured_questions = ai_response.get("structured_questions", [])

            session["known_fields"].update(new_fields)
            session["history"].append({"role": "assistant", "content": agent_message})

            if still_missing and structured_questions:
                session["stage"] = "needs_input"
                return {
                    "session_id": session_id,
                    "stage": "needs_input",
                    "status": "waiting_for_input",
                    "agent_status": "asking",
                    "agent_message": agent_message,
                    "structured_questions": structured_questions,
                    "files": {}
                }

            # All fields present → generate plan
            session["stage"] = "awaiting_approval"
            plan_md = self._generate_plan_md(
                session.get("selected_trigger", {}),
                session.get("selected_actions", []),
                session["known_fields"]
            )
            session["plan_md"] = plan_md
            return {
                "session_id": session_id,
                "stage": "awaiting_approval",
                "status": "chat",
                "agent_status": "planning",
                "agent_message": agent_message,
                "plan_md": plan_md,
                "files": {"plan.md": plan_md}
            }

        # Default fallback — treat as chat
        session["history"].append({"role": "assistant", "content": agent_message})
        return self._response(session_id, "idle", "chat", "greeting", agent_message)

    # ==========================================================
    # CONTINUE CHAT (follow-up field submissions)
    # ==========================================================
    def continue_chat(self, session_id: str, fields: Dict[str, Any], planning_model_id: str = "gemini_flash") -> Dict[str, Any]:
        session = _sessions[session_id]
        session["known_fields"].update(fields)

        # Build a natural message from the submitted fields
        fields_text = ", ".join([f"{k}: {v}" for k, v in fields.items()])
        user_msg = f"Here are the values: {fields_text}"
        session["history"].append({"role": "user", "content": user_msg})

        # Let Gemini decide if more fields are needed
        try:
            ai_response = self._ask_gemini(session["history"], planning_model_id)
        except Exception as e:
            print(f"[AEGIS Continue Error] {str(e)}")
            # Try to proceed with what we have
            return self._try_finalize_plan(session_id, session)

        intent = ai_response.get("intent", "field_update")
        agent_message = ai_response.get("message", "Got it! Let me process that.")

        new_fields = ai_response.get("extracted_fields", {})
        still_missing = ai_response.get("still_missing", ai_response.get("missing_fields", []))
        structured_questions = ai_response.get("structured_questions", [])

        session["known_fields"].update(new_fields)
        session["history"].append({"role": "assistant", "content": agent_message})

        if still_missing and structured_questions:
            session["stage"] = "needs_input"
            return {
                "session_id": session_id,
                "stage": "needs_input",
                "status": "waiting_for_input",
                "agent_status": "asking",
                "agent_message": agent_message,
                "structured_questions": structured_questions,
                "files": {}
            }

        # All fields → generate plan
        return self._try_finalize_plan(session_id, session, agent_message)

    # ==========================================================
    # APPROVE / REJECT PLAN → Gemini generates code
    # ==========================================================
    def approve_plan(self, session_id: str, approved: bool, feedback: Optional[str] = None) -> Dict[str, Any]:
        session = _sessions[session_id]
        if not approved:
            session["stage"] = "idle"
            return self._response(session_id, "idle", "chat", "reset",
                "No worries! I've scrapped that plan. What should we build instead? 🔄")

        # Approved → have Gemini generate the actual Python automation code
        spec = self._build_spec(session["selected_trigger"], session["selected_actions"], session["known_fields"])
        codegen_model = session.get("codegen_model_id", "gemini_flash")

        try:
            files = self._generate_code_with_gemini(spec, session["known_fields"], codegen_model)
        except Exception as e:
            print(f"[AEGIS Code Gen Error] {str(e)}")
            # Fallback to template-based generation
            files = self._generate_workspace_files_fallback(spec)

        session.update({"stage": "complete", "files": files})
        return {
            "session_id": session_id,
            "stage": "complete",
            "status": "success",
            "agent_status": "complete",
            "agent_message": "Your automation code is ready! 🚀 Check out the generated files in your workspace. The main.py has your full automation logic.",
            "files": files
        }

    # ==========================================================
    # GEMINI COMMUNICATION
    # ==========================================================
    def _ask_gemini(self, history: List[Dict[str, str]], model_id: str) -> Dict[str, Any]:
        """Send the conversation to Gemini and get a structured JSON response."""
        cfg = self.models.get(model_id, self.models["gemini_flash"])

        # Build the conversation for Gemini
        conversation_messages = []
        for msg in history:
            role = msg["role"]
            if role == "user":
                conversation_messages.append(f"USER: {msg['content']}")
            elif role == "assistant":
                conversation_messages.append(f"AEGIS: {msg['content']}")

        conversation_text = "\n".join(conversation_messages)

        payload = {"conversation": conversation_text}

        if cfg["provider"] == "gemini":
            raw_text = self._gemini_complete_text(self._system_prompt, payload, cfg)
        else:
            raw_text = self._claude_complete_text(self._system_prompt, payload, cfg)

        return self._extract_json(raw_text)

    def _generate_code_with_gemini(self, spec: Dict[str, Any], fields: Dict[str, Any], model_id: str) -> Dict[str, str]:
        """Have Gemini generate actual Python automation code."""
        cfg = self.models.get(model_id, self.models["gemini_flash"])

        trigger_type = spec["trigger"].get("type", "unknown") if isinstance(spec["trigger"], dict) else str(spec["trigger"])
        action_types = []
        for a in spec.get("actions", []):
            if isinstance(a, dict):
                action_types.append(a.get("type", "unknown"))
            else:
                action_types.append(str(a))

        code_prompt = f"""You are a Python code generator for Web3 on-chain automations.

Your goal is to generate a complete, structured, and user-extensible automation project.
THE PROJECT MUST BE HONEST: If an action involves a specific protocol (DEX, NFT marketplace, faucet, etc.), generate a MODULAR ADAPTER PATTERN with clear "// TODO" placeholders for implementation-specific logic.

### AUTOMATION SPECIFICATION:
TRIGGER TYPE: {trigger_type}
ACTION TYPES: {json.dumps(action_types)}
PARAMETERS: {json.dumps(fields, indent=2)}
SPEC ID: {spec['id']}

### GENERATION REQUIREMENTS:
Generate these files and return them as a JSON object (filename: content):

1. "main.py":
   - The primary orchestrator script.
   - MUST import and use `TriggerEngine` and `ActionEngine` from provided engine files.
   - MUST handle the main execution loop (check trigger -> execute actions).
   - MUST load and use the structured `config.json`.

2. "adapters.py" (Integration Adapters):
   - Create clean, modular adapter functions or classes for protocol-specific parts.
   - If an action like 'swap' or 'mint' is requested, provide a structured function (e.g., `perform_swap`) with clear comments on where to insert the specific protocol call (router address, ABI, etc.).
   - BE EXPLICIT with // TODO comments for tokens, contracts, and SDK calls.

        3. "config.json" (Runtime Configuration):
    - A runtime-ready JSON structure using nested objects for clarity.
    - Project Name: "{fields.get('name', 'Automation Project')}"
    - CHAIN & RPC: If 'tbnb' or 'bsc' is mentioned, YOU MUST set chain.name to "BSC Testnet" and chain.rpc to "https://data-seed-prebsc-1-s1.bnbchain.org:8545".
    - ACTIONS: Include ALL requested actions: {json.dumps(action_types)}.
    - MUST CLEAN ACTION PARAMS: Only include fields relevant to each specific action. For 'send_native_token', ONLY include 'recipient_address' and 'amount'. For 'send_email_notification', ONLY include 'to', 'subject', and 'message'. Do NOT put trigger-only fields like 'date' or 'timezone' into action params.
    - DATES: Use the extracted 'date' and 'time' for the trigger. If 'date' is 'today', keep it as 'today' (the engine now resolves this).
    - Example schema:
      {{
        "name": "{fields.get('name', 'Automation Project')}",
        "spec_id": "{spec['id']}",
        "chain": {{ "name": "BSC Testnet", "rpc": "https://data-seed-prebsc-1-s1.bnbchain.org:8545" }},
        "wallet": {{ "address": "{fields.get('wallet_address', '')}" }},
        "trigger": {{ "type": "{trigger_type}", "params": {{ "date": "today", "time": "22:30", "timezone": "IST" }} }},
        "actions": [
          {{ "type": "send_native_token", "params": {{ "recipient_address": "0x...", "amount": 0.001 }} }},
          {{ "type": "send_email_notification", "params": {{ "to": "...", "subject": "...", "message": "..." }} }}
        ],
        "runtime": {{ "interval_seconds": 30 }}
      }}

4. "README.md" (Manual Setup Guide):
   - MUST clearly list manual configuration steps.
   - MUST highlight which fields in `config.json` need to be replaced by the user (DEX router, specific contract addresses, etc.).
   - Explain that the automation uses the **Agent Wallet** (Smart Contract) as the sender.
   - Do NOT instruct the user to enter their private key in the Chat; only mention it in the readme as a local environment setup for the executor node if absolutely necessary.

5. "requirements.txt" & ".env.example":
    - web3, requests, python-dotenv, schedule.
    - .env.example should NOT include placeholders that encourage sharing keys in the UI.

IMPORTANT: Do not generate misleading "fully working" code for protocols we don't have built-in APIs for. Use clear placeholders. RETURN ONLY VALID JSON."""

        if cfg["provider"] == "gemini":
            raw_text = self._gemini_complete_text(code_prompt, {}, cfg)
        else:
            raw_text = self._claude_complete_text(code_prompt, {}, cfg)

        try:
            files = self._extract_json(raw_text)
            if files and isinstance(files, dict):
                # Programmatic Normalization: 
                # If chain is unknown but tbnb/bsc is mentioned, force BSC Testnet.
                config_json = files.get("config.json")
                if isinstance(config_json, str):
                    try:
                        config_data = json.loads(config_json)
                        chain_info = config_data.get("chain", {})
                        params = config_data.get("trigger", {}).get("params", {})
                        token = str(params.get("token", "")).lower()
                        asset = str(params.get("asset", "")).lower()
                        
                        # Broad Normalization: Force BSC if mentioned OR if name is unknown OR if rpc is empty
                        needs_bsc = (
                            token in ["tbnb", "bnb", "bsc"] or 
                            asset in ["tbnb", "bnb", "bsc"] or
                            chain_info.get("name") == "unknown" or
                            not chain_info.get("rpc")
                        )
                        
                        if needs_bsc:
                            config_data["chain"] = {
                                "name": "BSC Testnet",
                                "rpc": "https://data-seed-prebsc-1-s1.bnbchain.org:8545"
                            }
                            files["config.json"] = json.dumps(config_data, indent=2)
                    except Exception:
                        pass
                
                if any(k.endswith(('.py', '.json', '.txt', '.md')) for k in files.keys()):
                    return files
        except Exception:
            pass

        # Fallback to template if parsing fails
        return self._generate_workspace_files_fallback(spec)

    # ==========================================================
    # HELPERS
    # ==========================================================
    def _try_finalize_plan(self, session_id: str, session: Dict[str, Any], agent_message: Optional[str] = None) -> Dict[str, Any]:
        """Generate plan when all fields are collected."""
        session["stage"] = "awaiting_approval"
        plan_md = self._generate_plan_md(
            session.get("selected_trigger", {}),
            session.get("selected_actions", []),
            session["known_fields"]
        )
        session["plan_md"] = plan_md
        msg = agent_message or "All inputs received! I've drafted the execution plan. Review it and approve when ready. ✅"
        return {
            "session_id": session_id,
            "stage": "awaiting_approval",
            "status": "chat",
            "agent_status": "planning",
            "agent_message": msg,
            "plan_md": plan_md,
            "files": {"plan.md": plan_md}
        }

    def _response(self, sid: str, stage: str, status: str, agent_status: str, msg: str) -> Dict[str, Any]:
        return {
            "session_id": sid, "stage": stage, "status": status,
            "agent_status": agent_status, "agent_message": msg, "files": {}
        }

    def _build_spec(self, trigger: Any, actions: Any, fields: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": "AEGIS-" + str(uuid.uuid4())[:6],
            "trigger": trigger,
            "actions": actions if isinstance(actions, list) else [actions],
            "params": fields,
            "timestamp": time.time()
        }

    # ==========================================================
    # PLAN.MD GENERATION
    # ==========================================================
    def _generate_plan_md(self, tr: Any, acs: Any, fields: Dict[str, Any]) -> str:
        # Handle both dict and string trigger formats
        if isinstance(tr, dict):
            trigger_type = tr.get("type", "unknown")
            trigger_name = trigger_type.replace("_", " ").title()
        else:
            trigger_type = str(tr)
            trigger_name = str(tr).replace("_", " ").title()

        # Handle actions
        if not isinstance(acs, list):
            acs = [acs] if acs else []

        action_names = []
        action_lines = []
        for a in acs:
            if isinstance(a, dict):
                atype = a.get("type", "unknown")
                aname = atype.replace("_", " ").title()
            else:
                atype = str(a)
                aname = str(a).replace("_", " ").title()
            action_names.append(aname)
            action_lines.append(f"- **{aname}**: `{atype}`")

        field_lines = "\n".join([f"- **{k}**: `{v}`" for k, v in fields.items()])
        actions_section = "\n".join(action_lines) if action_lines else "- **Log Message**: `log_message`"

        return f"""# 🚀 AEGIS Automation Plan

## 1. Goal
Automate **{action_names[0] if action_names else 'process'}** when **{trigger_name}** is detected.

## 2. Trigger
- **Type**: `{trigger_type}`
- **Asset**: `{fields.get('asset') or fields.get('token') or 'N/A'}`
- **Threshold**: `{fields.get('threshold', 'N/A')}`

## 3. Actions
{actions_section}

## 4. Parameters
{field_lines}

## 5. Infrastructure
- **Executor**: Platform Runtime
- **Sender**: Agent Wallet (Smart Contract)
- **Chain**: `{fields.get('chain', 'To be configured')}`
- **Security**: Pre-flight validation enabled
- **Fail-safe**: Automatic retry on network congestion

---
*Approve this plan to generate the automation code.*
"""

    # ==========================================================
    # FALLBACK FILE GENERATION (if Gemini code gen fails)
    # ==========================================================
    def _generate_workspace_files_fallback(self, spec: Dict[str, Any]) -> Dict[str, str]:
        trigger = spec["trigger"]
        trigger_type = trigger.get("type", "unknown") if isinstance(trigger, dict) else str(trigger)
        spec_id = spec["id"]
        action_types = []
        for a in spec.get("actions", []):
            if isinstance(a, dict):
                action_types.append(a.get("type", "unknown"))
            else:
                action_types.append(str(a))
        action_list = ", ".join(action_types)

        main_py = '''"""
Orchestrator generated by AEGIS AI
Spec ID: {spec_id}
Status: Integration-Ready (Requires manual setup for protocol-specific parts)
"""
import json
import os
import time
import logging
import schedule
from dotenv import load_dotenv

# Engine Imports
from trigger_engine import TriggerEngine, TriggerContext
from action_engine import ActionEngine, ActionContext

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[AEGIS %(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting AEGIS Orchestrator: {spec_id}")
    
    with open("config.json", "r") as f:
        config = json.load(f)

    # The engines handle the core logic mapping.
    # Protocol-specific fields (like router or contract addresses) MUST be 
    # verified in config.json before running production tasks.
    tr_engine = TriggerEngine()
    ac_engine = ActionEngine()

    while True:
        try:
            # Contexts built from structured config
            ctx = TriggerContext(
                chain=config.get("chain", {}).get("name"),
                rpc_url=config.get("chain", {}).get("rpc") or os.getenv("RPC_URL"),
                wallet_address=config.get("wallet", {}).get("address") or os.getenv("WALLET_ADDRESS")
            )
            actx = ActionContext(
                chain=ctx.chain,
                rpc_url=ctx.rpc_url,
                wallet_address=ctx.wallet_address,
                secrets={"private_key": os.getenv("PRIVATE_KEY")}
            )

            trigger_config = config.get("trigger", {})
            if tr_engine.evaluate(trigger_config.get("type"), trigger_config.get("params"), ctx):
                logger.info(f"Trigger {trigger_config.get('type')} matched! Executing actions...")
                
                for action in config.get("actions", []):
                    logger.info(f"Executing action: {action.get('type')}")
                    # // TODO: If this is an external protocol (DEX/NFT/Faucet),
                    # ensure 'integration' fields in config.json are filled.
                    result = ac_engine.execute(action.get("type"), action.get("params"), actx)
                    logger.info(f"Action Result: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"Orchestration fatal error: {e}")

        time.sleep(config.get("runtime", {}).get("interval_seconds", 30))

if __name__ == "__main__":
    main()
'''.replace("{spec_id}", spec_id)

        # Structured configuration matching the prompt requirement
        config_data = {
            "spec_id": spec_id,
            "chain": {
                "name": spec["params"].get("chain", "unknown"),
                "rpc": spec["params"].get("rpc_url", "")
            },
            "wallet": {
                "address": spec["params"].get("wallet_address", "")
            },
            "trigger": {
                "type": trigger_type,
                "params": spec["params"]
            },
            "actions": [
                {
                    "type": atype,
                    "params": spec["params"],
                    "integration": {
                        "// TODO": "Replace with router_address, nft_contract, or faucet_url for this action"
                    }
                } for atype in action_types
            ],
            "runtime": {
                "interval_seconds": 30
            }
        }

        readme = f"""# AEGIS Automation Node: {spec_id}

This project was generated by AEGIS. It is structured as an **Integration-Ready** automation.

## ⚠️ Manual Setup Required
The generated code provided the orchestration logic, but protocol-specific details (DEX routers, NFT contracts, Faucet APIs) require manual configuration in `config.json`.

### Checklist:
1. **RPC URL**: Enter a valid RPC URL in `config.json` or `.env`.
2. **Executor Key**: Provide your node's EXECUTOR_PRIVATE_KEY in `.env`. This key is used only to trigger the Agent Wallet contract.
3. **Integration Fields**: In `config.json`, replace the TODO placeholders in the `actions[].integration` objects with real contract or router addresses.

## How to Run locally
1. `pip install -r requirements.txt`
2. Setup your `.env` following `.env.example`.
3. `python main.py`

*Node generated by AEGIS AI.*
"""

        return {
            "main.py": main_py,
            "config.json": json.dumps(config_data, indent=2),
            "requirements.txt": "web3\nrequests\npython-dotenv\nschedule",
            "README.md": readme,
            ".env.example": "# AEGIS Node Secrets\n# IMPORTANT: This is for the EXECUTOR NODE, NEVER enter your main wallet seed/key here!\nEXECUTOR_PRIVATE_KEY=\nRPC_URL=\nWALLET_ADDRESS=\n"
        }

    # ==========================================================
    # AI COMPLETION LAYER
    # ==========================================================
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response, handling various formats."""
        text = text.strip()
        # Remove markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        text = text.strip()

        try:
            s = text.find("{")
            e = text.rfind("}")
            if s == -1 or e == -1:
                return {"intent": "chat", "message": text}
            return json.loads(text[s:e + 1])
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as chat response
            return {"intent": "chat", "message": text}

    def _gemini_complete_text(self, sys: str, pl: Dict[str, Any], cfg: Dict[str, str]) -> str:
        import google.generativeai as genai
        api_key = os.getenv(str(cfg["api_key_env"]))
        if not api_key:
            raise ValueError(f"Missing API key: {cfg['api_key_env']}")
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(str(cfg["model_name"]), generation_config={"max_output_tokens": 4096, "temperature": 0.4})
        prompt = f"{sys}\n\nINPUT: {json.dumps(pl)}" if pl else sys

        # Retry with backoff for rate limits
        import time
        import random
        max_retries = 10
        for attempt in range(max_retries):
            try:
                return m.generate_content(prompt).text.strip()
            except Exception as e:
                err_msg = str(e)
                # 429 is Rate Limit or Quota Exceeded
                if "429" in err_msg or "Resource has been exhausted" in err_msg:
                    # Exponential backoff with jitter
                    wait = (2 ** attempt) + (random.randint(0, 1000) / 1000.0)
                    if attempt < max_retries - 1:
                        print(f"[Gemini 429] Rate limited (attempt {attempt + 1}/{max_retries}). Retrying in {wait:.1f}s...")
                        time.sleep(wait)
                        continue
                
                # For all other exceptions or after all retries exhausted
                print(f"[Gemini Error] {err_msg}")
                raise e
        return "" # Should not reach here due to raise

    def _claude_complete_text(self, sys: str, pl: Dict[str, Any], cfg: Dict[str, str]) -> str:
        from anthropic import Anthropic
        api_key = os.getenv(str(cfg["api_key_env"]))
        if not api_key:
            raise ValueError(f"Missing API key: {cfg['api_key_env']}")
        c = Anthropic(api_key=api_key)
        prompt = json.dumps(pl) if pl else "Respond."
        return c.messages.create(
            model=str(cfg["model_name"]), max_tokens=4096, system=sys,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text.strip()