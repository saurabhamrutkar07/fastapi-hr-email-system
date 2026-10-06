from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List 

from app.database.database import get_db 
from app.core.security import get_current_user,require_admin
from app.models.models import User
from app.schemas.users import UserResponse, UserRoleUpdateRequest, UserStatusUpdateRequest

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user : User = Depends(get_current_user),
):

    """
    Returns the currently logges-in user's own profile
    """
    return current_user

@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    current_user : User = Depends(require_admin),db: AsyncSession = Depends(get_db)
):

    """
    Admin-only: list every registered user.
    """
    result = await db.execute(select(User))
    return result.scalars().all()


@router.patch("/{user_id}/role",response_model=UserResponse)
async def update_user_role(
    user_id : int,
    payload : UserRoleUpdateRequest,
    admin : User = Depends(require_admin),
    db :AsyncSession = Depends(get_db)
):
    """
    Admin-only: changes a user's role (e.g. promote "user" to "admin")
    """

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "User not found"
        )

    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    admin : User = Depends(require_admin),
    db : AsyncSession = Depends(get_db) 
):
    """
    Admin - only : enables or disables a user account. A disabled 
    (is_active = False) user cannot log in 
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "User Not found"
        )

    user.is_active = payload.is_active
    await db.commit()
    await db.refresh(user)

    return user

