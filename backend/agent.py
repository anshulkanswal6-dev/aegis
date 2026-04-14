import json
import os
import re
import uuid
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
import config
import log_service

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
# Persistent session tracking
# =========================================================
class SessionManager(dict):
    """A dictionary that persists itself to a JSON file."""
    def __init__(self, filename="sessions.json"):
        super().__init__()
        self.filename = Path(__file__).parent / filename
        self._load()

    def _load(self):
        if self.filename.exists():
            try:
                with open(self.filename, "r") as f:
                    data = json.load(f)
                    self.update(data)
                print(f"[AEGIS SessionManager] Loaded {len(data)} sessions from {self.filename}")
            except Exception as e:
                print(f"[AEGIS SessionManager] Failed to load sessions: {e}")

    def _save(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.copy(), f, indent=2)
        except Exception as e:
            print(f"[AEGIS SessionManager] Failed to save sessions: {e}")

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._save()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._save()

_sessions = SessionManager()


def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a session's state from the global session manager."""
    return _sessions.get(session_id)


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
            "gemini_flash": {"provider": "gemini", "model_name": "models/gemini-flash-latest", "api_key_env": "GEMINI_API_KEY", "label": "Gemini Flash (Latest)"},
            "gemini_pro": {"provider": "gemini", "model_name": "models/gemini-pro-latest", "api_key_env": "GEMINI_API_KEY", "label": "Gemini Pro (Latest)"},
            "gemini_2_flash": {"provider": "gemini", "model_name": "models/gemini-2.0-flash", "api_key_env": "GEMINI_API_KEY", "label": "Gemini 2.0 Flash"},
            "gemini_3_flash": {"provider": "gemini", "model_name": "models/gemini-3-flash-preview", "api_key_env": "GEMINI_API_KEY", "label": "Gemini 3 Flash (Preview)"},
            "claude_sonnet": {"provider": "claude", "model_name": "claude-3-5-sonnet-latest", "api_key_env": "ANTHROPIC_API_KEY", "label": "Claude 3.5 Sonnet"},
        }

        self.mock_mode = os.getenv("MOCK_AGENT", "false").lower() == "true"



        # Build the system prompt with catalogue knowledge baked in
        self._system_prompt = self._build_system_prompt()

    # ==========================================================
    # SYSTEM PROMPT BUILDER
    # ==========================================================
    def _build_system_prompt(self) -> str:
        """Build a rich system prompt that includes all triggers and actions from catalogues."""
        import config
        project_context = f"PLATFORM_CONTEXT: The current platform default chain is '{config.CHAIN_NAME}' (Currency: {config.CURRENCY_SYMBOL})."

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

## IMPORTANT: NOTIFICATIONS (CRITICAL)
**DO NOT use legacy actions like `send_email_notification` or `send_telegram_message`. They are deprecated.**
For EVERY automation, you MUST process notifications through the dedicated `notification` field in the final spec.

### Notification Delivery (STEP-BY-STEP):
1. **Choose Channel**: If the user says "notifies me" without a channel, you MUST ask for their choice: [Email, Telegram, Both].
2. **Collect Details**: Once the channel is selected, ask for:
    - Telegram: `telegram_message` (what should the alert say?).
    - Email: `to` (recipient email) and `email_body`.
    - **Cooldown**: Ask if they want a specific cooldown period (e.g. "wait 60 seconds before sending another alert") using the `notification_cooldown` field. **IMPORTANT: Collect this value in SECONDS only.** If not mentioned, default to 300.
3. **Remind**: Always remind users to link their Telegram account in the **Integrations** tab if they select it.
4. **Draft Planning**: Only skip these questions if the user explicitly says "skip questions" or "fast track".

### FINAL SPEC STRUCTURE:
In your final generated JSON code for `config.json`, use this structure:
```json
"notification": {{
  "channels": ["telegram"],
  "cooldown": 300,
  "telegram": {{ "message": "..." }},
  "email": {{ "to": "...", "subject": "...", "body": "..." }}
}}
```
Do NOT place notification fields inside the `actions` array.

