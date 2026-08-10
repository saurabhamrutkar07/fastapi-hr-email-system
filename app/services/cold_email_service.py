""" 
    ===============================================================================
        Cold Email Orchestration Service (cold_email_service.py)
    =============================================================================== 
    Purpose: 
        -------- This module contains the business logic responsible for sending cold emails. 
        The API controller should NOT contain email-sending or transaction logic. Instead, the controller receives the HTTP request and delegates the work to this service. 
        This service is responsible for: 1. Fetching HR/recruiter contacts. 
        2. Generating a unique request_id for every email transaction. 
        3. Rendering the Jinja2 email template with dynamic applicant/HR data. 
        4. Sending the email through SMTP. 
        5. Classifying email/SMTP exceptions into standard error codes. 
        6. Recording SUCCESS/FAILED transactions in the database. 
        7. Logging important events for debugging and monitoring. 
        Important: ---------- One API request can result in MANY email transactions. 
            Example: POST /email/send-cold 
            | 
            +-- HR 1 -> request_id = UUID-1 -> SUCCESS 
            | 
            +-- HR 2 -> request_id = UUID-2 -> FAILED 
            | 
            +-- HR 3 -> request_id = UUID-3 -> SUCCESS 
            Therefore, request_id is generated inside the email transaction loop, not once at the API controller level. 
    =============================================================================== """

import uuid
import smtplib
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import os 
from app.core.mailer import send_email
from app.core.config import RESUME_PATH, TEMPLATE_DIR, USE_DUMMY_HR, BASE_DIR, linkedin_1, linkedin_2, LINKEDIN_URL
from app.database.repositories import get_all_fresh_recruiters, create_email_transaction 
from app.services.email_logger import log_email
from app.schemas.email import JobApplicationEmailRequest, SingleHREmailRequest
from common.Logger import Logger

# -----------------------------------------------------------------------------
# Jinja2 Environment Setup
# -----------------------------------------------------------------------------
# Initialize Jinja2 environment loading templates from `/app/templates`

# ============================================================================= 
#  Logger Initialization 
# ===== ======================================================================== 
# Create/get the configured application logger. 
# The logger itself is shared, but transaction-specific information such as 
# request_id is included in the log message because every email transaction 
# has a different request_id. 

logger = Logger.get_logger()

# ============================================================================= 
# Jinja2 Environment Setup 
# ======== ===================================================================== 
# Create the Jinja2 environment once when this module is loaded. 
# We do NOT create the Environment every time an email is sent because the # environment configuration is common to all emails. 
# TEMPLATE_DIR points to the directory containing our email templates.

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=False
)


def render_cold_email(context: dict) -> str:
    """
    Renders the Jinja2 email template (`cold-email-v2.j2`) with the provided context parameters.

    Context Keys Expected:
    - hr_name, company_name, job_position, experience_years, skills, email, contact_number, applicant_name, linkedin_url
    """
    template = env.get_template("cold-email-v2.j2")
    return template.render(**context)


