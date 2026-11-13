"""
Small helper functions the test files share.
(Fixtures live in conftest.py; plain functions live here.)
"""
import time

from jose import jwt

from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.core.security import create_access_token, hash_password
from app.database.database import AsyncSessionLocal
from app.models.models import User

PASSWORD = "Test@12345"   # every test user gets this password
PASSWORD_HASH = hash_password(PASSWORD)   # bcrypt is slow on purpose: hash it only once


async def create_user(email, role="user", name="Test User", **extra):
    """Put a ready-to-use user straight into the database."""
    fields = dict(name=name, email=email, mobile="9876543210", password_hash=PASSWORD_HASH,
                  is_email_verified=True, is_active=True, role=role, auth_provider="local")
    fields.update(extra)   # a test can change any field, e.g. is_active=False
    async with AsyncSessionLocal() as session:
        user = User(**fields)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def headers_for(user):
    """Login headers for a user, without going through /auth/login."""
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def old_headers_for(user, seconds_ago=60):
    """Login headers with a token issued some time ago (e.g. before a password reset)."""
    issued = int(time.time()) - seconds_ago
    token = jwt.encode({"sub": str(user.id), "role": user.role, "type": "access",
                        "iat": issued, "exp": issued + 3600},
                       JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


async def login(client, email, password=PASSWORD):
    """Sign in through the real /auth/login and return the response."""
    return await client.post("/auth/login", json={"email": email, "password": password})
