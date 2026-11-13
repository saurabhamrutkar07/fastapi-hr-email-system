"""
Email templates: Jinja syntax checks, the sandbox, the default template and privacy.
"""
from tests.helpers import headers_for

BODY = ("Hi {{ hr_name }}, I'm {{ applicant_name }} ({{ experience_years }} yrs, "
        "{{ skills | join(', ') }}) for {{ job_position }} at {{ company_name }}.")


async def create(client, who, name="Main", subject="{{ job_position }} at {{ company_name }}", content=BODY):
    return await client.post("/email-template/", headers=headers_for(who),
                             json={"name": name, "subject": subject, "content": content})


async def test_first_template_becomes_the_default(client, user):
    first = await create(client, user)
    second = await create(client, user, name="Second", content="Hi {{ hr_name }}")
    assert first.json()["is_default"] is True
    assert second.json()["is_default"] is False


async def test_syntax_error_is_shown_with_the_line(client, user):
    r = await create(client, user, content="Hello {{ hr_name ")
    assert r.status_code == 400
    assert "line" in r.json()["detail"].lower()


async def test_sandbox_blocks_access_to_python_internals(client, user):
    # Classic template-injection tricks: they must not run.
    tricks = ["{{ ''.__class__.__mro__[1].__subclasses__() }}",
              "{{ cycler.__init__.__globals__.os.popen('whoami').read() }}"]
    for trick in tricks:
        r = await create(client, user, name="Evil", content=trick)
        assert r.status_code == 400, trick


async def test_content_over_10000_characters_is_refused(client, user):
    assert (await create(client, user, content="a" * 10001)).status_code == 422


async def test_preview_fills_in_sample_values(client, user):
    r = await client.post("/email-template/preview", headers=headers_for(user),
                          json={"subject": "{{ job_position }}", "content": BODY})
    assert r.status_code == 200
    assert "{{" not in r.json()["body"]


async def test_default_template_cannot_be_deleted(client, user):
    tid = (await create(client, user)).json()["id"]
    assert (await client.delete(f"/email-template/{tid}", headers=headers_for(user))).status_code == 400


async def test_set_default_leaves_exactly_one_default(client, user):
    await create(client, user)
    second = (await create(client, user, name="Second", content="Hi")).json()["id"]
    await client.post(f"/email-template/{second}/set-default", headers=headers_for(user))

    templates = (await client.get("/email-template/", headers=headers_for(user))).json()
    assert [t["id"] for t in templates if t["is_default"]] == [second]


async def test_other_users_cannot_see_or_touch_my_templates(client, user, other_user):
    tid = (await create(client, user)).json()["id"]
    them = headers_for(other_user)

    assert (await client.get("/email-template/", headers=them)).json() == []
    assert (await client.put(f"/email-template/{tid}", headers=them,
                             json={"name": "x", "subject": "x", "content": "x"})).status_code == 404
    assert (await client.delete(f"/email-template/{tid}", headers=them)).status_code == 404
    assert (await client.post(f"/email-template/{tid}/set-default", headers=them)).status_code == 404
