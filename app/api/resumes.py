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

MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5  MB ; Gmail refuses attachments over 25 MB 
VIEW_LINK_SECONDS = 15 * 60


async def get_own_resume(db:AsyncSession, user_id : int , resume_id : int) -> UserResume:
    """
    The user's own resume with this id, or 404 (also for someone else's).
    """
    result = await db.execute(
        select(UserResume).where(
            UserResume.id == resume_id,
            UserResume.user_id == user_id
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,detail="Resume not found.")

    return resume

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

    # The browser's content type can be wrong, real pdfs start eith "%PDF"
    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This file isn't a valid PDF."
        )

    if len(file_bytes) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Resume must be 5 MB or smaller."
        )
    
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


@router.get("/{resume_id}/view-url")
async def get_resume_view_url(
    resume_id: int, 
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """
    A private link that opens this resume's PDF for 15 minutes. The 
    bucket stays private; the link only works for this one file.
    """

    resume = await get_own_resume(db,current_user.id,resume_id)
    url = s3_storage.generate_presigned_url(resume.file_path, expires_in=VIEW_LINK_SECONDS)
    return {"url": url, "expires_in": VIEW_LINK_SECONDS}


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id : int, 
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    """
    Deletes one resume version from s3 and the database. The active 
    version can't be deleted: the user makes another one active first, 
    so emails always have a resume to attach.
    """

    resume = await get_own_resume(db, current_user.id ,resume_id)

    if resume.is_active:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "This is your active resume. Make another version active before deleting it."
        )

    s3_storage.delete_file(resume.file_path)
    await db.delete(resume)
    await db.commit()
    return {"message": "Resume deleted."}
