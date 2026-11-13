"""
===============================================================================
Request ID + error safety net (app/core/request_id.py)
===============================================================================
Every request gets a short id:
- printed on every log line written while handling it (common/Logger.py)
- sent back in the X-request-ID response header
- tagged on Sentry errors, and shown to the user if something crashes
So "it failed, ref: 3f9c2a1b7d4e" leads stringht to the matching log lines. 
An unexpected error becomes a clean 500 {detail} insted of a raw crash. 
===============================================================================
"""

import re 
import time 
import uuid

import sentry_sdk
from fastapi import Request
from fastapi.responses import JSONResponse

from common.Logger import Logger, request_id_var

logger = Logger.get_logger()

HEADER = "X-Request-ID"

# Reuse an id from the proxy (Nginx) only if it looks safe to print in logs
SAFE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")
# Polled by uptime checks; logging each one would only add noise
QUIET_PATHS = {"/health"}

async def request_id_middleware(request: Request,call_next):
    incoming = request.headers.get(HEADER,"")
    request_id = incoming if SAFE_ID.match(incoming) else uuid.uuid4().hex[:12]
    token = request_id_var.set(request_id)
    sentry_sdk.set_tag("request_id", request_id)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception as exc:
            # Anything a route didn't handle: log it in full, report it,
            # and give user a short message with the reference id 
            logger.exception(f"Unhandled error on {request.method} {request.url.path}")
            sentry_sdk.capture_exception(exc)
            response = JSONResponse(
                status_code=500,
                content={"detail": f"Something went wrong on our side. Please try again. (ref: {request_id})"}
            )
        took_ms = (time.perf_counter() - started) * 1000 
        if request.url.path not in QUIET_PATHS:
            logger.info(f"{request.method} {request.url.path} -> {response.status_code} in {took_ms:.0f} ms")
        response.headers[HEADER] = request_id
        return response
    finally:
        request_id_var.reset(token)