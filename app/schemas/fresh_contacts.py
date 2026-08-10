"""
===============================================================================
Fresh Contacts V2 Pydantic Schemas (app/schemas/fresh_contacts.py)
===============================================================================
Defines data validation models for:
1. `AddFreshContactRequest`: Single fresh HR contact creation payload.
2. `BulkAddFreshContactsRequest`: Bulk fresh HR contacts creation payload.
3. `FreshContactResponse`: Fresh contact response object model.
===============================================================================
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class AddFreshContactRequest(BaseModel):
    """
    Request model for creating a single fresh recruiter contact entry.
    """
    name: str = Field(..., min_length=2, description="Name of HR or recruiter")
    email: EmailStr = Field(..., description="Valid work email address")
    title: Optional[str] = Field(None, description="Job title or designation")
    company_name: Optional[str] = Field(None, description="Company name")
    contact_number: Optional[str] = Field(None, description="Phone number or contact details")


class BulkAddFreshContactsRequest(BaseModel):
    """
    Request model for bulk inserting multiple fresh contacts.
    """
    contacts: List[AddFreshContactRequest] = Field(description="List of recruiter contact objects")


class FreshContactResponse(BaseModel):
    """
    Response model representing a fresh recruiter contact in v2 table.
    """
    id: int
    name: str
    email: str
    title: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True

