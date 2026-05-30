from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authz import StudentAuthz
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.student_portal import (
    StudentAssignmentDetailRead,
    StudentAssignmentRead,
    StudentDashboardRead,
    StudentSubmissionCreate,
    StudentSubmissionRead,
)
from app.services.student_portal_service import (
    get_student_assignment,
    get_student_dashboard,
    list_student_assignments,
    list_student_submissions,
    submit_assignment,
)

router = APIRouter(prefix="/student", tags=["student-portal"])


@router.get("/dashboard", response_model=StudentDashboardRead)
def student_dashboard(
    ctx: StudentAuthz,
    db: Session = Depends(get_db),
) -> StudentDashboardRead:
    return get_student_dashboard(
        db,
        student_id=ctx.student_id,
        school_id=ctx.school_id,
        campus_id=ctx.campus_id,
    )


@router.get("/assignments", response_model=PaginatedResponse[StudentAssignmentRead])
def student_assignments(
    ctx: StudentAuthz,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentAssignmentRead]:
    items, total = list_student_assignments(
        db,
        student_id=ctx.student_id,
        school_id=ctx.school_id,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.get("/assignments/{assignment_id}", response_model=StudentAssignmentDetailRead)
def student_assignment_detail(
    assignment_id: UUID,
    ctx: StudentAuthz,
    db: Session = Depends(get_db),
) -> StudentAssignmentDetailRead:
    return get_student_assignment(
        db,
        student_id=ctx.student_id,
        school_id=ctx.school_id,
        assignment_id=assignment_id,
    )


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=StudentSubmissionRead,
    status_code=201,
)
def student_submit_assignment(
    assignment_id: UUID,
    body: StudentSubmissionCreate,
    ctx: StudentAuthz,
    db: Session = Depends(get_db),
) -> StudentSubmissionRead:
    return submit_assignment(
        db,
        student_id=ctx.student_id,
        school_id=ctx.school_id,
        assignment_id=assignment_id,
        body=body,
    )


@router.get("/submissions", response_model=PaginatedResponse[StudentSubmissionRead])
def student_submissions(
    ctx: StudentAuthz,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentSubmissionRead]:
    items, total = list_student_submissions(
        db,
        student_id=ctx.student_id,
        school_id=ctx.school_id,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)
