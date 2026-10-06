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

import asyncio
import uuid
import smtplib
from fastapi import HTTPException, status
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from pathlib import Path
import os 
from sqlalchemy import select
from app.core.mailer import send_email
from app.core.config import RESUME_PATH, TEMPLATE_DIR, USE_DUMMY_HR, BASE_DIR, linkedin_1, linkedin_2
from app.database.database import AsyncSessionLocal
from app.models.models import UserSMTPCredential, UserEmailTemplate, UserResume
from app.core.encryption import decrypt_value
from app.core.s3_storage import s3_storage
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
# We do NOT create the Environment every time an email is sent because the 
# environment configuration is common to all emails. 
# TEMPLATE_DIR points to the directory containing our email templates.

# env = Environment(
#     loader=FileSystemLoader(TEMPLATE_DIR),
#     autoescape=False
# )

env = SandboxedEnvironment(
    loader = FileSystemLoader(TEMPLATE_DIR),
    autoescape = False
)

async def get_user_smtp_config(user_id: int)-> UserSMTPCredential:
    """
    Featches and returns the given user's SMTP credentual row.
    Raises 400 if user hasn't configured  their own SMTP sender
    yet -- cold emails are always sent from the user's own account,
    never a shared/global one.
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserSMTPCredential).where(UserSMTPCredential.user_id == user_id)
        )

        credential = result.scalar_one_or_none()

        if credential is None or not credential.is_active:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= "SMTP credential not configured. Please set them up before sending emails."
            )

        return credential

async def get_user_default_template(user_id: int) -> UserEmailTemplate:
    """
    Featches the given user's default template. Raise 400 if 
    the user hasn't created/marked one yet -- cold emails required a 
    pre-user template, these is no shared fallback.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserEmailTemplate).where(
                UserEmailTemplate.user_id == user_id,
                UserEmailTemplate.is_default == True,
            )
        )
        template = result.scalars().first()

    if template is None:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "No default email template configured. Please create one before sending emails."
        )

    return template


async def get_user_active_resume(user_id :int)->bytes:
    """
    Fetches the given user's active resume from s3 and returns its raw 
    bytes. Raises 400 if the user han's uploaded/activated one yet --
    cold emails require a pre-user resume, there is no shared fallback.
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserResume).where(
                UserResume.user_id == user_id,
                UserResume.is_active == True,
            )
        )
        resume = result.scalars().first()

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "No active resume found. Please uplaod one before sending emails."
        )

    return s3_storage.download_file(resume.file_path)
        
        

def render_cold_email(content: str,context: dict) -> str:
    """
    Renders a user-supplied Jinja template string (from the database)
    with the provided context parameters -- replaces the old
    hardcoded file based template.
    """
    #template = env.get_template("cold_email.j2")
    template = env.from_string(content)
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


# async def send_cold_emails(payload: JobApplicationEmailRequest,user_id:int):
#     """
#     Mass Cold Email Dispatcher:
#     ---------------------------
#     Fetches all recruiters from `hr_contacts_v2`, renders personalized templates,
#     dispatches emails over SMTP, and persists unique request IDs & transaction states.
#     """
#     smtp_credential = await get_user_smtp_config(user_id)
#     smtp_password = decrypt_value(smtp_credential.encrypted_password)
#     email_template = await get_user_default_template(user_id)
#     resume_bytes = await get_user_active_resume(user_id)

#     if USE_DUMMY_HR:
#         class DummyHR:
#             def __init__(self, name, email, company=None):
#                 self.name = name
#                 self.email = email 
#                 self.company = company
        
#         recruiters = [
#             DummyHR("Saurabh Amrutkar", "saurabhamrutkar83@gmail.com", "Tech Solutions"),
#         ]
#     else:
#         recruiters = await get_all_fresh_recruiters()

#     sent = 0
#     failed = 0
#     request_ids = []

#     for hr in recruiters:
#         # Generate a unique UUID request_id for each email transaction
#         request_id = str(uuid.uuid4())
#         request_ids.append(request_id)

#         try:
#             # Render Jinja email template
#             context = {
#                 "hr_name": getattr(hr, 'name', 'Hiring Manager') or 'Hiring Manager',
#                 "company_name": getattr(hr, 'company', None),
#                 "job_position": payload.job_position,
#                 "experience_years": payload.experience_years,
#                 "skills": payload.skills,
#                 "email": payload.email,
#                 "contact_number": payload.contact_number,
#                 "applicant_name": payload.applicant_name,
#                 "linkedin_url": payload.linkedin_url
#             }

#             body = render_cold_email(email_template.content,context)

#             if email_template.subject:
#                 subject = render_cold_email(email_template.subject,context)
#             else:
#                 subject = f"{payload.job_position} | Inquiry About Openings - {payload.applicant_name}"

#             # Send email with resume attachment
#                 await asyncio.to_thread(
#                 send_email,
#                 to_email=hr.email,
#                 subject=subject,
#                 body=body,
#                 byte_attachments=[{"filename": "resume.pdf", "content": resume_bytes}],
#                 smtp_server=smtp_credential.smtp_server,
#                 smtp_port= smtp_credential.smtp_port,
#                 email_address= smtp_credential.email_address,
#                 email_password=smtp_password
#             )

#             # Log success to JSONL file and database transaction table
#             log_email(hr.email, "SUCCESS")
#             await create_email_transaction(
#                 request_id=request_id,
#                 recipient_email=hr.email,
#                 status="SUCCESS",
#                 response_details="Email sent successfully via SMTP",
#                 user_id=user_id
#             )
#             sent += 1

