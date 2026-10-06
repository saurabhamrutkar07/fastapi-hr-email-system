from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.core.security import get_current_user
from app.core.encryption import encrypt_value
from app.models.models import User, UserSMTPCredential
from app.schemas.smtp_credentials import SMTPCredentialCreate, SMTPCredentialResponse


router = APIRouter()

@router.post("/", response_model=SMTPCredentialResponse)
async def save_smtp_credentials(
    payload : SMTPCredentialCreate,
    current_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):
    """
    Saves (or updated) the current user's own SMTP sender credentials.
    The password is encrypted before storage -- never stored in palintext.
    """
    result = await db.execute(
        select(UserSMTPCredential).where(UserSMTPCredential.user_id == current_user.id)
    )
    credential = result.scalar_one_or_none()

    encrypt_password = encrypt_value(payload.password)

    if credential is None:
        credential = UserSMTPCredential(
            user_id = current_user.id, 
            smtp_server = payload.smtp_server,
            smtp_port = payload.smtp_port,
            email_address = payload.email_address, 
            encrypted_password = encrypt_password, 
        )

        db.add(credential)

    else:
        credential.smtp_server = payload.smtp_server
        credential.smtp_port = payload.smtp_port
        credential.email_address = payload.email_address
        credential.encrypted_password = encrypt_password
        credential.is_active = True 

    await db.commit()                              # will this line execute every time 
    await db.refresh(credential)                   # will this line execute every time                         

    return SMTPCredentialResponse(
        smtp_server= credential.smtp_server,
        smtp_port= credential.smtp_port,
        email_address=credential.email_address,
        is_active= credential.is_active
    )


@router.get("/",response_model=SMTPCredentialResponse)
async def get_smtp_credentials(
    curret_user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
    ):
        """
        Retrive the current user's own SMTP configuration (never the 
        password itself -- only server/port/sender address/active status)
        """
        result = await db.execute(
            select(UserSMTPCredential).where(UserSMTPCredential.user_id == curret_user.id)
        )
        
        credential = result.scalar_one_or_none()

        if credential is None:
             raise HTTPException(
                  status_code=status.HTTP_404_NOT_FOUND,
                  detail = "No SMTP credentials cofigured yet"
             )

        return SMTPCredentialResponse(
             smtp_server= credential.smtp_server,
             smtp_port= credential.smtp_port,
             email_address= credential.email_address,
             is_active = credential.is_active,
        )











