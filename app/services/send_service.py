"""
===============================================================================
Send Service (app/services/send_service.py)
===============================================================================
Sends cold emails to contacts the user picked on the Send page, filled in
with one of their sender profiles and templates:
1. Previewing the exact email one contact will get.
2. Queuing emails to the chosen contacts (sent in the background).
3. Reporting how each queued email went, and who was emailed before. Each sent email's content is saved too, for the History page.
4. An admin's test mode, which only allows sends to their test emails.

The older /email/send-cold and /email/send-to-hr flows live in
cold_email_service.py and are unchanged.
===============================================================================
"""

import asyncio
import re
import uuid 
from email.utils import make_msgid

from fastapi import BackgroundTasks,HTTPException, status
from sqlalchemy import func, select

from app.core.encryption import decrypt_value
from app.core.mailer import send_email
from app.database.database import AsyncSessionLocal
from app.models.models import AdminTestMode, EmailSendDetail, EmailTransaction,HRContactsV2,User,UserEmailTemplate,UserResume,UserSenderProfile
from app.schemas.sending import SendEmailsRequest
from app.services.cold_email_service import(
    classify_email_exception,
    get_user_active_resume,
    get_user_smtp_config,
    render_cold_email,
)
from app.services.email_logger import log_email


def skills_list(profile: UserSenderProfile)-> list[str]:
    """Skills are stored comma-separated: "Python,FastAPI" -> ["Python", "FastAPI"]"""
    return [skill for skill in profile.skills.split(",") if skill]


def build_context(user: User, profile:UserSenderProfile, contact: HRContactsV2) -> dict:
    """
    The variables a template can use, for one recruiter. Names match the 
    older send flows, so the same templates work everywhere.
    """
    years = profile.experience_years
    return{
        "hr_name": contact.name,
        "company_name": contact.company or "",
        "job_position": profile.job_position,
        # 3.0 -> "3", 2.5 -> "2.5"
        "experience_years": int(years) if years == int(years) else years,
        "skills" : skills_list(profile),
        "applicant_name": user.name,
        "email": user.email,
        "contact_number": user.mobile or "",
        "linkedin_url": profile.linkedin_url or "",
    }


def render_email(template: UserEmailTemplate,context: dict) -> tuple[str,str]:
    """
    (subject, body) for one recruiter. An empty subject falls back to the 
    same default subject the other send flows use. 
    """
    try:
        body = render_cold_email(template.content, context)
        if template.subject:
            subject = render_cold_email(template.subject, context)
        else:
            subject = f"{context['job_position']} | Inquiry About Openings - {context['applicant_name']}"

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The template '{template.name}' has an error: {exc}",
        )
    return subject, body 


def attachment_name(user:User) -> str:
    """ "Saurabh Amrutkar" -> "Saurabh_Amrutkar_Resume.pdf", so recruiters can tell resumes apart """
    safe = re.sub(r"[^A-Za-z0-9]+", "_", user.name).strip("_")
    return f"{safe or 'My'}_Resume.pdf"


