"""
Sending emails, their status, and the history pages. Gmail is faked (see conftest.py):
an address containing "refuse" is rejected by the fake Gmail like a non-existent mailbox.
"""
import pytest
from sqlalchemy import update

from app.database.database import AsyncSessionLocal
from app.models.models import UserResume
from tests.helpers import headers_for


async def set_up_sender(client, person):
    """Give someone everything needed to send: Gmail, resume, template, profile, 3 contacts."""
    h = headers_for(person)
    await client.post("/smtp-credentials/", headers=h, json={"email_address": person.email, "password": "abcd efgh ijkl mnop"})
    await client.post("/resumes/upload", headers=h, files={"file": ("cv.pdf", b"%PDF-1.4 resume", "application/pdf")})
    template = await client.post("/email-template/", headers=h, json={
        "name": "Main", "subject": "{{ job_position }} at {{ company_name }}",
        "content": "Hi {{ hr_name }}, I'm {{ applicant_name }}, {{ skills | join(', ') }}."})
    profile = await client.post("/sender-profiles/", headers=h, json={
        "name": "Backend", "job_position": "Backend Developer", "experience_years": 3, "skills": ["Python", "FastAPI"]})

    contacts = {}
    for key, name, email in [("ok1", "Priya Sharma", "priya@zoho.com"),
                             ("ok2", "Rahul Verma", "rahul@tcs.com"),
                             ("bad", "No Mailbox", "refuse@nowhere.com")]:
        r = await client.post("/hr-contacts/v2/add", headers=h, json={"name": name, "email": email, "company_name": "Acme"})
        contacts[key] = r.json()["contact_id"]

    return {"h": h, "template_id": template.json()["id"], "profile_id": profile.json()["id"], "contacts": contacts}


@pytest.fixture
async def ready(client, user):
    """A normal user who can send."""
    return await set_up_sender(client, user)


@pytest.fixture
async def admin_ready(client, admin):
    """An admin who can send. Admins start with test mode ON."""
    return await set_up_sender(client, admin)


def send_body(ready, *keys, ids=None):
    contact_ids = ids if ids is not None else [ready["contacts"][k] for k in keys]
    return {"contact_ids": contact_ids, "template_id": ready["template_id"], "sender_profile_id": ready["profile_id"]}


async def statuses(client, h, request_ids):
    r = await client.get("/email/status", headers=h, params={"request_ids": ",".join(request_ids)})
    return r.json()


# ---------------------------------------------------------------- preview
async def test_preview_shows_the_real_email(client, ready):
    r = await client.post("/email/preview", headers=ready["h"], json={
        "contact_id": ready["contacts"]["ok1"], "template_id": ready["template_id"],
        "sender_profile_id": ready["profile_id"]})
    assert r.status_code == 200
    preview = r.json()
    assert "Hi Priya Sharma" in preview["body"] and "{{" not in preview["body"]
    assert preview["attachment_name"] == "Asha_User_Resume.pdf"


async def test_preview_with_someone_elses_template_gives_404(client, ready, other_user):
    r = await client.post("/email/preview", headers=headers_for(other_user), json={
        "contact_id": ready["contacts"]["ok1"], "template_id": ready["template_id"],
        "sender_profile_id": ready["profile_id"]})
    assert r.status_code == 404


# ---------------------------------------------------------------- send
async def test_send_delivers_and_reports_a_clear_failure(client, ready, fakes):
    # ok1 picked twice: still one email
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1", "ok2", "bad", "ok1"))
    assert r.status_code == 202
    assert r.json()["total"] == 3

    request_ids = [item["request_id"] for item in r.json()["items"]]
    result = sorted((s["status"], s["error_code"]) for s in await statuses(client, ready["h"], request_ids))
    assert result == [("FAILED", "RECIPIENT_NOT_FOUND"), ("SUCCESS", None), ("SUCCESS", None)]

    assert len(fakes.sent) == 3
    for email in fakes.sent:
        assert email["files"] == ["Asha_User_Resume.pdf"]   # resume attached
        assert email["message_id"]                          # each email has its own Message-ID


async def test_send_limits(client, ready):
    assert (await client.post("/email/send", headers=ready["h"], json=send_body(ready, ids=[]))).status_code == 422
    too_many = list(range(1, 52))   # 51 contacts, the limit is 50
    assert (await client.post("/email/send", headers=ready["h"], json=send_body(ready, ids=too_many))).status_code == 422


async def test_send_to_a_deleted_contact_sends_nothing(client, ready, fakes):
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, ids=[999]))
    assert r.status_code == 404
    assert fakes.sent == []


async def test_wrong_app_password_stops_the_whole_batch(client, ready, fakes):
    fakes.gmail = "wrong_password"
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1", "ok2", "bad"))
    request_ids = [item["request_id"] for item in r.json()["items"]]

    assert len(fakes.sent) == 1   # tried once, then stopped instead of failing 3 times
    codes = [s["error_code"] for s in await statuses(client, ready["h"], request_ids)]
    assert codes == ["CREDENTIALS_EXPIRED"] * 3


