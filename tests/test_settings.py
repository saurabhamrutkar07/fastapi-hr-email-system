"""
Settings: the user's Gmail App Password and their "about me" sender profiles.
Gmail is faked (see conftest.py).
"""
from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.models import UserSMTPCredential
from tests.helpers import headers_for

GMAIL = {"email_address": "user@example.com", "password": "abcd efgh ijkl mnop"}
PROFILE = {"name": "Backend", "job_position": "Backend Developer", "experience_years": 2.5,
           "skills": ["Python", "FastAPI"]}


# ---------------------------------------------------------------- Gmail App Password
async def test_no_gmail_saved_yet_gives_404(client, user):
    assert (await client.get("/smtp-credentials/", headers=headers_for(user))).status_code == 404


async def test_wrong_app_password_is_not_saved(client, user, fakes):
    fakes.gmail = "wrong_password"
    assert (await client.post("/smtp-credentials/", headers=headers_for(user), json=GMAIL)).status_code == 400


async def test_gmail_unreachable_gives_502(client, user, fakes):
    fakes.gmail = "down"
    assert (await client.post("/smtp-credentials/", headers=headers_for(user), json=GMAIL)).status_code == 502


async def test_app_password_is_stored_encrypted_and_never_returned(client, user):
    assert (await client.post("/smtp-credentials/", headers=headers_for(user), json=GMAIL)).status_code == 200

    r = await client.get("/smtp-credentials/", headers=headers_for(user))
    assert r.status_code == 200
    assert "abcd" not in r.text and "password" not in r.text.lower()

    async with AsyncSessionLocal() as session:
        saved = (await session.execute(select(UserSMTPCredential))).scalar_one()
    assert "abcd" not in saved.encrypted_password


async def test_send_test_email(client, user):
    await client.post("/smtp-credentials/", headers=headers_for(user), json=GMAIL)
    assert (await client.post("/smtp-credentials/test", headers=headers_for(user))).status_code == 200


# ---------------------------------------------------------------- sender profiles and account details
async def test_profile_needs_skills_and_sensible_experience(client, user):
    no_skills = {**PROFILE, "skills": []}
    negative = {**PROFILE, "experience_years": -1}
    assert (await client.post("/sender-profiles/", headers=headers_for(user), json=no_skills)).status_code == 422
    assert (await client.post("/sender-profiles/", headers=headers_for(user), json=negative)).status_code == 422


async def test_first_profile_is_default_and_cannot_be_deleted(client, user):
    r = await client.post("/sender-profiles/", headers=headers_for(user), json=PROFILE)
    assert r.json()["is_default"] is True
    pid = r.json()["id"]
    assert (await client.delete(f"/sender-profiles/{pid}", headers=headers_for(user))).status_code == 400


async def test_other_users_cannot_edit_my_profile(client, user, other_user):
    pid = (await client.post("/sender-profiles/", headers=headers_for(user), json=PROFILE)).json()["id"]
    r = await client.put(f"/sender-profiles/{pid}", headers=headers_for(other_user), json=PROFILE)
    assert r.status_code == 404


async def test_account_details_can_be_updated(client, user):
    r = await client.patch("/users/me", headers=headers_for(user), json={"name": "Asha New", "mobile": "9123456789"})
    assert r.status_code == 200 and r.json()["name"] == "Asha New"


async def test_account_update_cannot_change_role(client, user):
    await client.patch("/users/me", headers=headers_for(user), json={"name": "Asha", "role": "admin"})
    assert (await client.get("/users/me", headers=headers_for(user))).json()["role"] == "user"
