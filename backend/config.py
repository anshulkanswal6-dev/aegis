"""
AEGIS Runtime Configuration
Central config for the local runtime environment.
All values are designed to be overridden by environment variables later.
"""

import os
from pathlib import Path

# =========================================================
# Paths
# =========================================================
BASE_DIR = Path(__file__).parent.resolve()
RUNTIME_DATA_DIR = BASE_DIR / ".runtime_data"

# =========================================================
# Runtime Store Backend
# =========================================================
# Options: "memory", "json_file", "supabase"
STORE_BACKEND = os.getenv("AEGIS_STORE_BACKEND", "json_file")

# Supabase Credentials (only used when STORE_BACKEND == "supabase")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Path for the JSON-file store (only used when STORE_BACKEND == "json_file")
STORE_JSON_PATH = RUNTIME_DATA_DIR / "automations.json"
LOGS_JSON_PATH = RUNTIME_DATA_DIR / "logs.json"
TERMINAL_LOGS_JSON_PATH = RUNTIME_DATA_DIR / "terminal_logs.json"

# =========================================================
# Scheduler / Polling
# =========================================================
# How often (seconds) the worker polls monitoring-type automations
POLLING_INTERVAL_SECONDS = int(os.getenv("AEGIS_POLL_INTERVAL", "30"))

# Default interval for scheduled automations when none is specified
DEFAULT_SCHEDULE_INTERVAL_SECONDS = int(os.getenv("AEGIS_DEFAULT_INTERVAL", "60"))

# Maximum number of logs kept per automation (ring buffer)
MAX_LOGS_PER_AUTOMATION = int(os.getenv("AEGIS_MAX_LOGS", "200"))

# =========================================================
# Worker
# =========================================================
# Whether the background worker auto-starts with the API server
WORKER_AUTOSTART = os.getenv("AEGIS_WORKER_AUTOSTART", "true").lower() == "true"

# =========================================================
# Demo Flags
# =========================================================
# When True, triggers use mock/stub data (already the default in trigger_engine)
DEMO_MODE = os.getenv("AEGIS_DEMO_MODE", "true").lower() == "true"

# =========================================================
# RPC defaults (used by execution_service when spec doesn't provide one)
# =========================================================
DEFAULT_RPC_URL = os.getenv("RPC_URL", "https://testnet-rpc.monad.xyz")
DEFAULT_CHAIN = os.getenv("DEFAULT_CHAIN", "monad-testnet")
