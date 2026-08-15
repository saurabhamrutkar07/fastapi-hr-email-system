from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


class ExcelContact(BaseModel):
    """
    Normalized HR contact after Excel rows
    have been grouped together.
    """

    name: str

    emails: list[EmailStr] = Field(
        default_factory=list
    )

    phones: list[str] = Field(
        default_factory=list
    )

    company: Optional[str] = None

    position: Optional[str] = None

    openings: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "Name cannot be empty."
            )

        return value