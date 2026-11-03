"""
===============================================================================
Admin Users Service (app/services/admin_users_service.py)
===============================================================================

What the admin's users page needs: 
1. Every user with their status and how many emails they've sent.
2. Changing a user's role (user <-> admin).
3. Blocking and unblocking a user.

Safety rules: an admin can't change their own role or block themselves,
and the last admin can't lose admin rights, so the app always keeps one.
===============================================================================

"""

from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import func, select 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.models import EmailTransaction,User


def user_status(user:User) -> str :
    if user.blocked_at is not None:
        return "blocked"
    return "active" if user.is_active else "pending"


def users_query():
    """Users newest first, with who blocked them and their successful sends."""
    sent = (
        select(
            EmailTransaction.user_id,
            func.count().label("emails_sent"),
            func.max(EmailTransaction.created_at).label("last_sent_at"),
        )
        .where(EmailTransaction.status == "SUCCESS")
        .group_by(EmailTransaction.user_id)
        .subquery()
    )
    blocker = aliased(User)
    return(
        select(User,blocker.name, sent.c.emails_sent, sent.c.last_sent_at)
        .outerjoin(blocker, blocker.id == User.blocked_by)
        .outerjoin(sent, sent.c.user_id == User.id)
        .order_by(User.created_at.desc(),User.id.desc())
    )


def to_item(user:User, blocked_by_name:str| None, emails_sent: int | None, last_sent_at) -> dict:
    return {
        "id": user.id, 
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user_status(user),
        "auth_provider": user.auth_provider,
        "created_at": user.created_at,
        "blocked_at": user.blocked_at,
        "blocked_by_name": blocked_by_name,
        "emails_sent": emails_sent or 0, 
        "last_sent_at": last_sent_at,
    }


async def get_changeable_user(db:AsyncSession,admin:User, user_id: int ) -> User:
    """The user an admin is about to change, after the checks every chamge shares."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You can't change your own account here.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user hasn't finished signing up yet.")
    return user


async def change_role(db:AsyncSession, admin:User, user_id:int, role:str) -> dict:
    user = await get_changeable_user(db, admin, user_id)
    if user.role == "admin" and role != "admin":
        # Admins who can still sign in, apart from this one 
        other_admins = await db.scalar(
            select(func.count()).select_from(User).where(
                User.role == 'admin', User.blocked_at.is_(None), User.id != user.id
            )
        )
        if other_admins == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="The app needs at least one admin.")
    user.role = role 
    await db.commit()
    return await get_user_item(db, user_id)


async def set_blocked(db:AsyncSession, admin: User, user_id: int, blocked:bool) -> dict:
    user = await get_changeable_user(db, admin, user_id)
    if blocked and user.blocked_at is None :
        user.blocked_at = datetime.now(timezone.utc)
        user.blocked_by = admin.id 
    elif not blocked:
        user.blocked_at = None
        user.blocked_by = None
    await db.commit()
    return await get_user_item(db, user_id)




async def list_users(db:AsyncSession) -> list[dict]:
    result = await db.execute(users_query())
    return [to_item(*row) for row in result.all()]


async def get_user_item(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(users_query().where(User.id == user_id))
    return to_item(*result.one())


