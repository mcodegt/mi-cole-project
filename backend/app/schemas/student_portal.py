from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StudentDashboardRead(BaseModel):
    student_name: str
    student_code: Optional[str]
    school_name: str
    school_slug: str
    campus_name: Optional[str]
    pending_assignments_count: int
    submitted_assignments_count: int


class StudentAssignmentRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    status: str
    submission_status: Optional[str] = None
    submitted_at: Optional[datetime] = None


class StudentAssignmentDetailRead(StudentAssignmentRead):
    submission_body: Optional[str] = None


class StudentSubmissionRead(BaseModel):
    id: UUID
    assignment_id: UUID
    assignment_title: str
    body: Optional[str]
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime


class StudentSubmissionCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
