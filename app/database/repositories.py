"""
===============================================================================
Database Repository Access Layer (repositories.py)
===============================================================================
Encapsulates all asynchronous database operations (CRUD) for:
- Recruiter contact management (`HRContacts` and `HRContactsV2`)
- Email transaction audit logging (`EmailTransaction`)
===============================================================================
"""

from datetime import datetime, time, timedelta, timezone
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.database import AsyncSessionLocal
from app.models.models import (
    HRContacts,
    HRContactsV2,
    HRContactEmail,
    HRContactPhone,
    EmailTransaction,
)
from common.Logger import Logger


def _dedupe_preserve_order(items: list[str | None]) -> list[str]:
    """
    Drops `None`/empty values and duplicates while keeping first-seen order,
    so the first surviving item can be treated as "primary".
    """
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


async def _add_contact_emails_and_phones(
    session: AsyncSession,
    contact: HRContactsV2,
    emails: list[str],
    phones: list[str],
) -> None:
    """
    Inserts `HRContactEmail`/`HRContactPhone` child rows for `contact`.
    `email`/`phone` are globally unique columns, so any value that already
    belongs to another contact is silently skipped (same behavior as the
    Excel/CSV import path in `hr_contact_excel_service.py`).
    """
    for index, email in enumerate(emails):
        existing = await session.execute(
            select(HRContactEmail).where(HRContactEmail.email == email)
        )
        if existing.scalar_one_or_none():
            continue
        session.add(
            HRContactEmail(
                contact_id=contact.id,
                email=email,
                is_primary=(index == 0),
            )
        )

    for index, phone in enumerate(phones):
        existing = await session.execute(
            select(HRContactPhone).where(HRContactPhone.phone == phone)
        )
        if existing.scalar_one_or_none():
            continue
        session.add(
            HRContactPhone(
                contact_id=contact.id,
                phone=phone,
                is_primary=(index == 0),
            )
        )

async def find_existing_contact_by_email_or_phone(
    session: AsyncSession,
    emails: list[str],
    phones: list[str],
) -> HRContactsV2 | None:
    """
    Checks whether any of the given emails OR phones already belongs to a
    contact that is already saved in the database.

    WHY THIS FUNCTION EXISTS (read this before removing it):
    -----------------------------------------------------------------------
    `add_fresh_hr_contact()` / `add_fresh_hr_contact_bulk()` used to create
    a brand new `hr_contacts_v2` row every single time, with no check for
    whether the email/phone was already in use. That caused a silent bug:

      1. Contact A is added with primary email "x@y.com" and an extra
         email "z@y.com" (stored in `hr_contact_emails`).
      2. Later, someone adds a brand new Contact B whose PRIMARY email
         happens to be "z@y.com".
      3. `hr_contacts_v2.email` is only unique *within that column*, so
         Contact B's row gets created fine, with `email = "z@y.com"`.
      4. But when we then try to also insert "z@y.com" into
         `hr_contact_emails` for Contact B, it's rejected/skipped because
         that email already exists there for Contact A
         (`hr_contact_emails.email` is globally unique).
      5. Result: Contact B ends up with `email` set, but `emails: []`
         in the API response -- confusing and hard to debug.

    The EXACT same failure mode exists for phones: `hr_contacts_v2.phone`
    has NO unique constraint, but `hr_contact_phones.phone` does. So a new
    contact can get `phone` set on the parent row while its `phones: []`
    stays empty, if that phone number already belongs to someone else's
    `hr_contact_phones` row.

    Calling this function FIRST lets us detect "hey, this email/phone
    already belongs to someone" and merge into that existing contact
    instead of creating a broken duplicate.

    We check every place an email/phone can live:
      1. `hr_contact_emails` / `hr_contact_phones` -- the new, multi-value
         child tables.
      2. `hr_contacts_v2.email` / `hr_contacts_v2.phone` -- the old,
         single-value columns, kept around for backward compatibility.

    Returns the matching `HRContactsV2` row if one of the emails/phones is
    already known, otherwise `None` (meaning: safe to create a new
    contact).
    """
    for email in emails:

        # 1. Look in the multi-email table first.
        result = await session.execute(
            select(HRContactEmail).where(HRContactEmail.email == email)
        )
        existing_email_row = result.scalar_one_or_none()

        if existing_email_row:
            # Found the email -- now fetch the contact it belongs to.
            result = await session.execute(
                select(HRContactsV2).where(
                    HRContactsV2.id == existing_email_row.contact_id
                )
            )
            return result.scalar_one_or_none()

        # 2. Fall back to the legacy single-email column.
        result = await session.execute(
            select(HRContactsV2).where(HRContactsV2.email == email)
        )
        existing_contact = result.scalar_one_or_none()

        if existing_contact:
            return existing_contact

    for phone in phones:

        # 1. Look in the multi-phone table first.
        result = await session.execute(
            select(HRContactPhone).where(HRContactPhone.phone == phone)
        )
        existing_phone_row = result.scalar_one_or_none()

        if existing_phone_row:
            # Found the phone -- now fetch the contact it belongs to.
            result = await session.execute(
                select(HRContactsV2).where(
                    HRContactsV2.id == existing_phone_row.contact_id
                )
            )
            return result.scalar_one_or_none()

        # 2. Fall back to the legacy single-phone column.
        result = await session.execute(
            select(HRContactsV2).where(HRContactsV2.phone == phone)
        )
        existing_contact = result.scalar_one_or_none()

        if existing_contact:
            return existing_contact

    # None of the emails/phones matched an existing contact -- genuinely new.
    return None


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
    Fetches all upgraded recruiter contacts from `hr_contacts_v2` table,
    along with their related `hr_contact_emails` and `hr_contact_phones`
    rows (eager-loaded via `selectinload` since AsyncSession cannot
    lazy-load relationships on attribute access).
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(HRContactsV2).options(
                selectinload(HRContactsV2.emails),
                selectinload(HRContactsV2.phones),
            )
        )
        return result.scalars().all()


