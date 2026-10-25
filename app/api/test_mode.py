from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.database.database import get_db
from app.models.models import AdminTestMode, User
from app.schemas.sending import TestModeResponse, TestModeUpdate


# Admins only: while test mode is on, the admin's own sends may only go
# to their test emails, so new features can be tried on real Gmail
# without emailing real recruiters. Regular users are never affected.
router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/", response_model=TestModeResponse)
async def get_test_mode(
    admin : User = Depends(require_admin),
    db : AsyncSession = Depends(get_db),
):
    """The admin's test mode. It is on (with no test emails) until they change it."""
    row = await db.get(AdminTestMode, admin.id)
    if row is None:
        return TestModeResponse(enabled=True, test_emails=[])
    return TestModeResponse(enabled=row.enabled, test_emails=[e for e in row.test_emails.split(",") if e])


@router.put("/", response_model=TestModeResponse)
async def update_test_mode(
    payload : TestModeUpdate,
    admin : User = Depends(require_admin),
    db : AsyncSession = Depends(get_db),
):
    """Turns test mode on or off and replaces the list of test emails."""
    emails = list(dict.fromkeys(e.lower() for e in payload.test_emails))
    row = await db.get(AdminTestMode, admin.id)
    if row is None:
        row = AdminTestMode(user_id=admin.id)
        db.add(row)
    row.enabled = payload.enabled
    row.test_emails = ",".join(emails)
    await db.commit()
    return TestModeResponse(enabled=row.enabled, test_emails=emails)