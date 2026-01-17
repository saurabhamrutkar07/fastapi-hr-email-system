from fastapi import FastAPI
from app.api.email import router as email_router
from app.api.company import router as company_router
from app.api.hr_contacts_imports import router as hr_contacts_import_router


app = FastAPI()
app.include_router(email_router, prefix="/email", tags=["Email"])


app.include_router(company_router, prefix="/company", tags=["Company"])

app.include_router(hr_contacts_import_router,prefix="/hr-contacts",tags=["HR Contacts"])