async def add_hr_contact(payload,logger = None):
    """
    Inserts a single legacy HR contact into `hr_contacts`.
    """
    if logger is None: 
        logger = Logger.get_logger()
    logger.info("Execution of query add hr started")
    try:
        async with AsyncSessionLocal() as session:
            hr = HRContacts(
                name=payload.name,
                email=payload.email,
                title=payload.title,
                company=payload.company_name
            )
            session.add(hr)
            await session.commit()
            logger.info(
                    "HR contact inserted successfully."
                )
    except Exception as exc:

        # Roll back the current transaction.
        # This is important because the database session may
        # be left in a failed transaction state after an error.
        await session.rollback()

        # Log the complete exception and traceback.
        logger.exception(
            f"Failed to insert HR contact: {exc}"
        )

        # Re-raise the exception so the service/controller
        # knows that the operation failed.
        raise


async def add_fresh_hr_contact(payload) -> tuple[HRContactsV2, bool]:
    """
    Inserts a single fresh HR contact into `hr_contacts_v2`, plus any
    `additional_emails`/`additional_phones` into the `hr_contact_emails`/
    `hr_contact_phones` child tables.

    If one of the given emails OR phones already belongs to a contact
    that's already saved, we DON'T create a duplicate `hr_contacts_v2`
    row for it -- we just add any of the new emails/phones onto that
    existing contact instead. See `find_existing_contact_by_email_or_phone()`
    above for the full explanation of why this check is required.

    Returns a tuple: `(contact, is_new_contact)`.
      - `contact` is the created row, OR the existing row we merged into.
      - `is_new_contact` is `True` if we created a brand new row, `False`
        if we merged into an existing one. The caller (the API layer)
        uses this to tell the user which one actually happened, instead
        of always saying "added successfully" even when nothing new was
        created.
    """
    emails = _dedupe_preserve_order(
        [payload.email, *getattr(payload, "additional_emails", [])]
    )
    phones = _dedupe_preserve_order(
        [
            getattr(payload, "contact_number", None) or getattr(payload, "phone", None),
            *getattr(payload, "additional_phones", []),
        ]
    )

    async with AsyncSessionLocal() as session:

        # ------------------------------------------------------------
        # STEP 1: Has one of these emails/phones already been saved
        # before? If yes, reuse that contact instead of creating a new
        # row.
        # ------------------------------------------------------------
        hr = await find_existing_contact_by_email_or_phone(session, emails, phones)
        is_new_contact = hr is None

        if is_new_contact:
            # Genuinely new contact -- safe to create the parent row.
            hr = HRContactsV2(
                name=payload.name,
                email=emails[0],
                title=payload.title,
                company=payload.company_name,
                phone=phones[0] if phones else None,
            )
            session.add(hr)
            await session.flush()  # assigns hr.id, needed just below

        # ------------------------------------------------------------
        # STEP 2: Add any emails/phones that aren't already saved.
        # This works the same whether `hr` is brand new or an existing
        # match -- `_add_contact_emails_and_phones` already skips any
        # email/phone that's already in the database.
        # ------------------------------------------------------------
        await _add_contact_emails_and_phones(session, hr, emails, phones)

        await session.commit()
        await session.refresh(hr)
        return hr, is_new_contact


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


