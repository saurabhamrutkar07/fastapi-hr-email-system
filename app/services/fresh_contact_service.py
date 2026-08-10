"""
===============================================================================
Fresh Contacts V2 Service (fresh_contact_service.py)
===============================================================================
Coordinates business logic for:
1. Creating single fresh recruiter entries.
2. Bulk inserting multiple recruiter contacts.
3. Listing all fresh recruiter contacts.
===============================================================================
"""

from app.schemas.fresh_contacts import AddFreshContactRequest, BulkAddFreshContactsRequest
from app.database.repositories import add_fresh_hr_contact, add_fresh_hr_contact_bulk, get_all_fresh_recruiters


async def create_fresh_contact(payload: AddFreshContactRequest):
    """
    Business Logic: Inserts a single fresh HR contact into `hr_contacts_v2`.
    """
    contact = await add_fresh_hr_contact(payload)
    return {
        "status": "success",
        "message": "Fresh contact added successfully",
        "contact_id": contact.id,
        "email": contact.email
    }


async def create_fresh_contacts_bulk(payload: BulkAddFreshContactsRequest):
    """
    Business Logic: Bulk inserts a batch of fresh HR contacts into `hr_contacts_v2`.
    """
    data = [
        {
            "name": c.name,
            "email": c.email,
            "title": c.title,
            "company": c.company_name,
            "phone": c.contact_number
        }
        for c in payload.contacts
    ]
    inserted_count = await add_fresh_hr_contact_bulk(data)
    return {
        "status": "success",
        "message": f"Successfully inserted {inserted_count} fresh contacts",
        "count": inserted_count
    }


async def list_fresh_contacts():
    """
    Business Logic: Fetches and formats all recruiter contacts from `hr_contacts_v2`.
    """
    recruiters = await get_all_fresh_recruiters()
    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "title": r.title,
            "company": r.company,
            "phone": r.phone
        }
        for r in recruiters
    ]

