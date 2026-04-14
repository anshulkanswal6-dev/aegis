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
        "SMTP_AUTH": bool(SMTP_USER and SMTP_PASS),
        "RPC_URL": bool(RPC_URL),
        "FACTORY_ADDR": bool(AGENT_WALLET_FACTORY_ADDRESS),
        "CHAIN_NAME": CHAIN_NAME,
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
