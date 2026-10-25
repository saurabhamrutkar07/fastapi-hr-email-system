"""
===============================================================================
History Schemas (app/schemas/history.py)
===============================================================================
Defines the response models for the History page:
1. `HistoryItem`: one sent email in the list.
2. `HistoryPage`: one page of the list plus the total that matches the filters.
3. `HistoryDetail`: one email with everything that was sent.

Emails sent before the History step have no saved content, so their
contact_name, company, subject and body are empty.
===============================================================================
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class HistoryItem(BaseModel):
    request_id: str
    recipient_email: str
    status: str
    error_code: Optional[str] = None
    created_at: datetime
    contact_name: Optional[str] = None
    company: Optional[str] = None
    subject: Optional[str] = None
    # Who sent it; admins see everyone's emails
    sender_name: Optional[str] = None


class HistoryPage(BaseModel):
    total: int
    items: List[HistoryItem]


class HistoryDetail(HistoryItem):
    response_details: Optional[str] = None
    body: Optional[str] = None
    template_name: Optional[str] = None
    resume_version: Optional[int] = None
    sender_email: Optional[str] = None
