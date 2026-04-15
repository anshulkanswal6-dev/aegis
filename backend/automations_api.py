"""
AEGIS Automations API
=====================
FastAPI router for the local runtime environment.
Endpoints for deploy, list, detail, pause, resume, delete, logs, and runs.
Also manages worker lifecycle via FastAPI startup/shutdown events.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

import runtime_service
import log_service
from worker import get_worker
from config import WORKER_AUTOSTART
from integrations.telegram.poller import start_telegram_poller, stop_telegram_poller


import os
from web3 import Web3


router = APIRouter(prefix="/automations", tags=["automations"])


# =========================================================
# Request / Response Models
# =========================================================

class DeployRequest(BaseModel):
    name: str
    description: str = ""
    session_id: str = ""
    automation_id: Optional[str] = None # Added to prevent duplicates
    project_id: Optional[str] = None    # Explicit project linkage from frontend
    wallet_address: Optional[str] = None # Added for Supabase identity
    spec_json: Dict[str, Any]
    files: Dict[str, str] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    success: bool
    message: str
    automation_id: Optional[str] = None


# =========================================================
# Lifecycle — Worker auto-start/stop
# =========================================================

async def startup_worker():
    """Called on FastAPI startup to boot the worker."""
    from config import SYSTEM_STATUS
    if not WORKER_AUTOSTART:
        print("[AEGIS API] Worker autostart is disabled.")
        return

    # 1. Start Core Worker
    try:
        worker = get_worker()
        worker.start()
        print("[AEGIS API] Core Worker Engine started.")
    except Exception as e:
        print(f"[AEGIS API] ERROR starting Worker: {e}")
        SYSTEM_STATUS["worker"] = f"error: {str(e)}"

    # 2. Start Telegram Poller (Lazy)
    import config
    if config.TELEGRAM_BOT_TOKEN:
        try:
            from integrations.telegram.poller import _poller
            start_telegram_poller()
            SYSTEM_STATUS["telegram"] = "connected"
            print(f"[AEGIS API] Telegram Poller active (@{config.TELEGRAM_BOT_USERNAME or 'unknown'})")
        except Exception as e:
            print(f"[AEGIS API] ERROR starting Telegram Poller: {e}")
            SYSTEM_STATUS["telegram"] = "error"
    else:
        SYSTEM_STATUS["telegram"] = "disabled (missing token)"
        print("[AEGIS API] Telegram Poller skipped: TELEGRAM_BOT_TOKEN not found.")


async def shutdown_worker():
    """Called on FastAPI shutdown to stop the worker."""
    try:
        worker = get_worker()
        worker.stop()
        stop_telegram_poller()
        print("[AEGIS API] Subsystems shut down.")
    except:
        pass


# =========================================================
# Endpoints
# =========================================================

def _normalize_spec_json(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize spec_json: fix chain/rpc and clean action params before deploy."""
    chain_info = spec.get("chain", {})
    trigger = spec.get("trigger", {})
    trigger_params = {}
    
    if isinstance(trigger, dict):
        trigger_params = trigger.get("params", {})
    
    # Detect Monad Testnet from token/asset mentions
    token = str(trigger_params.get("token", "")).lower()
    asset = str(trigger_params.get("asset", "")).lower()
    chain_name = str(chain_info.get("name", "")).lower()
    rpc = str(chain_info.get("rpc", ""))
    
    if any(x in ["mon", "monad"] for x in [token, asset]) or chain_name == "unknown" or not rpc:
        spec["chain"] = {
            "name": "Monad Testnet",
            "rpc": "https://testnet-rpc.monad.xyz"
        }
    
    # Clean action params
    CLEAN_PARAMS = {
        "send_native_token": ["recipient_address", "amount"],
        "send_erc20": ["token_address", "recipient_address", "amount"],
        "swap": ["from_token", "to_token", "amount", "router_address"],
    }
    
    actions = spec.get("actions", [])
    if isinstance(actions, list):
        for action in actions:
            if isinstance(action, dict):
                atype = action.get("type", "")
                if atype in CLEAN_PARAMS:
                    raw_params = action.get("params", {})
                    action["params"] = {k: raw_params[k] for k in CLEAN_PARAMS[atype] if k in raw_params}
                action.pop("integration", None)
    
    # Clean notification params
    NOTIF_FIELDS = {
        "email": ["to", "subject", "body"],
        "telegram": ["message"]
    }
    notification = spec.get("notification")
    if isinstance(notification, dict):
        for channel, fields in NOTIF_FIELDS.items():
            if channel in notification and isinstance(notification[channel], dict):
                raw = notification[channel]
                notification[channel] = {k: raw[k] for k in fields if k in raw}

    # Clean trigger params: be inclusive to support balance monitoring and complex conditions
    TRIGGER_FIELDS = [
        "date", "time", "timezone", "wallet_address", "token", "asset", "threshold", 
        "target_balance", "chain", "network", "symbol", "operator", "value"
    ]
    if isinstance(trigger, dict) and "params" in trigger:
        raw_tp = trigger["params"]
        # Filter to known good, but also preserve anything that looks like a valid variable
        trigger["params"] = {k: raw_tp[k] for k in raw_tp if k in TRIGGER_FIELDS or not k.startswith("_")}
    
    return spec


