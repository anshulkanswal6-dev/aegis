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
    if WORKER_AUTOSTART:
        worker = get_worker()
        worker.start()
        print("[AEGIS API] Worker auto-started.")


async def shutdown_worker():
    """Called on FastAPI shutdown to stop the worker."""
    worker = get_worker()
    worker.stop()
    print("[AEGIS API] Worker stopped.")


# =========================================================
# Endpoints
# =========================================================

def _normalize_spec_json(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize spec_json: fix chain/rpc and clean action params before deploy."""
    chain_info = spec.get("chain", {})
    trigger_params = {}
    if isinstance(spec.get("trigger"), dict):
        trigger_params = spec["trigger"].get("params", {})
    
    # Detect Monad Testnet from token/asset mentions
    token = str(trigger_params.get("token", "")).lower()
    asset = str(trigger_params.get("asset", "")).lower()
    chain_name = str(chain_info.get("name", "")).lower()
    rpc = str(chain_info.get("rpc", ""))
    
    needs_monad = (
        token in ["mon", "monad"] or
        asset in ["mon", "monad"] or
        chain_name == "unknown" or
        not rpc
    )
    
    if needs_monad:
        spec["chain"] = {
            "name": "Monad Testnet",
            "rpc": "https://testnet-rpc.monad.xyz"
        }
    
    # Clean action params: only keep relevant fields per action type
    CLEAN_PARAMS = {
        "send_native_token": ["recipient_address", "amount"],
        "send_email_notification": ["to", "subject", "message"],
    }
    
    actions = spec.get("actions", [])
    for action in actions:
        if not isinstance(action, dict):
            continue
        atype = action.get("type", "")
        if atype in CLEAN_PARAMS:
            raw_params = action.get("params", {})
            clean = {k: raw_params[k] for k in CLEAN_PARAMS[atype] if k in raw_params}
            action["params"] = clean
        # Remove TODO integration stubs
        action.pop("integration", None)
    
    # Clean trigger params: only keep trigger-relevant fields
    TRIGGER_FIELDS = ["date", "time", "timezone", "wallet_address", "token", "asset", "threshold"]
    if trigger_params:
        clean_trigger = {k: trigger_params[k] for k in TRIGGER_FIELDS if k in trigger_params}
        spec["trigger"]["params"] = clean_trigger
    
    return spec


@router.post("/deploy", response_model=None)
async def deploy_automation(req: DeployRequest):
    """Deploy a new automation into the local runtime."""
    try:
        # Normalize spec before storing
        normalized_spec = _normalize_spec_json(req.spec_json)
        
        record = runtime_service.deploy_automation(
            name=req.name,
            spec_json=normalized_spec,
            session_id=req.session_id,
            wallet_address=req.wallet_address,
            description=req.description,
            files=req.files,
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_automations(status: Optional[str] = None):
    """List all automations, optionally filtered by status."""
    automations = runtime_service.get_all_automations(status=status)
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
