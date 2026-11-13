"""
===============================================================================
Rate Limiting (app/core/rate_limit.py)
===============================================================================
Caps how often one client (by IP address) may call endpoint that guess
password, send emails or cost money, using slowapi. A client over the limit 
gets 429 Too Many Requests With a message the frontend can show.

Limits are per worker process while counters live in memory (the default);
set RATE_LIMIT_STORAGE to a Redis URL to share them between workers.
Set RATE_LIMIT_ENABLED=false to switch limiting off, for example in tests.

Behind Nginx, run uvicorn with --proxy-headers so the client's real IP is 
used instead of Nginx's
===============================================================================
"""

import os 

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://")
)

# Password and code guessing 
LOGIN = "5/minute;30/hour"
VERIFY_OTP = "5/minute"
RESET_PASSWORD = "5/minute"
SET_PASSWORD = "5/minute"
REFRESH = "30/minute"
GOOGLE_EXCHANGE = "10/minute"
# Each of these sends an email, so they could be used to spam someone
SIGNUP = "3/minute;10/hour"
FORGOT_PASSWORD = "3/minute;10/hour"
SMTP_CHECK = "5/minute"
SEND_EMAILS = "10/minute"


async def rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """ 429 in the same {"detail": ...} shape as every other error, so the UI can show it."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many attempts. Please wait a minute and try again."}
    )