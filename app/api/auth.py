import asyncio
import hashlib
import smtplib
import secrets 
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException,status,Depends, Request,Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from fastapi.responses import RedirectResponse

from app.database.database import get_db
from app.models.models import User,OTP, OAuthLoginCode,RevokedRefreshToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token,create_signup_token,decode_token, ensure_not_blocked, ensure_token_still_valid
from app.core.mailer import send_email
from app.core import rate_limit
from app.core.rate_limit import limiter
from app.core.config import OTP_EXPIRE_MINUTES, OTP_MAX_ATTEMPTS, GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, FRONTEND_URL, REFRESH_TOKEN_EXPIRE_DAYS, COOKIE_SECURE
from common.Logger import Logger
from app.schemas.auth import SignupRequest, SignupResponse, VerifyOTPRequest,SetPasswordRequest,LoginRequest,TokenResponse,GoogleCodeRequest,ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter()

# The refresh token lives in this httpOnly cookie, which JavaScript can't 
# read, so a script injected into the page can't steal it. It is sent only 
# # to /auth/... (path), only over HTTPS (secure) and not with requests that 
# start on other sites (samesite).
REFRESH_COOKIE = "refresh_token"
GOOGLE_CODE_SECONDS = 60 

# Google sign-in sends a random "state" to Google and keeps the same value in
# this cookie. The callback accepts only a state that matches the cookie, so a 
# sign-in someone else started (a link they send you) can't log you into their account.
OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_SECONDS = 600 

def issue_tokens(user:User, response: Response)-> TokenResponse:
    """Access token in the body; refresh token in the httpOnly cookie."""
    token_data = {"sub": str(user.id), "role":user.role}
    response.set_cookie(
        REFRESH_COOKIE,
        create_refresh_token(token_data),
        max_age= REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True, secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth",
    )
    return TokenResponse(access_token=create_access_token(token_data))

def hash_code(code:str)-> str:
    """One-time codes are stored as a SHA-256 hash, never in plain text."""
    return hashlib.sha256(code.encode()).hexdigest()

logger = Logger.get_logger()

OTP_EMAIL_FAILED = "We couldn't send the verification email right now. Please try again in a few minutes."


async def generate_and_send_otp(user:User, purpose:str,db:AsyncSession)-> bool:
    """
    Generates a 6 digit otp, stores its has against the user, and 
    emails the plain code to them. Used by both signup and 
    forgot-password files
    """
    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    otp_now = OTP(
        user_id = user.id,
        otp_hash = hash_password(otp_code),
        purpose = purpose,
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp_now)
    await db.commit()
    # Return False if the email couldn't be sent; each caller decides what 
    # the user is told (forgot-password must not reveal it, see there)
    try : 
        await asyncio.to_thread(
            send_email,
            to_email=user.email,
            subject = "Your verification code",
            body = f"Your OTP is {otp_code}. It expires in {OTP_EXPIRE_MINUTES} minutes.",
        )
    except (smtplib.SMTPException, OSError) as exc:
        logger.error(f"OTP email ({purpose}) to user {user.id} could not be sent: {exc!r}")
        return False
    return True

@router.get("/google/login")
async def google_login():
    """
    Redirects the browser to Google's OAuth consent screen. The user
    approves, and Google redirects back to /auth/google/callback with
    an authorization code.
    """
    state = secrets.token_urlsafe(32)
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        f"&state={state}"
    )
    response = RedirectResponse(url=google_auth_url)
    response.set_cookie(
        OAUTH_STATE_COOKIE, state,
        max_age=OAUTH_STATE_SECONDS,
        httponly=True, secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth/google",
    )
    return response

def google_redirect(fragment: str) -> RedirectResponse:
    """Back to the frontend after Google sign-in; the state cookie is used up."""
    response = RedirectResponse(url=f"{FRONTEND_URL}/oauth-success#{fragment}")
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/auth/google", secure=COOKIE_SECURE, httponly=True,samesite="lax")
    return response

