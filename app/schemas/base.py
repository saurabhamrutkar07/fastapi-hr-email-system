from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Shared base for all request schemas -- strips leading/trailing
    whitespace from every string field, and caps string length at 
    255 characters by defauld. Override per-field with 
    Field(...,max_length=...) for fields that legitimately need more 
    room (e.g. email template content, which can be a full email body).
    """
    model_config = ConfigDict(str_strip_whitespace=True,str_max_length=255)