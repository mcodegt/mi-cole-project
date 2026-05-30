from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_staff_with_billing
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.edu import ParentCreate, ParentRead
from app.schemas.edu_updates import ParentUpdate
from app.schemas.invite import PortalInviteRequest, PortalInviteResponse
from app.services.edu_service import (
    create_parent,
    delete_parent,
    get_parent,
    list_parents,
    parent_to_read,
    update_parent,
)
from app.services.invite_service import invite_parent

router = APIRouter(prefix="/parents", tags=["parents"])


@router.get("", response_model=PaginatedResponse[ParentRead])
def list_parents_route(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.read")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
) -> PaginatedResponse[ParentRead]:
    rows, total = list_parents(
        db, ctx, page=page, limit=limit, status_filter=status_filter, q=q
    )
    return PaginatedResponse(
        items=[parent_to_read(p) for p in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=ParentRead, status_code=status.HTTP_201_CREATED)
def create_parent_route(
    body: ParentCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.write")),
) -> ParentRead:
    return create_parent(db, ctx, body)


@router.get("/{parent_id}", response_model=ParentRead)
def get_parent_route(
    parent_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.read")),
) -> ParentRead:
    parent = get_parent(db, ctx, parent_id)
    return parent_to_read(parent)


@router.patch("/{parent_id}", response_model=ParentRead)
def update_parent_route(
    parent_id: UUID,
    body: ParentUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.write")),
) -> ParentRead:
    return update_parent(db, ctx, parent_id, body)


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_parent_route(
    parent_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.write")),
) -> Response:
    delete_parent(db, ctx, parent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{parent_id}/invite", response_model=PortalInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_parent_route(
    parent_id: UUID,
    body: PortalInviteRequest,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.parents.write")),
) -> PortalInviteResponse:
    return invite_parent(db, ctx, parent_id=parent_id, body=body)
