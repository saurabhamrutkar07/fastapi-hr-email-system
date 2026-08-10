"""
===============================================================================
JSONL File Email Logger (email_logger.py)
===============================================================================
Provides append-only local file logging for email dispatches.
Writes JSON Lines (`.jsonl`) entries to `logs/email_logs.jsonl` for offline audit.
===============================================================================
"""

import json
from datetime import datetime
from pathlib import Path

# Path to local JSONL log file
LOG_FILE = Path("logs/email_logs.jsonl")


def log_email(
    recipient_email: str,
    status: str,
    error: str | None = None
):
    """
    Appends an email audit log entry to the local JSONL log file.

    Parameters:
    -----------
    recipient_email : str
        Email address of recipient HR.
    status : str
        "SUCCESS" or "FAILED".
    error : str | None
        Optional error string or exception details if status is "FAILED".
    """
    # Ensure `logs/` directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)

    # Construct log dictionary
    log_entry = {
        "recipient_email": recipient_email,
        "status": status,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Append JSON record as a new line
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

