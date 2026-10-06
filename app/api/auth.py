import asyncio
import random 
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException,status,Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from fastapi.responses import RedirectResponse

from app.database.database import get_db
from app.models.models import User,OTP, RevokedRefreshToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token,decode_token
from app.core.mailer import send_email
from app.core.config import OTP_EXPIRE_MINUTES, OTP_MAX_ATTEMPTS, GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, FRONTEND_URL
from app.schemas.auth import SignupRequest, SignupResponse, VerifyOTPRequest,SetPasswordRequest,LoginRequest,TokenResponse,RefreshTokenRequest,ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter()

async def generate_and_send_otp(user:User, purpose:str,db:AsyncSession)-> None:
    """
    Generates a 6 digit otp, stores its has against the user, and 
    emails the plain code to them. Used by both signup and 
    forgot-password files
    """
    otp_code = f"{random.randint(0,999999):06d}"
    otp_now = OTP(
        user_id = user.id,
        otp_hash = hash_password(otp_code),
        purpose = purpose,
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp_now)
    await db.commit()

    await asyncio.to_thread(
        send_email,
        to_email=user.email,
        subject = "Your verification code",
        body = f"Your OTP is {otp_code}. It expires in {OTP_EXPIRE_MINUTES} minutes.",
    )

@router.get("/google/login")
async def google_login():
    """
    Redirects the browser to Google's OAuth consent screen. The user
    approves, and Google redirects back to /auth/google/callback with
    an authorization code.
    """
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)

