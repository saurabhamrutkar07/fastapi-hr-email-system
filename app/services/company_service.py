from app.database.repositories import add_hr_contact

# from app.database import repositories
# print(hasattr(repositories,"add_hr_contact"))

async def create_company_contact(payload):
    await add_hr_contact(payload)
    return {"status": "success"}
