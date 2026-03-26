"""
AEGIS Runtime Service
=====================
Core orchestration logic:
- Deploy automations into the runtime store
- Evaluate trigger conditions using TriggerEngine
- Execute actions via execution_service when triggers match
- Update automation status and metrics
"""

from __future__ import annotations

import os
import re
import traceback
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from trigger_engine import TriggerEngine, TriggerContext
from runtime_store import AutomationRecord, get_store
from config import DEFAULT_CHAIN, DEFAULT_RPC_URL, DEFAULT_SCHEDULE_INTERVAL_SECONDS
import log_service
import execution_service


# Shared trigger engine instance
_trigger_engine = TriggerEngine()


# =========================================================
# Interval parsing helper
# =========================================================

_INTERVAL_MULTIPLIERS = {
    "s": 1, "sec": 1, "seconds": 1,
    "m": 60, "min": 60, "minutes": 60,
    "h": 60 * 60, "hr": 60 * 60, "hours": 60 * 60,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
}


def parse_interval_to_seconds(interval_str: str) -> int:
    """Parse '30s', '5m', '1h', '24h' etc. to seconds."""
    match = re.match(r"^(\d+)\s*([a-zA-Z]+)$", str(interval_str).strip())
    if not match:
        return DEFAULT_SCHEDULE_INTERVAL_SECONDS
    value = int(match.group(1))
    unit = match.group(2).lower()
    multiplier = _INTERVAL_MULTIPLIERS.get(unit, 1)
    return value * multiplier


# =========================================================
# Deploy
# =========================================================

