"""
===============================================================================
Company API Controller (app/api/company.py)
===============================================================================
Provides API routes for creating and managing company HR contacts.

Security:
---------
All routes require valid `key-secret` header authentication.
===============================================================================
"""

from fastapi import APIRouter, Depends
from app.schemas.company import AddCompanyDetailsRequest
from app.services.company_service import create_company_contact
from app.core.security import verify_key_secret

# Initialize Router with Security Dependency
router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)


@router.post("/add-company-details")
async def add_company_details(payload: AddCompanyDetailsRequest):
    """
    Add Company Contact Endpoint:
    -----------------------------
    Accepts company HR details (name, email, title, company_name) and saves them into the database.
    """
    return await create_company_contact(payload)

