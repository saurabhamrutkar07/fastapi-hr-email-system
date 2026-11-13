"""
Shared setup for every test. pytest reads this file by itself, before any test file.

What it does, in order:
  1. Points the app at a separate TEST database, and refuses to run on any other.
  2. Builds the tables once with Alembic (so the migrations get tested too).
  3. Empties every table before each test, so tests never affect each other.
  4. Replaces Gmail, S3 and Google with fakes, so nothing leaves the machine.
  5. Gives tests a client and ready-made users (helper functions are in helpers.py).
"""
import os 
import re 
import smtplib 
from pathlib import Path 

from dotenv import load_dotenv

# ---------------------------------------------------------------- 1. settings
# This part must run BEFORE anything from `app` is imported, because the app
# reads its settings (database URL, secret keys) the moment it is imported.

ROOT = Path(__file__).resolve().parent.parent # the project folder 
load_dotenv(ROOT / ".env") # on your laptop: read .env. In CI there is no .env file.

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("Set TEST_DATABASE_URL to a separate database whose name ends in _test.")
# Safety net: tests delete data, so they must never run on the real database.
if not TEST_DATABASE_URL.rsplit("/",1)[-1].endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point to a database whose name ends in _test.")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

os.environ["RATE_LIMIT_ENABLED"] = "false" # test sign in many times in a row 
os.environ["SENTRY_DSN"] = ""              # never report test errors to Sentry 
os.environ["DB_ECHO"] = "false"            # don't print every SQL query

# The app refuses to start without these. On your laptop the real values come 
# from .env; in CI these harmless fake values are used instead.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")
os.environ.setdefault("ENCRYPTION_KEY", "Y29sZHJlYWNoLXRlc3RzLW9ubHkta2V5LTAwMDAwMDA=")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# ---------------------------------------------------------------- app imports
import httpx  # noqa: E402  (imports below this line need the settings above)
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.api.auth as auth_api  # noqa: E402
import app.api.smtp_credentials as smtp_api  # noqa: E402
import app.services.send_service as send_service  # noqa: E402
from app.core.s3_storage import s3_storage  # noqa: E402
from app.database.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from tests.helpers import create_user  # noqa: E402


# ---------------------------------------------------------------- 2. tables
@pytest.fixture(scope="session", autouse=True)
def database_tables():
    """Once per test run: build every table by running all Alembic migrations."""
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")


# ---------------------------------------------------------------- 3. clean slate
@pytest.fixture(autouse=True)
async def empty_tables():
    """Before each test: empty every table, so no test sees another test's data."""
    async with engine.begin() as conn:
        tables = (await conn.execute(text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        ))).scalars().all()
        await conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    yield
    # Each test runs in its own event loop; drop connections made in this one.
    await engine.dispose()


# ---------------------------------------------------------------- 4. fakes
class Fakes:
    """What the fakes recorded during a test, plus switches to make them fail."""

    def __init__(self):
        self.sent = []               # emails "sent" from the user's Gmail
        self.otp = {}                # email address -> last OTP code "emailed" to it
        self.s3 = {}                 # S3 key -> file bytes
        self.gmail = "ok"            # "ok" | "wrong_password" | "down"
        self.otp_mail_down = False   # True = our OTP email can't be sent
        self.google_user = {"sub": "google-1", "email": "google.user@example.com",
                            "email_verified": True, "name": "Google User"}


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    """Swap every outside service for a fake, for the length of one test."""
    f = Fakes()

    # Gmail, used by "Send" (the user's own account)
    def fake_send_email(to_email, subject, body, byte_attachments=None, **kwargs):
        f.sent.append({"to": to_email, "subject": subject, "body": body,
                       "files": [a["filename"] for a in byte_attachments or []],
                       "message_id": kwargs.get("message_id")})
        if f.gmail == "wrong_password":
            raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")
        if "refuse" in to_email:   # any address with "refuse" in it doesn't exist
            raise smtplib.SMTPRecipientsRefused({to_email: (550, b"No such user")})

    monkeypatch.setattr(send_service, "send_email", fake_send_email)

    # Our own email that carries the OTP code (signup, forgot password)
    def fake_otp_email(to_email, subject, body, **kwargs):
        if f.otp_mail_down:
            raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")
        f.otp[to_email] = re.search(r"\b(\d{6})\b", body).group(1)

    monkeypatch.setattr(auth_api, "send_email", fake_otp_email)

    # Gmail settings page: "check this App Password" and "send me a test email"
    def fake_gmail_login(*args, **kwargs):
        if f.gmail == "wrong_password":
            raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")
        if f.gmail == "down":
            raise OSError("Network is unreachable")

    monkeypatch.setattr(smtp_api, "check_smtp_login", fake_gmail_login)
    monkeypatch.setattr(smtp_api, "send_email", fake_gmail_login)

    # S3: keep files in a dict instead of Amazon
    def fake_upload(file_bytes, key, content_type="application/pdf"):
        f.s3[key] = file_bytes
        return key

    monkeypatch.setattr(s3_storage, "upload_file", fake_upload)
    monkeypatch.setattr(s3_storage, "download_file", lambda key: f.s3[key])
    monkeypatch.setattr(s3_storage, "delete_file", lambda key: f.s3.pop(key, None))
    monkeypatch.setattr(s3_storage, "generate_presigned_url",
                        lambda key, expires_in=3600: f"https://fake-s3/{key}")

    # Google sign-in: answer only Google's addresses; every other call goes through.
    # (The test client is an httpx client too, so its calls must pass untouched.)
    real_post, real_get = httpx.AsyncClient.post, httpx.AsyncClient.get

    async def fake_post(self, url, *args, **kwargs):
        if "oauth2.googleapis.com/token" in str(url):
            ok = kwargs.get("data", {}).get("code") == "good-code"
            return httpx.Response(200 if ok else 400, json={"access_token": "google-token"})
        return await real_post(self, url, *args, **kwargs)

    async def fake_get(self, url, *args, **kwargs):
        if "googleapis.com/oauth2/v3/userinfo" in str(url):
            return httpx.Response(200, json=f.google_user)
        return await real_get(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    return f


# ---------------------------------------------------------------- 5. client and users
@pytest.fixture
async def client():
    """Calls the app directly, without starting a server. https so Secure cookies work."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="https://test") as c:
        yield c


@pytest.fixture
async def user():
    return await create_user("user@example.com", name="Asha User")


@pytest.fixture
async def other_user():
    return await create_user("other@example.com", name="Ravi Other")


@pytest.fixture
async def admin():
    return await create_user("admin@example.com", role="admin", name="Admin Person")