@router.post("/deploy", response_model=None)
async def deploy_automation(req: DeployRequest):
    """Deploy a new automation into the local runtime."""
    try:
        # Normalize incoming IDs: convert 'undefined' or '' to None
        proj_id = req.project_id if req.project_id and req.project_id != "undefined" else None
        auto_id = req.automation_id if req.automation_id and req.automation_id != "undefined" else None

        # Normalize spec before storing
        normalized_spec = _normalize_spec_json(req.spec_json)
        
        record = runtime_service.deploy_automation(
            name=req.name,
            spec_json=normalized_spec,
            session_id=req.session_id,
            automation_id=auto_id,
            project_id=proj_id,
            wallet_address=req.wallet_address or "",
            description=req.description,
            files=req.files
        )

        # Schedule it in the worker
        worker = get_worker()
        interval = runtime_service._get_interval_from_spec(req.spec_json)
        worker.schedule_new_automation(record.id, interval)

        print(f"[AEGIS API] Deploying automation: {record.id} ({record.name})")

        return {
            "success": True,
            "message": f"Automation '{record.name}' deployed successfully.",
            "automation_id": record.id,
            "automation": record.to_dict(),
        }
    except Exception as e:
        import traceback
        error_msg = f"Deployment Exception: {str(e)}\n{traceback.format_exc()}"
        print(f"[AEGIS Deployment ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/")
async def list_automations(status: Optional[str] = None, project_id: Optional[str] = None, wallet_address: Optional[str] = None):
    """List automations scoped to the requesting user's wallet.
    
    Privacy: If wallet_address is provided, only automations belonging to that
    wallet's profile are returned. This prevents cross-user data leakage.
    """
    automations = runtime_service.get_all_automations(
        status=status, 
        project_id=project_id, 
        wallet_address=wallet_address
    )
    return {
        "automations": [a.to_dict() for a in automations],
        "total": len(automations),
    }


@router.get("/{automation_id}")
async def get_automation(automation_id: str):
    """Get detailed info for a single automation."""
    data = runtime_service.get_automation_detail(automation_id)
    if not data:
        raise HTTPException(status_code=404, detail="Automation not found")
    return data


