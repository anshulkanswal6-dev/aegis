"""
AEGIS Runtime Store — Temporary Storage Abstraction
====================================================
Provides CRUD for deployed automations, run history, and logs.

Current backends:
  - InMemoryStore   (fast, no persistence across restarts)
  - JsonFileStore   (persists to local JSON files, survives restarts)

Future:
  - SupabaseStore   (swap in with single config change)

All backends implement the same abstract interface (RuntimeStoreBase).
"""

from __future__ import annotations

import json
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import STORE_JSON_PATH, LOGS_JSON_PATH, MAX_LOGS_PER_AUTOMATION, RUNTIME_DATA_DIR


# =========================================================
# Data Models
# =========================================================

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AutomationRecord:
    """Represents a deployed automation in the runtime."""
    id: str
    name: str
    description: str = ""
    session_id: str = ""
    # The structured spec produced by the agent (trigger + actions + params)
    spec_json: Dict[str, Any] = field(default_factory=dict)
    # status model: draft | planning | approved | ready_for_deploy | active | paused | failed
    status: str = "ready_for_deploy"
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    # Agent-generated workspace files (for reference / export)
    files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AutomationRecord":
        return AutomationRecord(**{k: v for k, v in d.items() if k in AutomationRecord.__dataclass_fields__})


