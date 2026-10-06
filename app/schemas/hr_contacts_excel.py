from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)
from app.schemas.base import BaseSchema


class ExcelContact(BaseSchema):
    """
    Normalized HR contact after Excel rows
    have been grouped together.
    """

    name: str = Field(max_length=100)

    emails: list[EmailStr] = Field(
        default_factory=list
    )

    phones: list[str] = Field(
        default_factory=list
    )

    company: Optional[str] = Field(None,max_length=150)

    position: Optional[str] = Field(None,max_length=150)

    openings: Optional[str] = Field(None,max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "Name cannot be empty."
            )

        return value