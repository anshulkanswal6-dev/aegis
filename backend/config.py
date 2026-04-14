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
# Mission-Critical Validation
# =========================================================
def validate_config():
    """Ensure essential variables are present for the current backend mode."""
    critical_errors = []
    
    # 1. AI Features
    if not os.getenv("GEMINI_API_KEY"):
        critical_errors.append("MISSING: GEMINI_API_KEY (Required for Chat/GenAI)")

    # 2. Persistence
    if STORE_BACKEND == "supabase":
        if not SUPABASE_URL or not SUPABASE_KEY:
            critical_errors.append("MISSING: SUPABASE_URL/KEY (Required for 'supabase' STORE_BACKEND)")
    
    # 3. Integrations
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("[Config] WARNING: TELEGRAM_BOT_TOKEN missing. Bot features will be disabled.")
    
    if critical_errors:
        print("\n❌ CRITICAL CONFIGURATION ERROR:")
        for err in critical_errors:
            print(f"  - {err}")
        print("\nPlease check your .env file or environment settings.\n")
        # In production, we might want to sys.exit(1), but for now we just log/notify.

validate_config()
