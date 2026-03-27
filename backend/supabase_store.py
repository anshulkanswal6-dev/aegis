"""
AEGIS Supabase Store — Production Persistence
==============================================
Implements RuntimeStoreBase using Supabase (PostgreSQL + PostgREST).
Anchors all records to wallet_address for identity persistence.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from supabase import create_client, Client

from runtime_store import RuntimeStoreBase, AutomationRecord, RunLogEntry, TerminalLogEntry
from config import SUPABASE_URL, SUPABASE_KEY

class SupabaseStore(RuntimeStoreBase):
    """Production-grade store using Supabase."""

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env for SupabaseStore")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # --- Automations ---

    def save_automation(self, record: AutomationRecord) -> AutomationRecord:
        data = record.to_dict()
        # Ensure we use snake_case for Supabase if needed, 
        # but our dataclass fields already match the SQL schema.
        result = self.client.table("automations").upsert(data).execute()
        return record

    def get_automation(self, automation_id: str) -> Optional[AutomationRecord]:
        result = self.client.table("automations").select("*").eq("id", automation_id).execute()
        if not result.data:
            return None
        return AutomationRecord.from_dict(result.data[0])

    def list_automations(self, status: Optional[str] = None) -> List[AutomationRecord]:
        query = self.client.table("automations").select("*")
        if status:
            query = query.eq("status", status)
        
        # Note: In a real multi-user app, we'd filter by wallet_address here too,
        # but the backend runtime service currently handles global listing for the worker.
        # RLS in Supabase will handle the user-specific filtering.
        
        result = query.execute()
        return [AutomationRecord.from_dict(d) for d in result.data]

    def update_automation(self, automation_id: str, updates: Dict[str, Any]) -> Optional[AutomationRecord]:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = self.client.table("automations").update(updates).eq("id", automation_id).execute()
        if not result.data:
            return None
        return AutomationRecord.from_dict(result.data[0])

    def delete_automation(self, automation_id: str) -> bool:
        result = self.client.table("automations").delete().eq("id", automation_id).execute()
        return len(result.data) > 0

    # --- Logs ---

    def add_log(self, entry: RunLogEntry) -> RunLogEntry:
        self.client.table("run_logs").insert(entry.to_dict()).execute()
        return entry

    def get_logs(self, automation_id: str, limit: int = 50) -> List[RunLogEntry]:
        result = self.client.table("run_logs") \
            .select("*") \
            .eq("automation_id", automation_id) \
            .order("timestamp", desc=True) \
            .limit(limit) \
            .execute()
        # Reverse to get chronological order for UI if needed, or keep desc
        return [RunLogEntry.from_dict(d) for d in result.data]

    def clear_logs(self, automation_id: str) -> int:
        result = self.client.table("run_logs").delete().eq("automation_id", automation_id).execute()
        return len(result.data)

    # --- Terminal Logs ---

    def add_terminal_log(self, entry: TerminalLogEntry) -> TerminalLogEntry:
        self.client.table("terminal_logs").insert(entry.to_dict()).execute()
        return entry

    def get_terminal_logs(self, project_id: str, limit: int = 100) -> List[TerminalLogEntry]:
        # Filter out soft-cleared logs
        result = self.client.table("terminal_logs") \
            .select("*") \
            .eq("project_id", project_id) \
            .is_("cleared_at", "null") \
            .order("timestamp", desc=True) \
            .limit(limit) \
            .execute()
        return [TerminalLogEntry.from_dict(d) for d in result.data]

    def clear_terminal_logs(self, project_id: str) -> int:
        # Soft clear: update cleared_at
        now = datetime.now(timezone.utc).isoformat()
        result = self.client.table("terminal_logs") \
            .update({"cleared_at": now}) \
            .eq("project_id", project_id) \
            .is_("cleared_at", "null") \
            .execute()
        return len(result.data)
