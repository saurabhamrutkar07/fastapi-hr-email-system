from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema


class SMTPCredentialCreate(BaseSchema):
    smtp_server : str = Field(default="smtp.gmail.com",max_length=255)
    smtp_port: int = Field(default=587)
    email_address: EmailStr
    password : str = Field(..., min_length=1,max_length=128, description="Gmail App Password, not your real account password")


class SMTPCredentialResponse(BaseModel):
    smtp_server: str 
    smtp_port : int 
    email_address : str 
    is_active : bool 
