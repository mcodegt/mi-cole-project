from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MembershipStatus(str, Enum):
    active = "active"
    invited = "invited"
    suspended = "suspended"


class TeamMemberInline(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class TeamMembershipCreate(BaseModel):
    role_id: UUID
    user_id: Optional[UUID] = None
    member: Optional[TeamMemberInline] = None
    all_campuses: bool = True
    campus_ids: list[UUID] = Field(default_factory=list)
    default_campus_id: Optional[UUID] = None
    status: MembershipStatus = MembershipStatus.active


class TeamMembershipUpdate(BaseModel):
    role_id: Optional[UUID] = None
    all_campuses: Optional[bool] = None
    campus_ids: Optional[list[UUID]] = None
    default_campus_id: Optional[UUID] = None
    status: Optional[MembershipStatus] = None


class TeamMembershipRead(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    user_full_name: str
    role_id: UUID
    role_code: str
    role_name: str
    status: MembershipStatus
    all_campuses: bool
    campus_ids: list[UUID]
    default_campus_id: Optional[UUID]

    model_config = {"from_attributes": True}
