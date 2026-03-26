"""
AEGIS Log Service
=================
Structured logging into the runtime store.
Thin wrapper around RunLogEntry creation + store.add_log().
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from runtime_store import RunLogEntry, get_store


def _write(automation_id: str, level: str, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> RunLogEntry:
    """Internal helper — creates and persists a log entry."""
    entry = RunLogEntry(
        automation_id=automation_id,
        level=level,
        event=event,
        message=message,
        details=details,
    )
    store = get_store()
    store.add_log(entry)
    # Also print to console for demo visibility
    print(f"[AEGIS {level.upper()}] [{automation_id[:8]}] {event}: {message}")
    return entry


def log_info(automation_id: str, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> RunLogEntry:
    return _write(automation_id, "info", event, message, details)


def log_warn(automation_id: str, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> RunLogEntry:
    return _write(automation_id, "warn", event, message, details)


def log_error(automation_id: str, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> RunLogEntry:
    return _write(automation_id, "error", event, message, details)


def log_debug(automation_id: str, event: str, message: str, details: Optional[Dict[str, Any]] = None) -> RunLogEntry:
    return _write(automation_id, "debug", event, message, details)


def log_exception(automation_id: str, event: str, exc: Exception) -> RunLogEntry:
    """Log an exception with full traceback in details."""
    return _write(
        automation_id, "error", event,
        str(exc),
        {"traceback": traceback.format_exc()}
    )


def get_logs(automation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent logs for an automation."""
    store = get_store()
    entries = store.get_logs(automation_id, limit=limit)
    return [e.to_dict() for e in entries]


def clear_logs(automation_id: str) -> int:
    """Clear all logs for an automation. Returns count deleted."""
    store = get_store()
    return store.clear_logs(automation_id)
