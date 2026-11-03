from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List 

from app.database.database import get_db 
from app.core.security import get_current_user,require_admin
from app.models.models import User
from app.schemas.users import UserResponse, UserProfileUpdateRequest ,UserRoleUpdateRequest, AdminUserItem, UserBlockRequest
from app.services.admin_users_service import change_role,list_users,set_blocked

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user : User = Depends(get_current_user),
):

    """
    Returns the currently logges-in user's own profile
    """
    return current_user

@router.patch("/me",response_model=UserResponse)
async def update_my_profile(
    payload : UserProfileUpdateRequest,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Update the logged-in user's own name and mobile number.
    """
    current_user.name = payload.name 
    current_user.mobile = payload.mobile
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/",  response_model=List[AdminUserItem])
async def list_all_users(
    current_user : User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    """
    Admin-Only: every user, newest first, with their status (active,
    blocked or pending signup) and how many emails they've sent.
    """

    return await list_users(db)

@router.patch("/{user_id}/role", response_model=AdminUserItem)
async def update_user_role(
    user_id : int, 
    payload: UserRoleUpdateRequest,
    admin : User = Depends(require_admin),
    db : AsyncSession = Depends(get_db)
):
    """
    Admin-only: changes a user's role (e.g. promote "admin").
    Not for your own account, and the last admin stays an admin.
    """
    return await change_role(db, admin, user_id, payload.role)


@router.patch("/{user_id}/block", response_model=AdminUserItem)
async def update_user_block(
    user_id : int, 
    payload: UserBlockRequest,
    admin : User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin-only: blocks or unblocks a user. A blocked user is signed out
    on their next request and can't sign in again, with any method.
    """
    return await set_blocked(db, admin, user_id, payload.blocked)


