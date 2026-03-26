from adapters import NotificationAdapter

notifier = NotificationAdapter()

print("--- First Attempt ---")
notifier.send_email(
    to_email="[anshulkanswal01@gmail.com]",
    subject="Security Alert: Unusual Activity Detected",
    body="Our monitoring system has detected unusual contract interaction in your watched wallet.",
    automation_id="demo-test-123",
    wallet="0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
)

print("\n--- Second Attempt (Should be skipped by cooldown) ---")
notifier.send_email(
    to_email="[anshulkanswal01@gmail.com]",
    subject="Security Alert: Unusual Activity Detected",
    body="Our monitoring system has detected unusual contract interaction in your watched wallet.",
    automation_id="demo-test-123",
    wallet="0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
)
