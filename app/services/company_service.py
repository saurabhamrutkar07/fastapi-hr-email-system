"""
===============================================================================
Company Contact Service (company_service.py)
===============================================================================
Provides business logic for adding company contacts via database repository.
===============================================================================
"""

from app.database.repositories import add_hr_contact
from common.Logger import Logger

async def create_company_contact(payload,logger = None):
    """
    Business Logic: Creates a new company contact record in the database repository.
    """
    if logger is None :
        logger = Logger.get_logger()

    
    logger.info("Started creating company contact.")
    
    await add_hr_contact(payload,logger=logger)
    logger.info("Company contact created successfully.")

    return {"status": "success", "message": "Company contact successfully created."}

