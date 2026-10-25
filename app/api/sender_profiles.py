from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.database import get_db
from app.models.models import User, UserSenderProfile
from app.schemas.sending import SenderProfileCreate, SenderProfileResponse
from app.services.send_service import get_owned, skills_list


# The user's saved "about me" details for emails: job position,
# experience, skills and LinkedIn. Name, email and phone come from the
# user's profile instead.
router = APIRouter(dependencies=[Depends(get_current_user)])

def to_response(profile: UserSenderProfile)-> SenderProfileResponse:
    return SenderProfileResponse(
        id=profile.id,
        name=profile.name,
        job_position=profile.job_position,
        experience_years=profile.experience_years,
        skills=skills_list(profile),
        linkedin_url=profile.linkedin_url,
        is_default=profile.is_default,
    )


async def unset_default(db:AsyncSession, user_id:int)-> None:
    """Clears the current default, so the next one set is the only one."""
    resut = await db.execute(
        select(UserSenderProfile).where(
            UserSenderProfile.user_id ==user_id,
            UserSenderProfile.is_default == True,
        )
    )
    for profile in resut.scalars().all():
        profile.is_default = False 


@router.get("/",response_model=List[SenderProfileResponse])
async def list_sender_profiles(
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """The user's sender details, default first."""
    result = await db.execute(
        select(UserSenderProfile)
        .where(UserSenderProfile.user_id == current_user.id)
        .order_by(UserSenderProfile.is_default.desc(), UserSenderProfile.name)
    )
    return [to_response(p) for p in result.scalars().all()]


@router.post("/", response_model=SenderProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_sender_profile(
    payload: SenderProfileCreate,
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Saves a new set of details, The user's first set becomes the default
    even if not asked, so the send page always has one picked.
    """
    has_default = await db.scalar(
        select(func.count()).select_from(UserSenderProfile).where(
            UserSenderProfile.user_id == current_user.id,
            UserSenderProfile.is_default == True,
        )
    )
    make_default = payload.is_default or not has_default
    if make_default:
        await unset_default(db, current_user.id)

    profile = UserSenderProfile(
        user_id = current_user.id,
        name =payload.name,
        job_position = payload.job_position,
        experience_years = payload.experience_years,
       skills = ",".join(payload.skills),
       linkedin_url = payload.linkedin_url or None,
       is_default = make_default, 
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return to_response(profile)


@router.put("/{profile_id}", response_model=SenderProfileResponse)
async def update_sender_profile(
    profile_id : int , 
    payload : SenderProfileCreate,
    current_user: User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """Changes a set of details; `is_default` is ignored here (use /set-default)."""
    profile = await get_owned(db, UserSenderProfile, profile_id,current_user.id, "Sender details")
    profile.name = payload.name
    profile.job_position = payload.job_position
    profile.experience_years = payload.experience_years
    profile.skills = ",".join(payload.skills)
    profile.linkedin_url = payload.linkedin_url or None
    await db.commit()
    await db.refresh(profile)
    return to_response(profile)


@router.post("/{profile_id}/set-default", response_model=SenderProfileResponse)
async def set_default_sender_profile(
    profile_id : int,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """Makes this set the one the Send page picks first."""
    profile = await get_owned(db, UserSenderProfile, profile_id, current_user.id, "Sender details")
    await unset_default(db, current_user.id)
    profile.is_default = True 
    await db.commit()
    await db.refresh(profile)
    return to_response(profile)


@router.delete("/{profile_id}")
async def delete_sender_profile(
    profile_id : int, 
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """Deletes a set of details. The default one can't be deleted until another is made the default."""
    profile = await get_owned(db, UserSenderProfile, profile_id,current_user.id, "Sender details")
    if profile.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="These are your default details. Make another set the default before deleting them."
        )
    await db.delete(profile)
    await db.commit()
    return {"message": "Sender details deleted."}