async def get_owned(session,model,item_id:int, user_id:int, label:str):
    """The user's own row of `model` with this id, or 404 (also for someone else's)."""
    result = await session.execute(select(model).where(model.id == item_id, model.user_id == user_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found.")
    return item


async def get_contacts(session, contact_ids: list[int])-> list[HRContactsV2]:
    """ The contacts in the order they were picked, or 404 if any has been deleted.""" 
    result = await session.execute(select(HRContactsV2).where(HRContactsV2.id.in_(contact_ids)))
    by_id = {contact.id: contact for contact in result.scalars().all()}
    missing = [i for i in contact_ids if i not in by_id]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some of the chosen contacts no longer exist. Reload the page and choose again."
        )
    return [by_id[i] for i in contact_ids]


async def allowed_test_emails(user: User) -> set[str] |None :
    """
    While an admin's test mode is on, the only addresses they may send to
    (lower-case). None when sends are unrestricted: regular users, or an 
    admin who switched test mode off. Admins start with it on. 
    """
    if user.role != "admin":
        return None
    async with AsyncSessionLocal() as session:
        row = await session.get(AdminTestMode, user.id)
    if row is not None and not row.enabled:
        return None 
    emails = row.test_emails if row else ""
    return {email.lower() for email in emails.split(",") if email}


async def preview_email(user:User, contact_id:int, template_id:int, sender_profile_id:int) -> dict: 
    """ The exact email `contact_id` would get. Nothing is sent or saved."""
    async with AsyncSessionLocal() as session:
        template = await get_owned(session, UserEmailTemplate,template_id, user.id ,"Template")
        profile = await get_owned(session, UserSenderProfile, sender_profile_id, user.id, "Sender details")
        [contact] = await get_contacts(session, [contact_id])

    subject, body = render_email(template,build_context(user, profile, contact))
    return {
        "contact_id": contact.id, 
        "to_name": contact.name,
        "to_email": contact.email,
        "company": contact.company,
        "subject": subject,
        "body": body,
        "attachment_name": attachment_name(user)
    }

async def active_resume_version(user_id: int) -> int | None:
    """The version number of the resume that goes with this user's emails, e.g. 2 for "v2"."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserResume.version_number).where(UserResume.user_id == user_id, UserResume.is_active == True)
        )
        return result.scalars().first()


async def queue_emails(user:User, payload: SendEmailsRequest, background_tasks: BackgroundTasks) -> dict:
    """
    Checks everything first (Gmail connected, an active resume, the 
    template, the sender details, the contacts and test mode), fills in 
    every email, then sends them in the background. Returns one request id 
    per contact, to follow with /email/status.
    """
    allowed = await allowed_test_emails(user)
    smtp_credential = await get_user_smtp_config(user.id)
    resume_bytes = await get_user_active_resume(user.id)
    resume_version = await active_resume_version(user.id)


    async with AsyncSessionLocal() as session:
        template = await get_owned(session, UserEmailTemplate, payload.template_id, user.id, "Template")
        profile = await get_owned(session, UserSenderProfile,payload.sender_profile_id, user.id, "Sender details")
        contacts = await get_contacts(session, payload.contact_ids)

    if allowed is not None:
        blocked = [c.email for c in contacts if c.email.lower() not in allowed]
        if blocked:
            more = f" and {len(blocked) - 3} more" if len(blocked) > 3 else ""
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= f"Test mode is on, so emails can only go to your test emails. Not in the list: {', '.join(blocked[:3])}{more}."
            )

    jobs = []
    # Message-IDs look like <...@gmail.com>, after the address the emails come from
    domain = smtp_credential.email_address.split("@")[-1]
    for contact in contacts:
        subject, body = render_email(template, build_context(user, profile,contact))
        jobs.append({
            "request_id" : str(uuid.uuid4()),
            "contact": contact,
            "subject": subject,
            "body": body,
            "template_name": template.name,
            "resume_version": resume_version,
            "message_id": make_msgid(domain=domain),
        })

    background_tasks.add_task(
        send_jobs,
        user_id = user.id,
        jobs=jobs,
        smtp_server=smtp_credential.smtp_server,
        smtp_port=smtp_credential.smtp_port,
        email_address=smtp_credential.email_address,
        email_password=decrypt_value(smtp_credential.encrypted_password),
        resume_bytes=resume_bytes,
        resume_name=attachment_name(user),             
    )

    return {
        "total": len(jobs),
        "test_mode": allowed is not None,
        "items": [
            {"contact_id" : j["contact"].id, "name":j["contact"].name, "email": j["contact"].email, "request_id": j["request_id"]}
            for j in jobs
        ],
    }


async def send_jobs(
        user_id : int,
        jobs: list[dict],
        smtp_server: str,
        smtp_port: int, 
        email_address: str, 
        email_password: str, 
        resume_bytes: bytes, 
        resume_name: str,
) -> None:
    """
    Runs after the response: sends each prepared email one after another
    and records the outcome under its request id. Never raises; a failed 
    email is recorded as FAILED with the reason.
    """

    for job in jobs:
        to_email = job["contact"].email
        try:
            await asyncio.to_thread(
                send_email,
                to_email=to_email,
                subject=job["subject"],
                body=job["body"],
                byte_attachments=[{"filename": resume_name, "content": resume_bytes}],
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                email_address=email_address,
                email_password=email_password,
                message_id=job["message_id"]      
            )
            log_email(to_email,"SUCCESS")
            await record_outcome(user_id, job, "SUCCESS", None, "Email sent successfully via SMTP")
        except Exception as exc:
            error_code, error_details = classify_email_exception(exc)
            log_email(to_email,"FAILED", error_details)
            await record_outcome(user_id, job, "FAILED", error_code, error_details)


async def record_outcome(user_id: int, job: dict, status: str, error_code: str | None, response_details: str) -> None:
    """Saves how one email went (email_transactions) and what it said (email_send_details)."""
    contact = job["contact"]
    async with AsyncSessionLocal() as session:
        session.add(EmailTransaction(
            request_id=job["request_id"],
            recipient_email=contact.email,
            status=status,
            error_code=error_code,
            response_details=response_details,
            user_id=user_id,
        ))
        # The details row points at the transaction, so the transaction is written first
        await session.flush()
        session.add(EmailSendDetail(
            request_id=job["request_id"],
            contact_name=contact.name,
            company=contact.company,
            subject=job["subject"],
            body=job["body"],
            template_name=job["template_name"],
            resume_version=job["resume_version"],
            message_id=job["message_id"],
        ))
        await session.commit()


async def email_statuses(user_id:int, request_ids: list[str])-> list[dict]:
    """How each queued email went; PENDING while it hasn't been tried yet."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EmailTransaction).where(
                EmailTransaction.user_id == user_id,
                EmailTransaction.request_id.in_(request_ids),
            )
        )
        done = {t.request_id: t for t in result.scalars().all()}

    return [
        {
            "request_id": request_id,
            "status": done[request_id].status if request_id in done else "PENDING",
            "error_code": done[request_id].error_code if request_id in done else None,
            "response_details": done[request_id].response_details if request_id in done else None,
        }
            for request_id in request_ids
        ]


async def last_sent(user_id: int) -> dict[str, str]:
    """{ recipient email (lower-case): when this user last emailed it successfully }"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.lower(EmailTransaction.recipient_email), func.max(EmailTransaction.created_at))
            .where(EmailTransaction.user_id == user_id, EmailTransaction.status == "SUCCESS")
            .group_by(func.lower(EmailTransaction.recipient_email))
        )
        return {email: sent_at.isoformat() for email, sent_at in result.all()}
