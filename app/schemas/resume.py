from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: int
    version_number: int
    is_active: bool
    uploaded_at: str
