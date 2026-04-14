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
# Platform / Admin Credentials (INTERNAL ONLY)
# =========================================================

# --- AI Engine ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEFAULT_PLANNING_MODEL = os.getenv("DEFAULT_PLANNING_MODEL", "gemini_flash")
DEFAULT_CODEGEN_MODEL = os.getenv("DEFAULT_CODEGEN_MODEL", "gemini_flash")

# --- Notifications (Infrastructure) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

# Legacy SMTP (to be deprecated)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# --- Blockchain / Monad (Platform Defaults) ---
RPC_URL = os.getenv("RPC_URL", "https://testnet-rpc.monad.xyz")
EXPLORER_URL = os.getenv("EXPLORER_URL", "https://testnet.monadexplorer.com")
CHAIN_ID = int(os.getenv("CHAIN_ID", "10143"))
CHAIN_NAME = os.getenv("CHAIN_NAME", "Monad Testnet")
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "MON")

# --- Smart Contracts ---
AGENT_WALLET_FACTORY_ADDRESS = os.getenv("AGENT_WALLET_FACTORY_ADDRESS", "0x8cbb60c06569E93a2A0AE09bc00988f62753E73E")
PLATFORM_EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS", "0xf7C7FfEdc58B49C75C56019710B2C5C597C5E29E")

# --- Execution Node ---
# This key is used by the backend worker to sign transactions
EXECUTOR_PRIVATE_KEY = os.getenv("EXECUTOR_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

# --- Storage (Supabase Admin) ---
# Options: "memory", "json_file", "supabase"
STORE_BACKEND = os.getenv("STORE_BACKEND") or "supabase"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") # Should be Service Role Key

# --- Telegram Bot ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "Aegis_telebot")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

# =========================================================
# Runtime / Scheduling Defaults
# =========================================================
DEFAULT_CHAIN = CHAIN_NAME                       # alias used by runtime_service
DEFAULT_RPC_URL = RPC_URL                        # alias used by runtime_service
DEFAULT_SCHEDULE_INTERVAL_SECONDS = int(os.getenv("DEFAULT_SCHEDULE_INTERVAL_SECONDS", "60"))
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "30"))
WORKER_AUTOSTART = os.getenv("WORKER_AUTOSTART", "true").lower() in ("true", "1", "yes")

# =========================================================
# Local JSON File Store Paths (fallback when STORE_BACKEND=json_file)
# =========================================================
RUNTIME_DATA_DIR = Path(os.getenv("RUNTIME_DATA_DIR", Path(__file__).parent / "runtime_data"))
STORE_JSON_PATH = RUNTIME_DATA_DIR / "automations.json"
LOGS_JSON_PATH = RUNTIME_DATA_DIR / "logs.json"
TERMINAL_LOGS_JSON_PATH = RUNTIME_DATA_DIR / "terminal_logs.json"
MAX_LOGS_PER_AUTOMATION = int(os.getenv("MAX_LOGS_PER_AUTOMATION", "200"))

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
        "GEMINI_API_KEY": bool(GEMINI_API_KEY),
        "TELEGRAM_BOT_TOKEN": bool(TELEGRAM_BOT_TOKEN),
        "SUPABASE_KEY": bool(SUPABASE_KEY),
        "EXECUTOR_PRIVATE_KEY": bool(EXECUTOR_PRIVATE_KEY),
        "RESEND_CONFIG": bool(RESEND_API_KEY),
        "RPC_URL": bool(RPC_URL),
        "FACTORY_ADDR": bool(AGENT_WALLET_FACTORY_ADDRESS),
        "CHAIN_NAME": CHAIN_NAME,
    }
    SYSTEM_STATUS["env_vars"] = vars_to_check
    return vars_to_check

# --- Feature Flags (Computed) ---
check_env_vars()

# Subsystem Status Flags
EMAIL_CONFIG_READY = bool(RESEND_API_KEY)
TELEGRAM_CONFIG_READY = bool(TELEGRAM_BOT_TOKEN)
SUPABASE_CONFIG_READY = bool(SUPABASE_URL and SUPABASE_KEY)
BLOCKCHAIN_CONFIG_READY = bool(EXECUTOR_PRIVATE_KEY and RPC_URL)

def get_system_report():
    """Build a report of the current system status for API/UI visibility."""
    return {
        "identity": {
            "name": CHAIN_NAME,
            "symbol": CURRENCY_SYMBOL,
            "chain_id": CHAIN_ID
        },
        "features": {
            "email": EMAIL_CONFIG_READY,
            "telegram": TELEGRAM_CONFIG_READY,
            "storage": STORE_BACKEND if SUPABASE_CONFIG_READY else "memory",
            "execution": BLOCKCHAIN_CONFIG_READY
        },
        "health": "healthy" if (SUPABASE_CONFIG_READY and BLOCKCHAIN_CONFIG_READY) else "degraded"
    }

def validate_config():
    """Print a startup report and return missing critical vars."""
    env = SYSTEM_STATUS["env_vars"]
    report = []
    
    print("\n" + "="*40)
    print(" AEGIS SYSTEM STARTUP ".center(40, "="))
    print("="*40)
    
    # Infrastructure
    infra = [
        ("Gemini AI", bool(GEMINI_API_KEY)),
        ("Supabase", SUPABASE_CONFIG_READY),
        ("Blockchain", BLOCKCHAIN_CONFIG_READY),
        ("Telegram", TELEGRAM_CONFIG_READY),
        ("Resend/Email", EMAIL_CONFIG_READY),
    ]
    
    for label, active in infra:
        status = "[READY]" if active else "[DISABLED / MISSING]"
        print(f"  {label.ljust(15)}: {status}")
        if not active:
            report.append(label)
            
    print("="*40)
    print(f" [Chain] {CHAIN_NAME} ({CHAIN_ID})")
    print(f" [RPC]   {RPC_URL}")
    print("="*40 + "\n")
    
    return report

# Perform initial check
validate_config()
