from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SchoolProfileRead(BaseModel):
    school_id: UUID
    school_name: str
    logo_url: Optional[str] = None
    sidebar_color: str = "#ffffff"
    sidebar_text_color: str = "#0f172a"
    suggested_text_color: str = "#0f172a"


class SchoolProfileUpdate(BaseModel):
    logo_url: Optional[str] = Field(default=None, max_length=2048)
    sidebar_color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sidebar_text_color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    clear_logo: Optional[bool] = None
