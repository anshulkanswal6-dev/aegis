"""
AEGIS Runtime Configuration
Central config for the local runtime environment.
All values are designed to be overridden by environment variables later.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# =========================================================
# Paths
# =========================================================
BASE_DIR = Path(__file__).parent.resolve()
RUNTIME_DATA_DIR = BASE_DIR / ".runtime_data"

# =========================================================
# Runtime Store Backend
# =========================================================
# Options: "memory", "json_file", "supabase"
STORE_BACKEND = os.getenv("STORE_BACKEND") or os.getenv("AEGIS_STORE_BACKEND") or "json_file"

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

# =========================================================
# System Status Tracking
# =========================================================
SYSTEM_STATUS = {
    "api": "active",
    "worker": "pending",
    "scheduler": "pending",
    "telegram": "pending",
    "storage": STORE_BACKEND,
    "env_vars": {}
}

def check_env_vars():
    """Build a map of critical environment variables for health checks."""
    vars_to_check = {
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
        "EXECUTOR_PRIVATE_KEY": bool(os.getenv("EXECUTOR_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")),
        "RPC_URL": bool(os.getenv("RPC_URL")),
    }
    SYSTEM_STATUS["env_vars"] = vars_to_check
    return vars_to_check

def validate_config():
    """Return a report of the current configuration status."""
    env = check_env_vars()
    report = []
    
    print("\n--- AEGIS STARTUP ENV CHECK ---")
    for var, exists in env.items():
        status = "✅ PRESENT" if exists else "❌ MISSING"
        print(f"  {var.ljust(22)}: {status}")
        if not exists:
            report.append(var)
    print("-------------------------------\n")
    return report

# Perform check on load but don't crash the module
check_env_vars()
