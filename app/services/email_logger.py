import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("logs/email_logs.jsonl")

def log_email(
    recipient_email: str,
    status: str,
    error: str | None = None
):
    LOG_FILE.parent.mkdir(exist_ok=True)

    log_entry = {
        "recipient_email": recipient_email,
        "status": status,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
