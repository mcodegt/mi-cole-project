from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_staff_with_billing
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.team import TeamMembershipCreate, TeamMembershipRead, TeamMembershipUpdate
from app.services.team_service import (
    create_team_membership,
    delete_team_membership,
    get_team_membership,
    list_team_memberships,
    update_team_membership,
)

router = APIRouter(prefix="/team/memberships", tags=["team"])


@router.get("", response_model=PaginatedResponse[TeamMembershipRead])
def list_memberships(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.team.read")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> PaginatedResponse[TeamMembershipRead]:
    items, total = list_team_memberships(
        db, ctx, page=page, limit=limit, q=q, status_filter=status_filter
    )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=TeamMembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(
    body: TeamMembershipCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.team.write")),
) -> TeamMembershipRead:
    return create_team_membership(db, ctx, body)


@router.get("/{membership_id}", response_model=TeamMembershipRead)
def get_membership(
    membership_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.team.read")),
) -> TeamMembershipRead:
    return get_team_membership(db, ctx, membership_id)


@router.patch("/{membership_id}", response_model=TeamMembershipRead)
def update_membership(
    membership_id: UUID,
    body: TeamMembershipUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.team.write")),
) -> TeamMembershipRead:
    return update_team_membership(db, ctx, membership_id, body)


@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_membership(
    membership_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.team.write")),
) -> Response:
    delete_team_membership(db, ctx, membership_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
