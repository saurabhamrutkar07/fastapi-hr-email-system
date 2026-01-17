from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import re

class AddCompanyDetailsRequest(BaseModel):
    name: str = Field(min_length=3)
    email: EmailStr
    title: str
    company_name: str
    contact_number: Optional[str] = None

    @classmethod
    def validate_text(cls, v: str):
        if not re.fullmatch(r"[A-Za-z0-9 .&'-]+", v):
            raise ValueError("Only letters and spaces allowed")
        return v.strip()
