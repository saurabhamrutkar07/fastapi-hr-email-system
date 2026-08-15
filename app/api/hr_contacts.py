from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.database import init_db

from app.services.hr_contact_excel_service import (
    ALLOWED_EXTENSIONS,
    get_file_extension,
    process_hr_contacts_file,
)


router = APIRouter(
    prefix="/api/v2/hr-contacts",
    tags=["HR Contacts"],
)


@router.post(
    "/upload-file",
)
async def upload_hr_contacts_file(
    file: UploadFile = File(...),
    db: Session = Depends(init_db),
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

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded file.",
        )

    finally:

        await file.close()