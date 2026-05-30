from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_staff_with_billing
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.edu import ParentCreate, ParentRead, StudentCreate, StudentRead
from app.schemas.edu_updates import ParentUpdate, StudentParentLink, StudentUpdate
from app.services.edu_service import (
    create_student as create_student_svc,
    delete_student as delete_student_svc,
    get_student as get_student_svc,
    link_student_parent as link_student_parent_svc,
    list_students as list_students_svc,
    student_to_read,
    update_student as update_student_svc,
)
from app.schemas.invite import PortalInviteRequest, PortalInviteResponse
from app.services.invite_service import invite_student

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=PaginatedResponse[StudentRead])
def list_students_route(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.read")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    campus_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
) -> PaginatedResponse[StudentRead]:
    rows, total = list_students_svc(
        db, ctx, page=page, limit=limit, campus_id=campus_id, status_filter=status_filter, q=q
    )
    return PaginatedResponse(
        items=[student_to_read(s) for s in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student_route(
    body: StudentCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.write")),
) -> StudentRead:
    return create_student_svc(db, ctx, body)


@router.get("/{student_id}", response_model=StudentRead)
def get_student_route(
    student_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.read")),
) -> StudentRead:
    student = get_student_svc(db, ctx, student_id)
    return student_to_read(student)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student_route(
    student_id: UUID,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.write")),
) -> StudentRead:
    return update_student_svc(db, ctx, student_id, body)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_student_route(
    student_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.write")),
) -> Response:
    delete_student_svc(db, ctx, student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{student_id}/parents", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def link_parent_route(
    student_id: UUID,
    body: StudentParentLink,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.write")),
) -> Response:
    link_student_parent_svc(db, ctx, student_id, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{student_id}/invite", response_model=PortalInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_student_route(
    student_id: UUID,
    body: PortalInviteRequest,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.students.write")),
) -> PortalInviteResponse:
    return invite_student(db, ctx, student_id=student_id, body=body)
