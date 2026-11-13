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


def classify_email_exception(e: Exception) -> tuple[str,str]:
    """
    Turns an SMTP/Python exception into (error_code, error_details):
    CREDENTIALS_EXPIRED, RECIPENT_NOT_FOUND, ATTACHMENT_MISSING, 
    CONNECTION_FAILED, SMTP_ERROR or UNKNOWN_ERROR.
    """
    if isinstance(e, smtplib.SMTPAuthenticationError):
        error_code = "CREDENTIALS_EXPIRED"
        error_details = f"Authentication failed: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e)}"
    elif isinstance(e, smtplib.SMTPRecipientsRefused):
        error_code = "RECIPIENT_NOT_FOUND"
        error_details = f"Recipient email invalid or refused: {str(e)}"
    elif isinstance(e, FileNotFoundError):
        error_code = "ATTACHMENT_MISSING"
        error_details = str(e)
    elif isinstance(e, (smtplib.SMTPServerDisconnected, TimeoutError, ConnectionError)):
        error_code = "CONNECTION_FAILED"
        error_details = f"SMTP connection failed: {str(e)}"
    elif isinstance(e, smtplib.SMTPException):
        error_code = "SMTP_ERROR"
        error_details = str(e)
    else:
        error_code = "UNKNOWN_ERROR"
        error_details = str(e)
    return error_code, error_details
