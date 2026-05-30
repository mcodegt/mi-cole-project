from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StudentStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class StudentCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    campus_id: Optional[UUID] = None
    code: Optional[str] = Field(default=None, max_length=64)
    status: StudentStatus = StudentStatus.active


class StudentRead(BaseModel):
    id: UUID
    school_id: UUID
    campus_id: Optional[UUID]
    full_name: str
    code: Optional[str]
    status: StudentStatus

    model_config = {"from_attributes": True}


class ParentRelationship(str, Enum):
    father = "father"
    mother = "mother"
    guardian = "guardian"
    other = "other"


class ParentStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class ParentCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=320)
    phone: Optional[str] = Field(default=None, max_length=32)
    relationship: ParentRelationship = ParentRelationship.guardian
    status: ParentStatus = ParentStatus.active


class ParentRead(BaseModel):
    id: UUID
    school_id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    relationship: ParentRelationship
    status: ParentStatus

    model_config = {"from_attributes": True}
