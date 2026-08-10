"""
===============================================================================
API Security Dependency (security.py)
===============================================================================
Provides authentication dependency functions used to protect API routes.
Enforces header-based authentication by validating the `key-secret` HTTP header
against the configured `ADMIN_KEY` environment variable.
===============================================================================
"""

from fastapi import HTTPException, Header, status
from app.core.config import ADMIN_KEY


def verify_key_secret(key_secret: str = Header(...)):
    """
    FastAPI Security Dependency:
    ----------------------------
    Inspects incoming HTTP request headers for `key-secret`.
    Compares the provided header value against `ADMIN_KEY`.

    Raises:
    -------
    HTTPException (401 Unauthorized):
        If `key-secret` header is missing or does not match `ADMIN_KEY`.
    """
    if key_secret != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing key secret. Access denied."
        )



