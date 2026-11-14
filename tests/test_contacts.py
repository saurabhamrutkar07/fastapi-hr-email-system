"""
HR contacts: add, merge, edit, delete and CSV upload.
Contacts are shared by everyone; only admins can edit, delete or upload files.
"""
from tests.helpers import headers_for

ONE = {"name": "Priya Sharma", "email": "priya@zoho.com", "additional_emails": ["priya.s@zoho.com"],
       "company_name": "Zoho", "title": "HR", "contact_number": "9876500001"}


async def add(client, who, body):
    return await client.post("/hr-contacts/v2/add", headers=headers_for(who), json=body)


async def all_contacts(client, who):
    return (await client.get("/hr-contacts/v2/list", headers=headers_for(who))).json()


async def upload(client, who, filename, content, content_type="text/csv"):
    return await client.post("/hr-contacts/v2/upload-file", headers=headers_for(who),
                             files={"file": (filename, content, content_type)})


# ---------------------------------------------------------------- add / list
async def test_user_adds_a_contact_and_everyone_sees_it(client, user, other_user):
    r = await add(client, user, ONE)
    assert r.status_code == 201

    contacts = await all_contacts(client, other_user)
    assert len(contacts) == 1
    assert len(contacts[0]["emails"]) == 2            # the extra email is kept
    assert contacts[0]["phone"] == "9876500001"


async def test_add_rejects_bad_input(client, user):
    assert (await add(client, user, {"name": "P", "email": "priya@zoho.com"})).status_code == 422   # 1-letter name
    assert (await add(client, user, {"name": "Priya", "email": "not-an-email"})).status_code == 422


async def test_same_email_in_capitals_merges_into_the_same_contact(client, user, other_user):
    first = (await add(client, user, ONE)).json()["contact_id"]
    r = await add(client, other_user, {"name": "Priya Again", "email": "PRIYA@Zoho.com"})
    assert r.json()["contact_id"] == first
    assert len(await all_contacts(client, user)) == 1


# ---------------------------------------------------------------- edit / delete (admin only)
async def test_normal_user_cannot_edit_or_delete(client, user):
    cid = (await add(client, user, ONE)).json()["contact_id"]
    r = await client.put(f"/hr-contacts/v2/{cid}", headers=headers_for(user), json=ONE)
    assert r.status_code == 403
    assert (await client.delete(f"/hr-contacts/v2/{cid}", headers=headers_for(user))).status_code == 403


async def test_admin_edits_a_contact(client, user, admin):
    cid = (await add(client, user, ONE)).json()["contact_id"]
    r = await client.put(f"/hr-contacts/v2/{cid}", headers=headers_for(admin),
                         json={"name": "Priya S", "email": "priya@zoho.com", "company_name": "Zoho Corp"})
    assert r.status_code == 200
    assert (await all_contacts(client, user))[0]["company"] == "Zoho Corp"


async def test_edit_to_another_contacts_email_is_refused(client, user, admin):
    cid = (await add(client, user, ONE)).json()["contact_id"]
    await add(client, user, {"name": "Rahul Verma", "email": "rahul@tcs.com"})
    r = await client.put(f"/hr-contacts/v2/{cid}", headers=headers_for(admin), json={"name": "Priya", "email": "rahul@tcs.com"})
    assert r.status_code == 409


async def test_edit_or_delete_a_missing_contact_gives_404(client, admin):
    r = await client.put("/hr-contacts/v2/999", headers=headers_for(admin), json={"name": "Nobody", "email": "x@y.com"})
    assert r.status_code == 404
    assert (await client.delete("/hr-contacts/v2/999", headers=headers_for(admin))).status_code == 404


async def test_admin_deletes_a_contact(client, user, admin):
    cid = (await add(client, user, ONE)).json()["contact_id"]
    assert (await client.delete(f"/hr-contacts/v2/{cid}", headers=headers_for(admin))).status_code == 200
    assert await all_contacts(client, user) == []


# ---------------------------------------------------------------- CSV / Excel upload (admin only)
CSV = ("Name,Email,Contact Number,Company,Position,Openings\n"
       "Priya Sharma,priya@zoho.com; priya.s@zoho.com,9876500011,Zoho,HR,2\n"
       ",priya.hr@zoho.com,,,,\n"                      # no name: belongs to the row above
       "Rahul Verma,rahul@tcs.com,9876500012,TCS,TA,1\n").encode()


async def test_csv_upload_with_several_emails_and_a_continuation_row(client, admin):
    r = await upload(client, admin, "contacts.csv", CSV)
    assert r.status_code == 200

    contacts = {c["name"]: c for c in await all_contacts(client, admin)}
    assert set(contacts) == {"Priya Sharma", "Rahul Verma"}
    assert len(contacts["Priya Sharma"]["emails"]) == 3


async def test_uploading_the_same_file_twice_makes_no_duplicates(client, admin):
    await upload(client, admin, "contacts.csv", CSV)
    await upload(client, admin, "contacts.csv", CSV)
    assert len(await all_contacts(client, admin)) == 2


async def test_upload_refuses_bad_files(client, user, admin):
    assert (await upload(client, user, "c.csv", CSV)).status_code == 403                    # not an admin
    assert (await upload(client, admin, "c.exe", b"MZ", "application/octet-stream")).status_code == 400
    assert (await upload(client, admin, "c.csv", b"")).status_code == 400                   # empty
    assert (await upload(client, admin, "c.csv", b"\x00\x01garbage\xff\xfe")).status_code == 400   # not 500


async def test_bulk_add_is_admin_only(client, user):
    r = await client.post("/hr-contacts/v2/bulk-add", headers=headers_for(user), json={"contacts": []})
    assert r.status_code == 403
