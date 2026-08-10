"""
===============================================================================
Company Contact Service (company_service.py)
===============================================================================
Provides business logic for adding company contacts via database repository.
===============================================================================
"""

from app.database.repositories import add_hr_contact


async def create_company_contact(payload):
    """
    Business Logic: Creates a new company contact record in the database repository.
    """
    await add_hr_contact(payload)
    return {"status": "success", "message": "Company contact successfully created."}

