"""
Application Entry Point (main.py)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import FRONTEND_URL

# ============================================================
# API Routers
# ============================================================

from app.api.email import router as email_router
from app.api.company import router as company_router
from app.api.hr_contacts_imports import (
    router as hr_contacts_import_router,
)
from app.api.hr_contacts import (
    router as hr_contacts_router,
)
from app.api.auth import router as auth_router
from app.api.smtp_credentials import router as smtp_credentials_router
from app.api.email_templates import router as email_tmeplate_router
from app.api.resumes import router as resume_rouer
from app.api.users import router as users_router
# ============================================================
# Database
# ============================================================

from app.database.database import create_tables

# ============================================================
# Logger
# ============================================================

from common.Logger import Logger


logger = Logger.get_logger()


# ============================================================
# Application Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager.

    Startup:
        Initializes missing database tables.

    Shutdown:
        Performs application shutdown logging.
    """

    logger.info(
        "Application setup initiated"
    )

    # --------------------------------------------------------
    # Initialize database
    #
    # `create_tables()` only creates missing tables -- it is not
    # the per-request DB session dependency (that's `get_db()`,
    # used via `Depends()` inside individual routers).
    # --------------------------------------------------------

    await create_tables()

    logger.info(
        "Application setup initiated successfully"
    )

    # --------------------------------------------------------
    # Application runs here
    # --------------------------------------------------------

    yield

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    logger.info(
        "Application shutdown initiated."
    )


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="HR Contact & Cold Email System",
    description=(
        "Automated Cold Emailing System with "
        "HR Contact Management and "
        "Transaction Tracking"
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]

)


# ============================================================
# Router Registrations
# ============================================================

# ------------------------------------------------------------
# Email APIs
#
# Example:
# POST /email/...
# ------------------------------------------------------------

logger.info(
    "Registering Email Router"
)

app.include_router(
    email_router,
    prefix="/email",
    tags=["Email"],
)


# ------------------------------------------------------------
# Company APIs
#
# Example:
# POST /company/...
# ------------------------------------------------------------

logger.info(
    "Registering Company Router"
)

app.include_router(
    company_router,
    prefix="/company",
    tags=["Company"],
)


# ------------------------------------------------------------
# HR Contact Import APIs
#
# This router should contain:
#
# - Excel upload
# - CSV upload
# - Other HR contact import functionality
#
# Example:
#
# POST /hr-contacts/upload-file
# ------------------------------------------------------------

logger.info(
    "Registering HR Contact Import Router"
)

app.include_router(
    hr_contacts_import_router,
    prefix="/hr-contacts",
    tags=["HR Contacts"],
)


# ------------------------------------------------------------
# HR Contacts V2 APIs
#
# All routes for the v2 schema (`hr_contacts_v2`,
# `hr_contact_emails`, `hr_contact_phones`) live in one place:
# app/api/hr_contacts.py. Mounted under a prefix that identifies
# it as the v2 table, distinct from the legacy `/hr-contacts`
# import router below.
#
# Example:
#
# POST /hr-contacts/v2/upload-file
# POST /hr-contacts/v2/add
# POST /hr-contacts/v2/bulk-add
# GET  /hr-contacts/v2/list
# ------------------------------------------------------------

logger.info(
    "Registering HR Contacts V2 Router"
)

app.include_router(
    hr_contacts_router,
    prefix="/hr-contacts/v2",
    tags=["HR Contacts V2"],
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)

app.include_router(
    smtp_credentials_router,
    prefix="/smtp-credentials",
    tags = ["SMTP Credentaials"],
)

app.include_router(
    email_tmeplate_router,
    prefix="/email-template",
    tags=["Email Templates"]
)

app.include_router(
    resume_rouer,
    prefix="/resumes",
    tags = ["Resumes"],
)

app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)