@router.post("/{automation_id}/pause")
async def pause_automation(automation_id: str):
    """Pause an active automation."""
    record = runtime_service.pause_automation(automation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Automation not found")

    # Remove from scheduler
    worker = get_worker()
    worker.unschedule_automation(automation_id)

    return {"success": True, "message": "Automation paused", "automation": record.to_dict()}


@router.post("/{automation_id}/resume")
async def resume_automation(automation_id: str):
    """Resume a paused automation."""
    record = runtime_service.resume_automation(automation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Automation not found")

    # Re-schedule in worker
    worker = get_worker()
    interval = runtime_service._get_interval_from_spec(record.spec_json)
    worker.schedule_new_automation(automation_id, interval)

    return {"success": True, "message": "Automation resumed", "automation": record.to_dict()}


@router.delete("/{automation_id}")
async def delete_automation(automation_id: str):
    """Delete an automation."""
    # Remove from scheduler first
    worker = get_worker()
    worker.unschedule_automation(automation_id)

    deleted = runtime_service.delete_automation(automation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Automation not found")

    return {"success": True, "message": "Automation deleted"}
 
 
@router.patch("/{automation_id}")
async def update_automation(automation_id: str, updates: Dict[str, Any]):
    """Update an automation's metadata (name, description, etc)."""
    try:
        from runtime_service import update_automation_record
        record = update_automation_record(automation_id, updates)
        if not record:
            raise HTTPException(status_code=404, detail="Automation not found")
        return {"success": True, "automation": record.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{automation_id}/logs")
async def get_automation_logs(automation_id: str, limit: int = 50):
    """Get execution logs for an automation."""
    logs = log_service.get_logs(automation_id, limit=limit)
    return {"automation_id": automation_id, "logs": logs, "total": len(logs)}


@router.get("/{automation_id}/runs")
async def get_automation_runs(automation_id: str):
    """Get run history summary for an automation."""
    data = runtime_service.get_automation_detail(automation_id)
    if not data:
        raise HTTPException(status_code=404, detail="Automation not found")

    return {
        "automation_id": automation_id,
        "name": data.get("name"),
        "status": data.get("status"),
        "run_count": data.get("run_count", 0),
        "error_count": data.get("error_count", 0),
        "last_run_at": data.get("last_run_at"),
        "next_run_at": data.get("next_run_at"),
        "last_error": data.get("last_error"),
        "created_at": data.get("created_at"),
    }


@router.get("/{automation_id}/trigger-now")
async def trigger_now(automation_id: str):
    """Manually trigger an automation evaluation (for testing/debugging)."""
    result = runtime_service.evaluate_automation(automation_id)
    return {"automation_id": automation_id, "result": result}


@router.get("/worker/status")
async def worker_status():
    """Get the worker status."""
    worker = get_worker()
    return {"running": worker.is_running}


@router.get("/executor/address")
async def get_executor_address():
    """Return the public address of the backend executor node."""
    key = os.getenv("EXECUTOR_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
    if not key:
        return {"address": None, "error": "No executor key found in .env"}
    try:
        w3 = Web3()
        acc = w3.eth.account.from_key(key)
        return {"address": acc.address}
    except Exception as e:
        return {"address": None, "error": str(e)}


# --- Terminal Logs ---

@router.get("/terminal/{session_id}/logs")
async def get_terminal_logs(session_id: str, limit: int = 100):
    """Get terminal logs for a project session."""
    logs = log_service.get_terminal_logs(session_id, limit=limit)
    return {"session_id": session_id, "logs": logs, "total": len(logs)}


@router.post("/terminal/{session_id}/clear")
async def clear_terminal_logs(session_id: str):
    """Clear terminal logs for a session."""
    count = log_service.clear_terminal_logs(session_id)
    return {"success": True, "count": count}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get the persistent agent session state (for workspace restoration)."""
    import agent
    state = agent.get_session_state(session_id)
    if not state:
        return {"success": False, "message": "Session not found"}
    return {
        "success": True,
        "session": {
           "id": state.get("id"),
           "stage": state.get("stage"),
           "files": state.get("files", {}),
           "plan_md": state.get("plan_md", ""),
           "known_fields": state.get("known_fields", {}),
           "selected_trigger": state.get("selected_trigger"),
           "selected_actions": state.get("selected_actions", [])
        }
    }
