"""
===============================================================================
Database Repository Access Layer (repositories.py)
===============================================================================
Encapsulates all asynchronous database operations (CRUD) for:
- Recruiter contact management (`HRContacts` and `HRContactsV2`)
- Email transaction audit logging (`EmailTransaction`)
===============================================================================
"""

from sqlalchemy import select, desc
from app.database.database import AsyncSessionLocal
from app.models.models import HRContacts, HRContactsV2, EmailTransaction


# -----------------------------------------------------------------------------
# Recruiter & HR Contact Queries
# -----------------------------------------------------------------------------
async def get_all_recruiters() -> list[HRContacts]:
    """
    Fetches all legacy recruiter contacts from `hr_contacts` table.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(HRContacts))
        return result.scalars().all()


async def get_all_fresh_recruiters() -> list[HRContactsV2]:
    """
    Fetches all upgraded recruiter contacts from `hr_contacts_v2` table.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(HRContactsV2))
        return result.scalars().all()


async def add_hr_contact(payload):
    """
    Inserts a single legacy HR contact into `hr_contacts`.
    """
    async with AsyncSessionLocal() as session:
        hr = HRContacts(
            name=payload.name,
            email=payload.email,
            title=payload.title,
            company=payload.company_name
        )
        session.add(hr)
        await session.commit()


async def add_fresh_hr_contact(payload) -> HRContactsV2:
    """
    Inserts a single fresh HR contact into `hr_contacts_v2` and returns the created instance.
    """
    async with AsyncSessionLocal() as session:
        hr = HRContactsV2(
            name=payload.name,
            email=payload.email,
            title=payload.title,
            company=payload.company_name,
            phone=getattr(payload, 'contact_number', None) or getattr(payload, 'phone', None)
        )
        session.add(hr)
        await session.commit()
        await session.refresh(hr)
        return hr


async def add_hr_contact_bulk(data: list[dict]) -> int:
    """
    Bulk inserts multiple legacy contacts into `hr_contacts`.
    Returns count of inserted rows.
    """
    async with AsyncSessionLocal() as session:
        contacts = [
            HRContacts(
                name=item.get("name"),
                email=item.get("email"),
                title=item.get("title"),
                company=item.get("company"),
                phone=item.get("phone")
            )
            for item in data
        ]
        session.add_all(contacts)
        await session.commit()
        return len(contacts)


async def add_fresh_hr_contact_bulk(data: list[dict]) -> int:
    """
    Bulk inserts multiple fresh contacts into `hr_contacts_v2`.
    Returns count of inserted rows.
    """
    async with AsyncSessionLocal() as session:
        contacts = [
            HRContactsV2(
                name=item.get("name"),
                email=item.get("email"),
                title=item.get("title"),
                company=item.get("company"),
                phone=item.get("phone")
            )
            for item in data
        ]
        session.add_all(contacts)
        await session.commit()
        return len(contacts)


# -----------------------------------------------------------------------------
# Email Transaction Repository Functions
# -----------------------------------------------------------------------------
async def create_email_transaction(
    request_id: str,
    recipient_email: str,
    status: str,
    error_code: str | None = None,
    response_details: str | None = None
) -> EmailTransaction:
    """
    Creates and persists an email transaction record in `email_transactions`.

    Parameters:
    -----------
    request_id : str
        Unique UUID identifying the email request context.
    recipient_email : str
        Target HR email address.
    status : str
        "SUCCESS" or "FAILED".
    error_code : str | None
        Standardized error code (e.g. CREDENTIALS_EXPIRED, RECIPIENT_NOT_FOUND).
    response_details : str | None
        Success message or raw exception message.
    """
    async with AsyncSessionLocal() as session:
        transaction = EmailTransaction(
            request_id=request_id,
            recipient_email=recipient_email,
            status=status,
            error_code=error_code,
            response_details=response_details
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction


async def get_transaction_by_request_id(request_id: str) -> EmailTransaction | None:
    """
    Queries and returns a single transaction by its unique `request_id`.
    Returns None if no matching record exists.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EmailTransaction).where(EmailTransaction.request_id == request_id)
        )
        return result.scalars().first()


async def list_email_transactions(limit: int = 50, offset: int = 0) -> list[EmailTransaction]:
    """
    Retrieves recent email transactions sorted by creation timestamp descending.
    Supports pagination via `limit` and `offset`.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EmailTransaction).order_by(desc(EmailTransaction.created_at)).offset(offset).limit(limit)
        )
        return result.scalars().all()


