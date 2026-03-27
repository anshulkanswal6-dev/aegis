"""
AEGIS Execution Service
=======================
Executes actions from a structured spec_json using the existing ActionEngine.
Does NOT run generated main.py files — uses engines directly.
"""

from __future__ import annotations

import os
import traceback
from typing import Any, Callable, Dict, List, Optional

from action_engine import ActionEngine, ActionContext
from config import DEFAULT_RPC_URL, DEFAULT_CHAIN


# Shared engine instance
_action_engine = ActionEngine()


def execute_actions(
    spec_json: Dict[str, Any],
    log_fn: Optional[Callable] = None,
    automation_id: str = "unknown",
) -> Dict[str, Any]:
    """
    Execute all actions defined in a spec_json.

    Args:
        spec_json: The automation specification with trigger/actions/params.
        log_fn: Optional callable(event, message, details) for logging.
        automation_id: Unique ID for the automation being executed.

    Returns:
        {"success": bool, "results": [...], "errors": [...]}
    """
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # Build ActionContext from new spec structure
    chain_info = spec_json.get("chain", {})
    wallet_info = spec_json.get("wallet", {})
    trigger_params = {}
    if isinstance(spec_json.get("trigger"), dict):
        trigger_params = spec_json["trigger"].get("params", {})
    
    # Merge for backward compatibility
    top_params = spec_json.get("params", {})
    merged = {**top_params, **trigger_params}

    chain = chain_info.get("name") or merged.get("chain", DEFAULT_CHAIN)
    rpc_url = chain_info.get("rpc") or merged.get("rpc_url", DEFAULT_RPC_URL) or os.getenv("RPC_URL", "")
    wallet_address = wallet_info.get("address") or merged.get("wallet_address", "") or os.getenv("WALLET_ADDRESS", "")

    ctx = ActionContext(
        chain=chain,
        rpc_url=rpc_url,
        wallet_address=wallet_address,
        automation_id=automation_id,
        secrets={"private_key": os.getenv("PRIVATE_KEY", "")},
        memory={},
    )

    actions = spec_json.get("actions", [])
    if not isinstance(actions, list):
        actions = [actions]

    def safe_log(event: str, message: str, details: Optional[Dict] = None):
        if not log_fn:
            return
        try:
            log_fn(event, message, details)
        except Exception as le:
            print(f"[AEGIS CRITICAL] Logging system failed: {le}")

    for i, action in enumerate(actions):
        action_type = action.get("type", "unknown") if isinstance(action, dict) else str(action)
        
        # Build action_params by merging global context with action-specific overrides
        action_params = {merged_key: merged_val for merged_key, merged_val in merged.items()}
        if isinstance(action, dict) and action.get("params"):
            action_params.update(action["params"])

        safe_log("action_start", f"Executing action {i+1}/{len(actions)}: {action_type}", {"action_type": action_type})

        try:
            result = _action_engine.execute(action_type, action_params, ctx)
            success = result.get("success", False)
            
            # Map action type to natural language for the status stream
            msg = f"automation executed {action_type}"
            if action_type == "send_native_token":
                if success:
                    msg = f"automation sent payment to {action_params.get('recipient_address', 'recipient')}"
                else:
                    msg = f"payment failed: {result.get('error', 'unknown error')}"
            elif action_type == "send_erc20":
                if success:
                    msg = f"automation sent ERC20 to {action_params.get('recipient_address', 'recipient')}"
                else:
                    msg = f"ERC20 transfer failed: {result.get('error', 'unknown error')}"
            elif action_type == "swap":
                msg = f"automation swapped {action_params.get('from_token', 'token')} to {action_params.get('to_token', 'token')}"
            elif action_type == "send_email_notification":
                if success:
                    msg = "email sent"
                elif result.get("error") == "cooldown_active":
                    msg = f"email skipped (cooldown: {result.get('remaining')}s)"
                else:
                    msg = "email failed"
            elif action_type == "notify":
                msg = f"automation sent notification via {action_params.get('channel', 'email')}"
            elif action_type == "log_message":
                msg = action_params.get('message', 'automation logged a message')

            if success:
                safe_log("action_executed", msg, result)
            else:
                safe_log("action_failed", msg, result)

            results.append({
                "index": i,
                "action_type": action_type,
                "result": result,
            })

            if not success:
                errors.append({
                    "index": i,
                    "action_type": action_type,
                    "error": result.get("error", "Action returned success=False"),
                })
                # ABORT remaining actions (like notifications) if a critical action fails
                safe_log("execution_aborted", "stopping automation cycle due to action failure", {"failed_index": i})
                break

        except Exception as e:
            error_info = {
                "index": i,
                "action_type": action_type,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            errors.append(error_info)
            safe_log("action_error", f"Action {action_type} failed with exception: {str(e)}", error_info)
            break

    overall_success = len(errors) == 0
    return {
        "success": overall_success,
        "total_actions": len(actions),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }
