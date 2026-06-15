from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext
from app.models.school import School, SchoolProfile, SchoolSettings
from app.schemas.school_profile import SchoolProfileRead, SchoolProfileUpdate
from app.services.color_utils import suggest_text_color_for_background
from app.services.storage_service import StorageService, get_storage

DEFAULT_SIDEBAR_COLOR = "#ffffff"
DEFAULT_SIDEBAR_TEXT_COLOR = "#0f172a"


def _public_logo_url(storage_key: Optional[str]) -> Optional[str]:
    if not storage_key:
        return None
    return f"/api/v1/public/branding-file?key={storage_key}"


def _ensure_profile(db: Session, school_id: uuid.UUID) -> SchoolProfile:
    profile = db.get(SchoolProfile, school_id)
    if profile:
        return profile

    settings = db.get(SchoolSettings, school_id)
    if not settings:
        settings = SchoolSettings(school_id=school_id)
        db.add(settings)
        db.flush()

    profile = SchoolProfile(school_id=school_id)
    db.add(profile)
    db.flush()
    return profile


def _to_read(school: School, profile: SchoolProfile) -> SchoolProfileRead:
    sidebar_color = profile.sidebar_color or DEFAULT_SIDEBAR_COLOR
    sidebar_text_color = profile.sidebar_text_color or suggest_text_color_for_background(sidebar_color)
    return SchoolProfileRead(
        school_id=school.id,
        school_name=school.name,
        logo_url=profile.logo_url,
        sidebar_color=sidebar_color,
        sidebar_text_color=sidebar_text_color,
        suggested_text_color=suggest_text_color_for_background(sidebar_color),
    )


def get_school_profile(db: Session, ctx: AuthzContext) -> SchoolProfileRead:
    if ctx.school_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contexto de colegio requerido")

    school = db.get(School, ctx.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    profile = _ensure_profile(db, school.id)
    return _to_read(school, profile)


def update_school_profile(
    db: Session, ctx: AuthzContext, body: SchoolProfileUpdate
) -> SchoolProfileRead:
    if ctx.school_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contexto de colegio requerido")

    school = db.get(School, ctx.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    profile = _ensure_profile(db, school.id)
    data = body.model_dump(exclude_unset=True)

    if data.pop("clear_logo", False):
        profile.logo_url = None

    if "logo_url" in data:
        value = data.pop("logo_url")
        profile.logo_url = value.strip() if isinstance(value, str) and value.strip() else None

    if "sidebar_color" in data:
        profile.sidebar_color = data.pop("sidebar_color")

    if "sidebar_text_color" in data:
        profile.sidebar_text_color = data.pop("sidebar_text_color")
    elif "sidebar_color" in body.model_fields_set and profile.sidebar_color:
        profile.sidebar_text_color = suggest_text_color_for_background(profile.sidebar_color)

    db.commit()
    db.refresh(profile)
    return _to_read(school, profile)


async def upload_school_logo(
    db: Session,
    ctx: AuthzContext,
    file: UploadFile,
    storage: Optional[StorageService] = None,
) -> SchoolProfileRead:
    if ctx.school_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contexto de colegio requerido")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo requerido")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo demasiado grande (máx. 2 MB)")

    school = db.get(School, ctx.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    storage = storage or get_storage()
    key = storage.put(
        content=content,
        school_id=school.id,
        filename=f"school-profile/logo/{file.filename}",
    )

    profile = _ensure_profile(db, school.id)
    profile.logo_url = _public_logo_url(key)
    db.commit()
    db.refresh(profile)
    return _to_read(school, profile)
