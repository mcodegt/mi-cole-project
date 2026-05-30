from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.campus import Campus
from app.models.edu import Assignment, AssignmentSubmission, Parent, Student, StudentParent
from app.models.school import School
from app.schemas.parent_portal import ParentAssignmentRead, ParentChildRead, ParentDashboardRead
from app.services.plan_limits import assert_parent_portal_enabled


def _get_parent_record(db: Session, *, parent_id: uuid.UUID, school_id: uuid.UUID) -> Parent:
    parent = db.get(Parent, parent_id)
    if not parent or parent.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso padre no válido")
    if parent.parent_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta de padre inactiva")
    return parent


def _list_children(db: Session, *, parent_id: uuid.UUID, school_id: uuid.UUID) -> list[Student]:
    return list(
        db.scalars(
            select(Student)
            .join(StudentParent, StudentParent.student_id == Student.id)
            .where(
                StudentParent.parent_id == parent_id,
                Student.school_id == school_id,
            )
            .order_by(Student.full_name)
        ).all()
    )


def assert_parent_child(
    db: Session, *, parent_id: uuid.UUID, school_id: uuid.UUID, student_id: uuid.UUID
) -> Student:
    student = db.scalar(
        select(Student)
        .join(StudentParent, StudentParent.student_id == Student.id)
        .where(
            StudentParent.parent_id == parent_id,
            Student.id == student_id,
            Student.school_id == school_id,
        )
    )
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este estudiante")
    return student


def list_parent_children(
    db: Session, *, parent_id: uuid.UUID, school_id: uuid.UUID
) -> list[ParentChildRead]:
    assert_parent_portal_enabled(db, school_id)
    _get_parent_record(db, parent_id=parent_id, school_id=school_id)
    rows = _list_children(db, parent_id=parent_id, school_id=school_id)
    return [
        ParentChildRead(
            id=s.id,
            full_name=s.full_name,
            code=s.code,
            status=s.status,
            campus_id=s.campus_id,
        )
        for s in rows
    ]


def get_parent_dashboard(
    db: Session,
    *,
    parent_id: uuid.UUID,
    school_id: uuid.UUID,
    campus_id: Optional[uuid.UUID],
) -> ParentDashboardRead:
    assert_parent_portal_enabled(db, school_id)
    parent = _get_parent_record(db, parent_id=parent_id, school_id=school_id)
    school = db.get(School, school_id)
    campus = db.get(Campus, campus_id) if campus_id else None
    children = _list_children(db, parent_id=parent_id, school_id=school_id)

    pending = 0
    for child in children:
        pending += _count_pending_assignments(db, school_id=school_id, student=child)

    return ParentDashboardRead(
        parent_name=parent.full_name,
        school_name=school.name if school else "",
        school_slug=school.slug if school else "",
        campus_name=campus.name if campus else None,
        children_count=len(children),
        pending_assignments_count=pending,
        children=[
            ParentChildRead(
                id=s.id,
                full_name=s.full_name,
                code=s.code,
                status=s.status,
                campus_id=s.campus_id,
            )
            for s in children
        ],
    )


def _count_pending_assignments(db: Session, *, school_id: uuid.UUID, student: Student) -> int:
    assignments = db.scalars(
        select(Assignment.id).where(
            Assignment.school_id == school_id,
            Assignment.status == "published",
            or_(Assignment.campus_id == student.campus_id, Assignment.campus_id.is_(None)),
        )
    ).all()
    if not assignments:
        return 0
    submitted = set(
        db.scalars(
            select(AssignmentSubmission.assignment_id).where(
                AssignmentSubmission.student_id == student.id,
                AssignmentSubmission.assignment_id.in_(assignments),
                AssignmentSubmission.status.in_(("submitted", "graded")),
            )
        ).all()
    )
    return len(assignments) - len(submitted)


def list_child_assignments(
    db: Session,
    *,
    parent_id: uuid.UUID,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
) -> list[ParentAssignmentRead]:
    assert_parent_portal_enabled(db, school_id)
    _get_parent_record(db, parent_id=parent_id, school_id=school_id)
    student = assert_parent_child(db, parent_id=parent_id, school_id=school_id, student_id=student_id)

    rows = db.scalars(
        select(Assignment)
        .where(
            Assignment.school_id == school_id,
            Assignment.status == "published",
            or_(Assignment.campus_id == student.campus_id, Assignment.campus_id.is_(None)),
        )
        .order_by(Assignment.due_at.asc().nullslast(), Assignment.created_at.desc())
    ).all()

    assignment_ids = [a.id for a in rows]
    submissions: dict[uuid.UUID, AssignmentSubmission] = {}
    if assignment_ids:
        for sub in db.scalars(
            select(AssignmentSubmission).where(
                AssignmentSubmission.student_id == student.id,
                AssignmentSubmission.assignment_id.in_(assignment_ids),
            )
        ).all():
            submissions[sub.assignment_id] = sub

    return [
        ParentAssignmentRead(
            id=a.id,
            title=a.title,
            description=a.description,
            due_at=a.due_at,
            status=a.status,
            submission_status=submissions[a.id].status if a.id in submissions else None,
            submitted_at=submissions[a.id].submitted_at if a.id in submissions else None,
        )
        for a in rows
    ]
