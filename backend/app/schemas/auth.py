from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AuthPortal(str, Enum):
    platform = "platform"
    staff = "staff"
    parent = "parent"
    student = "student"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    portal: AuthPortal = AuthPortal.platform
    school_slug: Optional[str] = None
    campus_slug: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PlatformContext(BaseModel):
    is_superadmin: bool = False
    permissions: list[str] = []


class UserInfo(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    must_change_password: bool = False


class StaffMeContext(BaseModel):
    school_id: UUID
    school_slug: str
    school_name: str
    role_code: str
    billing_access_mode: str
    permissions: list[str]
    all_campuses: bool


class ParentMeContext(BaseModel):
    parent_id: UUID
    school_id: UUID
    school_slug: str
    school_name: str
    campus_name: Optional[str] = None


class StudentMeContext(BaseModel):
    student_id: UUID
    school_id: UUID
    school_slug: str
    school_name: str
    campus_name: Optional[str] = None
    student_code: Optional[str] = None


class MembershipSummary(BaseModel):
    membership_id: UUID
    school_id: UUID
    school_slug: str
    school_name: str
    role_code: str
    all_campuses: bool


class SwitchSchoolRequest(BaseModel):
    membership_id: UUID


class SwitchCampusRequest(BaseModel):
    campus_id: UUID


class SwitchPortalRequest(BaseModel):
    portal: AuthPortal
    school_slug: str = Field(min_length=1)
    campus_slug: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class MeResponse(BaseModel):
    user: UserInfo
    portal: AuthPortal
    platform: Optional[PlatformContext] = None
    staff: Optional[StaffMeContext] = None
    parent: Optional[ParentMeContext] = None
    student: Optional[StudentMeContext] = None
    sid: Optional[UUID] = None
    mid: Optional[UUID] = None
    pid: Optional[UUID] = None
    stid: Optional[UUID] = None
    campus_id: Optional[UUID] = None
    portals: list[str] = []


class LoginResponse(TokenPair):
    user: UserInfo
    portal: AuthPortal
    platform: Optional[PlatformContext] = None
    sid: Optional[UUID] = None
    mid: Optional[UUID] = None
    pid: Optional[UUID] = None
    stid: Optional[UUID] = None
    campus_id: Optional[UUID] = None
    portals: list[str] = []
