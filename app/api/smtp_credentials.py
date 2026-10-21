import asyncio
import smtplib

from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.core.security import get_current_user
from app.core.encryption import encrypt_value, decrypt_value
from app.models.models import User, UserSMTPCredential
from app.schemas.smtp_credentials import SMTPCredentialCreate, SMTPCredentialResponse
from app.core.mailer import check_smtp_login, send_email

router = APIRouter()

WRONG_LOGIN = "Gmail rejected this email address or App Password. Check both and try again."
UNREACHABLE = "Could not reach Gmail. Check your internet connection and try again."

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

    # Google shows App Passwords in groups of four ("abcd efgh ijkl mnop");
    # the spaces are not part of the password.
    password = payload.password.replace(" ","")

    # Log in to the mail server first, so a wrong address or App Password
    # is reported now instead of when the first cold email fails. 
    try:
         await asyncio.to_thread(
              check_smtp_login,
              payload.smtp_server,
              payload.smtp_port,
              payload.email_address,
              password
         )
    except smtplib.SMTPAuthenticationError:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=WRONG_LOGIN)
    except (smtplib.SMTPException, OSError):
         raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=UNREACHABLE)
    
    encrypt_password = encrypt_value(password)

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

@router.post('/test')
async def send_test_email(
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sends a short email from the user's saved account to itself, so they 
    can see that sending works before emailing recruiters. 
    """
    result = await db.execute(
         select(UserSMTPCredential).where(UserSMTPCredential.user_id == current_user.id)
    )
    credential = result.scalar_one_or_none()

    if credential is None or not credential.is_active:
         raise HTTPException(
              status_code= status.HTTP_400_BAD_REQUEST,
              detail= "Connect your Gmail first."
         )
    try:
         await asyncio.to_thread(
              send_email,
              to_email = credential.email_address,
              subject = 'ColdReach test email',
              body = (
                   f"Hi {current_user.name}, \n\n"
                   "This test email was sent from ColdReach through your Gmail account. "
                   "If you can read it, your cold emails will go out from this address.\n"
              ),
              smtp_server = credential.smtp_server,
              smtp_port = credential.smtp_port,
              email_address = credential.email_address,
              email_password = decrypt_value(credential.encrypted_password),
         ) 
    except smtplib.SMTPAuthenticationError:
         raise HTTPException(
              status_code= status.HTTP_400_BAD_REQUEST,
              detail= "Gmail rejected the saved App Password. Create a new one and save it again.",
        )
    except (smtplib.SMTPException, OSError):
         raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=UNREACHABLE)

    return {"message": f"Test email sent to {credential.email_address}. Check your inbox."}








