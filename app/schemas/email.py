"""
===============================================================================
Email Service Pydantic Schemas (app/schemas/email.py)
===============================================================================
Defines data validation models for:
1. `JobApplicationEmailRequest`: Mass cold email request payload.
2. `SingleHREmailRequest`: Targeted individual HR cold email request payload.
3. `EmailTransactionResponse`: Response schema for database transaction queries.
===============================================================================
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.base import BaseSchema


class JobApplicationEmailRequest(BaseSchema):
    """
    Payload model for sending mass cold application emails to all DB recruiters.
    """
    applicant_name: str = Field(min_length=2, max_length=100,description="Applicant full name")
    email: EmailStr = Field(description="Applicant contact email address")
    contact_number: str = Field(max_length=20,description="Applicant phone number")
    job_position: str = Field(min_length=2, max_length=150,description="Target job title / role")
    experience_years: float = Field(ge=0, description="Years of professional experience")
    skills: List[str] = Field(min_length=1, description="List of primary technical skills")
    linkedin_url: str = Field(min_length=1, max_length=500,description="Applicant LinkedIn profile URL")


class SingleHREmailRequest(BaseSchema):
    """
    Payload model for sending a targeted cold application email to a specific HR.
    """
    # Applicant details
    applicant_name: str = Field(min_length=2, max_length=100, description="Applicant full name")
    email: EmailStr = Field(description="Applicant contact email address")
    contact_number: str = Field(max_length=20,description="Applicant phone number")
    job_position: str = Field(min_length=2,max_length=150, description="Target job title / role")
    experience_years: float = Field(ge=0, description="Years of professional experience")
    skills: List[str] = Field(min_length=1, description="List of primary technical skills")

    # Target HR details
    hr_name: str = Field(min_length=2,max_length=100, description="Recruiter / HR full name")
    hr_email: EmailStr = Field(description="Recruiter / HR work email address")

    company_name: str = Field(min_length=1,max_length=150, description="Hiring company name")
    linkedin_url: str = Field(min_length=1,max_length=500, description="Applicant LinkedIn profile URL")

    # Optional employer details
    title: Optional[str] = Field(None,max_length=150, description="Recruiter job title")


class EmailTransactionResponse(BaseModel):
    """
    Response schema representing an email transaction audit log record.
    """
    id: int
    request_id: str = Field(description="Unique UUID request tracking ID")
    recipient_email: str = Field(description="Target recipient email address")
    status: str = Field(description="Execution status: SUCCESS or FAILED")
    error_code: Optional[str] = Field(None, description="Categorized failure type if failed")
    response_details: Optional[str] = Field(None, description="Success details or raw error message")
    created_at: datetime = Field(description="Transaction timestamp")

    class Config:
        from_attributes = True