@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, db:AsyncSession = Depends(get_db)):
    """
    Handles Google's redirect after the user approves consent. Exchanges
    the authorization code for tokens, fetches the user's Google profile,
    finds or creates the matching local user, and redirects to the
    frontend with our own access + referesh tokens in the URL fragment (#).
    """
    # No code: the user pressed Cancel on Google's screen. Wrong or missing state:
    # an old link, or a sign-in that was started on another browser.
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not code or not state or not expected_state or not secrets.compare_digest(state.encode(), expected_state.encode()):
        return google_redirect("error=failed")
    
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

    # Only trust the email if Google has verified it. Otherwise someone could make a
    # Google account with another person's address and take over that person's account.
    if not google_user.get('email_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google email address is not verified. Verify with Google, then try again."
        )
    
    google_id = google_user["sub"]
    email = google_user["email"].strip().lower()
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
        # Same email already registered by normal signup: link Google to that account.
        # If that signup was never finished (no password yet), Google has just proven
        # the email is theirs, so finish it here instead of failing the sign-in.
        if user.password_hash is None and not user.is_active:
            user.is_email_verified = True
            user.is_active = True
        user.google_id = google_id
        await db.commit()
    if user.blocked_at is not None:
        # The sign-in page shows the reason instead of signing them in 
        return google_redirect("error=blocked")

    # Hand the frontend a one-time code, not tokens: URLs end up in browser
    # history and logs. It trades the code at /auth/google/exchange.
    code = secrets.token_urlsafe(32)
    db.add(OAuthLoginCode(
        code_hash=hash_code(code),
        user_id=user.id,
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=GOOGLE_CODE_SECONDS),
    ))
    await db.commit()
    return google_redirect(f"code={code}")

@router.post("/google/exchange", response_model=TokenResponse)
@limiter.limit(rate_limit.GOOGLE_EXCHANGE)
async def google_exchange(request: Request, response: Response, payload: GoogleCodeRequest, db: AsyncSession = Depends(get_db)):
    """
    Trades the one-time code from Google sign-in for tokens. A code works 
    once and only within 60 seconds of sign-in.
    """
    now = datetime.now(timezone.utc)
    # One UPDATE both checks and uses the code, so two requests racing with 
    # the same code can't both succeed
    result = await db.execute(
        update(OAuthLoginCode)
        .where(
            OAuthLoginCode.code_hash == hash_code(payload.code),
            OAuthLoginCode.used_at.is_(None),
            OAuthLoginCode.expires_at >  now, 
        )
        .values(used_at=now)
        .returning(OAuthLoginCode.user_id)
    )
    user_id = result.scalar_one_or_none()
    await db.commit()
    if user_id is None:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="This sign-in link has expired. Please sign in with Google again."
        )

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
    ensure_not_blocked(user)
    return issue_tokens(user,response)

@router.post("/signup", response_model = SignupResponse)
@limiter.limit(rate_limit.SIGNUP)
async def signup(request:Request, payload: SignupRequest,db: AsyncSession=Depends(get_db)):
    """
    Creates a new user in a pending state and emails them a 
    verification OTP. Account is unusable untill verify-otp and 
    set-password both complete
    """

    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        if existing.is_active:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= "An account with this email already exists."
            )
        #Signup was started but never finished (OTP or signup token expired).
        #Send a fresh code insted of locking this email out forever.
        if not await generate_and_send_otp(existing,purpose='signup',db=db):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail=OTP_EMAIL_FAILED)
        return SignupResponse(
            user_id=existing.id,
            message="Signup initiated. Check your email for the verification OTP."
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

    if not await generate_and_send_otp(user,purpose="signup",db=db):
        # The pending account stays; signing up again sends a fresh code 
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=OTP_EMAIL_FAILED) 

    return SignupResponse(
        user_id=user.id,
        message="Signup initiated. Check your email for the verification OTP."
    )

@router.post("/verify-otp")
@limiter.limit(rate_limit.VERIFY_OTP)
async def verify_otp(request: Request,payload:VerifyOTPRequest, db:AsyncSession = Depends(get_db)):
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

    return {
        "message": "Email Verified successfully. Proceed to set your password.",
         "signup_token": create_signup_token(user.id,user.email),   
        }