def classify_email_exception(e: Exception) -> tuple[str, str]:
    """
    Classifies raw Python/SMTP exceptions into standardized error codes and detailed messages.

    Returns:
    --------
    tuple[str, str]: (error_code, error_details)
    - CREDENTIALS_EXPIRED: Invalid SMTP username/password or expired OAuth App Token.
    - RECIPIENT_NOT_FOUND: Recipient email refused or inbox does not exist (SMTP 550).
    - ATTACHMENT_MISSING: PDF resume file missing on disk.
    - CONNECTION_FAILED: Network timeout or server disconnection.
    - SMTP_ERROR: General SMTP protocol exception.
    - UNKNOWN_ERROR: Any unhandled system exception.
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


async def send_cold_emails(payload: JobApplicationEmailRequest):
    """
    Mass Cold Email Dispatcher:
    ---------------------------
    Fetches all recruiters from `hr_contacts_v2`, renders personalized templates,
    dispatches emails over SMTP, and persists unique request IDs & transaction states.
    """
    if USE_DUMMY_HR:
        class DummyHR:
            def __init__(self, name, email, company=None):
                self.name = name
                self.email = email 
                self.company = company
        
        recruiters = [
            DummyHR("Saurabh Amrutkar", "saurabhamrutkar83@gmail.com", "Tech Solutions"),
        ]
    else:
        recruiters = await get_all_fresh_recruiters()

    subject = f"{payload.job_position} | Inquiry About Openings - {payload.applicant_name}"
    sent = 0
    failed = 0
    request_ids = []

    for hr in recruiters:
        # Generate a unique UUID request_id for each email transaction
        request_id = str(uuid.uuid4())
        request_ids.append(request_id)

        try:
            # Render Jinja email template
            body = render_cold_email({
                "hr_name": getattr(hr, 'name', 'Hiring Manager') or 'Hiring Manager',
                "company_name": getattr(hr, 'company', None),
                "job_position": payload.job_position,
                "experience_years": payload.experience_years,
                "skills": payload.skills,
                "email": payload.email,
                "contact_number": payload.contact_number,
                "applicant_name": payload.applicant_name,
                "linkedin_url": LINKEDIN_URL
            })

            # Send email with resume attachment
            send_email(
                to_email=hr.email,
                subject=subject,
                body=body,
                attachments=[RESUME_PATH]
            )

            # Log success to JSONL file and database transaction table
            log_email(hr.email, "SUCCESS")
            await create_email_transaction(
                request_id=request_id,
                recipient_email=hr.email,
                status="SUCCESS",
                response_details="Email sent successfully via SMTP"
            )
            sent += 1

        except Exception as e:
            # Classify error and record failure details
            error_code, error_details = classify_email_exception(e)
            log_email(hr.email, "FAILED", error_details)
            await create_email_transaction(
                request_id=request_id,
                recipient_email=hr.email,
                status="FAILED",
                error_code=error_code,
                response_details=error_details
            )
            failed += 1

    return {
        "total": len(recruiters),
        "sent": sent,
        "failed": failed,
        "request_ids": request_ids
    }


async def send_email_to_individual(payload: SingleHREmailRequest):
    """
    Direct Targeted Cold Email Dispatcher:
    --------------------------------------
    Sends a targeted job application email to a specific individual HR contact.
    Generates a unique request_id and returns transaction status.
    """
    subject = f"{payload.job_position} | Inquiry About Openings - {payload.applicant_name}"
    request_id = str(uuid.uuid4())

    try:
        # Render Jinja template
        body = render_cold_email({
            "hr_name": payload.hr_name,
            "company_name": payload.company_name,
            "job_position": payload.job_position,
            "experience_years": payload.experience_years,
            "skills": payload.skills,
            "email": payload.email,
            "contact_number": payload.contact_number,
            "applicant_name": payload.applicant_name,
            "linkedin_url": LINKEDIN_URL
        })

        # Transmit email over SMTP
        send_email(
            to_email=payload.hr_email,
            subject=subject,
            body=body,
            attachments=[RESUME_PATH]
        )

        # Record success
        log_email(payload.hr_email, "SUCCESS")
        await create_email_transaction(
            request_id=request_id,
            recipient_email=payload.hr_email,
            status="SUCCESS",
            response_details="Email sent successfully via SMTP"
        )
        return {
            "request_id": request_id,
            "status": "SUCCESS",
            "hr_email": payload.hr_email
        }

    except Exception as e:
        # Classify error and record failure
        error_code, error_details = classify_email_exception(e)
        log_email(payload.hr_email, "FAILED", error_details)
        await create_email_transaction(
            request_id=request_id,
            recipient_email=payload.hr_email,
            status="FAILED",
            error_code=error_code,
            response_details=error_details
        )
        return {
            "request_id": request_id,
            "status": "FAILED",
            "hr_email": payload.hr_email,
            "error_code": error_code,
            "error": error_details
        }




