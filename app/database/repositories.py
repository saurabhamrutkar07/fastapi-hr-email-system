from sqlalchemy import select
from app.database.database import AsyncSessionLocal
from app.models.models import HRContacts 

#, EmailLogs

async def get_all_recruiters():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(HRContacts))
        return result.scalars().all()



async def add_hr_contact(payload):
    async with AsyncSessionLocal() as session:
        hr = HRContacts(
            name=payload.name,
            email=payload.email,
            title=payload.title,
            company=payload.company_name
        )
        print(f"HR Details : {hr}")
        session.add(hr)
        await session.commit()


# async def add_hr_contact_bulk(data: list[dict])-> int:
#     async with AsyncSessionLocal as session:
#         contacts = [
#             HRContacts(
#                 name = item.get("name"),
#                 email = item.get("email"),
#                 title = item.get("title"),
#                 company = item.get("company"),
#                 phone = item.get("phone")
#             )
#             for item in data
#         ]


async def add_hr_contact_bulk(data: list[dict]) -> int:

    async with AsyncSessionLocal() as session:
        contacts = [
            HRContacts(
                name = item.get("name"),
                email = item.get("email"),
                title = item.get("title"),
                company = item.get("company"),
                phone = item.get("phone")
            )

            for item in data
        ]


        session.add_all(contacts)
        await session.commit()
        return len(contacts)



# async def log_email(email: str, staAtus: str, error: str | None = None):
#     async with AsyncSessionLocal() as session:
#         log = EmailLogs(
#             recipient_email=email,
#             status=status,
#             error_message=error
#         )
#         session.add(log)
#         await session.commit()
