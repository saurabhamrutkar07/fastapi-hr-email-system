from pydantic import BaseModel, EmailStr, Field
from typing import List

class JobApplicationEmailRequest(BaseModel):
    applicant_name: str = Field(min_length=2)
    email: EmailStr
    contact_number: str
    job_position: str = Field(min_length=2)
    experience_years: float = Field(ge=0)
    skills: List[str]
