"""
===============================================================================
API Security Dependency (security.py)
===============================================================================
Provides authentication dependency functions used to protect API routes.
Enforces header-based authentication by validating the `key-secret` HTTP header
against the configured `ADMIN_KEY` environment variable.
===============================================================================
"""
import uuid
from fastapi import HTTPException, Header, status, Depends
from passlib.context import CryptContext 
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import (
    ADMIN_KEY,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.models import User 


def verify_key_secret(key_secret: str = Header(...)):
    """
    FastAPI Security Dependency:
    ----------------------------
    Inspects incoming HTTP request headers for `key-secret`.
    Compares the provided header value against `ADMIN_KEY`.

    Raises:
    -------
    HTTPException (401 Unauthorized):
        If `key-secret` header is missing or does not match `ADMIN_KEY`.
    """
    if key_secret != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing key secret. Access denied."
        )

pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

def hash_password(password:str)-> str:
    """
    Hashes a plain-text password using bcrypt.
    One-way -- the original password can never be recovered from this hash.

    """
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)-> bool:
    """
    Compares a plain-text password against a stored bcrypt hash.
    Used at login -- never decrypts, only re-hashes and compares.
    """
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict)-> str:
    """
    Creates a short-lived JWT access token 
    `data` should contain at least {"sub": str(user.id), "role": user.role}.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)

def create_refresh_token(data:dict) -> str:
    """
    Creates a long-lived JWT referesh token, used only to obtain a new 
    access token -- never accpeted directly by protected api routes
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh","jti": str(uuid.uuid4())})
    return jwt.encode(to_encode,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)

def decode_token(token:str)-> dict:
    """
    decodes and validate the JWT (checks signature + expiry).
    Raises JWTError if the token is invalid, tamperd, or expired.
    """
    return jwt.decode(token,JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

bearer_scheme = HTTPBearer()
async def get_current_user(
        credentials : HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
) -> User:
    """
    FASTAPI dependency : decodes the barer token, loads the matching
    User row from the DB, and returns it - or raises 401 if the 
    token is invalid/expired or the user no kinger exisit/ is inactive.
    """
    token = credentials .credentials

    try: 
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid or expired token."
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Access token required."
        )
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload."
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "User not found or inactive."
        )

    return user

def require_admin(current_user: User = Depends(get_current_user))-> User:
    """
    FASTAPI dependency: builds on get_current_user, additionally
    requiring role == "admin". Raises 403 otherwise.
    """ 
    if current_user.role != 'admin':
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= "Admin privileges required."
        )
    return current_user
