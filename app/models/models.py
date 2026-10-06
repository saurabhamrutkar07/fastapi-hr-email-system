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

6. User:
   Registered application user (signup/login), email + mobile.

7. OTP:
   One-time-password records used to verify a user's email
   during signup (and, later, password reset).
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

class User(Base):
    """
    Registered Application User.

    Created in a "pending" state at signup (`is_email_verified=False`,
    `is_active=False`, `password_hash=None`). Only becomes usable for
    login once the signup flow completes end-to-end:

        1. POST /auth/signup        -> row created here, OTP emailed.
        2. POST /auth/verify-otp    -> `is_email_verified` set True.
        3. POST /auth/set-password  -> `password_hash` set,
                                        `is_active` set True.

    `mobile` is collected but never OTP-verified (email-only
    verification, by design) -- do not treat it as a trusted contact
    method.
    """

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True 
        )

    name = Column(String,
                  nullable=False,
                  )

    mobile = Column(String,
                    nullable= True)

    email = Column(String,
          unique=True,
                nullable=False,
                index=True
                )
    password_hash = Column(
        String,
        nullable=True,
        )
    is_email_verified = Column(
      Boolean, nullable=False, default=False  
    )

    is_active = Column(
        Boolean, nullable=False, default=False
    )
    role = Column(String, nullable=False,default="user")
    google_id = Column(String,unique=True, nullable=True)
    auth_provider = Column(String,nullable=False,default="local")
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    email_transactions = relationship("EmailTransaction",back_populates="user")

class OTP(Base):
    """
    One-Time-Password Records.

    One row per OTP sent to a user. `otp_hash` stores a hash of the
    code (same as a password), never the plain digits -- verification
    hashes the submitted code and compares, mirroring password login.

    `purpose` distinguishes what the OTP is for (e.g. "signup" today,
    "password_reset" later), so a user can have multiple OTP rows
    without them being usable interchangeably.

    `attempts` counts failed verification tries against this specific
    OTP, so repeated wrong guesses can be capped instead of allowing
    unlimited brute-force attempts against a 6-digit code.
    """

    __tablename__ = "otps"

    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    otp_hash = Column(String,nullable=False)
    purpose = Column(String,nullable=False)
    expires_at = Column(DateTime(timezone=True),nullable=False)
    is_used = Column(Boolean,nullable=False,default=False)
    attempts = Column(Integer,nullable=False,default=0)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

class UserSMTPCredential(Base):
    """
        Per-User SMTP Credential.

        Stores each user's own SMTP sender email and encrypted app
        password, used to send cold emails from their own account.
        Encrypted (not hashed) because the raw password must be
        recoverable at send time to authenticate with the SMTP server.
    """
    __tablename__ = "user_smtp_credentials"
    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),unique=True,nullable=False,index=True)
    smtp_server = Column(String,nullable=False,default="smtp.gmail.com")
    smtp_port = Column(Integer,nullable=False,default=587)
    email_address = Column(String,nullable=False)
    encrypted_password = Column(String,nullable=False)
    is_active = Column(Boolean, nullable=False,default=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now())


class UserEmailTemplate(Base):
    """
    Per-User Email Template.

    Stores each user's own cold email templates, replacing the
    previously hardcoded template file. `is_default` marks which
    template is used automatically when sending, if a user has
    more than one saved.
    """
    __tablename__ = "user_email_templates"

    id = Column(Integer, primary_key=True,index=True)
    user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    name = Column(String,nullable=False)
    subject = Column(String,nullable=True)
    content = Column(String,nullable=False)
    is_default = Column(Boolean,nullable=False,default=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    
     

class UserResume(Base):
    """
    Per-User Resume.

    Stores multiple resume versions per user; only one version
    is marked active (`is_active=True`) at a time -- that is the
    one attached when sending cold emails.
    """
    __tablename__ = "user_resumes"

    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    file_path = Column(String,nullable=False)
    version_number = Column(Integer,nullable=False)
    is_active= Column(Boolean,nullable=False,default=True)
    uploaded_at = Column(DateTime(timezone=True),server_default=func.now())


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

    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=True,index=True)

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

    user = relationship("User", back_populates="email_transactions")

class RevokedRefreshToken(Base):
    """
    Tracks refresh tokens that have been revoked (e.g. vai logout).
    Checked by /auth/refresh before issuing a new access token --
    access tokens themselves are never checked here, they simply
    expire naturally on their own short TTL (the accepted industry
    tradeoff for stateless JWRs).
    """

    __tablename__ = "revoked_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
