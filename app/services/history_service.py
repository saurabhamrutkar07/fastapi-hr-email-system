"""
===============================================================================
History Service (app/services/history_service.py)
===============================================================================
Every email a user has sent, newest first, for the History page:
1. One page of emails, filtered by status, words and how many days back.
2. One email with everything that was sent.

Regular users see their own emails; admins see everyone's.
===============================================================================
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select

from app.database.database import AsyncSessionLocal
from app.models.models import EmailSendDetail, EmailTransaction, User


def visible_to(query, user: User):
    """Joins in what was sent, and limits a regular user to their own emails."""
    query = query.outerjoin(EmailSendDetail, EmailSendDetail.request_id == EmailTransaction.request_id)
    if user.role != "admin":
        query = query.where(EmailTransaction.user_id == user.id)
    return query


def filtered(query, status_filter: str | None, q: str, days: int | None):
    """The History filters: SUCCESS / FAILED, words in the recipient, company or subject, last N days."""
    if status_filter:
        query = query.where(EmailTransaction.status == status_filter)
    if days:
        query = query.where(EmailTransaction.created_at >= datetime.now(timezone.utc) - timedelta(days=days))
    if q:
        like = f"%{q}%"
        query = query.where(or_(
            EmailTransaction.recipient_email.ilike(like),
            EmailSendDetail.contact_name.ilike(like),
            EmailSendDetail.company.ilike(like),
            EmailSendDetail.subject.ilike(like),
        ))
    return query


def to_item(transaction: EmailTransaction, detail: EmailSendDetail | None, sender: User | None) -> dict:
    return {
        "request_id": transaction.request_id,
        "recipient_email": transaction.recipient_email,
        "status": transaction.status,
        "error_code": transaction.error_code,
        "created_at": transaction.created_at,
        "contact_name": detail.contact_name if detail else None,
        "company": detail.company if detail else None,
        "subject": detail.subject if detail else None,
        "sender_name": sender.name if sender else None,
    }


async def list_history(user: User, status_filter: str | None, q: str, days: int | None, limit: int, offset: int) -> dict:
    """One page of emails plus how many match the filters in total (for "Page 2 of 7")."""
    rows_query = filtered(
        visible_to(select(EmailTransaction, EmailSendDetail, User), user).outerjoin(User, User.id == EmailTransaction.user_id),
        status_filter, q, days,
    )
    count_query = filtered(visible_to(select(func.count()).select_from(EmailTransaction), user), status_filter, q, days)

    async with AsyncSessionLocal() as session:
        total = await session.scalar(count_query)
        result = await session.execute(
            rows_query.order_by(EmailTransaction.created_at.desc(), EmailTransaction.id.desc()).limit(limit).offset(offset)
        )
        rows = result.all()

    return {"total": total, "items": [to_item(*row) for row in rows]}


async def get_history_item(user: User, request_id: str) -> dict:
    """One email with its full content, or 404 (also for someone else's, unless admin)."""
    query = visible_to(select(EmailTransaction, EmailSendDetail, User), user).outerjoin(User, User.id == EmailTransaction.user_id)
    async with AsyncSessionLocal() as session:
        result = await session.execute(query.where(EmailTransaction.request_id == request_id))
        row = result.first()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")

    transaction, detail, sender = row
    return {
        **to_item(transaction, detail, sender),
        "response_details": transaction.response_details,
        "body": detail.body if detail else None,
        "template_name": detail.template_name if detail else None,
        "resume_version": detail.resume_version if detail else None,
        "sender_email": sender.email if sender else None,
    }