## DYNAMIC MESSAGES & PLACEHOLDERS (POWERFUL)
When sending notifications (Email, Telegram, etc.), you can use dynamic placeholders that the execution engine will fill with real-time data from the trigger:
- `{{amount}}`: The amount responsible for triggering the automation (e.g., amount received, price delta).
- `{{delta}}`: Same as amount.
- `{{new_balance}}`: The wallet's balance after the trigger matched.

Encourage users to use these (e.g., "Received {{amount}} MON in my wallet!") to make alerts more informative.

## BALANCE MONITORING
For monitoring incoming payments or wallet growth, use the `balance_increased` or `incoming_transfer_detected` triggers. They use persistent memory to track balance changes.

## IMPORTANT: INFRASTRUCTURE & CREDENTIALS (CRITICAL)
- **ZERO-SECRET POLICY**: NEVER ask for or include infrastructure secrets like `SMTP_PASS`, `TELEGRAM_BOT_TOKEN`, `SUPABASE_KEY`, or `PRIVATE_KEY` in the conversation or generated files.
- **PLATFORM-MANAGED**: The AEGIS platform handles all email delivery, Telegram routing, and blockchain execution using **Admin Credentials** stored in the secure host environment (Render).
- **USER INPUTS ONLY**: In your plan and code, only focus on **User Inputs**:
    - Notifications: `to` (email), `subject`, `message`, `cooldown`.
    - Transactions: `recipient_address`, `amount`, `thresholds`.
    - Blockchain: You do NOT need to ask for RPC URLs or Chain IDs unless the user wants a non-Monad chain. Default to {config.CHAIN_NAME} infrastructure.
- **GENERATED CODE**: The generated `main.py` and `config.json` should NOT expect a `.env` with platform secrets. They should rely on the platform's internal `adapters` and `config` which pull from the admin env.

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

## PROJECT CONTEXT
{project_context}

## IMPORTANT RULES:
1. ALWAYS respond with valid JSON only. No markdown, no code fences, no extra text.
2. **ZERO-PLACEHOLDER RULE**: NEVER invent values or use placeholders like `[[current_time_plus_2_minutes]]`, `[[HH:MM]]`, or `0x...` for missing fields. If a field is required in the catalogue and the user hasn't provided it, you MUST mark it as missing and ASK the user.
3. For automation intents, be smart about mapping and TECHNICAL completeness. For example:
   - "swap ETH to USDC" → ask for the DEX name AND the router address.
   - "mint an NFT" → ask for the contract address AND the mint function signature.
