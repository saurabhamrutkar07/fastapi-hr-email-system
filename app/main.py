"""
===============================================================================
Application Entry Point (main.py)
===============================================================================
This module serves as the primary entry point for the FastAPI application.
It configures application lifecycle hooks, initializes database schemas,
and registers all API routes across different modular domain controllers.
===============================================================================
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

# Import API Routers from modular domain modules
from app.api.email import router as email_router
from app.api.company import router as company_router
from app.api.hr_contacts_imports import router as hr_contacts_import_router
from app.api.fresh_contacts_api import router as fresh_contacts_router
from app.database.database import init_db
from common.Logger import Logger

logger = Logger.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager:
    -------------------------
    Executes startup and shutdown tasks.
    On application startup, `init_db()` is called to automatically inspect models
    and create missing database tables (e.g., hr_contacts_v2, email_transactions).
    """
    logger.info("Application setup initiated")
    # Initialize database tables on server startup
    await init_db()

    logger.info("Application setup initiated successfull")
    
    # Yield control back to FastAPI to handle incoming HTTP requests
    yield

    logger.info("Application shutdown initiated.")
    
    # Clean-up code on server shutdown can be placed here if needed


# Initialize main FastAPI application instance
app = FastAPI(
    title="HR Contact & Cold Email System",
    description="Automated Cold Emailing System with HR Contact Management and Transaction Tracking",
    version="2.0.0",
    lifespan=lifespan
)

# -----------------------------------------------------------------------------
# Router Registrations
# -----------------------------------------------------------------------------
# Mount Email operations endpoints under `/email` prefix
logger.info("Registering Email Router")
app.include_router(email_router, prefix="/email", tags=["Email"])

# Mount Company contact endpoints under `/company` prefix
logger.info("Registering Company Router")
app.include_router(company_router, prefix="/company", tags=["Company"])

# Mount PDF import endpoints under `/hr-contacts` prefix
logger.info("Registering HR Contacts Router")
app.include_router(hr_contacts_import_router, prefix="/hr-contacts", tags=["HR Contacts"])

# Mount Fresh Contacts (V2 API) endpoints under `/contacts/v2` prefix
logger.info("Registering Fresh Contacts Router")
app.include_router(fresh_contacts_router, prefix="/contacts/v2", tags=["Fresh Contacts (v2)"])