@router.get("/google/callback")
async def google_callback(code:str,db:AsyncSession = Depends(get_db)):
    """
    Handles Google's redirect after the user approves consent. Exchanges
    the authorization code for tokens, fetches the user's Google profile,
    finds or creates the matching local user, and redirects to the
    frontend with our own access + referesh tokens in the query string.
    """

    import httpx # circular import

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data = {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code with Google."
            )

        google_access_token = token_response.json()["access_token"]

        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= "Failed to featch user info from Google."
            )

        google_user = userinfo_response.json()

    google_id = google_user["sub"]
    email = google_user["email"]
    name = google_user.get("name",email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            name = name,
            email = email,
            mobile = None,
            password_hash = None,
            is_email_verified = True,
            is_active = True,
            role = "user",
            google_id = google_id,
            auth_provider = "google",
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.google_id is None:
        user.google_id = google_id
        await db.commit()

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    redirect_url = f"{FRONTEND_URL}/oauth-success?token={access_token}&refresh={refresh_token}"
    return RedirectResponse(url=redirect_url)

@router.post("/signup", response_model = SignupResponse)
async def signup(payload: SignupRequest,db: AsyncSession=Depends(get_db)):
    """
    Creates a new user in a pending state and emails them a 
    verification OTP. Account is unusable untill verify-otp and 
    set-password both complete
    """

    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "An account with this email already exists."
        )

    user = User(
        name = payload.name,
        email= payload.email,
        mobile = payload.mobile,
        password_hash = None,
        is_email_verified = False,
        is_active = False,
        role = "user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await generate_and_send_otp(user,purpose="signup",db=db)

    return SignupResponse(
        user_id=user.id,
        message="Signup initiated. Check your email for the verification OTP."
    )

@router.post("/verify-otp")
async def verify_otp(payload:VerifyOTPRequest, db:AsyncSession = Depends(get_db)):
    """
    Verifies the otp emails during signup. On success, makes the 
    user's email as verified -- does NOT activate the account yet
    (that happens at auth/set-password)
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None: 
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "No account found with this email"
        )

    result = await db.execute(
        select(OTP)
        .where(OTP.user_id == user.id, OTP.purpose == "signup", OTP.is_used == False)
        .order_by(OTP.created_at.desc())
    )

    otp_row = result.scalars().first()

    if otp_row is None:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "No pending otp found. Please request a new one."
        )

    if otp_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "OTP has expired. Please request a new one."
        )

    if otp_row.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Too many incorrect attempts. Please request a new OTP"
        )

    if not verify_password(payload.otp_code,otp_row.otp_hash):
        otp_row.attempts += 1 
        await db.commit()
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Incorrect OTP."
        )

    otp_row.is_used = True
    user.is_email_verified = True 
    await db.commit()

    return {"message": "Email Verified successfully. Proceed to set your password."}

@router.post("/set-password")
async def set_password(payload:SetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Final step of sign up -- sets the user's password and activates the account. Requires email to already be verified.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "No account found with this email."
        )

    if not user.is_email_verified: 
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Please verify your email before setting a password."
        )

    if user.is_active:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Password already set. Use forgot-password to reset it."
        )

    user.password_hash = hash_password(payload.password)
    user.is_active = True 
    await db.commit()

    return {"message" : "Password set successfully. You can now log in."}

@router.post("/login", response_model=TokenResponse)
async def login(paylaod:LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies email + password and issues an access + refresh token pair.
    """
    result = await db.execute(select(User).where(User.email == paylaod.email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or not verify_password(paylaod.password, user.password_hash):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid email or password."
        )

    token_data = {"sub": str(user.id), "role": user.role}
    return TokenResponse(
        access_token = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
    )

@router.post("/refresh",response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchanges a valid refresh token for a new access token. The
    orignal refresh token is returned unchanged (not rotated).
    """
    try :
        decoded = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid or expired refresh token."
        ) 

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid token type. Resfresh token required."
        )

    result = await db.execute(select(RevokedRefreshToken).where(RevokedRefreshToken.jti == decoded.get("jti")))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="This refresh token has been revoked."
        )

    user_id = decoded.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))

    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "User not found or inactive."
        )

    token_data = {"sub": str(user.id), "role": user.role}

    return TokenResponse(
        access_token= create_access_token(token_data),
        refresh_token= payload.refresh_token
    )

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Sends a password-reset OTP if the email belongs to an active
    acconut. Always returns the same genereic message regardless --
    this prevents attackers from using this endpoint to discover
    which emails are registered (email enumeration) 
    """

    result = await db.execute(select(User).where(User.email == payload.email))

    user = result.scalar_one_or_none()

    if user is not None and user.is_active:
        await generate_and_send_otp(user,purpose="password_reset",db=db)

    return {"message": "If an account with this email exists, a password reset OTP has been sent."}

@router.post("/reset-password")
async def reset_password(payload:ResetPasswordRequest,db:AsyncSession = Depends(get_db)):
    """
    Verifies  a pssword-reset OTP and sets a new password. Uses a 
    generic "invalid or expired OTP" error for every failure case
    (unknown email, no OTP, wrong code, expired, too many attempts)
    to avoid leaking whether an email is registered -- consistent
    with forgot-password's generic response.
    """
    generic_error = HTTPException(
        status_code= status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP."
    )
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise generic_error

    result = await db.execute(
        select(OTP)
        .where(OTP.user_id == user.id, OTP.purpose == "password_reset",OTP.is_used == False)
        .order_by(OTP.created_at.desc())
    )
    otp_row = result.scalars().first()

    if otp_row is None:
        raise generic_error

    if otp_row.expires_at < datetime.now(timezone.utc):
        raise generic_error

    if otp_row.attempts >= OTP_MAX_ATTEMPTS:
        raise generic_error

    if not verify_password(payload.otp_code,otp_row.otp_hash):
        otp_row.attempts += 1 
        await db.commit()
        raise generic_error

    otp_row.is_used = True
    user.password_hash = hash_password(payload.new_password)
    await db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}

@router.post("/logout")
async def logout(payload:RefreshTokenRequest ,db:AsyncSession=Depends(get_db)):
    """
    Revikes the given refresh token so it can no longer be used to
    obtain new access tokens. The current access token (if any)
    remains valid until its own short expiry -- this is the accepted
    industry tradeoff for stateless JWTs (see /auth/refresh).
    """
    try:
        decode = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "invalid refresh token."
        )

    if decode.get("type") != "refresh":
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="A refresh token is required to log out."
        )

    jti = decode.get("jti")
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This token predates logut support and connot be revoked"
        )

    revoked = RevokedRefreshToken(jti=jti)
    db.add(revoked)
    await db.commit()

    return {"message": "Logged out successfully."}
    




