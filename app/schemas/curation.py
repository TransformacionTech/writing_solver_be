from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class SourceCreate(BaseModel):
    name: str
    url: str


class SourceOut(BaseModel):
    id: str
    name: str
    url: str
    active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------

class SubscriberCreate(BaseModel):
    email: EmailStr


class SubscriberOut(BaseModel):
    id: str
    email: str
    active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Curation run
# ---------------------------------------------------------------------------

class CurationRunOut(BaseModel):
    id: str
    run_at: datetime
    status: str
    topics_found: int
    email_sent: bool
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Manual trigger response
# ---------------------------------------------------------------------------

class CurationTriggerResponse(BaseModel):
    status: str
    topics_found: int = 0
    email_sent: bool = False
    run_id: str | None = None
    reason: str | None = None