def deploy_automation(
    name: str,
    spec_json: Dict[str, Any],
    session_id: str = "",
    description: str = "",
    files: Optional[Dict[str, str]] = None,
) -> AutomationRecord:
    """
    Deploy an automation into the runtime store.
    Returns the created AutomationRecord.
    """
    store = get_store()
    
    # Optional: Check if session already exists in store and update it
    # This prevents duplicate active registrations for the same session
    existing = None
    if session_id:
        all_records = store.list_automations()
        for r in all_records:
            if r.session_id == session_id:
                existing = r
                break
    
    # Calculate next_run_at based on trigger type
    interval_seconds = _get_interval_from_spec(spec_json)
    next_run = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)

    if existing:
        automation_id = existing.id
        print(f"[AEGIS Deployment] Updating existing automation: {automation_id}")
        record = store.update_automation(automation_id, {
            "name": name,
            "description": description,
            "spec_json": spec_json,
            "status": "active",
            "next_run_at": next_run.isoformat(),
            "files": files or {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        if not record:
             raise Exception(f"Failed to update existing record {automation_id}")
    else:
        automation_id = str(uuid.uuid4())
        record = AutomationRecord(
            id=automation_id,
            name=name,
            description=description,
            session_id=session_id,
            spec_json=spec_json,
            status="active", # Explicitly set to active upon deployment
            next_run_at=next_run.isoformat(),
            files=files or {},
        )
        store.save_automation(record)

    # Specific Deployment Log
    log_service.log_info(
        automation_id, "deployed",
        f"Automation '{name}' deployed and activated.",
        {"trigger_type": _get_trigger_type(spec_json), "interval_seconds": interval_seconds}
    )
    print(f"[AEGIS Deployment] Automation {automation_id} is now ACTIVE.")

    return record


# =========================================================
# Evaluate a single automation
# =========================================================

def evaluate_automation(automation_id: str) -> Dict[str, Any]:
    """
    Evaluate a single automation:
    1. Load from store
    2. Check trigger condition
    3. If matched, execute actions
    4. Update metrics and logs

    Returns: {"triggered": bool, "result": ...}
    """
    store = get_store()
    record = store.get_automation(automation_id)

    if not record:
        return {"triggered": False, "error": "Automation not found"}

    if record.status != "active":
        return {"triggered": False, "error": f"Automation is {record.status}"}

    spec = record.spec_json
    trigger_type = _get_trigger_type(spec)
    trigger_params = _get_trigger_params(spec)

    # Build TriggerContext with new spec structure support
    # Structure: spec["chain"]["name"], spec["wallet"]["address"], etc.
    chain_info = spec.get("chain", {})
    wallet_info = spec.get("wallet", {})
    
    chain = chain_info.get("name") or spec.get("params", {}).get("chain", DEFAULT_CHAIN)
    rpc_url = chain_info.get("rpc") or spec.get("params", {}).get("rpc_url", DEFAULT_RPC_URL) or os.getenv("RPC_URL", "")
    
    # Wallet address with fallback to trigger params
    wallet_address = wallet_info.get("address") or trigger_params.get("wallet_address") or spec.get("params", {}).get("wallet_address", "") or os.getenv("WALLET_ADDRESS", "")

    ctx = TriggerContext(
        chain=chain,
        rpc_url=rpc_url,
        wallet_address=wallet_address,
        now=datetime.now(timezone.utc),
        memory={},
    )

    # Defensive validation: Log if wallet_address is missing for known sensitive triggers
    wallet_sensitive_triggers = ["wallet_balance_below", "wallet_balance_above", "test_balance_low_then_claim_faucet"]
    if trigger_type in wallet_sensitive_triggers and not wallet_address:
        log_service.log_error(automation_id, "context_error", "wallet_address missing from deployed automation spec during trigger evaluation")

    # Debug Logging
    print(f"[AEGIS DEBUG] evaluating {trigger_type} for wallet {wallet_address or 'N/A'} on {chain or 'N/A'}")
    log_service.log_debug(automation_id, "trigger_check", "automation checked condition", {
        "trigger_type": trigger_type,
        "wallet": wallet_address,
        "chain": chain,
        "rpc": rpc_url
    })

    try:
        triggered = _trigger_engine.evaluate(trigger_type, trigger_params, ctx)
    except Exception as e:
        log_service.log_exception(automation_id, "trigger_error", e)
        store.update_automation(automation_id, {
            "error_count": record.error_count + 1,
            "last_error": str(e),
        })
        return {"triggered": False, "error": str(e)}

    now_iso = datetime.now(timezone.utc).isoformat()

    if triggered:
        log_service.log_info(automation_id, "trigger_matched", "automation live")

        # Execute actions
        def _log_fn(event: str, message: str, details: Optional[Dict] = None):
            log_service.log_info(automation_id, event, message, details)

        result = execution_service.execute_actions(spec, _log_fn, automation_id=automation_id)

        # Calculate next_run_at
        interval_seconds = _get_interval_from_spec(spec)
        next_run = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)

        update_fields = {
            "last_run_at": now_iso,
            "next_run_at": next_run.isoformat(),
            "run_count": record.run_count + 1,
        }

        # Auto-complete for run_once triggers
        if trigger_type == "run_once_at_datetime":
            update_fields["status"] = "completed"
            print(f"[AEGIS Runtime] Automation {automation_id} marked as COMPLETED (run-once).")

        if not result["success"]:
            update_fields["error_count"] = record.error_count + 1
            update_fields["last_error"] = str(result.get("errors", []))

        store.update_automation(automation_id, update_fields)
        return {"triggered": True, "result": result}
    else:
        # Not triggered — still update next_run_at
        interval_seconds = _get_interval_from_spec(spec)
        next_run = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
        store.update_automation(automation_id, {"next_run_at": next_run.isoformat()})
        return {"triggered": False}


# =========================================================
# Query helpers
# =========================================================

def get_active_automations() -> List[AutomationRecord]:
    """Return all active automations."""
    store = get_store()
    return store.list_automations(status="active")


def get_all_automations(status: Optional[str] = None) -> List[AutomationRecord]:
    """Return all automations, optionally filtered by status."""
    store = get_store()
    return store.list_automations(status=status)


def pause_automation(automation_id: str) -> Optional[AutomationRecord]:
    """Pause an active automation."""
    store = get_store()
    record = store.update_automation(automation_id, {"status": "paused"})
    if record:
        log_service.log_info(automation_id, "paused", "automation paused")
    return record


def resume_automation(automation_id: str) -> Optional[AutomationRecord]:
    """Resume a paused automation."""
    store = get_store()
    record = store.update_automation(automation_id, {"status": "active"})
    if record:
        log_service.log_info(automation_id, "resumed", "automation live")
    return record


def delete_automation(automation_id: str) -> bool:
    """Delete an automation from the store."""
    store = get_store()
    log_service.log_info(automation_id, "deleted", "Automation deleted by user")
    return store.delete_automation(automation_id)


def get_automation_detail(automation_id: str) -> Optional[Dict[str, Any]]:
    """Get full automation details including recent logs."""
    store = get_store()
    record = store.get_automation(automation_id)
    if not record:
        return None
    data = record.to_dict()
    data["recent_logs"] = log_service.get_logs(automation_id, limit=20)
    return data


# =========================================================
# Internal helpers
# =========================================================

def _get_trigger_type(spec: Dict[str, Any]) -> str:
    """Extract trigger type from spec_json."""
    trigger = spec.get("trigger", {})
    if isinstance(trigger, dict):
        return trigger.get("type", "run_every_interval")
    return str(trigger)


def _get_trigger_params(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Extract trigger params from spec_json."""
    trigger = spec.get("trigger", {})
    if isinstance(trigger, dict):
        # Params can be nested under trigger.params or at top-level spec.params
        trigger_params = trigger.get("params", {})
        # Merge with top-level params for backward compatibility
        top_params = spec.get("params", {})
        return {**top_params, **trigger_params}
    return spec.get("params", {})


def _get_interval_from_spec(spec: Dict[str, Any]) -> int:
    """Determine the polling/scheduling interval from spec_json."""
    # Check runtime.interval_seconds first
    runtime = spec.get("runtime", {})
    if isinstance(runtime, dict) and "interval_seconds" in runtime:
        return int(runtime["interval_seconds"])

    # Check trigger params for interval
    trigger_params = _get_trigger_params(spec)
    if "interval" in trigger_params:
        return parse_interval_to_seconds(str(trigger_params["interval"]))

    return DEFAULT_SCHEDULE_INTERVAL_SECONDS
