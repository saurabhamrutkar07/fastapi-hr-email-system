from fastapi import HTTPException,Header,status
from app.core.config import ADMIN_KEY

def verify_key_secret(key_secret: str = Header(...)):
    
    if key_secret != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing key secret"
        )


