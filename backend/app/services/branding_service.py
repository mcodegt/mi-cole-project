from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.authz import AuthzContext, assert_campus_access
from app.models.branding import LOGIN_PORTALS, CampusPortalBranding
from app.models.campus import Campus
from app.models.school import School, SchoolProfile
from app.schemas.branding import (
    BrandingPresentation,
    CampusAccessLinks,
    CampusLoginSummary,
    LoginContextResponse,
    LoginPortal,
    PortalBrandingRead,
    PortalBrandingUpdate,
    SchoolLoginSummary,
)
from app.services.storage_service import StorageService, get_storage


def login_path(portal: str, school_slug: str, campus_slug: str) -> str:
    return f"/login/{portal}/{school_slug}/{campus_slug}"


def _public_logo_url(storage_key: Optional[str]) -> Optional[str]:
    if not storage_key:
        return None
    return f"/api/v1/public/branding-file?key={storage_key}"


def _resolve_school_campus(
    db: Session, *, school_slug: str, campus_slug: str
) -> tuple[School, Campus]:
    school = db.scalar(select(School).where(School.slug == school_slug.lower()))
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")
    campus = db.scalar(
        select(Campus).where(
            Campus.school_id == school.id,
            Campus.slug == campus_slug.lower(),
            Campus.is_active.is_(True),
        )
    )
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    return school, campus


def _get_branding_row(db: Session, campus_id: uuid.UUID, portal: str) -> Optional[CampusPortalBranding]:
    return db.get(CampusPortalBranding, {"campus_id": campus_id, "portal": portal})


def _resolve_establishment_logo(
    db: Session,
    *,
    school: School,
    branding: Optional[CampusPortalBranding],
) -> Optional[str]:
    if branding and branding.logo_storage_key:
        return _public_logo_url(branding.logo_storage_key)
    profile = db.get(SchoolProfile, school.id)
    if profile and profile.logo_url:
        return profile.logo_url
    return None


def _presentation_for(
    db: Session,
    *,
    school: School,
    campus: Campus,
    portal: str,
    branding: Optional[CampusPortalBranding],
    use_platform_logo_fallback: bool = False,
) -> BrandingPresentation:
    settings = get_settings()
    logo_url = _resolve_establishment_logo(db, school=school, branding=branding)
    title: Optional[str] = None
    subtitle: Optional[str] = None
    color: Optional[str] = None

    if branding:
        title = branding.login_title
        subtitle = branding.login_subtitle
        color = branding.primary_color_hex

    if not logo_url and use_platform_logo_fallback and settings.platform_login_logo_url:
        logo_url = settings.platform_login_logo_url

    if not title:
        portal_labels = {
            "staff": "Administración y maestros",
            "parent": "Padres de familia",
            "student": "Estudiantes",
        }
        title = f"{portal_labels.get(portal, 'Acceso')} — {campus.name}"

    if not subtitle:
        subtitle = school.name

    if not color:
        profile = db.get(SchoolProfile, school.id)
        if profile and profile.sidebar_color and profile.sidebar_color.startswith("#"):
            color = profile.sidebar_color
        else:
            color = settings.platform_login_primary_color

    return BrandingPresentation(
        login_title=title,
        login_subtitle=subtitle,
        primary_color_hex=color,
        logo_url=logo_url,
    )


def get_login_context(
    db: Session, *, school_slug: str, campus_slug: str, portal: LoginPortal
) -> LoginContextResponse:
    portal_value = portal.value
    if portal_value not in LOGIN_PORTALS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Portal inválido")

    school, campus = _resolve_school_campus(db, school_slug=school_slug, campus_slug=campus_slug)
    branding = _get_branding_row(db, campus.id, portal_value)

    if branding is not None and not branding.login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login no disponible para este portal")

    return LoginContextResponse(
        school=SchoolLoginSummary(id=school.id, slug=school.slug, name=school.name),
        campus=CampusLoginSummary(id=campus.id, slug=campus.slug, name=campus.name),
        portal=portal,
        login_enabled=True if branding is None else branding.login_enabled,
        branding=_presentation_for(db, school=school, campus=campus, portal=portal_value, branding=branding),
        login_path=login_path(portal_value, school.slug, campus.slug),
    )


def portal_login_is_enabled(db: Session, campus_id: uuid.UUID, portal: str) -> bool:
    if portal not in LOGIN_PORTALS:
        return True
    branding = _get_branding_row(db, campus_id, portal)
    if branding is None:
        return True
    return branding.login_enabled


def assert_portal_login_enabled(db: Session, campus_id: uuid.UUID, portal: str) -> None:
    if not portal_login_is_enabled(db, campus_id, portal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login deshabilitado para este portal en esta sede",
        )


def get_portal_branding(
    db: Session, ctx: AuthzContext, campus_id: uuid.UUID, portal: LoginPortal
) -> PortalBrandingRead:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)

    school = db.get(School, campus.school_id)
    assert school is not None
    branding = _get_branding_row(db, campus_id, portal.value)
    presentation = _presentation_for(
        db, school=school, campus=campus, portal=portal.value, branding=branding
    )
    return PortalBrandingRead(
        campus_id=campus_id,
        portal=portal,
        login_enabled=True if branding is None else branding.login_enabled,
        login_title=presentation.login_title,
        login_subtitle=presentation.login_subtitle,
        primary_color_hex=presentation.primary_color_hex,
        logo_url=presentation.logo_url,
        login_path=login_path(portal.value, school.slug, campus.slug),
    )


def update_portal_branding(
    db: Session,
    ctx: AuthzContext,
    campus_id: uuid.UUID,
    portal: LoginPortal,
    body: PortalBrandingUpdate,
) -> PortalBrandingRead:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)

    branding = _get_branding_row(db, campus_id, portal.value)
    if not branding:
        branding = CampusPortalBranding(campus_id=campus_id, portal=portal.value)
        db.add(branding)

    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(branding, key, value)

    db.commit()
    db.refresh(branding)
    return get_portal_branding(db, ctx, campus_id, portal)


async def upload_portal_logo(
    db: Session,
    ctx: AuthzContext,
    campus_id: uuid.UUID,
    portal: LoginPortal,
    file: UploadFile,
    storage: Optional[StorageService] = None,
) -> PortalBrandingRead:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo requerido")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo demasiado grande (máx. 2 MB)")

    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)

    storage = storage or get_storage()
    key = storage.put(
        content=content,
        school_id=campus.school_id,
        filename=f"branding/{campus_id}/{portal.value}/{file.filename}",
    )

    branding = _get_branding_row(db, campus_id, portal.value)
    if not branding:
        branding = CampusPortalBranding(campus_id=campus_id, portal=portal.value, login_enabled=True)
        db.add(branding)
    branding.logo_storage_key = key
    db.commit()
    return get_portal_branding(db, ctx, campus_id, portal)


def get_campus_access_links(db: Session, ctx: AuthzContext, campus_id: uuid.UUID) -> CampusAccessLinks:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)
    school = db.get(School, campus.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")
    return CampusAccessLinks(
        staff=login_path("staff", school.slug, campus.slug),
        parent=login_path("parent", school.slug, campus.slug),
        student=login_path("student", school.slug, campus.slug),
    )
