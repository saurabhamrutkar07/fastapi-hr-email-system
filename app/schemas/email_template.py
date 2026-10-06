from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema

class EmailTemplateCreate(BaseSchema):
    name : str = Field(..., min_length = 1,max_length=100)
    subject : str | None = Field(None,max_length=255) 
    content : str = Field(..., min_length = 1,max_length=10000)
    is_default : bool = False


class EmailTemplateResponse(BaseModel):
    id : int 
    name : str 
    subject : str | None 
    content : str 
    is_default : bool 



