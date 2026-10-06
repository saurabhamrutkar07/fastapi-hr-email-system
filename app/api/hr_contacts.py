from typing import List

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
#from app.core.security import verify_key_secret
from app.core.security import get_current_user,require_admin
from app.models.models import User
from app.services.cold_email_service import get_user_smtp_config

from app.services.hr_contact_excel_service import (
    ALLOWED_EXTENSIONS,
    get_file_extension,
    process_hr_contacts_file,
)
from app.schemas.fresh_contacts import (
    AddFreshContactRequest,
    BulkAddFreshContactsRequest,
    FreshContactResponse,
)
from app.services.fresh_contact_service import (
    create_fresh_contact,
    create_fresh_contacts_bulk,
    list_fresh_contacts,
)


# All routes here operate on the v2 schema only:
# `hr_contacts_v2`, `hr_contact_emails`, `hr_contact_phones`.
# Mounted under `/hr-contacts/v2` (see main.py) and protected by
# `key-secret` header auth on every route.
router = APIRouter(
    tags=["HR Contacts"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/upload-file", dependencies = [Depends(require_admin)]
)
async def upload_hr_contacts_file(
    file: UploadFile = File(...),
    # AsyncSession: every DB call made with `db` below must be awaited.
    db: AsyncSession = Depends(get_db),
):
    """
    Upload HR contacts from:

        .xlsx
        .xls
        .xlsm
        .xlsb
        .ods
        .csv

    Supports:

        - Multiple emails in one row
        - Multiple emails in subsequent rows
        - Multiple phones
        - Missing phones
        - Extra email columns
        - Duplicate detection
        - Existing contacts
    """

    # ========================================================
    # Filename validation
    # ========================================================

    print("Filename:", file.filename)
    print("Content type:", file.content_type)

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    # ========================================================
    # Extension validation
    # ========================================================

    extension = get_file_extension(
        file.filename
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported file format.",
                "supported_formats": sorted(
                    ALLOWED_EXTENSIONS
                ),
            },
        )

    try:

        # ====================================================
        # Read file
        # ====================================================

        contents = await file.read()

        if not contents:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # ====================================================
        # Process
        # ====================================================

        result = await process_hr_contacts_file(
            contents=contents,
            filename=file.filename,
            db=db,
        )

        # ====================================================
        # Validation failure
        # ====================================================

        if (
            result["status"]
            == "validation_failed"
        ):

            raise HTTPException(
                status_code=400,
                detail=result,
            )

        return result

    except HTTPException:
        raise

    except ValueError as exc:

        await db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded file.",
        )

    finally:

        await file.close()


@router.post("/add", status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_admin)])
async def add_hr_contact_v2(payload: AddFreshContactRequest):
    """
    Adds a single HR contact into `hr_contacts_v2`.
    """
    return await create_fresh_contact(payload)


@router.post("/bulk-add", status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_admin)])
async def bulk_add_hr_contacts_v2(payload: BulkAddFreshContactsRequest):
    """
    Adds multiple HR contacts into `hr_contacts_v2` in a single JSON request.
    """
    return await create_fresh_contacts_bulk(payload)


@router.get("/list", response_model=List[FreshContactResponse])
async def get_hr_contacts_v2(current_user: User = Depends(get_current_user)):
    """
    Retrieves all HR contacts from `hr_contacts_v2`, including their full
    `hr_contact_emails` and `hr_contact_phones` lists. Requires the 
    current user to have their own SMTP credentialsconfigutred first -- 
    no point shoiwnig hte list to someone who can't send from it yet.
    """
    await get_user_smtp_config(current_user.id)
    return await list_fresh_contacts()