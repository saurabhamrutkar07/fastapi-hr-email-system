"""
Application Entry Point (main.py)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import FRONTEND_URL, APP_ENV
from app.core.rate_limit import limiter,rate_limit_exceeded
from app.core.monitoring import init_sentry
from app.core.request_id import request_id_middleware

# ============================================================
# API Routers
# ============================================================

from app.api.email import router as email_router
from app.api.hr_contacts import (
    router as hr_contacts_router,
)
from app.api.auth import router as auth_router
from app.api.smtp_credentials import router as smtp_credentials_router
from app.api.email_templates import router as email_tmeplate_router
from app.api.resumes import router as resume_rouer
from app.api.users import router as users_router
from app.api.sender_profiles import router as sender_profiles_router
from app.api.test_mode import router as test_mode_router
from app.api.health import router as health_router


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
        Only logs. Database tables are created and changed by
        migrations: run `alembic upgrade head` before starting the app.


    Shutdown:
        Performs application shutdown logging.
    """

    logger.info(
        "Application setup initiated"
    )

    
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
# Before the app is created, so Sentry can hook into FastAPI
init_sentry()

# API docs (/docs, /redoc, /openapi.json) only outside production.
# On the live server they would hand out a map of every endpoint.
SHOW_DOCS = APP_ENV != "production"

app = FastAPI(
    title="HR Contact & Cold Email System",
    description=(
        "Automated Cold Emailing System with "
        "HR Contact Management and "
        "Transaction Tracking"
    ),
    version="2.0.0",
    lifespan=lifespan,
    # None = FastAPI does not create that route at all
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)
# Request id on every log line + clean 500s (app/core/request_id.py).
# Added before CORS: the middleware added last runs first, so CORS wraps
# this one and even a crash's 500 gets CORS headers the browser can read.
app.middleware("http")(request_id_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]

)

# Rate limits on login, OTP and email-sending endpoints (app/core/rate_limit.py)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,rate_limit_exceeded)

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

app.include_router(
    sender_profiles_router,
    prefix="/sender-profiles",
    tags=["Sender Details"],
)

app.include_router(
    test_mode_router,
    prefix="/test-mode",
    tags=["Test Mode (admin)"],
)

# GET /health (no login): is the app and its database up?
app.include_router(health_router, tags=["Health"])