async def add_fresh_hr_contact_bulk(payloads: list) -> dict[str, int]:
    """
    Bulk inserts multiple fresh contacts into `hr_contacts_v2`, plus each
    contact's `additional_emails`/`additional_phones` into the
    `hr_contact_emails`/`hr_contact_phones` child tables.

    Same duplicate-email/phone check as `add_fresh_hr_contact()`, just
    run once per contact in the loop. This matters even more for bulk
    inserts, since it's easy for two rows in the same batch (or a row in
    this batch and a contact added earlier) to share an email or phone.

    Returns `{"created_count": int, "merged_count": int}` instead of a
    single total -- this lets the caller tell the user exactly how many
    contacts were brand new vs. how many were merged into an existing
    contact (see `find_existing_contact_by_email_or_phone()` above), the
    same distinction `add_fresh_hr_contact()` reports for a single add.
    """
    async with AsyncSessionLocal() as session:
        created_count = 0
        merged_count = 0

        for payload in payloads:
            emails = _dedupe_preserve_order(
                [payload.email, *getattr(payload, "additional_emails", [])]
            )
            phones = _dedupe_preserve_order(
                [
                    getattr(payload, "contact_number", None) or getattr(payload, "phone", None),
                    *getattr(payload, "additional_phones", []),
                ]
            )

            # ----------------------------------------------------------
            # STEP 1: Has one of these emails/phones already been saved
            # before (either from an earlier contact in this same batch,
            # or from a previous request)? If yes, reuse that contact.
            # ----------------------------------------------------------
            hr = await find_existing_contact_by_email_or_phone(session, emails, phones)
            is_new_contact = hr is None

            if is_new_contact:
                # Genuinely new contact -- safe to create the parent row.
                hr = HRContactsV2(
                    name=payload.name,
                    email=emails[0],
                    title=payload.title,
                    company=payload.company_name,
                    phone=phones[0] if phones else None,
                )
                session.add(hr)
                await session.flush()  # assigns hr.id, needed just below

            # ----------------------------------------------------------
            # STEP 2: Add any emails/phones that aren't already saved.
            # ----------------------------------------------------------
            await _add_contact_emails_and_phones(session, hr, emails, phones)

            if is_new_contact:
                created_count += 1
            else:
                merged_count += 1

        await session.commit()
        return {"created_count": created_count, "merged_count": merged_count}


