"""
===============================================================================
PDF HR Contact Import Service (hr_contacts_import_service.py)
===============================================================================
Coordinates threadpool PDF text extraction and bulk contact database insertion.
Uses `run_in_threadpool` to prevent blocking FastAPI's async event loop during CPU-heavy PDF parsing.
===============================================================================
"""

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from app.services.pdf_hr_extraction_service import extract_pdf_contact_from_pdf
from app.database.repositories import add_fresh_hr_contact_bulk


async def import_hr_contact_from_pdf(file: UploadFile):
    """
    Asynchronously parses uploaded PDF documents and imports extracted HR contact data into the database.

    Flow:
    -----
    1. Delegates CPU-bound PDF parsing to a background worker thread (`run_in_threadpool`).
    2. Validates extracted contact dictionary array.
    3. Persists valid records in `hr_contacts_v2` database table via `add_fresh_hr_contact_bulk`.
    """
    # Execute CPU-bound PDF extraction off the main asyncio event loop thread
    extracted_data = await run_in_threadpool(extract_pdf_contact_from_pdf, file.file)
    
    if not extracted_data:
        return {
            "status": "no_data_found",
            "inserted": 0,
            "message": "No valid HR contact entries could be extracted from the provided PDF."
        }

    # Bulk insert extracted records into database
    inserted_count = await add_fresh_hr_contact_bulk(extracted_data)

    return {
        "status": "success",
        "inserted": inserted_count,
        "message": f"Successfully parsed and imported {inserted_count} HR contacts from PDF."
    }


