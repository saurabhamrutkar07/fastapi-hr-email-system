from fastapi import APIRouter,Depends
from app.schemas.email import JobApplicationEmailRequest
from app.services.cold_email_service import send_cold_emails
from app.core.security import verify_key_secret

router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)

@router.post("/send-cold")
async def send_cold_email(payload: JobApplicationEmailRequest):
    return await send_cold_emails(payload)
