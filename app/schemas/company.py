"""
===============================================================================
Company Contact Pydantic Schemas (app/schemas/company.py)
===============================================================================
Defines data validation models for incoming company contact creation requests.
===============================================================================
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import re


class AddCompanyDetailsRequest(BaseModel):
    """
    Request payload schema for adding new company HR details.
    
    Fields:
    -------
    - name: HR recruiter full name (minimum 3 characters).
    - email: Valid email address format.
    - title: Job title or designation (e.g. Talent Acquisition Lead).
    - company_name: Name of hiring organization.
    - contact_number: Optional phone number string.
    """
    name: str = Field(min_length=3, description="HR contact full name")
    email: EmailStr = Field(description="Valid work email address")
    title: str = Field(description="Designation / job title")
    company_name: str = Field(description="Company or employer name")
    contact_number: Optional[str] = Field(None, description="Optional phone number")

    @classmethod
    def validate_text(cls, v: str):
        """
        Custom text sanitizer ensuring input contains only allowed characters.
        """
        if not re.fullmatch(r"[A-Za-z0-9 .&'-]+", v):
            raise ValueError("Only alphanumeric characters and standard punctuation allowed")
        return v.strip()

