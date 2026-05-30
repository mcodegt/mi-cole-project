from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_platform_permission
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.platform import (
    PlatformUserCreate,
    PlatformUserRead,
    PlatformUserRolesUpdate,
    PlatformUserUpdate,
)
from app.services.platform_service import (
    create_platform_user,
    get_platform_user,
    list_platform_users,
    set_platform_user_roles,
    update_platform_user,
    user_to_read,
)

router = APIRouter(prefix="/users", tags=["platform-users"])


@router.get("", response_model=PaginatedResponse[PlatformUserRead])
def list_users(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.users.manage")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None),
) -> PaginatedResponse[PlatformUserRead]:
    users, total = list_platform_users(db, page=page, limit=limit, q=q)
    return PaginatedResponse(
        items=[user_to_read(u) for u in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=PlatformUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    body: PlatformUserCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.users.manage")),
) -> PlatformUserRead:
    user = create_platform_user(db, body)
    user = get_platform_user(db, user.id)
    return user_to_read(user)


@router.get("/{user_id}", response_model=PlatformUserRead)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.users.manage")),
) -> PlatformUserRead:
    user = get_platform_user(db, user_id)
    return user_to_read(user)


@router.patch("/{user_id}", response_model=PlatformUserRead)
def update_user(
    user_id: UUID,
    body: PlatformUserUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.users.manage")),
) -> PlatformUserRead:
    update_platform_user(db, user_id, body)
    user = get_platform_user(db, user_id)
    return user_to_read(user)


@router.put("/{user_id}/platform-roles", response_model=PlatformUserRead)
def set_user_platform_roles(
    user_id: UUID,
    body: PlatformUserRolesUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.users.manage")),
) -> PlatformUserRead:
    set_platform_user_roles(db, user_id, body.platform_role_ids)
    user = get_platform_user(db, user_id)
    return user_to_read(user)
