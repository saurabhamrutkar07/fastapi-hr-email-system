"""
Sign up, sign in, tokens, password reset and Google sign-in.
"""
import re
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import func, select, update

from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY, OTP_MAX_ATTEMPTS
from app.core.security import create_access_token
from app.database.database import AsyncSessionLocal
from app.models.models import OTP, User
from tests.helpers import PASSWORD, headers_for, login, old_headers_for

NEW_EMAIL = "new.person@example.com"


async def signup(client, email=NEW_EMAIL):
    return await client.post("/auth/signup", json={"name": "New Person", "email": email, "mobile": "9999999999"})


async def finish_signup(client, fakes, email=NEW_EMAIL):
    """Sign up, enter the emailed OTP, set a password. Returns the set-password response."""
    await signup(client, email)
    r = await client.post("/auth/verify-otp", json={"email": email, "otp_code": fakes.otp[email]})
    token = r.json()["signup_token"]
    return await client.post("/auth/set-password", json={"email": email, "signup_token": token, "password": PASSWORD})


async def count_users(email):
    async with AsyncSessionLocal() as session:
        query = select(func.count()).select_from(User).where(func.lower(User.email) == email.lower())
        return (await session.execute(query)).scalar()


# ---------------------------------------------------------------- signup
async def test_full_signup_then_login(client, fakes):
    r = await finish_signup(client, fakes)
    assert r.status_code == 200

    r = await login(client, NEW_EMAIL)
    assert r.status_code == 200

    me = await client.get("/users/me", headers={"Authorization": "Bearer " + r.json()["access_token"]})
    assert me.json()["role"] == "user"   # new accounts are never admins


async def test_signup_rejects_bad_input(client):
    assert (await signup(client, "not-an-email")).status_code == 422
    r = await client.post("/auth/signup", json={"name": "N", "email": NEW_EMAIL, "mobile": "123"})
    assert r.status_code == 422   # mobile too short


async def test_signup_cannot_make_itself_admin(client, fakes):
    await client.post("/auth/signup", json={"name": "N", "email": NEW_EMAIL, "mobile": "9999999999", "role": "admin"})
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == NEW_EMAIL))).scalar_one()
    assert user.role == "user"


async def test_cannot_login_before_signup_is_finished(client, fakes):
    await signup(client)
    assert (await login(client, NEW_EMAIL)).status_code == 401


async def test_signup_when_otp_email_fails_gives_503(client, fakes):
    fakes.otp_mail_down = True
    r = await signup(client)
    assert r.status_code == 503
    assert "couldn't send" in r.json()["detail"]


# ---------------------------------------------------------------- OTP
async def test_wrong_otp_is_refused(client, fakes):
    await signup(client)
    wrong = "000000" if fakes.otp[NEW_EMAIL] != "000000" else "111111"
    r = await client.post("/auth/verify-otp", json={"email": NEW_EMAIL, "otp_code": wrong})
    assert r.status_code == 400


async def test_too_many_wrong_otps_locks_even_the_right_one(client, fakes):
    await signup(client)
    right = fakes.otp[NEW_EMAIL]
    wrong = "000000" if right != "000000" else "111111"
    for _ in range(OTP_MAX_ATTEMPTS):
        await client.post("/auth/verify-otp", json={"email": NEW_EMAIL, "otp_code": wrong})

    r = await client.post("/auth/verify-otp", json={"email": NEW_EMAIL, "otp_code": right})
    assert r.status_code == 400
    assert "Too many" in r.json()["detail"]


