from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from app.services.pdf_hr_extraction_service import extract_pdf_contact_from_pdf
from app.database.repositories import add_hr_contact_bulk

async def import_hr_contact_from_pdf(file:UploadFile):
    extracted_data = await run_in_threadpool(extract_pdf_contact_from_pdf,file.file)
    if not extracted_data:
        return{
            "status": "no data found",
            "inserted": 0 
        }
    # inserted_count = await add_hr_contact_bulk(extracted_data)

    # return {
    #     "status": "success",
    #     "inserted": inserted_count
    # }
    return {
        "result" : "success"
    }
