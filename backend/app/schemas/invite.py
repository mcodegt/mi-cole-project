from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PortalInviteRequest(BaseModel):
    email: EmailStr
    campus_slug: Optional[str] = Field(
        default=None,
        description="Sede para URL de login; por defecto sede del estudiante o primera sede activa",
    )


class PortalInviteResponse(BaseModel):
    email: str
    portal: str
    login_path: str
    temporary_password: str
    user_created: bool
    must_change_password: bool = True
    message: str
