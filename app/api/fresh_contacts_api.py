"""
===============================================================================
Fresh Contacts V2 API Controller (app/api/fresh_contacts_api.py)
===============================================================================
Provides CRUD endpoints for managing upgraded recruiter contact entries (`hr_contacts_v2`):
1. `POST /contacts/v2/add`: Insert a single contact.
2. `POST /contacts/v2/bulk-add`: Insert multiple contacts in a single bulk request.
3. `GET /contacts/v2/list`: List all stored contacts in v2 format.

Security:
---------
All routes require header authentication via `key-secret`.
===============================================================================
"""

from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.fresh_contacts import AddFreshContactRequest, BulkAddFreshContactsRequest, FreshContactResponse
from app.services.fresh_contact_service import create_fresh_contact, create_fresh_contacts_bulk, list_fresh_contacts
from app.core.security import verify_key_secret

# Initialize Router with Security Dependency
router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_fresh_contact(payload: AddFreshContactRequest):
    """
    Single Contact Creation Endpoint:
    ---------------------------------
    Adds a single fresh HR/recruiter contact into the `hr_contacts_v2` database table.
    Returns status 201 Created.
    """
    return await create_fresh_contact(payload)


@router.post("/bulk-add", status_code=status.HTTP_201_CREATED)
async def bulk_add_fresh_contacts(payload: BulkAddFreshContactsRequest):
    """
    Bulk Contacts Insertion Endpoint:
    ---------------------------------
    Adds multiple HR contacts into `hr_contacts_v2` in a single request.
    Returns status 201 Created.
    """
    return await create_fresh_contacts_bulk(payload)


@router.get("/list", response_model=List[FreshContactResponse])
async def get_fresh_contacts():
    """
    List Contacts Endpoint:
    -----------------------
    Retrieves all fresh HR contacts from the `hr_contacts_v2` database table.
    """
    return await list_fresh_contacts()

