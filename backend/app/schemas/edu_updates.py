from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class StudentUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    campus_id: Optional[UUID] = None
    code: Optional[str] = Field(default=None, max_length=64)
    status: Optional[str] = None


class StudentParentLink(BaseModel):
    parent_id: UUID


class ParentUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=320)
    phone: Optional[str] = Field(default=None, max_length=32)
    relationship: Optional[str] = None
    status: Optional[str] = None
