import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load env from parent directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class NotificationAdapter:
    # In-memory cooldown cache: {automation_id: timestamp}
    _last_sent_cache = {}
    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASS")

    def send_email(self, to_email: str, subject: str, body: str, automation_id: str = "unknown", wallet: str = "unknown"):
        # 1. Safety Check: Config missing
        if not self.smtp_user or not self.smtp_password:
            print("[NotificationAdapter] SMTP not configured — skipping email")
            return {"success": False, "error": "SMTP not configured"}

        # 2. Cooldown Check
        now = time.time()
        last_sent = self._last_sent_cache.get(automation_id, 0)
        if (now - last_sent) < self.COOLDOWN_SECONDS:
            remaining = int(self.COOLDOWN_SECONDS - (now - last_sent))
            print(f"[NotificationAdapter] Email skipped (cooldown active for {automation_id}: {remaining}s left)")
            return {"success": False, "error": "cooldown_active", "remaining": remaining}

        # 3. Handle to_email parsing
        clean_email = to_email.strip("[]")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 4. Standardize Email Format (Branding + Footer)
        formatted_subject = f"[OnchainAgent] {subject}"
        
        branded_body = f"""
--------------------------------
⚡ OnchainAgent Automation Alert
--------------------------------

{body}

--------------------------------
Automation ID: {automation_id}
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