#         except Exception as e:
#             # Classify error and record failure details
#             error_code, error_details = classify_email_exception(e)
#             log_email(hr.email, "FAILED", error_details)
#             await create_email_transaction(
#                 request_id=request_id,
#                 recipient_email=hr.email,
#                 status="FAILED",
#                 error_code=error_code,
#                 response_details=error_details,
#                 user_id=user_id
#             )
#             failed += 1

#     return {
#         "total": len(recruiters),
#         "sent": sent,
#         "failed": failed,
#         "request_ids": request_ids
#     }


async def get_recruiters_for_sending():
    """
    Returns the list of HR recruiter contacts to send cold emails to --
    the hardcoded dummy recruiter when USE_DURRM_HR is enabled (testing
    safeground), otherwise the real list from hr_contacts_v2
    """
    if USE_DUMMY_HR:
        class DummyHR:
            def __init__(self,name,email,company=None):
                self.name = name
                self.email = email 
                self.company = company

        return [DummyHR("Saurabh Amrutkar", "saurabhamrutkar83@gmail.com","Tech Solutions")]

    else:
        return await get_all_fresh_recruiters()


async def send_cold_emails_background(
        payload: JobApplicationEmailRequest,
        user_id : int,
        recruiters : list,
        request_ids : list,
        smtp_credential: UserSMTPCredential,
        smtp_password : str,
        email_template: UserEmailTemplate,
        resume_bytes: bytes,
)->None:
    """
    Background version of cold-email dispatcher. All prerequisite
    data (SMTP creds, template, resume, recruiter list, pre-generated
    request_ids) is fetched by the caller (the API endpoint) BEFORE
    queuing this as a background task -- this function only does the
    actual pre-recruiter send + transaction-recording loop. No one is
    listening for an HTTP response by the time this runs, so it never 
    raises -- every outcome (success or failure) is recorded as an 
    EmailTransaction instead. 
    """
    for hr, request_id in zip(recruiters, request_ids):
        try:
            context = {
                "hr_name": getattr(hr, 'name', 'Hiring Manager') or 'Hiring Manager',
                "company_name": getattr(hr,'company',None),
                "job_position": payload.job_position,
                "experience_years": payload.experience_years,
                "skills": payload.skills,
                "email": payload.email,
                "contact_number": payload.contact_number,
                "applicant_name": payload.applicant_name,
                "linkedin_url": payload.linkedin_url
            } 

            body = render_cold_email(email_template.content, context)

            if email_template.subject:
                subject = render_cold_email(email_template.subject, context)
            else:
                subject = f"{payload.job_position} | Inquiry About Openings - {payload.applicant_name}"

            await asyncio.to_thread(
                send_email,
                to_email=hr.email,
                subject = subject,
                body = body,
                byte_attachments= [{"filename": "resume.pdf", "content": resume_bytes}],
                smtp_server = smtp_credential.smtp_server,
                smtp_port= smtp_credential.smtp_port,
                email_address=smtp_credential.email_address,
                email_password=smtp_password
            )

            log_email(hr.email, "SUCCESS")
            await create_email_transaction(
                request_id= request_id,
                recipient_email = hr.email,
                status = "SUCCESS",
                response_details = "Email sent successfully vai SMTP",
                user_id=user_id
            )

        except Exception as e:
            error_code, error_details = classify_email_exception(e)
            log_email(hr.email, "FAILED", error_details)
            await create_email_transaction(
                request_id=request_id,
                recipient_email=hr.email,
                status= "FAILED",
                error_code=error_code,
                response_details=error_details,
                user_id=user_id
            )


                


async def send_email_to_individual(payload: SingleHREmailRequest,user_id:int):
    """
    Direct Targeted Cold Email Dispatcher:
    --------------------------------------
    Sends a targeted job application email to a specific individual HR contact.
    Generates a unique request_id and returns transaction status.
    """
    smtp_credential = await get_user_smtp_config(user_id)
    smtp_password = decrypt_value(smtp_credential.encrypted_password)
    email_template = await get_user_default_template(user_id)
    resume_bytes = await get_user_active_resume(user_id)
    request_id = str(uuid.uuid4())

    try:
        context = {
            "hr_name": payload.hr_name,
            "company_name": payload.company_name,
            "job_position": payload.job_position,
            "experience_years": payload.experience_years,
            "skills": payload.skills,
            "email": payload.email,
            "contact_number": payload.contact_number,
            "applicant_name": payload.applicant_name,
            "linkedin_url": payload.linkedin_url
        }

        body = render_cold_email(email_template.content,context)

        if email_template.subject:
            subject = render_cold_email(email_template.subject,context)
        else:
            subject = f"{payload.job_position} | Inquiry About Openings - {payload.applicant_name}"


        # Transmit email over SMTP
        await asyncio.to_thread(
            send_email,
            to_email=payload.hr_email,
            subject=subject,
            body=body,
            byte_attachments=[{"filename": "resume.pdf", "content":resume_bytes}],
            smtp_server= smtp_credential.smtp_server,
            smtp_port= smtp_credential.smtp_port,
            email_address= smtp_credential.email_address,
            email_password= smtp_password
        )

        # Record success
        log_email(payload.hr_email, "SUCCESS")
        await create_email_transaction(
            request_id=request_id,
            recipient_email=payload.hr_email,
            status="SUCCESS",
            response_details="Email sent successfully via SMTP",
            user_id=user_id
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
            response_details=error_details,
            user_id=user_id
        )
        return {
            "request_id": request_id,
            "status": "FAILED",
            "hr_email": payload.hr_email,
            "error_code": error_code,
            "error": error_details
        }