@router.post("/set-password")
@limiter.limit(rate_limit.SET_PASSWORD)
async def set_password(request: Request,payload:SetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
      Final step of sign up -- sets the user's password and activated the account.
      Requires the signup_token returned by /auth.verify-otp, so only the person 
      who just entered the correct OTP can choose the password.  
    """
    invalid_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your verification has expired. Sign up again to get a new code."
    )
    try:
        token_data = decode_token(payload.signup_token)
    except JWTError:
        raise invalid_token

    if token_data.get('type') != "signup":
        raise invalid_token
    
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # The token must belong to this exact user, not just any valid signup token
    if user is None or str(user.id) != token_data.get("sub"):
        raise invalid_token

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
@limiter.limit(rate_limit.LOGIN)
async def login(request: Request,response: Response,paylaod:LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies email + password. Returns an access token and sets the
    refresh token as an httpOnly cookie.
    """
    result = await db.execute(select(User).where(User.email == paylaod.email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or not verify_password(paylaod.password, user.password_hash):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid email or password."
        )

    # Only after the password matched, so nobody learns an account is blocked by guessing
    ensure_not_blocked(user)

    
    return issue_tokens(user,response)

@router.post("/refresh",response_model=TokenResponse)
@limiter.limit(rate_limit.REFRESH)
async def refresh_token(request: Request ,db: AsyncSession = Depends(get_db)):
    """
    Exchanges the refresh-token cookie for a new access token. The cookie
    itself stays as it is (not rotated). The frontend calls this on every
    page load, since it keeps the access token only in memory.
    """
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in."
        )
    try :
        decoded = decode_token(token)
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

    ensure_not_blocked(user, status.HTTP_401_UNAUTHORIZED)
    ensure_token_still_valid(user,decoded)

    token_data = {"sub": str(user.id), "role": user.role}

    return TokenResponse(access_token= create_access_token(token_data))

@router.post("/forgot-password")
@limiter.limit(rate_limit.FORGOT_PASSWORD)
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Sends a password-reset OTP if the email belongs to an active
    acconut. Always returns the same genereic message regardless --
    this prevents attackers from using this endpoint to discover
    which emails are registered (email enumeration) 
    """

    result = await db.execute(select(User).where(User.email == payload.email))

    user = result.scalar_one_or_none()

    if user is not None and user.is_active and user.blocked_at is None:
        # A failure is only logged : an error here would tell a stranger
        # this email has an account, which the same reply below hides
        await generate_and_send_otp(user,purpose="password_reset",db=db)

    return {"message": "If an account with this email exists, a password reset OTP has been sent."}

@router.post("/reset-password")
@limiter.limit(rate_limit.RESET_PASSWORD)
async def reset_password(request:Request,payload:ResetPasswordRequest,db:AsyncSession = Depends(get_db)):
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
    # Sign out every existing session: tokens issued before now stop working.
    # Whole seconds, because a token's iat is in whole seconds.
    user.sessions_valid_after = datetime.now(timezone.utc).replace(microsecond=0)
    await db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}

@router.post("/logout")
async def logout(request: Request,response: Response ,db:AsyncSession=Depends(get_db)):
    """
    Revokes the refresh-token cookie so it can no longer be used to obtain 
    new access tokens, and deletes the cookie. Safe to call when already 
    signed out. The current access token (if any) remains valid until its 
    own short expiry -- the accepted tradeoff for stateless JWTs.
    """
    token = request.cookies.get(REFRESH_COOKIE)
    try:
        decoded = decode_token(token) if token else {}
    except JWTError:
        decoded = {}

    jti = decoded.get("jti")
    if decoded.get("type") == "refresh" and jti:
        already = await db.execute(select(RevokedRefreshToken).where(RevokedRefreshToken.jti == jti))
        if already.scalar_one_or_none() is None:
            db.add(RevokedRefreshToken(jti=jti))
            await db.commit()

    response.delete_cookie(REFRESH_COOKIE,path="/auth", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    return {"message": "Logged out successfully."}
    




