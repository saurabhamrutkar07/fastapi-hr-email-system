# from jinja2 import Environment, FileSystemLoader

# from database.repositories import get_all_recruiters, log_email
# from core.mailer import send_email
# from core.config import RESUME_PATH, TEMPLATE_DIR

# # Jinja environment created once
# env = Environment(
#     loader=FileSystemLoader(TEMPLATE_DIR),
#     autoescape=False
# )

# def render_cold_email(context: dict) -> str:
#     template = env.get_template("cold_email.j2")
#     return template.render(**context)


# async def send_cold_emails(payload):
#     recruiters = await get_all_recruiters()

#     subject = f"{payload.job_position} | Inquiry About Openings"
#     sent = 0
#     failed = 0

#     for hr in recruiters:
#         try:
#             body = render_cold_email({
#                 "hr_name": hr.name,
#                 "job_position": payload.job_position,
#                 "experience_years": payload.experience_years,
#                 "skills": payload.skills,
#                 "email": payload.email,
#                 "contact_number": payload.contact_number,
#                 "applicant_name": payload.applicant_name
#             })

#             send_email(
#                 to_email=hr.email,
#                 subject=subject,
#                 body=body,
#                 attachments=[RESUME_PATH]
#             )

#             await log_email(hr.email, "SUCCESS")
#             sent += 1

#         except Exception as e:
#             await log_email(hr.email, "FAILED", str(e))
#             failed += 1

#     return {
#         "total": len(recruiters),
#         "sent": sent,
#         "failed": failed
#     }




from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import os 
from app.core.mailer import send_email
from app.core.config import RESUME_PATH, TEMPLATE_DIR,USE_DUMMY_HR,BASE_DIR,LINKEDIN_URL
from app.database.repositories import get_all_recruiters 
from app.services.email_logger import log_email


# Jinja environment (created once)
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=False
)

def render_cold_email(context: dict) -> str:
    
    template = env.get_template("cold_email.j2")
    return template.render(**context)


async def send_cold_emails(payload):
    if USE_DUMMY_HR:
        class DummyHR:
            def __init__(self,name,email):
                self.name = name
                self.email= email 
        
        recruiters = [
            DummyHR("Saurabh Amrutkar","saurabhamrutkar83@gmail.com"),
            # DummyHR("Anuja Amrutkar","anujaamrutkar4@gmail.com"), 
            # DummyHR("Test HR","test.hr@test.com")
        ]
    else:
        recruiters = await get_all_recruiters()

    subject = f"{payload.job_position} | Inquiry About Openings"
    sent = 0
    failed = 0
    print(f"This is base dir : {BASE_DIR}")

    for hr in recruiters:
        try:
            body = render_cold_email({
                "hr_name": hr.name,
                "job_position": payload.job_position,
                "experience_years": payload.experience_years,
                "skills": payload.skills,
                "email": payload.email,
                "contact_number": payload.contact_number,
                "applicant_name": payload.applicant_name,
                "linedIn_url" : LINKEDIN_URL
            })

            send_email(
                to_email=hr.email,
                subject=subject,
                body=body,
                attachments=[RESUME_PATH]
            )

            log_email(hr.email, "SUCCESS")
            sent += 1

        except Exception as e:
            log_email(hr.email, "FAILED", str(e))
            failed += 1

    return {
        "total": len(recruiters),
        "sent": sent,
        "failed": failed
    }
