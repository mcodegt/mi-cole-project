from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ParentChildRead(BaseModel):
    id: UUID
    full_name: str
    code: Optional[str]
    status: str
    campus_id: Optional[UUID]


class ParentAssignmentRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    status: str
    submission_status: Optional[str] = None
    submitted_at: Optional[datetime] = None


class ParentDashboardRead(BaseModel):
    parent_name: str
    school_name: str
    school_slug: str
    campus_name: Optional[str]
    children_count: int
    pending_assignments_count: int
    children: list[ParentChildRead]
