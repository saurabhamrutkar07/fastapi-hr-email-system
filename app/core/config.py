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

