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


class UserRoleUpdateRequest(BaseSchema):
    role: Literal["user","admin"]


class UserStatusUpdateRequest(BaseSchema):
    is_active : bool 