# -----------------------------------------------------------------------------
# Email Transaction Repository Functions
# -----------------------------------------------------------------------------
async def create_email_transaction(
    request_id: str,
    recipient_email: str,
    status: str,
    error_code: str | None = None,
    response_details: str | None = None,
    user_id : int | None = None
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
            response_details=response_details,
            user_id=user_id
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


async def list_email_transactions(limit: int = 50, offset: int = 0,user_id:int | None = None) -> list[EmailTransaction]:
    """
    Retrieves recent email transactions sorted by creation timestamp descending.
    Supports pagination via `limit` and `offset`.

    `user_id=None` returns transactions across ALL users (adimn view)
    A specif user_id resticts results to that user  
    """

    query = select(EmailTransaction).order_by(desc(EmailTransaction.created_at)).offset(offset).limit(limit)

    if user_id is not None: 
        query = query.where(EmailTransaction.user_id == user_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        return result.scalars().all()


async def get_email_stats(days:int, tz_offset_minutes:int, user_id:int|None = None)-> dict :
    """
    Counts sent and failed emails for each of the last `days` days, for the 
    dashboard. Days are calendar days in the viewer's timezone
    (`tz_offset_minutes` ahead of UTC, e.g. 330 for India), so an email sent
    at 00:30 IST counts on that day, not on the previous UTC day.
    
    `user_id=None` counts every user's emails (admin view), like 
    `list_email_transactions`. 
    """

    offset = timedelta(minutes=tz_offset_minutes)
    today = (datetime.now(timezone.utc)+ offset).date()
    first_day = today - timedelta(days=days-1)
    # Midnight at the start of first_day in the viewer's timezone, expressed in UTC
    window_start = datetime.combine(first_day, time.min, tzinfo=timezone.utc) - offset

    query = select(EmailTransaction.created_at, EmailTransaction.status).where(
        EmailTransaction.created_at >= window_start
    )
    if user_id is not None:
        query = query.where(EmailTransaction.user_id == user_id)

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(query)).all()
        contacts_total = await session.scalar(select(func.count()).select_from(HRContactsV2))

    # One bucket per day, including days with no emails, so the chart has no gaps 
    daily = {first_day + timedelta(days=i): {"sent":0, "failed":0} for i in range(days)}
    for created_at, status in rows:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        day = (created_at.astimezone(timezone.utc) + offset).date()
        if day not in daily:
            continue
        if status == 'SUCCESS':
            daily[day]["sent"] += 1 
        elif status == "FAILED":
            daily[day]["failed"] += 1

    sent = sum(counts["sent"] for counts in daily.values())
    failed = sum(counts["failed"] for counts in daily.values())
    total = sent + failed 

    return{
        "days": days,
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": round(sent/total * 100 , 1) if total else None,
        "contacts_total": contacts_total or 0, 
        "daily": [{"date":day, **counts} for day, counts in daily.items()],
    }

async def update_fresh_hr_contact(contact_id: int, payload)-> HRContactsV2| None:
    """
    Replace a contact's details and its full email/phone lists with the 
    ones in `payload` (same shape as an add). Emails/phones the contact 
    already had are kept (so `is_verified` survives), removed ones are deleted, new ones are inserted; the first email/phone becomes primary. 
    
    Returns `None` if there is no contact with this id. Raises `ValueError`
    if one of the emails/phones already belongs to a DIFFERENT contact,
    since emails and phones are unique across all contacts.
    """
    emails = _dedupe_preserve_order(
        [payload.email, *getattr(payload,"additional_emails",[])]   
    )

    phones = _dedupe_preserve_order(
        [payload.contact_number, *getattr(payload,"additional_phones",[])]
    )

    async with AsyncSessionLocal() as session:
        contact = await session.get(
            HRContactsV2,
            contact_id,
            options=[selectinload(HRContactsV2.emails), selectinload(HRContactsV2.phones)],
        )

        if contact is None:
            return None

        # ------------------------------------------------------------
        # STEP 1: Refuse emails/phones that belong to someone else,
        # checking both the child tables and the old parent columns.
        # ------------------------------------------------------------
        taken_email = await session.scalar(
            select(HRContactEmail.email)
            .where(HRContactEmail.email.in_(emails),HRContactEmail.contact_id != contact_id)
            .union(
                select(HRContactsV2.email)
                .where(HRContactsV2.email.in_(emails), HRContactsV2.id != contact_id)
            )
            .limit(1)
        )
        if taken_email:
            raise ValueError(f"{taken_email} already belongs to another contact")

        if phones:
            taken_phone = await session.scalar(
                select(HRContactPhone.phone)
                .where(HRContactPhone.phone.in_(phones), HRContactPhone.contact_id != contact_id)
                .union(
                    select(HRContactsV2.phone)
                    .where(HRContactsV2.phone.in_(phones), HRContactsV2.id != contact_id)
                )
                .limit(1)
            )
            if taken_phone:
                raise ValueError(f"{taken_phone} already belongs to another contact")

        #------------------------------------------------------------
        # STEP 2: Update the contact row itself.
        #------------------------------------------------------------
        contact.name = payload.name
        contact.title = payload.title
        contact.company = payload.company_name
        contact.email = emails[0]
        contact.phone = phones[0] if phones else None

        # ------------------------------------------------------------
        # STEP 3: Sync the child rows. Removing a row from the list
        # deletes it (`delete-orphan` on the relationship).
        # ------------------------------------------------------------
        current_emails = {row.email: row for row in contact.emails}
        for row in list(contact.emails):
            if row.email not in emails:
                contact.emails.remove(row)

        for index,email in enumerate(emails):
            row = current_emails.get(email)
            if row:
                row.is_primary = index == 0
            else:
                contact.emails.append(HRContactEmail(email=email,is_primary=index ==0))

        current_phones = {row.phone: row for row in contact.phones}
        for row in list(contact.phones):
            if row.phone not in phones:
                contact.phones.remove(row)
        for index,phone in enumerate(phones):
            row = current_phones.get(phone)
            if row:
                row.is_primary = index == 0
            else:
                contact.phones.append(HRContactPhone(phone= phone, is_primary=index == 0)) 

        await session.commit()
        return contact


async def delete_fresh_hr_contact(contact_id: int)-> bool:
    """
    Deletes a contact along with its emails and phones. Returns `False`
    if there is no contact with this id 
    """
    async with AsyncSessionLocal() as session:
        contact = await session.get(
            HRContactsV2,
            contact_id,
            options=[selectinload(HRContactsV2.emails), selectinload(HRContactsV2.phones)],
        )
        if contact is None:
            return False 
        await session.delete(contact)
        await session.commit()
        return True








