from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select, func 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


from app.database.database import get_db
from app.core.security import get_current_user
from app.core.s3_storage import s3_storage
from app.models.models import User, UserResume
from app.schemas.resume import ResumeResponse

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse,status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Upload a new resume version for the current user to s3, deactivates 
    any previously-active version, and marks this one active.
    """

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "Only PDF files are accepted for resumes."
        )

    result = await db.execute(
        select(func.max(UserResume.version_number)).where(UserResume.user_id == current_user.id)
    )

    max_version = result.scalar() or 0
    new_version = max_version + 1 

    file_bytes = await file.read()
    key = f"resumes/{current_user.id}/v{new_version}.pdf"
    s3_storage.upload_file(file_bytes,key,content_type="application/pdf")

    result = await db.execute(
        select(UserResume).where(
            UserResume.user_id == current_user.id,
            UserResume.is_active == True,
        )
    )

    for existing_active in result.scalars().all():
        existing_active.is_active = False

    resume = UserResume(
        user_id = current_user.id,
        file_path = key,
        version_number = new_version,
        is_active = True,
    )

    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeResponse(
        id = resume.id,
        version_number= resume.version_number,
        is_active= resume.is_active,
        uploaded_at= resume.uploaded_at.isoformat(),
    )

@router.get("/",response_model=List[ResumeResponse])
async def list_resumes(
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    List all the resume version belonging to the current user.
    """

    result = await db.execute(
        select(UserResume)
        .where(UserResume.user_id == current_user.id)
        .order_by(UserResume.version_number.desc())
    )

    resumes = result.scalars().all()

    return [
        ResumeResponse(
            id = r.id,
            version_number= r.version_number,
            is_active= r.is_active,
            uploaded_at=r.uploaded_at.isoformat()
        )
        for r in resumes
    ]


@router.post("/{resume_id}/set-active", response_model=ResumeResponse)
async def set_active_resume(
    resume_id : int,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Marks the given resume version (must belong to the current user)
    as active, deactivating any other version that was perviously active.
    """
    result = await db.execute(
        select(UserResume).where(
            UserResume.id == resume_id,
            UserResume.user_id == current_user.id,
        )
    )

    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Resume not found."
        )

    result = await db.execute(
        select(UserResume).where(
            UserResume.user_id == current_user.id,
            UserResume.is_active == True,
        )
    )

    for existing_active in result.scalars().all():
        existing_active.is_active = False 

    resume.is_active = True 
    await db.commit()
    await db.refresh(resume)

    return ResumeResponse(
        id = resume.id,
        version_number=resume.version_number,
        is_active=resume.is_active,
        uploaded_at=resume.uploaded_at.isoformat(),
    )

