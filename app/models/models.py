"""
===============================================================================
SQLAlchemy Database Models (models.py)
===============================================================================
Defines ORM database schemas for:
1. `HRContacts`: Legacy HR contact records table (`hr_contacts`).
2. `HRContactsV2`: Fresh HR contact records table (`hr_contacts_v2`).
3. `EmailTransaction`: Transaction tracking table for email delivery state (`email_transactions`).
===============================================================================
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.database import Base


class HRContacts(Base):
    """
    Legacy HR Contacts Table:
    -------------------------
    Stores basic recruiter and company representative contact information.
    """
    __tablename__ = "hr_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)


class HRContactsV2(Base):
    """
    Fresh HR Contacts Table (v2):
    -----------------------------
    Stores upgraded recruiter contacts with automatic server creation timestamp (`created_at`).
    """
    __tablename__ = "hr_contacts_v2"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailTransaction(Base):
    """
    Email Transaction Log Table:
    ----------------------------
    Persists audit records for every single email dispatch attempt.
    
    Columns:
    --------
    - request_id: Unique UUID identifier per email request context.
    - recipient_email: Recipient HR email address.
    - status: "SUCCESS" or "FAILED".
    - error_code: Categorized failure code (CREDENTIALS_EXPIRED, RECIPIENT_NOT_FOUND, etc.).
    - response_details: Human-readable success message or full exception string.
    - created_at: Creation timestamp.
    """
    __tablename__ = "email_transactions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, nullable=False, index=True)
    recipient_email = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    error_code = Column(String, nullable=True)
    response_details = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


