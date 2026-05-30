from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SchoolStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    trial = "trial"
    inactive = "inactive"


class BillingAccessMode(str, Enum):
    full = "full"
    payment_evidence_only = "payment_evidence_only"


class OwnerInline(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class SchoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    status: SchoolStatus = SchoolStatus.active
    subscription_plan_id: Optional[UUID] = None
    billing_access_mode: BillingAccessMode = BillingAccessMode.full
    currency: str = Field(default="GTQ", min_length=3, max_length=3)
    notes: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    owner: Optional[OwnerInline] = None


class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    status: Optional[SchoolStatus] = None
    subscription_plan_id: Optional[UUID] = None
    billing_access_mode: Optional[BillingAccessMode] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    notes: Optional[str] = None


class SchoolRead(BaseModel):
    id: UUID
    name: str
    slug: str
    status: SchoolStatus
    subscription_plan_id: Optional[UUID]
    billing_access_mode: BillingAccessMode
    payment_reference_code: Optional[str]
    currency: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlatformUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    platform_role_ids: list[UUID] = Field(default_factory=list)


class PlatformUserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)


class PlatformRoleRead(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = {"from_attributes": True}


class PlatformUserRead(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    platform_roles: list[PlatformRoleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlatformUserRolesUpdate(BaseModel):
    platform_role_ids: list[UUID]
