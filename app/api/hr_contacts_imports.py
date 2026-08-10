"""
===============================================================================
PDF HR Contact Import API Controller (app/api/hr_contacts_imports.py)
===============================================================================
Provides multipart upload endpoints to parse and import HR contact data 
from PDF files.

Security:
---------
All routes require header authentication via `key-secret`.
===============================================================================
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.hr_contacts_import_service import import_hr_contact_from_pdf
from app.core.security import verify_key_secret

# Initialize Router with Security Dependency
router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)


@router.post("/import")
async def import_hr_contacts(file: UploadFile = File(...)):
    """
    PDF Import Endpoint:
    --------------------
    Uploads a `.pdf` file containing HR contacts, parses text/tables from the document,
    and imports extracted contacts into the database.
    
    Raises:
    -------
    HTTPException 400: If uploaded file does not end with `.pdf`.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files (.pdf) are supported for contact import."
        )
    
    return await import_hr_contact_from_pdf(file)