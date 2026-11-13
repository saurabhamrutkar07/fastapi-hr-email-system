"""
Admin "Users" page: list users, change roles, block and unblock.
"""
from tests.helpers import create_user, headers_for, login


async def test_only_admins_see_the_user_list(client, user, admin):
    assert (await client.get("/users/", headers=headers_for(user))).status_code == 403
    r = await client.get("/users/", headers=headers_for(admin))
    assert r.status_code == 200
    assert {u["email"] for u in r.json()} == {"user@example.com", "admin@example.com"}


async def test_admin_cannot_change_or_block_themselves(client, admin):
    h = headers_for(admin)
    assert (await client.patch(f"/users/{admin.id}/role", headers=h, json={"role": "user"})).status_code == 400
    assert (await client.patch(f"/users/{admin.id}/block", headers=h, json={"blocked": True})).status_code == 400


async def test_unknown_user_and_unknown_role(client, user, admin):
    h = headers_for(admin)
    assert (await client.patch("/users/999/role", headers=h, json={"role": "admin"})).status_code == 404
    assert (await client.patch(f"/users/{user.id}/role", headers=h, json={"role": "owner"})).status_code == 422


async def test_unfinished_signup_cannot_be_made_admin(client, admin):
    pending = await create_user("pending@example.com", is_active=False, is_email_verified=False, password_hash=None)
    r = await client.patch(f"/users/{pending.id}/role", headers=headers_for(admin), json={"role": "admin"})
    assert r.status_code == 400


async def test_promote_then_new_admin_can_open_admin_pages(client, user, admin):
    r = await client.patch(f"/users/{user.id}/role", headers=headers_for(admin), json={"role": "admin"})
    assert r.status_code == 200
    # an old token still says "user", but the database decides
    assert (await client.get("/users/", headers=headers_for(user))).status_code == 200


async def test_block_and_unblock(client, user, admin):
    h = headers_for(admin)
    await client.patch(f"/users/{user.id}/block", headers=h, json={"blocked": True})

    assert (await client.get("/users/me", headers=headers_for(user))).status_code == 401
    assert (await login(client, user.email)).status_code == 403
    assert (await login(client, user.email, "Wrong@1234")).status_code == 401   # don't confirm the password

    await client.patch(f"/users/{user.id}/block", headers=h, json={"blocked": False})
    assert (await login(client, user.email)).status_code == 200


async def test_blocked_user_cannot_sign_up_again(client, user, admin):
    await client.patch(f"/users/{user.id}/block", headers=headers_for(admin), json={"blocked": True})
    r = await client.post("/auth/signup", json={"name": "Again", "email": user.email, "mobile": "9999999999"})
    assert r.status_code == 400
