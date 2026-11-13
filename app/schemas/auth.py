from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema, NormEmail

class SignupRequest(BaseSchema):
    name : str = Field(...,min_length=1,max_length=100) 
    email : NormEmail
    mobile : str = Field(min_length= 10,max_length=15)

class SignupResponse(BaseModel):
    user_id : int 
    message : str 


class VerifyOTPRequest(BaseSchema):
    email: NormEmail
    otp_code: str = Field(min_length = 6, max_length = 6)

class SetPasswordRequest(BaseSchema):
    email : NormEmail
    signup_token : str = Field(max_length=1024)
    password : str = Field(min_length=8,max_length=128)

class LoginRequest(BaseSchema):
    email: NormEmail
    password: str = Field(min_length=8,max_length=128)

class TokenResponse(BaseModel):
    """The refresh token is not in the body: it is set as an httpOnly cookie."""
    access_token : str 
    token_type : str = "bearer"

class GoogleCodeRequest(BaseSchema):
    """The one-time code from /oauth-success#code=..."""
    code : str = Field(max_length=128)

class ForgotPasswordRequest(BaseSchema):
    email: NormEmail

class ResetPasswordRequest(BaseSchema):
    email : NormEmail
    otp_code : str = Field(min_length = 6, max_length = 6)
    new_password: str = Field(min_length = 8, max_length=128)
