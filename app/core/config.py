"""
===============================================================================
Application Configuration (config.py)
===============================================================================
Loads environment variables from `.env` using `python-dotenv` and defines
global configuration constants for SMTP mail settings, directory paths,
external URLs, resume attachment paths, and security tokens.
===============================================================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from local `.env` file into system environment
load_dotenv()

# -----------------------------------------------------------------------------
# SMTP Mailer Settings
# -----------------------------------------------------------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# -----------------------------------------------------------------------------
# Social Profiles & Portfolio Links
# -----------------------------------------------------------------------------
linkedin_1 = os.getenv("linkedin_1", 'https://www.linkedin.com/in/saurabh-amrutkar-0a07b5179/')
linkedin_2 = os.getenv("linkedin_2", "https://www.linkedin.com/in/saurabh-amrutkar-11b923278/") 
LINKEDIN_URL = os.getenv("LINKEDIN_URL", linkedin_2)

# -----------------------------------------------------------------------------
# Base Directories & Resource Paths
# -----------------------------------------------------------------------------
# BASE_DIR points to the `/app` directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Absolute path to applicant resume file attached during cold emailing
RESUME_PATH = BASE_DIR / "resumes" / "Saurabh_Amrutkar_Resume.pdf"

# Directory where Jinja2 email HTML/Text templates reside (`/app/templates`)
TEMPLATE_DIR = BASE_DIR / "templates"

# Feature Flag: Set True to send emails ONLY to hardcoded test recipients (safeguard)
USE_DUMMY_HR = False

# -----------------------------------------------------------------------------
# API Security Configuration
# -----------------------------------------------------------------------------
ADMIN_KEY = os.getenv("ADMIN_KEY", None)

# Ensure application refuses to start if ADMIN_KEY environment variable is missing
if not ADMIN_KEY:
    raise RuntimeError("Admin key is not set. Please specify ADMIN_KEY in your .env file.")



# -----------------------------------------------------------------------------
# AUTH / JWT / OTP Configuration
# -----------------------------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", None)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))
SIGNUP_TOKEN_EXPIRE_MINUTES = int(os.getenv("SIGNUP_TOKEN_EXPIRE_MINUTES", 15))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)

# -----------------------------------------------------------------------------
# AWS S3 Configuration (Resume Storage)
# -----------------------------------------------------------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", None)

# Ensure application refuses to start if S3 credentials are missing
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not S3_BUCKET_NAME:
    raise RuntimeError("AWS S3 credentials are not fully set. Please specify AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME in your .env file.")



# Ensure application refuses to start if JWT SECRET KEY environment variable is missing
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT secret key is not set. Please specify JWT_SECRET_KEY in your .env file.")

# Ensure application refuses to start if ENCRYPTION_KEY environment variable is missing
if not ENCRYPTION_KEY:
    raise RuntimeError("Encryption key is not set. Please specify ENCRYPTION_KEY in your .env file.")


# -----------------------------------------------------------------------------
# Google OAuth Configuration
# -----------------------------------------------------------------------------

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID",None)
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI",None)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Ensure application refuses to start if Google OAuth credentials are missing
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
    raise RuntimeError("Google OAuth credentials are not fully set. Please specify GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in your .env file.")


