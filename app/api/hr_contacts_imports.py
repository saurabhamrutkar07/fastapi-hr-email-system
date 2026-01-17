from fastapi import APIRouter, UploadFile, File, HTTPException,Depends
from app.services.hr_contacts_import_service import import_hr_contact_from_pdf
from app.core.security import verify_key_secret

router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)

@router.post("/import")
async def import_hr_contacts(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400,detail="only pdf files are supported")
    
    return await import_hr_contact_from_pdf(file)