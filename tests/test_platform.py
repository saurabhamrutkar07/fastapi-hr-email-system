"""
App-wide behaviour: health check, request ids, CORS, and refusing anonymous calls.
"""
import pytest

from app.core.config import FRONTEND_URL

PROTECTED = [("GET", "/users/me"), ("GET", "/hr-contacts/v2/list"), ("GET", "/email/history"),
             ("GET", "/email/stats"), ("GET", "/email-template/"), ("GET", "/resumes/"),
             ("GET", "/smtp-credentials/"), ("GET", "/sender-profiles/"), ("GET", "/test-mode/"),
             ("GET", "/users/"), ("POST", "/email/send"), ("POST", "/hr-contacts/v2/add"),
             ("POST", "/resumes/upload"), ("PATCH", "/users/1/block")]


@pytest.mark.parametrize("method,url", PROTECTED)
async def test_protected_routes_refuse_anonymous_calls(client, method, url):
    r = await client.request(method, url)
    assert r.status_code in (401, 403)


async def test_health_says_ok_and_returns_a_request_id(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": "ok"}
    assert r.headers["x-request-id"]


async def test_health_gives_503_when_the_database_is_down(client, monkeypatch):
    async def broken_ping():
        raise OSError("connection refused to 10.0.0.5 password=secret")

    monkeypatch.setattr("app.api.health.ping_database", broken_ping)
    r = await client.get("/health")
    assert r.status_code == 503
    assert "secret" not in r.text   # no internal details leak out


async def test_cors_allows_only_our_frontend(client):
    preflight = {"Access-Control-Request-Method": "POST"}
    evil = await client.options("/auth/login", headers={**preflight, "Origin": "https://evil.example"})
    ours = await client.options("/auth/login", headers={**preflight, "Origin": FRONTEND_URL})

    assert evil.headers.get("access-control-allow-origin") is None
    assert ours.headers["access-control-allow-origin"] == FRONTEND_URL
    assert ours.headers["access-control-allow-credentials"] == "true"


async def test_malformed_json_gives_422_not_500(client):
    r = await client.post("/auth/login", content=b"{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422

