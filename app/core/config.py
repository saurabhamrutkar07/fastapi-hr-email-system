import os
from pathlib import Path



SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
LINKEDIN_URL = os.getenv("LINKEDIN_URL",'https://www.linkedin.com/in/saurabh-amrutkar-11b923278/')
BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR/"resumes"/"Saurabh_Amrutkar_8830624190.pdf"
TEMPLATE_DIR = BASE_DIR / "templates"
USE_DUMMY_HR = True 
ADMIN_KEY = os.getenv("ADMIN_KEY")

if not ADMIN_KEY:
    raise RuntimeError("Admin key is not set")
