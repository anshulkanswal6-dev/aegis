# AEGIS Telegram Setup Guide

This document covers the architecture, setup, and usage of the Telegram integration for AEGIS.

## 🚀 Architecture Overview
The Telegram integration consists of a thin backend module that bridges the AEGIS automation system with the Telegram Bot API.

- **Linking Engine**: Generated 10-minute one-time tokens to link Web3 wallets to Telegram accounts.
- **Webhook Handler**: Validates and processes incoming bot messages (e.g., `/start <token>`).
- **Notification Adapter**: An additional channel in the core notification adapter that delivers real-time updates.

## ⚙️ Environment Setup
Add the following to your `backend/.env` file:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_custom_random_secret
```

## 🛠️ Installation & Setup

1. **Create your Bot**:
   - Open Telegram and message [@BotFather](https://t.me/botfather).
   - Create a new bot and copy the API Token.
2. **Apply DB Schema**:
   - Run the SQL in `backend/scripts/telegram_migration.sql` in your Supabase SQL Editor.
3. **Set Webhook**:
   - Ensure your backend is public (e.g., using ngrok for local testing).
   - Run: `python backend/scripts/setup_telegram.py`
4. **Restart Backend**:
   - The `/api/telegram` endpoints are now active.

## 🔔 Usage in Automations
To enable Telegram notifications for an automation, include a `notify` action in the `spec_json` with `channel: "telegram"`.

**JSON Example:**
```json
{
  "type": "notify",
  "params": {
    "channel": "telegram",
    "message": "Automation success! Payment of 1 ETH sent."
  }
}
```

## 🧪 Testing Checklist
- [x] **Link Flow**: Navigate to /integrations, click Connect, and follow bot prompts.
- [x] **Relinking**: Linking a new account overwrites the old one.
- [x] **Collisions**: One Telegram account cannot be linked to multiple AEGIS users.
- [x] **Test Message**: Use the "Send Test" button on the Integrations page.
- [x] **Silent Failure**: If the bot is blocked by a user, the automation execution still completes.
