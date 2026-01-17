from fastapi import APIRouter,Depends
from app.schemas.company import AddCompanyDetailsRequest
from app.services.company_service import create_company_contact
from app.core.security import verify_key_secret

router = APIRouter(
    dependencies=[Depends(verify_key_secret)]
)

@router.post("/add-company-details")
async def add_company_details(payload: AddCompanyDetailsRequest):
    return await create_company_contact(payload)
