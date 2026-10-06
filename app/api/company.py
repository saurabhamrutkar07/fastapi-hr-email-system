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
from app.core.security import require_admin
from common.Logger import Logger

logger = Logger.get_logger()

# Initialize Router with Security Dependency
router = APIRouter(
    dependencies=[Depends(require_admin)]
)


@router.post("/add-company-details")
async def add_company_details(payload: AddCompanyDetailsRequest):
    """
    Add Company Contact Endpoint:
    -----------------------------
    Accepts company HR details (name, email, title, company_name) and saves them into the database.
    """
    logger.info("Execution of function create_company_contact started")
    return await create_company_contact(payload,logger)

