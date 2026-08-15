"""
SQLAlchemy Database Models (models.py)

Defines ORM database schemas for:

1. HRContacts:
   Legacy HR contact records table (`hr_contacts`).

2. HRContactsV2:
   Fresh HR contact records table (`hr_contacts_v2`).

3. HRContactEmail:
   Stores multiple email addresses for a single HR contact.

4. HRContactPhone:
   Stores multiple phone numbers for a single HR contact.

5. EmailTransaction:
   Transaction tracking table for email delivery state.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class HRContacts(Base):
    """
    Legacy HR Contacts Table.

    Stores basic recruiter and company representative
    contact information.
    """

    __tablename__ = "hr_contacts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    title = Column(
        String,
        nullable=True
    )

    company = Column(
        String,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )


class HRContactsV2(Base):
    """
    Fresh HR Contacts Table (v2).

    Stores the main HR contact information.

    NOTE:
    `email` and `phone` are intentionally kept here for now
    to avoid breaking existing data/application logic.

    They can be removed later after migration to:
        - HRContactEmail
        - HRContactPhone
    """

    __tablename__ = "hr_contacts_v2"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    # Existing column - kept for backward compatibility
    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    title = Column(
        String,
        nullable=True
    )

    company = Column(
        String,
        nullable=True
    )

    # Existing column - kept for backward compatibility
    phone = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # One contact -> multiple emails
    emails = relationship(
        "HRContactEmail",
        back_populates="contact",
        cascade="all, delete-orphan"
    )

    # One contact -> multiple phones
    phones = relationship(
        "HRContactPhone",
        back_populates="contact",
        cascade="all, delete-orphan"
    )


class HRContactEmail(Base):
    """
    Stores multiple email addresses for an HR contact.

    Example:

        HR Contact
            |
            +-- email1@gmail.com
            +-- email2@gmail.com
            +-- email3@gmail.com
    """

    __tablename__ = "hr_contact_emails"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    contact_id = Column(
        Integer,
        ForeignKey(
            "hr_contacts_v2.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    is_primary = Column(
        Boolean,
        nullable=False,
        default=False
    )

    is_verified = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    contact = relationship(
        "HRContactsV2",
        back_populates="emails"
    )


class HRContactPhone(Base):
    """
    Stores multiple phone numbers for an HR contact.

    Example:

        HR Contact
            |
            +-- 9876543210
            +-- 9123456780
            +-- 9988776655
    """

    __tablename__ = "hr_contact_phones"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    contact_id = Column(
        Integer,
        ForeignKey(
            "hr_contacts_v2.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    phone = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    is_primary = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    contact = relationship(
        "HRContactsV2",
        back_populates="phones"
    )


class EmailTransaction(Base):
    """
    Email Transaction Log Table.

    Persists audit records for every single email dispatch attempt.

    Columns:
        - request_id:
            Unique UUID identifier per email request context.

        - recipient_email:
            Recipient HR email address.

        - status:
            SUCCESS or FAILED.

        - error_code:
            Categorized failure code.

        - response_details:
            Human-readable success message or exception details.

        - created_at:
            Creation timestamp.
    """

    __tablename__ = "email_transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    request_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    recipient_email = Column(
        String,
        nullable=False,
        index=True
    )

    status = Column(
        String,
        nullable=False
    )

    error_code = Column(
        String,
        nullable=True
    )

    response_details = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )