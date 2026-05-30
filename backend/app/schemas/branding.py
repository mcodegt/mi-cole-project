from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginPortal(str, Enum):
    staff = "staff"
    parent = "parent"
    student = "student"


class BrandingPresentation(BaseModel):
    login_title: Optional[str] = None
    login_subtitle: Optional[str] = None
    primary_color_hex: Optional[str] = None
    logo_url: Optional[str] = None


class SchoolLoginSummary(BaseModel):
    id: UUID
    slug: str
    name: str


class CampusLoginSummary(BaseModel):
    id: UUID
    slug: str
    name: str


class LoginContextResponse(BaseModel):
    school: SchoolLoginSummary
    campus: CampusLoginSummary
    portal: LoginPortal
    login_enabled: bool
    branding: BrandingPresentation
    login_path: str


class PortalBrandingUpdate(BaseModel):
    login_enabled: Optional[bool] = None
    login_title: Optional[str] = Field(default=None, max_length=255)
    login_subtitle: Optional[str] = Field(default=None, max_length=255)
    primary_color_hex: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class PortalBrandingRead(BaseModel):
    campus_id: UUID
    portal: LoginPortal
    login_enabled: bool
    login_title: Optional[str] = None
    login_subtitle: Optional[str] = None
    primary_color_hex: Optional[str] = None
    logo_url: Optional[str] = None
    login_path: str


class CampusAccessLinks(BaseModel):
    staff: str
    parent: str
    student: str
