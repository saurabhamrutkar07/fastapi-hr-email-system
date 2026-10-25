"""
===============================================================================
Sending Schemas (app/schemas/sending.py)
===============================================================================
Defines data validation models for the Send Email page:
1. `SenderProfileCreate` / `SenderProfileResponse`: the user's saved
   "about me" details (job position, experience, skills, LinkedIn).
2. `TestModeUpdate` / `TestModeResponse`: an admin's test switch.
3. `EmailPreviewRequest` / `EmailPreviewResponse`: one filled-in email.
4. `SendEmailsRequest` / `SendEmailsResponse`: emails to chosen contacts.
5. `EmailStatusItem`: how one queued email went.
===============================================================================
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr,Field,field_validator
from app.schemas.base import BaseSchema

# Most emails one Send click may queue; well under Gmail's ~500 a day 
MAX_RECIPIENTS = 50 


class SenderProfileCreate(BaseSchema):
    """
    Also used to edit a profile; `is_default` only matters when creating 
    (the default is changed with /set-default).
    """

    name : str = Field(...,min_length=1, max_length=60,description="Only you see this, e.g. 'Backend roles'")
    job_position : str = Field(..., min_length=2, max_length=150)
    experience_years : float = Field(...,ge=0,le=50)
    skills : List[str] = Field(...,min_length=1, max_length=20)
    linkedin_url : Optional[str] = Field(None, max_length=500)
    is_default : bool = False

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, skills: List[str]) -> List[str]:
        """
        Splits "Python, FastAPI" typed in one box, drops empty entries 
        and repeats (ignoring case), since skills are stored comma-separated.
        """
        cleaned = []
        for item in skills:
            for skill in item.split(","):
                skill = skill.strip()
                if skill and skill.lower() not in [s.lower() for s in cleaned]:
                    if len(skill) > 50:
                        raise ValueError("Keep each skill under 50 characters.")
                    cleaned.append(skill)

        if not cleaned:
            raise ValueError("Add at least one skill.")
        return cleaned


class SenderProfileResponse(BaseModel):
    id : int 
    name : str 
    job_position : str 
    experience_years : float 
    skills : List[str]
    linkedin_url : Optional[str]
    is_default : bool 


class TestModeUpdate(BaseSchema):
    enabled : bool 
    test_emails : List[EmailStr] = Field(default_factory=list, max_length=20)


class TestModeResponse(BaseModel):
    enabled : bool 
    test_emails : List[str]


class EmailPreviewRequest(BaseSchema):
    contact_id : int 
    template_id : int 
    sender_profile_id : int 


class EmailPreviewResponse(BaseModel):
    contact_id : int 
    to_name : str 
    to_email : str 
    company : Optional[str]
    subject : str 
    body : str 
    attachment_name : str 


class SendEmailsRequest(BaseSchema):
    contact_ids : List[int] = Field(..., min_length=1, max_length=MAX_RECIPIENTS)
    template_id : int 
    sender_profile_id : int 

    @field_validator("contact_ids")
    @classmethod
    def unique_contacts(cls, contact_ids: List[int]) -> List[int]:
        """The same contact picked twice still gets one email."""
        return list(dict.fromkeys(contact_ids))


class QueuedEmail(BaseModel):
    contact_id : int 
    name : str 
    email : str 
    request_id : str 


class SendEmailsResponse(BaseModel):
    total : int 
    test_mode : bool 
    items : List[QueuedEmail]


class EmailStatusItem(BaseModel):
    request_id : str 
    status : str = Field(description="PENDING until the email is tried, then SUCCESS or FAILED")
    error_code : Optional[str] = None
    response_details : Optional[str] = None
