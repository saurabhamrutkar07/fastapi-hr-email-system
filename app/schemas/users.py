from pydantic import BaseModel,Field
from sqlalchemy import select 
from typing import Literal
from datetime import datetime 
from app.schemas.base import BaseSchema

class UserResponse(BaseModel):
    id : int 
    name : str 
    email : str
    mobile: str | None
    role : str 
    is_active : bool 
    is_email_verified : bool 
    auth_provider : str 
    created_at : datetime 

class UserProfileUpdateRequest(BaseSchema):
    """
    What users may change on their own profile. The email stays fixed:
    it is the login and the address OTPs are sent to 
    """
    name : str = Field(min_length=1, max_length=100)
    mobile: str| None = Field(None, min_length=10, max_length=15)

class UserRoleUpdateRequest(BaseSchema):
    role: Literal["user","admin"]


class UserStatusUpdateRequest(BaseSchema):
    is_active : bool 

