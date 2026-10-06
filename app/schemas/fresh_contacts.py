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
from app.schemas.base import BaseSchema


class AddFreshContactRequest(BaseSchema):
    """
    Request model for creating a single fresh recruiter contact entry.

    `email`/`contact_number` are the primary email/phone (stored on
    `hr_contacts_v2` for backward compatibility). `additional_emails`/
    `additional_phones` are optional extra values stored in the
    `hr_contact_emails`/`hr_contact_phones` child tables alongside the
    primary one.
    """
    name: str = Field(..., min_length=2,max_length=100, description="Name of HR or recruiter")
    email: EmailStr = Field(..., description="Primary work email address")
    additional_emails: List[EmailStr] = Field(
        default_factory=list,
        description="Any extra email addresses for this contact",
    )
    title: Optional[str] = Field(None,max_length=150, description="Job title or designation")
    company_name: Optional[str] = Field(None,max_length=150, description="Company name")
    contact_number: Optional[str] = Field(None,max_length=20 ,description="Primary phone number")
    additional_phones: List[str] = Field(
        default_factory=list,
        description="Any extra phone numbers for this contact",
    )


class BulkAddFreshContactsRequest(BaseSchema):
    """
    Request model for bulk inserting multiple fresh contacts.
    """
    contacts: List[AddFreshContactRequest] = Field(description="List of recruiter contact objects")


class EmailItem(BaseModel):
    """
    A single email address belonging to a contact, from `hr_contact_emails`.
    """
    email: str
    is_primary: bool
    is_verified: bool

    class Config:
        from_attributes = True


class PhoneItem(BaseModel):
    """
    A single phone number belonging to a contact, from `hr_contact_phones`.
    """
    phone: str
    is_primary: bool

    class Config:
        from_attributes = True


class FreshContactResponse(BaseModel):
    """
    Response model representing a fresh recruiter contact in v2 table,
    including its full email/phone lists from `hr_contact_emails` and
    `hr_contact_phones`.
    """
    id: int
    name: str
    email: str
    title: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    emails: List[EmailItem] = []
    phones: List[PhoneItem] = []

    class Config:
        from_attributes = True

