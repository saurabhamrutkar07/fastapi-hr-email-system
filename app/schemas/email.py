"""
===============================================================================
Email Service Pydantic Schemas (app/schemas/email.py)
===============================================================================
Defines data validation models for:
1. EmailTransactionResponse: one row of GET /email/transactions. 
2. DailyEmailCount / EmailStatsResponse: the dashboard numbers.
===============================================================================
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime



class EmailTransactionResponse(BaseModel):
    """
    Response schema representing an email transaction audit log record.
    """
    id: int
    request_id: str = Field(description="Unique UUID request tracking ID")
    recipient_email: str = Field(description="Target recipient email address")
    status: str = Field(description="Execution status: SUCCESS or FAILED")
    error_code: Optional[str] = Field(None, description="Categorized failure type if failed")
    response_details: Optional[str] = Field(None, description="Success details or raw error message")
    created_at: datetime = Field(description="Transaction timestamp")

    class Config:
        from_attributes = True

class DailyEmailCount(BaseModel):
    """
    Emails for one calendar day (in the viewer's timezone).
    """
    date: date 
    sent : int = Field(description="Emails the mail server accepted (SUCCESS)")
    failed: int = Field(description="Emails that could not be sent (FAILED)")

class EmailStatsResponse(BaseModel):
    """
    Dashboard summary for the last `days` days, oldest day first in `daily`.
    """
    days: int 
    total: int = Field(description="sent + failed in the window")
    sent: int 
    failed: int 
    success_rate : Optional[float] = Field(None, description="Percent sent, one decimal; null when nothing was attempted")
    contacts_total: int = Field(description="HR contacts available to email")
    daily: List[DailyEmailCount]