4. Extract as many field values as possible from the user's natural language.
5. For missing fields, generate friendly but technically accurate questions.
6. For "select" type fields with options, include the options array.
7. When a user mentions a token like BNB, ETH, USDC — extract it as both "token" and "asset".
8. Be conversational in your messages, but maintain a high degree of Web3 technical accuracy.
9. NEVER pretend a protocol is "ready to go" if we need a contract address. Be honest about TODO fragments.
10. **TIME & DATE PRECISION**: For time-based triggers, ALWAYS ask for the exact time (HH:MM) and date. Do NOT assume "now" or "in 2 minutes" unless the user explicitly says so."""

    def list_available_models(self) -> List[Dict[str, Union[str, bool]]]:
        return [{"id": mid, "label": str(cfg["label"]), "active": bool(os.getenv(str(cfg["api_key_env"])))} for mid, cfg in self.models.items()]

    # ==========================================================
    # MAIN CHAT ENTRY POINT
    # ==========================================================
    def chat(self, user_message: str, session_id: Optional[str] = None, wallet_address: Optional[str] = None, 
             known_fields: Optional[Dict[str, Any]] = None, planning_model_id: str = "gemini_flash", 
             codegen_model_id: str = "gemini_flash", project_name: Optional[str] = None) -> Dict[str, Any]:
        if not session_id:
            session_id = str(uuid.uuid4())
        if session_id not in _sessions:
            _sessions[session_id] = {
                "id": session_id, "stage": "idle",
                "wallet_address": wallet_address,
                "project_name": project_name, # Preserved project name
                "known_fields": known_fields or {},
                "history": [], "selected_trigger": None,
                "selected_actions": [], "plan_md": "", "files": {},
                "codegen_model_id": codegen_model_id,
            }

        session = _sessions[session_id]
        if wallet_address:
            session["wallet_address"] = wallet_address
            # Sync with Supabase so terminal logs can be persisted
            try:
                from runtime_store import get_store
                store = get_store()
                u_id = store.ensure_profile(wallet_address)
                p_name = session.get("project_name") or f"Chat {session_id[:8]}"
                store.get_or_create_project(name=p_name, user_id=u_id, wallet_address=wallet_address, project_id=session_id)
            except Exception as e:
                print(f"[AEGIS DB Sync Error] {e}")

        session["history"].append({"role": "user", "content": user_message})
        _sessions._save() # Explicit Save
        session["codegen_model_id"] = codegen_model_id
        if known_fields:
            session["known_fields"].update(known_fields)
        if project_name:
            session["project_name"] = project_name

        # Send everything to Gemini
        try:
            project_ctx = f"CURRENT PROJECT NAME: {session.get('project_name')}\n" if session.get('project_name') else ""
            ai_response = self._ask_gemini(session["history"], planning_model_id, project_ctx)
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
            _sessions._save() # Explicit Save
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

            # DECISION: To Plan or to Ask?
            # We only skip questions if the missing fields are "minor" technical ones.
            # Notification channels and wallet address are CRITICAL and user expects to be asked.
            critical_missing = [f for f in missing_fields if f in ["notification_channels", "wallet_address", "telegram_message", "to"]]
            
            user_input = user_message.lower()
            wants_fast_track = any(w in user_input for w in ["fast track", "skip questions", "just build it"])
            
            # If there are critical missing fields AND user didn't explicitly say "fast track", ask questions
            if critical_missing and structured_questions and not wants_fast_track:
                session["stage"] = "needs_input"
                session["history"].append({"role": "assistant", "content": agent_message})
                
                # Ensure project exists before logging (fixes FK error)
                if wallet_address:
                    try:
                        from runtime_store import get_store
                        store = get_store()
                        u_id = store.ensure_profile(wallet_address)
                        store.get_or_create_project(name=f"Chat {session_id[:8]}", user_id=u_id, wallet_address=wallet_address, project_id=session_id)
                    except Exception: pass

                log_service.log_terminal(session_id, f"❓ Critical fields missing: {', '.join(critical_missing)}. Asking user.")
                _sessions._save()
                return {
                    "session_id": session_id,
                    "stage": "needs_input",
                    "status": "waiting_for_input",
                    "agent_status": "asking",
                    "agent_message": agent_message,
                    "structured_questions": structured_questions,
                    "files": {}
                }
            
            # If we are here, we are either missing nothing, or it's non-critical/fast-track.
            log_service.log_terminal(session_id, "📝 Proceeding to planning...")

            # All fields present → generate plan
            session["stage"] = "awaiting_approval"
            log_service.log_terminal(session_id, "📝 All fields collected. Generating plan.md...")
            plan_md = self._generate_plan_md(trigger_data, actions_data, session["known_fields"])
            session["plan_md"] = plan_md
            session["history"].append({"role": "assistant", "content": agent_message})
            _sessions._save() # Explicit Save
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
                log_service.log_terminal(session_id, f"❓ Still missing fields: {', '.join(still_missing)}. Asking user for input.")
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
            log_service.log_terminal(session_id, "📝 All fields collected. Generating plan.md...")
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
        _sessions._save()
        return self._response(session_id, "idle", "chat", "greeting", agent_message)

    # ==========================================================
    # CONTINUE CHAT (follow-up field submissions)
    # ==========================================================
    def continue_chat(self, session_id: str, fields: Dict[str, Any], wallet_address: Optional[str] = None, 
                      planning_model_id: str = "gemini_flash", project_name: Optional[str] = None) -> Dict[str, Any]:
        if session_id not in _sessions:
            # Session lost after restart - gracefully transition back to a new chat
            log_service.log_terminal(session_id, "⚠️ Session not found. Restarting chat with provided context.")
            return self.chat("I'm back! Let's resume where we left off.", session_id, wallet_address=wallet_address, known_fields=fields, planning_model_id=planning_model_id, project_name=project_name)

        session = _sessions[session_id]
        if project_name:
            session["project_name"] = project_name
        if wallet_address:
            session["wallet_address"] = wallet_address
            # Sync with Supabase
            try:
                from runtime_store import get_store
                store = get_store()
                u_id = store.ensure_profile(wallet_address)
                p_name = session.get("project_name") or f"Chat {session_id[:8]}"
                store.get_or_create_project(name=p_name, user_id=u_id, wallet_address=wallet_address, project_id=session_id)
            except Exception as e:
                print(f"[AEGIS DB Sync Error] {e}")

        session["known_fields"].update(fields)

        # Build a natural message from the submitted fields
        fields_text = ", ".join([f"{k}: {v}" for k, v in fields.items()])
        user_msg = f"Here are the values: {fields_text}"
        session["history"].append({"role": "user", "content": user_msg})
        _sessions._save() # Explicit Save

        log_service.log_terminal(session_id, f"Received follow-up fields: {fields_text}")

        # Let Gemini decide if more fields are needed
        try:
            project_ctx = f"CURRENT PROJECT NAME: {session.get('project_name')}\n" if session.get('project_name') else ""
            ai_response = self._ask_gemini(session["history"], planning_model_id, project_ctx)
        except Exception as e:
            print(f"[AEGIS Continue Error] {str(e)}")
            # Try to proceed with what we have
            log_service.log_terminal(session_id, "⚠️ AI error during field update. Attempting to finalize plan with available data.")
            return self._try_finalize_plan(session_id, session)

        intent = ai_response.get("intent", "field_update")
        agent_message = ai_response.get("message", "Got it! Let me process that.")

        new_fields = ai_response.get("extracted_fields", {})
        still_missing = ai_response.get("still_missing", ai_response.get("missing_fields", []))
        structured_questions = ai_response.get("structured_questions", [])

        session["known_fields"].update(new_fields)
        session["history"].append({"role": "assistant", "content": agent_message})
        _sessions._save() # Explicit Save

        if still_missing and structured_questions:
            session["stage"] = "needs_input"
            log_service.log_terminal(session_id, f"❓ Still missing fields: {', '.join(still_missing)}. Asking user for input.")
            _sessions._save()
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
        log_service.log_terminal(session_id, "📝 All fields collected. Generating plan.md...")
        return self._try_finalize_plan(session_id, session, agent_message)

    # ==========================================================
    # APPROVE / REJECT PLAN → Gemini generates code
    # ==========================================================
    def approve_plan(self, session_id: str, approved: bool, feedback: Optional[str] = None) -> Dict[str, Any]:
        session = _sessions[session_id]
        if not approved:
            session["stage"] = "idle"
            log_service.log_terminal(session_id, "❌ Plan rejected by user. Resetting session.")
            return self._response(session_id, "idle", "chat", "reset",
                "No worries! I've scrapped that plan. What should we build instead? 🔄")

        log_service.log_terminal(session_id, "👍 Plan approved! Starting code generation...")

        # Approved → have Gemini generate the actual Python automation code
        spec = self._build_spec(session["selected_trigger"], session["selected_actions"], session["known_fields"])
        codegen_model = session.get("codegen_model_id", "gemini_flash")

        try:
            files = self._generate_code_with_gemini(spec, session["known_fields"], codegen_model)
            # Normalization: Ensure files is a Dict[str, str]
            if isinstance(files, dict):
                normalized = {}
                for name, data in files.items():
                    if isinstance(data, dict) and "content" in data:
                        normalized[name] = data["content"]
                    elif isinstance(data, str):
                        normalized[name] = data
                    else:
                        normalized[name] = str(data)
                files = normalized
        except Exception as e:
            print(f"[AEGIS Code Gen Error] {str(e)}")
            log_service.log_terminal(session_id, "❌ Code generation failed. Falling back to template-based generation.")
            # Fallback to template-based generation
            files = self._generate_workspace_files_fallback(spec, session)

        session.update({"stage": "complete", "files": files})
        log_service.log_terminal(session_id, "✅ Code generation complete!")
        _sessions._save()
        return {
            "session_id": session_id,
            "stage": "complete",
            "status": "success",
            "agent_status": "complete",
            "agent_message": "Your automation code is ready! 🚀 Check out the generated files in your workspace. The main.py has your full automation logic.",
            "files": files,
            "spec": spec
        }

    # ==========================================================
    # GEMINI COMMUNICATION
    # ==========================================================
    def _ask_gemini(self, history: List[Dict[str, str]], model_id: str, project_context: str = "") -> Dict[str, Any]:
        """Send the conversation to Gemini and get a structured JSON response."""
        if self.mock_mode:
            print("[AEGIS MOCK] MOCK_AGENT is true. Returning simulated response.")
            # Basic fallback if they turned on MOCK_AGENT due to rate limits
            return {
                "intent": "chat",
                "message": "Hey! I'm running in mock mode right now (usually because we hit API rate limits). I can't generate specific automations but I can still chat with you. Try checking your Gemini key or waiting for the quota to reset! 🤖"
            }

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

        # project_context is now passed in as an argument
        payload = {
            "conversation": conversation_text,
            "project_context": project_context
        }

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
NOTIFICATION: {json.dumps(spec.get('notification', {}), indent=2)}
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
    - CHAIN & RPC: If 'mon' or 'monad' is mentioned, YOU MUST set chain.name to "{config.CHAIN_NAME}" and chain.rpc to "{config.RPC_URL}".
    - ACTIONS: Include ALL requested actions: {json.dumps(action_types)}.
    - MUST CLEAN ACTION PARAMS: Only include fields relevant to each specific action. For 'send_native_token', ONLY include 'recipient_address' and 'amount'. For 'send_email_notification', ONLY include 'to', 'subject', and 'message'. Do NOT put trigger-only fields like 'date' or 'timezone' into action params.
    - DATES: Use the extracted 'date' and 'time' for the trigger. If 'date' is 'today', keep it as 'today' (the engine now resolves this).
    - Example schema:
        "trigger": {{ "type": "{trigger_type}", "params": {{ "date": "today", "time": "22:30", "timezone": "IST" }} }},
        "actions": [
          {{ "type": "send_native_token", "params": {{ "recipient_address": "0x...", "amount": 0.001 }} }}
        ],
        "notification": {{
          "channels": ["telegram"],
          "telegram": {{ "message": "The automation triggered successfully!" }},
          "email": {{ "to": "...", "subject": "...", "body": "..." }}
   4. "README.md" (Manual Setup Guide):
   - MUST clearly list manual configuration steps.
   - MUST highlight which fields in `config.json` need to be replaced by the user (DEX router, specific contract addresses, etc.).
   - Explain that the automation uses the **Agent Wallet** (Smart Contract) as the sender.
   - Do NOT instruct the user to enter their private key in the Chat; only mention it in the readme as a local environment setup for the executor node if absolutely necessary.

5. ".env.example":
    - Only include placeholders for **user-level** variables (e.g., specific recipient addresses or custom thresholds).
    - DO NOT include placeholders for SMTP, Supabase, or Telegram bot tokens.

IMPORTANT:
- TRIGGER PARAMS: For 'wallet_balance_below', YOU MUST include 'wallet_address', 'threshold', and 'token' inside 'trigger.params'.
- ZERO MISPLACEMENT: Do NOT put 'wallet_address' or 'threshold' in a separate 'wallet' or 'params' block outside the trigger.
- Do not generate misleading "fully working" code for protocols we don't have built-in APIs for. Use clear placeholders. RETURN ONLY VALID JSON."""

        if cfg["provider"] == "gemini":
            raw_text = self._gemini_complete_text(code_prompt, {}, cfg)
        else:
            raw_text = self._claude_complete_text(code_prompt, {}, cfg)

        try:
            files = self._extract_json(raw_text)
            if files and isinstance(files, dict) and "config.json" in files:
                config_json = files["config.json"]
                if isinstance(config_json, str):
                    try:
                        config_data = json.loads(config_json)
                        
                        # 1. Ensure Trigger structure exists
                        if "trigger" not in config_data or not isinstance(config_data["trigger"], dict):
                            config_data["trigger"] = {"type": trigger_type, "params": {}}
                        if "params" not in config_data["trigger"] or not isinstance(config_data["trigger"]["params"], dict):
                            config_data["trigger"]["params"] = {}
                        
                        tr_params = config_data["trigger"]["params"]
                        tr_type = config_data["trigger"].get("type", trigger_type)

                        # 2. Hoist MISPLACED fields from top-level "wallet" or "params"
                        misplaced_sources = [config_data.get("wallet", {}), config_data.get("params", {}), fields]
                        
                        # Define relevant fields per trigger type to avoid hallucinating unrelated fields (like date/time on wallet triggers)
                        relevant_fields = ["token", "asset", "wallet_address"] 
                        if tr_type in ["wallet_balance_below", "wallet_balance_above", "incoming_transfer_detected"]:
                            relevant_fields += ["threshold", "minimum_amount"]
                        elif tr_type.startswith("run_") or "date" in tr_type:
                            relevant_fields += ["date", "time", "timezone", "interval", "cron"]
                        elif tr_type.startswith("token_price"):
                            relevant_fields += ["threshold", "quote_currency", "price_source", "lower_bound", "upper_bound"]

                        for src in misplaced_sources:
                            if not isinstance(src, dict): continue
                            for k in relevant_fields:
                                if k in src and not tr_params.get(k):
                                    tr_params[k] = src[k]

                        # 3. CRITICAL VALIDATION: Wallet-Specific rules
                        if tr_type in ["wallet_balance_below", "wallet_balance_above", "incoming_transfer_detected"]:
                            # Force wallet consistency
                            if not tr_params.get("wallet_address") and fields.get("wallet_address"):
                                tr_params["wallet_address"] = fields["wallet_address"]
                            
                            # Force token - payment triggers NEED this
                            if not tr_params.get("token"):
                                tr_params["token"] = fields.get("token") or "MON"

                            # Threshold/Amount cleaning
                            t_key = "minimum_amount" if tr_type == "incoming_transfer_detected" else "threshold"
                            if not tr_params.get(t_key) and fields.get(t_key):
                                tr_params[t_key] = fields[t_key]
                            
                            if tr_params.get(t_key):
                                try:
                                    # Clean and convert to float
                                    val_str = str(tr_params[t_key])
                                    for unit in ["MON", "ETH", "USDT"]:
                                        val_str = val_str.replace(unit, "")
                                    tr_params[t_key] = float(val_str.strip())
                                except: pass

                        # 4. Chain Normalization
                        chain_info = config_data.get("chain", {})
                        token = str(tr_params.get("token", "")).lower()
                        asset = str(tr_params.get("asset", "")).lower()
                        
                        needs_platform_default = (
                            token in ["mon", "monad", config.CURRENCY_SYMBOL.lower()] or 
                            asset in ["mon", "monad", config.CURRENCY_SYMBOL.lower()] or
                            chain_info.get("name") == "unknown" or
                            not chain_info.get("rpc")
                        )
                        if needs_platform_default:
                            config_data["chain"] = {"name": config.CHAIN_NAME, "rpc": config.RPC_URL}

                        # 5. REMOVE Misplaced Top-Level Blocks (per user request)
                        config_data.pop("wallet", None)
                        if "params" in config_data and config_data["params"] == fields:
                             # Only remove if it's the raw fields block we passed in
                             config_data.pop("params", None)

                        # Re-sync files
                        files["config.json"] = json.dumps(config_data, indent=2)
                    except Exception as e:
                        print(f"[AEGIS Normalization Warning] {e}")
                
                if any(k.endswith(('.py', '.json', '.txt', '.md')) for k in files.keys()):
                    return files
        except Exception:
            pass

        # Fallback to template if parsing fails
        return self._generate_workspace_files_fallback(spec, {"known_fields": fields})

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
        _sessions._save() # Explicit Save
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
        # Extract notification settings for top-level spec access
        notification = {
            "channels": fields.get("notification_channels", ["email"]),
            "cooldown": fields.get("notification_cooldown") or 300,
            "telegram": {"message": fields.get("telegram_message") or "AEGIS Alert: Automation Condition Met"},
            "email": {
                "to": fields.get("to") or fields.get("email_address"),
                "subject": fields.get("email_subject") or fields.get("subject") or "AEGIS Alert",
                "body": fields.get("email_body") or fields.get("message") or "Automation condition met."
            }
        }
        
        return {
            "id": "AEGIS-" + str(uuid.uuid4())[:6],
            "trigger": trigger,
            "actions": actions if isinstance(actions, list) else [actions],
            "notification": notification,
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
    def _generate_workspace_files_fallback(self, spec: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, str]:
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

        # Clean parameters for trigger and actions
        all_params = spec["params"]
        
        # Trigger specific params
        trigger_params = {}
        if trigger_type in ["run_once_at_datetime", "run_daily_at_time", "run_between_time_window", "run_weekly_on_day_time", "run_monthly_on_date_time"]:
            trigger_params = {k: all_params[k] for k in ["date", "time", "timezone", "weekday", "day_of_month", "start_time", "end_time"] if k in all_params}
        # 1. Recover trigger if AI PLANNING failed but Fields are known
        all_params = session.get("known_fields", {})
        
        raw_trigger = spec.get("trigger")
        if isinstance(raw_trigger, dict):
            trigger_type = raw_trigger.get("type", "None")
            trigger_params = raw_trigger.get("params", {})
        else:
            trigger_type = str(raw_trigger) if raw_trigger else "None"
            trigger_params = {}
        
        # Heuristic: If planning has "None" but we have balance params, recover!
        if trigger_type == "None":
            if "token" in all_params or "asset" in all_params or "threshold" in all_params:
                trigger_type = "wallet_balance_below"
                trigger_params = {
                    "token": all_params.get("token") or all_params.get("asset") or "MON",
                    "threshold": all_params.get("threshold") or 2,
                    "wallet_address": all_params.get("wallet_address") or session.get("wallet_address") or ""
                }
            else:
                # Merge existing trigger params with known fields for persistence
                trigger_params.update({
                    "wallet_address": trigger_params.get("wallet_address") or all_params.get("wallet_address") or session.get("wallet_address") or "",
                    "threshold": trigger_params.get("threshold") or all_params.get("threshold") or 2,
                    "token": trigger_params.get("token") or all_params.get("token") or all_params.get("asset") or "MON"
                })

        # 2. Recover Chain if unknown
        chain_name = session.get("known_fields", {}).get("chain_name", config.CHAIN_NAME)
        chain_rpc = session.get("known_fields", {}).get("rpc_url", config.RPC_URL)
        
        # Broad Normalization for Platform Chain
        ctx_lower = str(all_params).lower()
        if "mon" in ctx_lower or config.CHAIN_NAME.lower() in ctx_lower:
            chain_name = config.CHAIN_NAME
            chain_rpc = config.RPC_URL

        action_types = [a.get("type", "unknown") if isinstance(a, dict) else str(a) for a in spec.get("actions", [])]
        if not action_types:
            action_types = ["log_message"] # Default useful action

        config_data = {
            "project_name": f"Automation Project {spec_id[:6]}",
            "spec_id": spec_id,
            "chain": {
                "name": chain_name,
                "rpc": chain_rpc
            },
            "wallet": {
                "address": all_params.get("wallet_address") or session.get("wallet_address") or ""
            },
            "trigger": {
                "type": trigger_type,
                "params": trigger_params
            },
            "actions": [
                {
                    "type": atype,
                    "params": {k: all_params[k] for k in ["recipient_address", "amount", "to", "subject", "message", "token", "asset"] if k in all_params},
                    "integration": {
                        "// TODO": "Replace with router_address, nft_contract, or faucet_url for this action"
                    }
                } for atype in action_types if atype not in ["send_email_notification", "send_telegram_message"]
            ],
            "notification": {
                "channels": all_params.get("notification_channels", ["email"]),
                "cooldown": all_params.get("notification_cooldown") or 300,
                "telegram": {
                    "message": all_params.get("telegram_message") or all_params.get("message") or "AEGIS Alert: Automation Condition Met"
                },
                "email": {
                    "to": all_params.get("to"),
                    "subject": all_params.get("email_subject") or all_params.get("subject") or "AEGIS Alert",
                    "body": all_params.get("email_body") or all_params.get("message") or "Your automation condition has been met."
                }
            },
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
            ".env.example": "# AEGIS Node Secrets\n# IMPORTANT: Use the PLATFORM_EXECUTOR_ADDRESS for secure execution.\n# This local .env is for advanced users running their own node infrastructure.\nRPC_URL=https://testnet-rpc.monad.xyz\nWALLET_ADDRESS=\n"
        }

    # ==========================================================
    # AI COMPLETION LAYER
    # ==========================================================
    def _fix_truncated_json(self, json_str: str) -> str:
        """Attempt to close open braces/brackets and remove trailing commas in truncated JSON."""
        json_str = json_str.strip()
        # Remove trailing commas that break parsing
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        json_str = re.sub(r',\s*$', '', json_str)
        
        # Balance braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
            
        return json_str

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
            if s == -1:
                return {"intent": "chat", "message": text}
            
            # If no closing brace, or closing brace is before opening, try to fix it
            if e == -1 or e < s:
                fixed_text = self._fix_truncated_json(text[s:])
                return json.loads(fixed_text)
                
            json_payload = text[s:e + 1]
            try:
                return json.loads(json_payload)
            except json.JSONDecodeError:
                fixed_payload = self._fix_truncated_json(json_payload)
                return json.loads(fixed_payload)
        except Exception:
            # If all fails, treat as chat response
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
        max_retries = 5  # Reduced from 10 to fail faster and notify user
        for attempt in range(max_retries):
            try:
                return m.generate_content(prompt).text.strip()
            except Exception as e:
                err_msg = str(e)
                # 429 is Rate Limit or Quota Exceeded (Resource exhausted)
                if "429" in err_msg or "Resource has been exhausted" in err_msg or "quota" in err_msg.lower():
                    # Exponential backoff with jitter
                    wait = (2 ** (attempt + 1)) + (random.randint(0, 1000) / 1000.0)
                    if attempt < max_retries - 1:
                        print(f"[Gemini 429] Rate limited (attempt {attempt + 1}/{max_retries}). Retrying in {wait:.1f}s...")
                        time.sleep(wait)
                        continue
                    else:
                        print("[Gemini 429] Quota exceeded after multiple retries. Informing user.")
                        return json.dumps({
                            "intent": "chat", 
                            "message": "I'm currently hitting a Google Gemini rate limit or quota exceeded with your key. You might need to wait a few minutes or switch to a paid tier key! 🚦"
                        })
                
                # For all other exceptions
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