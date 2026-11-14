"""
Resumes: PDF checks, size limit, versions, and privacy. S3 is faked (see conftest.py).
"""
from tests.helpers import headers_for

PDF = b"%PDF-1.4 a small fake resume"


async def upload(client, who, filename="cv.pdf", content=PDF, content_type="application/pdf"):
    return await client.post("/resumes/upload", headers=headers_for(who),
                             files={"file": (filename, content, content_type)})


async def my_resumes(client, who):
    return (await client.get("/resumes/", headers=headers_for(who))).json()


async def test_upload_refuses_files_that_are_not_pdfs(client, user):
    assert (await upload(client, user, "cv.docx", b"PK..", "application/msword")).status_code == 400
    assert (await upload(client, user, "cv.pdf", b"MZ an exe file")).status_code == 400   # named .pdf, isn't one


async def test_upload_over_5_mb_is_refused(client, user):
    big = b"%PDF" + b"0" * (5 * 1024 * 1024)
    assert (await upload(client, user, content=big)).status_code == 400


async def test_new_upload_becomes_the_active_version(client, user):
    await upload(client, user)
    await upload(client, user)
    resumes = await my_resumes(client, user)
    active = [r["version_number"] for r in resumes if r["is_active"]]
    assert len(resumes) == 2 and active == [2]


async def test_filename_is_never_used_as_the_storage_path(client, user, fakes):
    r = await upload(client, user, filename="../../etc/passwd.pdf")
    assert r.status_code in (200, 201)
    assert not any(".." in key for key in fakes.s3)


async def test_switch_active_version(client, user):
    await upload(client, user)
    await upload(client, user)
    v1 = next(r for r in await my_resumes(client, user) if r["version_number"] == 1)

    assert (await client.post(f"/resumes/{v1['id']}/set-active", headers=headers_for(user))).status_code == 200
    assert [r["version_number"] for r in await my_resumes(client, user) if r["is_active"]] == [1]


async def test_active_resume_cannot_be_deleted_but_an_old_one_can(client, user):
    await upload(client, user)
    await upload(client, user)
    resumes = {r["version_number"]: r["id"] for r in await my_resumes(client, user)}

    assert (await client.delete(f"/resumes/{resumes[2]}", headers=headers_for(user))).status_code == 400
    assert (await client.delete(f"/resumes/{resumes[1]}", headers=headers_for(user))).status_code in (200, 204)


async def test_other_users_cannot_open_or_delete_my_resume(client, user, other_user):
    await upload(client, user)
    rid = (await my_resumes(client, user))[0]["id"]

    r = await client.get(f"/resumes/{rid}/view-url", headers=headers_for(user))
    assert r.status_code == 200 and "fake-s3" in r.text
    assert (await client.get(f"/resumes/{rid}/view-url", headers=headers_for(other_user))).status_code == 404
    assert (await client.delete(f"/resumes/{rid}", headers=headers_for(other_user))).status_code == 404
