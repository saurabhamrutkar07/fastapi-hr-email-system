"""
===============================================================================
Fresh Contacts V2 Service (fresh_contact_service.py)
===============================================================================
Coordinates business logic for:
1. Creating single fresh recruiter entries.
2. Bulk inserting multiple recruiter contacts.
3. Listing all fresh recruiter contacts.
4. Editing and deleting a contact.
===============================================================================
"""

from fastapi import HTTPException, status
from app.schemas.fresh_contacts import AddFreshContactRequest, BulkAddFreshContactsRequest
from app.database.repositories import add_fresh_hr_contact, add_fresh_hr_contact_bulk, delete_fresh_hr_contact ,get_all_fresh_recruiters, update_fresh_hr_contact


async def create_fresh_contact(payload: AddFreshContactRequest):
    """
    Business Logic: Inserts a single fresh HR contact into `hr_contacts_v2`.

    `add_fresh_hr_contact()` may not always create a brand new row -- if
    the email/phone already belongs to an existing contact, it merges
    into that contact instead (see `find_existing_contact_by_email_or_phone()`
    in `repositories.py`). We use the `is_new_contact` flag it returns to
    make the response say what actually happened, instead of always
    claiming "added successfully".
    """
    contact, is_new_contact = await add_fresh_hr_contact(payload)
    return {
        "status": "success",
        "message": (
            "Fresh contact added successfully"
            if is_new_contact
            else "Contact already existed -- new emails/phones (if any) were merged into it"
        ),
        "contact_id": contact.id,
        "email": contact.email,
        "merged": not is_new_contact,
    }


async def create_fresh_contacts_bulk(payload: BulkAddFreshContactsRequest):
    """
    Business Logic: Bulk inserts a batch of fresh HR contacts into
    `hr_contacts_v2` (plus each contact's extra emails/phones into the
    child tables).

    Some contacts in the batch may get merged into already-existing
    contacts instead of creating new rows (same reasoning as
    `create_fresh_contact()` above) -- so we report `created_count` and
    `merged_count` separately rather than one misleading total.
    """
    counts = await add_fresh_hr_contact_bulk(payload.contacts)
    total_processed = counts["created_count"] + counts["merged_count"]
    return {
        "status": "success",
        "message": (
            f"Processed {total_processed} contacts "
            f"({counts['created_count']} created, {counts['merged_count']} merged)"
        ),
        "created_count": counts["created_count"],
        "merged_count": counts["merged_count"],
        "count": total_processed,
    }


async def list_fresh_contacts():
    """
    Business Logic: Fetches and formats all recruiter contacts from
    `hr_contacts_v2`, along with their full email list (`hr_contact_emails`)
    and phone list (`hr_contact_phones`). The UI searches, filters and 
    pages this list itself.
    """
    recruiters = await get_all_fresh_recruiters()
    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "title": r.title,
            "company": r.company,
            "phone": r.phone,
            "created_at": r.created_at,
            "emails": [
                {
                    "email": e.email,
                    "is_primary": e.is_primary,
                    "is_verified": e.is_verified,
                }
                for e in r.emails
            ],
            "phones": [
                {
                    "phone": p.phone,
                    "is_primary": p.is_primary,
                }
                for p in r.phones
            ],
        }
        for r in recruiters
    ]


async def edit_fresh_contact(contact_id:int, payload:AddFreshContactRequest):
    """
    Business logic: Replaces a contact's details and email/phone lists.
    404 if the contact doesn't exist, 409 if an email/phone belongs to
    another contact.
    """

    try:
        contact = await update_fresh_hr_contact(contact_id,payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')

    return{
        "status": "success",
        "message": "Contact updated",
        "contact_id": contact.id
    }


async def remove_fresh_contact(contact_id:int):
    """
    Business Logic: Deletes a contact with its emails and phones.
    404 if the contact doesn't exist.
    """

    if not await delete_fresh_hr_contact(contact_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Contact not found")

    return {"status": "success", "message": "Contact deleted"}