async def test_send_without_gmail_set_up_gives_a_clear_message(client, ready, other_user):
    r = await client.post("/email/send", headers=headers_for(other_user), json=send_body(ready, "ok1"))
    assert r.status_code == 400


async def test_send_without_an_active_resume_gives_a_clear_message(client, ready):
    async with AsyncSessionLocal() as session:
        await session.execute(update(UserResume).values(is_active=False))
        await session.commit()
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1"))
    assert r.status_code == 400
    assert "resume" in r.json()["detail"].lower()


# ---------------------------------------------------------------- after sending
async def test_last_sent_lists_delivered_addresses(client, ready):
    await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1", "bad"))
    r = await client.get("/email/last-sent", headers=ready["h"])
    assert set(r.json()) == {"priya@zoho.com"}


async def test_history_filter_and_detail(client, ready):
    await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1", "bad"))

    failed = (await client.get("/email/history", headers=ready["h"], params={"status": "FAILED"})).json()["items"]
    assert len(failed) == 1 and failed[0]["error_code"] == "RECIPIENT_NOT_FOUND"

    detail = (await client.get(f"/email/history/{failed[0]['request_id']}", headers=ready["h"])).json()
    assert "refused this address" in detail["response_details"]   # a message a person can understand
    assert detail["body"]


async def test_history_is_private(client, ready, other_user):
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1"))
    rid = r.json()["items"][0]["request_id"]
    them = headers_for(other_user)

    assert (await client.get("/email/history", headers=them)).json()["total"] == 0
    assert (await client.get(f"/email/history/{rid}", headers=them)).status_code == 404
    assert all(s["status"] == "PENDING" for s in await statuses(client, them, [rid]))   # can't see my status


async def test_history_search_with_sql_injection_text_is_harmless(client, ready):
    r = await client.get("/email/history", headers=ready["h"], params={"q": "' OR 1=1 --"})
    assert r.status_code == 200 and r.json()["total"] == 0


async def test_history_rejects_bad_filters(client, ready):
    h = ready["h"]
    assert (await client.get("/email/history", headers=h, params={"limit": 101})).status_code == 422
    assert (await client.get("/email/history", headers=h, params={"status": "PENDING"})).status_code == 422
    assert (await client.get("/email/history", headers=h, params={"limit": "abc"})).status_code == 422


# ---------------------------------------------------------------- admin test mode
async def test_test_mode_saves_emails_in_lowercase(client, admin):
    h = headers_for(admin)
    assert (await client.get("/test-mode/", headers=h)).json() == {"enabled": True, "test_emails": []}

    r = await client.put("/test-mode/", headers=h, json={"enabled": True, "test_emails": ["ME+Test@Example.com"]})
    assert r.json()["test_emails"] == ["me+test@example.com"]


async def test_test_mode_is_admin_only(client, user):
    assert (await client.get("/test-mode/", headers=headers_for(user))).status_code == 403


async def test_admin_in_test_mode_can_only_send_to_test_emails(client, admin_ready, fakes):
    h = admin_ready["h"]

    # Test mode is on from the start, with no test emails: nothing can be sent
    r = await client.post("/email/send", headers=h, json=send_body(admin_ready, "ok1"))
    assert r.status_code == 400
    assert "Test mode is on" in r.json()["detail"]

    # Add one test email: sending to it works
    await client.put("/test-mode/", headers=h, json={"enabled": True, "test_emails": ["priya@zoho.com"]})
    r = await client.post("/email/send", headers=h, json=send_body(admin_ready, "ok1"))
    assert r.status_code == 202
    assert r.json()["test_mode"] is True

    # One contact outside the list: the whole batch is refused, nothing more is sent
    r = await client.post("/email/send", headers=h, json=send_body(admin_ready, "ok1", "ok2"))
    assert r.status_code == 400
    assert "rahul@tcs.com" in r.json()["detail"]
    assert [email["to"] for email in fakes.sent] == ["priya@zoho.com"]


async def test_admin_with_test_mode_off_can_send_to_anyone(client, admin_ready, fakes):
    h = admin_ready["h"]
    await client.put("/test-mode/", headers=h, json={"enabled": False, "test_emails": []})

    r = await client.post("/email/send", headers=h, json=send_body(admin_ready, "ok1", "ok2"))
    assert r.status_code == 202
    assert r.json()["test_mode"] is False
    assert len(fakes.sent) == 2


async def test_test_mode_never_limits_normal_users(client, ready, fakes):
    r = await client.post("/email/send", headers=ready["h"], json=send_body(ready, "ok1", "ok2"))
    assert r.status_code == 202
    assert r.json()["test_mode"] is False
