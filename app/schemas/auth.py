from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema

class SignupRequest(BaseSchema):
    name : str = Field(...,min_length=1,max_length=100) 
    email : EmailStr
    mobile : str = Field(min_length= 10,max_length=15)

class SignupResponse(BaseModel):
    user_id : int 
    message : str 


class VerifyOTPRequest(BaseSchema):
    email: EmailStr
    otp_code: str = Field(min_length = 6, max_length = 6)

class SetPasswordRequest(BaseSchema):
    email : EmailStr
    password : str = Field(min_length=8,max_length=128)

class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8,max_length=128)

class TokenResponse(BaseModel):
    access_token : str 
    refresh_token : str 
    token_type : str = "bearer"

class RefreshTokenRequest(BaseSchema):
    refresh_token : str = Field(max_length=1024) 

class ForgotPasswordRequest(BaseSchema):
    email: EmailStr

class ResetPasswordRequest(BaseSchema):
    email : EmailStr
    otp_code : str = Field(min_length = 6, max_length = 6)
    new_password: str = Field(min_length = 8, max_length=128)
