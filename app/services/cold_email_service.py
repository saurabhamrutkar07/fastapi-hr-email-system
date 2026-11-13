"""
===============================================================================
Cold Email Helpers (cold_email_service.py)
===============================================================================
Small helpers the Send page's flow (send_service.py) uses:
1. The user's Gmail settings and active resume, from the request's session.
2. Downloading the resume from S3 without blocking the event loop.
3. Rendering a user's Jinja template safely (sandboxed).
4. Turning an SMTP exception into an error code and a readable message.
===============================================================================
"""

import asyncio
import smtplib
from fastapi import HTTPException, status
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import TEMPLATE_DIR
from app.models.models import UserSMTPCredential, UserResume
from app.core.s3_storage import s3_storage
from common.Logger import Logger

logger = Logger.get_logger()

# Created once at import; sandboxed so a user's template can't run Python
env = SandboxedEnvironment(
    loader = FileSystemLoader(TEMPLATE_DIR),
    autoescape = False
)

async def get_user_smtp_config(db: AsyncSession, user_id: int)-> UserSMTPCredential:
    """
    Fetches and returns the given user's SMTP credential row.
    Raises 400 if user hasn't configured their own SMTP sender
    yet -- cold emails are always sent from the user's own account,
    never a shared/global one.
    """
    result = await db.execute(
        select(UserSMTPCredential).where(UserSMTPCredential.user_id == user_id)
    )
    credential = result.scalar_one_or_none()
    if credential is None or not credential.is_active:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "SMTP credential not configured. Please set them up before sending emails."
        )
    return credential


async def get_user_active_resume_path(db: AsyncSession, user_id: int) -> str:
    """
    Where the given user's active resume is kept in S3. Raises 400 if the
    user hasn't uploaded/activated one yet -- cold emails require a
    per-user resume, there is no shared fallback.
    """
    result = await db.execute(
        select(UserResume.file_path).where(
            UserResume.user_id == user_id,
            UserResume.is_active == True,
        )
    )
    file_path = result.scalars().first()
    if file_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "No active resume found. Please upload one before sending emails."
        )
    return file_path


async def download_resume(file_path: str) -> bytes:
    """The resume's bytes from S3, without blocking the event loop."""
    return await asyncio.to_thread(s3_storage.download_file, file_path)


def render_cold_email(content: str,context: dict) -> str:
    """
    Renders a user-supplied Jinja template string (from the database)
    with the provided context parameters.
    """
    template = env.from_string(content)
    return template.render(**context)


def smtp_reason(e: Exception) -> str:
    """The mail server's own words for an SMTP error, shortened."""
    text = getattr(e, "smtp_error", b"") or str(e)
    if isinstance(text, bytes):
        text = text.decode(errors="replace")
    return " ".join(text.split())[:200]


def is_sending_limit(e: Exception) -> bool:
    """Gmail's "daily sending limit exceeded" / "rate limited" answers."""
    if not isinstance(e, smtplib.SMTPResponseException):
        return False
    reason = smtp_reason(e).lower()
    return any(word in reason for word in ("limit", "quota", "rate"))


def classify_email_exception(e: Exception) -> tuple[str, str]:
    """
    Turns an exception from sending one email into (error_code, message).
    The message is what the user sees on the Send and History pages: what
    happened and what to do. The raw error is logged by the caller.

    - CREDENTIALS_EXPIRED: Gmail rejected the App Password
    - SENDING_LIMIT: Gmail's sending limit (daily or per-minute) is reached
    - RECIPIENT_NOT_FOUND: the address was refused (may not exist)
    - ATTACHMENT_MISSING: the resume couldn't be attached
    - CONNECTION_FAILED: the mail server couldn't be reached / timed out
    - SMTP_ERROR: any other refusal, with the server's reason
    - UNKNOWN_ERROR: anything else
    """
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return "CREDENTIALS_EXPIRED", "Gmail didn't accept your App Password. Create a new one and save it on the Gmail settings page."
    if isinstance(e, smtplib.SMTPRecipientsRefused):
        return "RECIPIENT_NOT_FOUND", "The mail server refused this address. It may be mistyped or no longer exist."
    if is_sending_limit(e):
        return "SENDING_LIMIT", "Gmail's sending limit is reached. Try again later; the daily limit resets within 24 hours."
    if isinstance(e, FileNotFoundError):
        return "ATTACHMENT_MISSING", "Your resume couldn't be attached. Upload it again and retry."
    if isinstance(e, (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError)):
        return "CONNECTION_FAILED", "Couldn't reach the mail server. Try again in a few minutes."
    # Before OSError: every smtplib error is also an OSError
    if isinstance(e, smtplib.SMTPException):
        return "SMTP_ERROR", f"The mail server didn't accept this email: {smtp_reason(e)}"
    if isinstance(e, OSError):
        # Timeouts, refused connections, DNS failures
        return "CONNECTION_FAILED", "Couldn't reach the mail server. Try again in a few minutes."
    return "UNKNOWN_ERROR", "Something went wrong while sending this email. Try again."
