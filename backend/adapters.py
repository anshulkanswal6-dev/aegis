import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests
from typing import Optional

# Load env from parent directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

import config

class NotificationAdapter:
    # In-memory cooldown cache: {automation_id: timestamp}
    _last_sent_cache = {}
    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASS

    def send_email(self, to_email: str, subject: str, body: str, automation_id: str = "unknown", wallet: str = "unknown", cooldown: Optional[int] = None, project_name: str = ""):
        # 1. Safety Check: Config missing
        if not self.smtp_user or not self.smtp_password:
            print("[NotificationAdapter] SMTP not configured — skipping email")
            return {"success": False, "error": "SMTP not configured"}

        # 2. Cooldown Check
        now = time.time()
        last_sent = self._last_sent_cache.get(automation_id, 0)
        cooldown_period = cooldown if cooldown is not None else self.COOLDOWN_SECONDS
        
        if (now - last_sent) < cooldown_period:
            remaining = int(cooldown_period - (now - last_sent))
            print(f"[NotificationAdapter] Email skipped (cooldown active for {automation_id}: {remaining}s left)")
            return {"success": False, "error": "cooldown_active", "remaining": remaining}

        # 3. Handle to_email parsing
        clean_email = to_email.strip("[]")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 4. Standardize Email Format (Branding + Footer)
        formatted_subject = f"[AEGIS] {project_name if project_name else subject}"
        
        p_info = f"Project: {project_name}\n" if project_name else ""
        branded_body = f"""
--------------------------------
⚡ AEGIS Automation Alert
--------------------------------

{body}

--------------------------------
{p_info}Automation ID: {automation_id}
Wallet: {wallet}
Time: {timestamp}
--------------------------------
"""

        msg = MIMEMultipart()
        # ALWAYS use the admin email as sender
        msg['From'] = f"Aegis Platform <{self.smtp_user}>"
        msg['To'] = clean_email
        msg['Subject'] = formatted_subject

        msg.attach(MIMEText(branded_body, 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_user, clean_email, text)
            server.quit()
            
            # Update cache on success
            self._last_sent_cache[automation_id] = now
            
            print(f"[NotificationAdapter] SUCCESS: Email sent to {clean_email} for automation {automation_id}")
            return {"success": True}
        except Exception as e:
            print(f"[NotificationAdapter] FAILURE: Could not send email: {str(e)}")
            return {"success": False, "error": str(e)}

    def send_telegram(self, user_id: str, message: str, automation_id: str = "unknown", cooldown: Optional[int] = None, project_name: str = ""):
        """Sends a Telegram notification to a linked account."""
        # 1. Cooldown Check
        now = time.time()
        cooldown_period = cooldown if cooldown is not None else self.COOLDOWN_SECONDS

        # Shared cache with email for now, or separate if preferred.
        # Let's keep it shared so we don't spam both channels.
        last_sent = self._last_sent_cache.get(f"tg_{automation_id}", 0)
        if (now - last_sent) < cooldown_period:
            remaining = int(cooldown_period - (now - last_sent))
            print(f"[NotificationAdapter] Telegram skipped (cooldown active for {automation_id}: {remaining}s left)")
            return {"success": False, "error": "cooldown_active", "remaining": remaining}

        # 2. Get Chat ID (Import locally to avoid core circularity)
        try:
            from integrations.telegram.linking import get_telegram_account
            account = get_telegram_account(user_id)
            if not account:
                return {"success": False, "error": "no_account_linked"}
            
            # Resolve account info (chat_id)
            print(f"[NotificationAdapter] Resolving Telegram account for Profile ID: {user_id}")
            
            chat_id = account.get("telegram_chat_id")
            if not chat_id:
                  error_code = "no_account_linked" if user_id != "00000000-0000-0000-0000-000000000000" else "system_user_no_channel"
                  print(f"[NotificationAdapter] FAILURE: No Telegram account linked to Profile {user_id}")
                  return {"success": False, "error": error_code}

            from integrations.telegram.service import TelegramService
            tg_service = TelegramService()
            
            print(f"[NotificationAdapter] Sending Telegram to Profile ID: {user_id}, Chat ID: {chat_id}")
            
            # Rich HTML formatting with ID and Project Name
            formatted = f"<b>⚠️ AEGIS Alert</b>\n"
            formatted += f"🆔 <code>{automation_id}</code>\n"
            if project_name:
                formatted += f"📂 <b>Project: {project_name}</b>\n"
            
            formatted += f"\n{message}"
            
            res = tg_service.send_message_detailed(chat_id, formatted)
            if res.get("success"):
                self._last_sent_cache[f"tg_{automation_id}"] = now
                print(f"[NotificationAdapter] SUCCESS: Telegram sent to chat {chat_id}")
                return {"success": True}
            else:
                err = res.get("error", "send_failed")
                print(f"[NotificationAdapter] FAILURE: Telegram delivery failed for {chat_id}: {err}")
                return {"success": False, "error": err}

        except Exception as e:
            print(f"[NotificationAdapter] Telegram failure: {str(e)}")
            return {"success": False, "error": str(e)}
