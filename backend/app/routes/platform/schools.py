from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_platform_permission
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.platform import SchoolCreate, SchoolRead, SchoolUpdate
from app.services.platform_service import (
    create_school as create_school_svc,
    get_school as get_school_svc,
    list_schools as list_schools_svc,
    update_school as update_school_svc,
)

router = APIRouter(prefix="/schools", tags=["platform-schools"])


@router.get("", response_model=PaginatedResponse[SchoolRead])
def list_schools(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.schools.manage")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> PaginatedResponse[SchoolRead]:
    items, total = list_schools_svc(db, page=page, limit=limit, q=q, status_filter=status_filter)
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    body: SchoolCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.schools.manage")),
) -> SchoolRead:
    return create_school_svc(db, body)


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.schools.manage")),
) -> SchoolRead:
    return get_school_svc(db, school_id)


@router.patch("/{school_id}", response_model=SchoolRead)
def update_school(
    school_id: UUID,
    body: SchoolUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.schools.manage")),
) -> SchoolRead:
    return update_school_svc(db, school_id, body)
