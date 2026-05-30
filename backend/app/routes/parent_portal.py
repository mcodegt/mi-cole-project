from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authz import ParentAuthz
from app.database import get_db
from app.schemas.parent_portal import ParentAssignmentRead, ParentChildRead, ParentDashboardRead
from app.services.parent_portal_service import (
    get_parent_dashboard,
    list_child_assignments,
    list_parent_children,
)

router = APIRouter(prefix="/parent", tags=["parent-portal"])


@router.get("/dashboard", response_model=ParentDashboardRead)
def parent_dashboard(
    ctx: ParentAuthz,
    db: Session = Depends(get_db),
) -> ParentDashboardRead:
    return get_parent_dashboard(
        db,
        parent_id=ctx.parent_id,
        school_id=ctx.school_id,
        campus_id=ctx.campus_id,
    )


@router.get("/children", response_model=list[ParentChildRead])
def parent_children(
    ctx: ParentAuthz,
    db: Session = Depends(get_db),
) -> list[ParentChildRead]:
    return list_parent_children(db, parent_id=ctx.parent_id, school_id=ctx.school_id)


@router.get("/assignments", response_model=list[ParentAssignmentRead])
def parent_assignments(
    ctx: ParentAuthz,
    student_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> list[ParentAssignmentRead]:
    return list_child_assignments(
        db,
        parent_id=ctx.parent_id,
        school_id=ctx.school_id,
        student_id=student_id,
    )
