"""
Application Entry Point (main.py)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

# ============================================================
# API Routers
# ============================================================

from app.api.email import router as email_router
from app.api.company import router as company_router
from app.api.hr_contacts_imports import (
    router as hr_contacts_import_router,
)
from app.api.fresh_contacts_api import (
    router as fresh_contacts_router,
)
from app.api.hr_contacts import (
    router as hr_contacts_router,
)

# ============================================================
# Database
# ============================================================

from app.database.database import init_db

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
    # --------------------------------------------------------

    await init_db()

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
# Fresh Contacts V2 APIs
#
# Example:
#
# POST /contacts/v2/...
# ------------------------------------------------------------

logger.info(
    "Registering Fresh Contacts Router"
)

app.include_router(
    fresh_contacts_router,
    prefix="/contacts/v2",
    tags=["Fresh Contacts (v2)"],
)


# ------------------------------------------------------------
# HR Contacts APIs
#
# Keep this separate from import APIs if this router
# contains normal CRUD/business operations.
#
# Example:
#
# GET /hr-contacts/...
#
# IMPORTANT:
# If hr_contacts_router already uses the same paths as
# hr_contacts_import_router, don't register duplicate routes.
# ------------------------------------------------------------

logger.info(
    "Registering HR Contacts Router"
)

app.include_router(
    hr_contacts_router,
    prefix="/hr-contacts",
    tags=["HR Contacts"],
)