async def test_expired_otp_is_refused(client, fakes):
    await signup(client)
    async with AsyncSessionLocal() as session:   # move the expiry into the past
        await session.execute(update(OTP).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        await session.commit()
    r = await client.post("/auth/verify-otp", json={"email": NEW_EMAIL, "otp_code": fakes.otp[NEW_EMAIL]})
    assert r.status_code == 400
    assert "expired" in r.json()["detail"].lower()


async def test_otp_works_only_once(client, fakes):
    await signup(client)
    body = {"email": NEW_EMAIL, "otp_code": fakes.otp[NEW_EMAIL]}
    assert (await client.post("/auth/verify-otp", json=body)).status_code == 200
    assert (await client.post("/auth/verify-otp", json=body)).status_code == 400


async def test_signup_token_only_works_for_its_own_email(client, fakes, user):
    await signup(client)
    r = await client.post("/auth/verify-otp", json={"email": NEW_EMAIL, "otp_code": fakes.otp[NEW_EMAIL]})
    token = r.json()["signup_token"]
    # try to use MY token to set a password on someone else's account
    r = await client.post("/auth/set-password", json={"email": user.email, "signup_token": token, "password": PASSWORD})
    assert r.status_code in (400, 401, 403)


# ---------------------------------------------------------------- email case (bug found in E2E testing)
async def test_login_with_email_in_capitals(client, user):
    r = await login(client, "USER@Example.COM")
    assert r.status_code == 200


async def test_same_email_in_capitals_cannot_make_a_second_account(client, fakes):
    await finish_signup(client, fakes)
    r = await signup(client, "  NEW.Person@EXAMPLE.com ")
    assert r.status_code == 400
    assert await count_users(NEW_EMAIL) == 1


# ---------------------------------------------------------------- login and tokens
async def test_wrong_password_and_unknown_email_look_the_same(client, user):
    r1 = await login(client, user.email, "Wrong@1234")
    r2 = await login(client, "nobody@example.com", "Wrong@1234")
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()   # don't reveal which emails have accounts


async def test_login_puts_refresh_token_only_in_an_httponly_cookie(client, user):
    r = await login(client, user.email)
    assert "refresh_token" not in r.json()
    cookie = r.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie and "httponly" in cookie and "path=/auth" in cookie


async def test_refresh_with_cookie_then_logout(client, user):
    await login(client, user.email)             # the client keeps the cookie, like a browser
    assert (await client.post("/auth/refresh")).status_code == 200

    await client.post("/auth/logout")
    assert (await client.post("/auth/refresh")).status_code == 401


async def test_bad_tokens_are_refused(client, user, admin):
    def bearer(token):
        return {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    forged = jwt.encode({"sub": str(admin.id), "role": "admin", "type": "access", "exp": now + timedelta(minutes=5)},
                        "wrong-secret", algorithm="HS256")
    expired = jwt.encode({"sub": str(user.id), "role": "user", "type": "access", "exp": now - timedelta(minutes=1)},
                         JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    assert (await client.get("/users/me")).status_code in (401, 403)                      # no token
    assert (await client.get("/users/me", headers=bearer("garbage"))).status_code == 401
    assert (await client.get("/users/", headers=bearer(forged))).status_code == 401       # wrong secret
    assert (await client.get("/users/me", headers=bearer(expired))).status_code == 401


async def test_token_saying_admin_is_not_enough(client, user):
    # the token claims "admin", but the database says this user is a normal user
    token = create_access_token({"sub": str(user.id), "role": "admin"})
    r = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


async def test_access_token_cannot_be_used_as_refresh_token(client, user):
    access = headers_for(user)["Authorization"].removeprefix("Bearer ")
    client.cookies.set("refresh_token", access, path="/auth")
    assert (await client.post("/auth/refresh")).status_code == 401


# ---------------------------------------------------------------- password reset
async def test_password_reset_signs_out_every_old_session(client, fakes, user):
    old = old_headers_for(user)   # a token from before the reset (e.g. a stolen one)
    assert (await client.get("/users/me", headers=old)).status_code == 200

    await client.post("/auth/forgot-password", json={"email": user.email})
    r = await client.post("/auth/reset-password",
                          json={"email": user.email, "otp_code": fakes.otp[user.email], "new_password": "New@12345"})
    assert r.status_code == 200

    r = await client.get("/users/me", headers=old)
    assert r.status_code == 401
    assert "password was changed" in r.json()["detail"]
    assert (await login(client, user.email, PASSWORD)).status_code == 401      # old password
    assert (await login(client, user.email, "New@12345")).status_code == 200   # new password


async def test_forgot_password_never_reveals_if_the_email_exists(client, fakes, user):
    r1 = await client.post("/auth/forgot-password", json={"email": user.email})
    r2 = await client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


async def test_forgot_password_with_email_in_capitals(client, fakes, user):
    await client.post("/auth/forgot-password", json={"email": "USER@EXAMPLE.COM"})
    assert user.email in fakes.otp


# ---------------------------------------------------------------- Google sign-in
async def start_google(client):
    """Click "Sign in with Google": returns the redirect and the state sent to Google."""
    r = await client.get("/auth/google/login", follow_redirects=False)
    state = re.search(r"[?&]state=([^&]+)", r.headers["location"]).group(1)
    return r, state


def refused(r):
    """Sent back to the app with an error instead of being signed in."""
    return r.status_code in (302, 307) and r.headers["location"].endswith("/oauth-success#error=failed")


async def test_google_login_sends_a_random_state_and_keeps_it_in_a_cookie(client):
    r, state = await start_google(client)
    assert "accounts.google.com" in r.headers["location"]
    cookie = r.headers["set-cookie"].lower()
    assert f"oauth_state={state}".lower() in cookie and "httponly" in cookie

    _, second_state = await start_google(client)
    assert second_state != state


async def test_google_full_sign_in(client, fakes):
    fakes.google_user["email"] = "Google.User@Example.com"   # Google may send capitals
    _, state = await start_google(client)

    r = await client.get(f"/auth/google/callback?code=good-code&state={state}", follow_redirects=False)
    code = r.headers["location"].split("#code=")[1]   # a one-time code, not tokens
    r = await client.post("/auth/google/exchange", json={"code": code})
    assert r.status_code == 200

    me = await client.get("/users/me", headers={"Authorization": "Bearer " + r.json()["access_token"]})
    assert me.json()["email"] == "google.user@example.com"
    assert me.json()["auth_provider"] == "google"


async def test_google_callback_refuses_missing_or_wrong_state(client):
    await start_google(client)
    assert refused(await client.get("/auth/google/callback?code=good-code", follow_redirects=False))
    assert refused(await client.get("/auth/google/callback?code=good-code&state=attacker", follow_redirects=False))
    assert await count_users("google.user@example.com") == 0


async def test_attackers_link_does_not_work_in_another_browser(client):
    _, state = await start_google(client)   # the attacker starts a sign-in...
    client.cookies.clear()                  # ...and sends the link to a victim without the cookie
    r = await client.get(f"/auth/google/callback?code=good-code&state={state}", follow_redirects=False)
    assert refused(r)


async def test_cancel_on_google_screen_shows_an_error_page(client):
    _, state = await start_google(client)
    r = await client.get(f"/auth/google/callback?error=access_denied&state={state}", follow_redirects=False)
    assert refused(r)   # not a raw 422 error


async def test_google_state_works_only_once(client):
    _, state = await start_google(client)
    url = f"/auth/google/callback?code=good-code&state={state}"
    first = await client.get(url, follow_redirects=False)
    assert "#code=" in first.headers["location"]
    assert refused(await client.get(url, follow_redirects=False))


async def test_google_email_not_verified_is_refused(client, fakes):
    fakes.google_user["email_verified"] = False
    _, state = await start_google(client)
    r = await client.get(f"/auth/google/callback?code=good-code&state={state}", follow_redirects=False)
    assert r.status_code == 400


async def test_google_only_user_cannot_use_password_login(client, fakes):
    _, state = await start_google(client)
    await client.get(f"/auth/google/callback?code=good-code&state={state}", follow_redirects=False)
    assert (await login(client, "google.user@example.com")).status_code == 401


# ---------------------------------------------------------------- blocked users
async def test_blocked_user_is_signed_out_and_cannot_log_in(client, user, admin):
    r = await client.patch(f"/users/{user.id}/block", headers=headers_for(admin), json={"blocked": True})
    assert r.status_code == 200

    assert (await client.get("/users/me", headers=headers_for(user))).status_code == 401
    r = await login(client, user.email)
    assert r.status_code == 403
    assert "blocked" in r.json()["detail"]
