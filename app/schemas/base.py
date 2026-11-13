from typing import Annotated
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr

# An email address saved and compared in lowercase, so "HR@Zoho.com" and 
# "hr@zoho.com" are the same person (one account, one contact)
NormEmail = Annotated[EmailStr, AfterValidator(lambda v: v.strip().lower())]
class BaseSchema(BaseModel):
    """
    Shared base for all request schemas -- strips leading/trailing
    whitespace from every string field, and caps string length at 
    255 characters by defauld. Override per-field with 
    Field(...,max_length=...) for fields that legitimately need more 
    room (e.g. email template content, which can be a full email body).
    """
    model_config = ConfigDict(str_strip_whitespace=True,str_max_length=255)