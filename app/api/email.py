"""
===============================================================================
Email API Router (app/api/email.py)
===============================================================================
Every route needs a signed-in user (router-level get_current_user):
- GET  /email/transactions          recent sends (dashboard)
- GET  /email/stats                 dashboard numbers
- POST /email/preview               the exact email one contact would get
- POST /email/send                  queue up to 50 emails, sent in the background
- GET  /email/status                how each queued email went
- GET  /email/last-sent             when each address was last emailed
- GET  /email/history[/{id}]        sent emails with filters / one in full
Each route hands its one request DB session (get_db) to the services.
===============================================================================
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import rate_limit
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.database.database import get_db
from app.database.repositories import get_email_stats, list_email_transactions
from app.models.models import User
from app.schemas.email import EmailStatsResponse, EmailTransactionResponse
from app.schemas.history import HistoryDetail, HistoryPage
from app.schemas.sending import EmailPreviewRequest, EmailPreviewResponse, EmailStatusItem, MAX_RECIPIENTS, SendEmailsRequest, SendEmailsResponse
from app.services.history_service import get_history_item, list_history
from app.services.send_service import email_statuses, last_sent, preview_email, queue_emails
from common.Logger import Logger

logger = Logger.get_logger()

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)


@router.get("/transactions", response_model=List[EmailTransactionResponse])
async def get_email_transactions_list(limit: int = Query(50, ge=1, le=100), offset: int = Query(0,ge=0),current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    """
    Retrieve recent email transactions with pagination.

    Parameters:
        limit:
            Maximum number of transactions to return.

        offset:
            Number of records to skip before returning results.

    Example:

        /email/transactions?limit=50&offset=0

    Flow:
        Client
          ↓
        FastAPI Endpoint
          ↓
        Repository
          ↓
        Database
          ↓
        List of transactions
          ↓
        Response
    """
    logger.info(
        f"Fetching email transactions. "
        f"limit={limit}, offset={offset}"
    )

    filter_user_id = None if current_user.role == "admin" else current_user.id

    # Delegate database operation to the repository layer.
    transactions = await list_email_transactions(
        db,
        limit=limit,
        offset=offset,
        user_id = filter_user_id,
    )

    logger.info(
        f"Successfully retrieved {len(transactions)} email transactions."
    )

    return transactions

@router.get("/stats", response_model=EmailStatsResponse)
async def get_email_stats_summary(
    days:int = Query(14,ge=1,le=90,description="How many days back, today included"),
    tz_offset_minutes: int = Query(0,ge=-720, le=840, description="Viewer's offset from UTC in minutes, e.g. 330 for India"),
    current_user: User =Depends(get_current_user),db: AsyncSession = Depends(get_db)
):
    """
    Dashboard numbers : sent/failed per day for the last `days` days ,
    their totals and success rate, and how many HR contacts exist. 
    
    Example: 
        /email/stats?days=14&tz_offset_minutes=330

    Admins see every user's emails like GET/email/transactions; everyone 
    else sees only their own. 
    """

    filter_user_id = None if current_user.role == 'admin' else current_user.id 
    return await get_email_stats(db,days=days,tz_offset_minutes=tz_offset_minutes,user_id=filter_user_id)




# ---------------------------------------------------------------------------
# Send Page: preview, send to chosen contacts, follow the results
# ---------------------------------------------------------------------------


@router.post("/preview", response_model=EmailPreviewResponse)
async def preview_email_for_contact(
    payload: EmailPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The exact email one contact would get with this template and sender
    details: subject, body and the attachment's file name. Nothing is sent.
    """
    return await preview_email(db,current_user, payload.contact_id, payload.template_id, payload.sender_profile_id)


@router.post("/send", response_model=SendEmailsResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(rate_limit.SEND_EMAILS)
async def send_emails_to_contacts(
    request: Request,
    payload: SendEmailsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the template to up to 50 chosen contacts, one email each, in the
    background. Everything is checked first, so a missing Gmail, resume,
    template or contact fails right away with nothing sent. Follow the
    returned request ids with /email/status.
    """
    return await queue_emails(db,current_user, payload, background_tasks)


@router.get("/status", response_model=List[EmailStatusItem])
async def get_email_statuses(
    request_ids: str = Query(..., max_length=2000, description="Request ids from /email/send, comma-separated"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """How each of these emails went: PENDING, SUCCESS or FAILED (with the reason)."""
    ids = [i.strip() for i in request_ids.split(",") if i.strip()][:MAX_RECIPIENTS]
    return await email_statuses(db,current_user.id, ids)


@router.get("/last-sent")
async def get_last_sent(current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    When the user last emailed each address successfully, so the Send
    page can say "Emailed on 20 Oct": { "hr@company.com": "2026-10-20T..." }
    """
    return await last_sent(db,current_user.id)




# ============================================================
# History
# ============================================================

@router.get("/history", response_model=HistoryPage)
async def get_email_history(
    status_filter: Optional[Literal["SUCCESS", "FAILED"]] = Query(None, alias="status"),
    q: str = Query("", max_length=100, description="Words in the recipient, company or subject"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Only the last N days"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    One page of sent emails, newest first, and how many match in total.

    Example:
        /email/history?status=FAILED&q=zoho&days=30&limit=25&offset=0
    """
    return await list_history(db,current_user, status_filter, q.strip(), days, limit, offset)


@router.get("/history/{request_id}", response_model=HistoryDetail)
async def get_email_history_item(request_id: str, current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    """One sent email with what it said, the template and resume version used."""
    return await get_history_item(db,current_user, request_id)
