from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, assert_campus_access, require_staff_with_billing
from app.database import get_db
from app.models.campus import Campus
from app.schemas.branding import CampusAccessLinks, LoginPortal, PortalBrandingRead, PortalBrandingUpdate
from app.schemas.campus import CampusCreate, CampusRead, CampusUpdate, PaginatedResponse
from app.services.branding_service import (
    get_campus_access_links,
    get_portal_branding,
    update_portal_branding,
    upload_portal_logo,
)

router = APIRouter(prefix="/campuses", tags=["campuses"])

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _campus_query_for_ctx(db: Session, ctx: AuthzContext):
    stmt = select(Campus).where(Campus.school_id == ctx.school_id)
    if not ctx.all_campuses:
        if not ctx.allowed_campus_ids:
            return stmt.where(Campus.id.is_(None))  # sin sedes → vacío
        stmt = stmt.where(Campus.id.in_(ctx.allowed_campus_ids))
    return stmt


@router.get("", response_model=PaginatedResponse[CampusRead])
def list_campuses(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.read")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
) -> PaginatedResponse[CampusRead]:
    base = _campus_query_for_ctx(db, ctx)
    if is_active is not None:
        base = base.where(Campus.is_active == is_active)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        base.order_by(Campus.name).offset((page - 1) * limit).limit(limit)
    ).all()

    return PaginatedResponse(
        items=[CampusRead.model_validate(c) for c in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=CampusRead, status_code=status.HTTP_201_CREATED)
def create_campus(
    body: CampusCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.write")),
) -> CampusRead:
    campus = Campus(
        school_id=ctx.school_id,
        name=body.name,
        slug=body.slug.lower(),
        campus_type=body.campus_type.value,
        is_active=body.is_active,
        address=body.address,
    )
    db.add(campus)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de sede ya existe") from exc
    db.refresh(campus)
    return CampusRead.model_validate(campus)


@router.get("/{campus_id}", response_model=CampusRead)
def get_campus(
    campus_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.read")),
) -> CampusRead:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)
    return CampusRead.model_validate(campus)


@router.patch("/{campus_id}", response_model=CampusRead)
def update_campus(
    campus_id: UUID,
    body: CampusUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.write")),
) -> CampusRead:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    assert_campus_access(ctx, campus_id, db=db)

    data = body.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] is not None:
        data["slug"] = data["slug"].lower()
    if "campus_type" in data and data["campus_type"] is not None:
        data["campus_type"] = data["campus_type"].value

    for key, value in data.items():
        setattr(campus, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de sede ya existe") from exc
    db.refresh(campus)
    return CampusRead.model_validate(campus)


@router.get("/{campus_id}/access-links", response_model=CampusAccessLinks)
def campus_access_links(
    campus_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.read")),
) -> CampusAccessLinks:
    return get_campus_access_links(db, ctx, campus_id)


@router.get("/{campus_id}/portal-branding/{portal}", response_model=PortalBrandingRead)
def read_portal_branding(
    campus_id: UUID,
    portal: LoginPortal,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.read")),
) -> PortalBrandingRead:
    return get_portal_branding(db, ctx, campus_id, portal)


@router.patch("/{campus_id}/portal-branding/{portal}", response_model=PortalBrandingRead)
def patch_portal_branding(
    campus_id: UUID,
    portal: LoginPortal,
    body: PortalBrandingUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.write")),
) -> PortalBrandingRead:
    return update_portal_branding(db, ctx, campus_id, portal, body)


@router.post("/{campus_id}/portal-branding/{portal}/logo", response_model=PortalBrandingRead)
async def post_portal_logo(
    campus_id: UUID,
    portal: LoginPortal,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.campuses.write")),
) -> PortalBrandingRead:
    return await upload_portal_logo(db, ctx, campus_id, portal, file)