@dataclass
class RunLogEntry:
    """A single execution log entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    automation_id: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)
    level: str = "info"  # info | warn | error | debug
    event: str = ""      # trigger_check | trigger_matched | action_executed | error
    message: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "RunLogEntry":
        return RunLogEntry(**{k: v for k, v in d.items() if k in RunLogEntry.__dataclass_fields__})


# =========================================================
# Abstract Base
# =========================================================

class RuntimeStoreBase(ABC):
    """Abstract interface — swap implementations without changing callers."""

    # --- Automations ---
    @abstractmethod
    def save_automation(self, record: AutomationRecord) -> AutomationRecord: ...

    @abstractmethod
    def get_automation(self, automation_id: str) -> Optional[AutomationRecord]: ...

    @abstractmethod
    def list_automations(self, status: Optional[str] = None) -> List[AutomationRecord]: ...

    @abstractmethod
    def update_automation(self, automation_id: str, updates: Dict[str, Any]) -> Optional[AutomationRecord]: ...

    @abstractmethod
    def delete_automation(self, automation_id: str) -> bool: ...

    # --- Logs ---
    @abstractmethod
    def add_log(self, entry: RunLogEntry) -> RunLogEntry: ...

    @abstractmethod
    def get_logs(self, automation_id: str, limit: int = 50) -> List[RunLogEntry]: ...

    @abstractmethod
    def clear_logs(self, automation_id: str) -> int: ...


# =========================================================
# In-Memory Store
# =========================================================

class InMemoryStore(RuntimeStoreBase):
    """Thread-safe in-memory store. Data lost on restart."""

    def __init__(self):
        self._lock = threading.Lock()
        self._automations: Dict[str, Dict[str, Any]] = {}
        self._logs: Dict[str, List[Dict[str, Any]]] = {}

    def save_automation(self, record: AutomationRecord) -> AutomationRecord:
        with self._lock:
            self._automations[record.id] = record.to_dict()
            return record

    def get_automation(self, automation_id: str) -> Optional[AutomationRecord]:
        with self._lock:
            d = self._automations.get(automation_id)
            return AutomationRecord.from_dict(d) if d else None

    def list_automations(self, status: Optional[str] = None) -> List[AutomationRecord]:
        with self._lock:
            items = list(self._automations.values())
        records = [AutomationRecord.from_dict(d) for d in items]
        if status:
            records = [r for r in records if r.status == status]
        return records

    def update_automation(self, automation_id: str, updates: Dict[str, Any]) -> Optional[AutomationRecord]:
        with self._lock:
            if automation_id not in self._automations:
                return None
            self._automations[automation_id].update(updates)
            self._automations[automation_id]["updated_at"] = _utcnow_iso()
            return AutomationRecord.from_dict(self._automations[automation_id])

    def delete_automation(self, automation_id: str) -> bool:
        with self._lock:
            if automation_id in self._automations:
                del self._automations[automation_id]
                self._logs.pop(automation_id, None)
                return True
            return False

    def add_log(self, entry: RunLogEntry) -> RunLogEntry:
        with self._lock:
            bucket = self._logs.setdefault(entry.automation_id, [])
            bucket.append(entry.to_dict())
            if len(bucket) > MAX_LOGS_PER_AUTOMATION:
                self._logs[entry.automation_id] = bucket[-MAX_LOGS_PER_AUTOMATION:]
            return entry

    def get_logs(self, automation_id: str, limit: int = 50) -> List[RunLogEntry]:
        with self._lock:
            bucket = self._logs.get(automation_id, [])
            return [RunLogEntry.from_dict(d) for d in bucket[-limit:]]

    def clear_logs(self, automation_id: str) -> int:
        with self._lock:
            count = len(self._logs.get(automation_id, []))
            self._logs.pop(automation_id, None)
            return count


# =========================================================
# JSON File Store
# =========================================================

class JsonFileStore(RuntimeStoreBase):
    """Persists to local JSON files. Survives restarts."""

    def __init__(self, automations_path: Path = STORE_JSON_PATH, logs_path: Path = LOGS_JSON_PATH):
        self._lock = threading.Lock()
        self._auto_path = automations_path
        self._logs_path = logs_path
        # Ensure directory exists
        self._auto_path.parent.mkdir(parents=True, exist_ok=True)
        self._logs_path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing data
        self._automations = self._load_json(self._auto_path)
        self._logs = self._load_json(self._logs_path)

    def _reload(self):
        """Reload data from disk if it exists."""
        # Note: In a production scenario, we'd check mtime first.
        # For a local demo, a simple reload is robust.
        self._automations = self._load_json(self._auto_path)
        self._logs = self._load_json(self._logs_path)

    @staticmethod
    def _load_json(path: Path) -> Dict:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                         print(f"WARNING: {path.name} was not a dict, resetting to empty.")
                         return {}
                    return data
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _flush_automations(self):
        with open(self._auto_path, "w", encoding="utf-8") as f:
            json.dump(self._automations, f, indent=2, default=str)

    def _flush_logs(self):
        with open(self._logs_path, "w", encoding="utf-8") as f:
            json.dump(self._logs, f, indent=2, default=str)

    def save_automation(self, record: AutomationRecord) -> AutomationRecord:
        with self._lock:
            self._automations[record.id] = record.to_dict()
            self._flush_automations()
            return record

    def get_automation(self, automation_id: str) -> Optional[AutomationRecord]:
        with self._lock:
            self._reload()
            d = self._automations.get(automation_id)
            return AutomationRecord.from_dict(d) if d else None

    def list_automations(self, status: Optional[str] = None) -> List[AutomationRecord]:
        with self._lock:
            self._reload()
            items = list(self._automations.values())
        records = [AutomationRecord.from_dict(d) for d in items]
        if status:
            records = [r for r in records if r.status == status]
        return records

    def update_automation(self, automation_id: str, updates: Dict[str, Any]) -> Optional[AutomationRecord]:
        with self._lock:
            self._reload()
            if automation_id not in self._automations:
                return None
            self._automations[automation_id].update(updates)
            self._automations[automation_id]["updated_at"] = _utcnow_iso()
            self._flush_automations()
            return AutomationRecord.from_dict(self._automations[automation_id])

    def delete_automation(self, automation_id: str) -> bool:
        with self._lock:
            self._reload()
            if automation_id in self._automations:
                del self._automations[automation_id]
                self._logs.pop(automation_id, None)
                self._flush_automations()
                self._flush_logs()
                return True
            return False

    def add_log(self, entry: RunLogEntry) -> RunLogEntry:
        with self._lock:
            self._reload()
            bucket = self._logs.setdefault(entry.automation_id, [])
            bucket.append(entry.to_dict())
            if len(bucket) > MAX_LOGS_PER_AUTOMATION:
                self._logs[entry.automation_id] = bucket[-MAX_LOGS_PER_AUTOMATION:]
            self._flush_logs()
            return entry

    def get_logs(self, automation_id: str, limit: int = 50) -> List[RunLogEntry]:
        with self._lock:
            self._reload()
            bucket = self._logs.get(automation_id, [])
            return [RunLogEntry.from_dict(d) for d in bucket[-limit:]]

    def clear_logs(self, automation_id: str) -> int:
        with self._lock:
            self._reload()
            count = len(self._logs.get(automation_id, []))
            self._logs.pop(automation_id, None)
            self._flush_logs()
            return count


# =========================================================
# Factory — returns the configured store singleton
# =========================================================

_store_instance: Optional[RuntimeStoreBase] = None
_store_lock = threading.Lock()


def get_store() -> RuntimeStoreBase:
    """Return the global store singleton based on config.STORE_BACKEND."""
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                from config import STORE_BACKEND
                if STORE_BACKEND == "json_file":
                    _store_instance = JsonFileStore()
                else:
                    _store_instance = InMemoryStore()
    return _store_instance
