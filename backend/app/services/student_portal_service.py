from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.campus import Campus
from app.models.edu import Assignment, AssignmentSubmission, Student
from app.models.school import School
from app.schemas.student_portal import (
    StudentAssignmentDetailRead,
    StudentAssignmentRead,
    StudentDashboardRead,
    StudentSubmissionCreate,
    StudentSubmissionRead,
)
from app.services.plan_limits import assert_student_portal_enabled


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_student_record(db: Session, *, student_id: uuid.UUID, school_id: uuid.UUID) -> Student:
    student = db.get(Student, student_id)
    if not student or student.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso estudiante no válido")
    if student.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta de estudiante inactiva")
    return student


def _assignment_visible_filter(student: Student):
    return (
        Assignment.status == "published",
        or_(Assignment.campus_id == student.campus_id, Assignment.campus_id.is_(None)),
    )


def _get_assignment_for_student(
    db: Session, *, student: Student, school_id: uuid.UUID, assignment_id: uuid.UUID
) -> Assignment:
    assignment = db.scalar(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.school_id == school_id,
            *_assignment_visible_filter(student),
        )
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return assignment


def _submission_map(
    db: Session, *, student_id: uuid.UUID, assignment_ids: list[uuid.UUID]
) -> dict[uuid.UUID, AssignmentSubmission]:
    if not assignment_ids:
        return {}
    rows = db.scalars(
        select(AssignmentSubmission).where(
            AssignmentSubmission.student_id == student_id,
            AssignmentSubmission.assignment_id.in_(assignment_ids),
        )
    ).all()
    return {row.assignment_id: row for row in rows}


def get_student_dashboard(
    db: Session,
    *,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
    campus_id: Optional[uuid.UUID],
) -> StudentDashboardRead:
    assert_student_portal_enabled(db, school_id)
    student = _get_student_record(db, student_id=student_id, school_id=school_id)
    school = db.get(School, school_id)
    campus = db.get(Campus, campus_id) if campus_id else None

    assignment_ids = list(
        db.scalars(
            select(Assignment.id).where(
                Assignment.school_id == school_id,
                *_assignment_visible_filter(student),
            )
        ).all()
    )
    submissions = _submission_map(db, student_id=student_id, assignment_ids=assignment_ids)
    submitted = sum(1 for s in submissions.values() if s.status in ("submitted", "graded"))
    pending = len(assignment_ids) - submitted

    return StudentDashboardRead(
        student_name=student.full_name,
        student_code=student.code,
        school_name=school.name if school else "",
        school_slug=school.slug if school else "",
        campus_name=campus.name if campus else None,
        pending_assignments_count=pending,
        submitted_assignments_count=submitted,
    )


def list_student_assignments(
    db: Session,
    *,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[StudentAssignmentRead], int]:
    assert_student_portal_enabled(db, school_id)
    student = _get_student_record(db, student_id=student_id, school_id=school_id)

    base = select(Assignment).where(
        Assignment.school_id == school_id,
        *_assignment_visible_filter(student),
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    offset = max(page - 1, 0) * limit
    rows = db.scalars(
        base.order_by(Assignment.due_at.asc().nullslast(), Assignment.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    submissions = _submission_map(db, student_id=student_id, assignment_ids=[a.id for a in rows])
    items = [
        StudentAssignmentRead(
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
    return items, total


def get_student_assignment(
    db: Session,
    *,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> StudentAssignmentDetailRead:
    assert_student_portal_enabled(db, school_id)
    student = _get_student_record(db, student_id=student_id, school_id=school_id)
    assignment = _get_assignment_for_student(
        db, student=student, school_id=school_id, assignment_id=assignment_id
    )
    submission = db.scalar(
        select(AssignmentSubmission).where(
            AssignmentSubmission.student_id == student_id,
            AssignmentSubmission.assignment_id == assignment_id,
        )
    )
    return StudentAssignmentDetailRead(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        due_at=assignment.due_at,
        status=assignment.status,
        submission_status=submission.status if submission else None,
        submitted_at=submission.submitted_at if submission else None,
        submission_body=submission.body if submission else None,
    )


def list_student_submissions(
    db: Session,
    *,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[StudentSubmissionRead], int]:
    assert_student_portal_enabled(db, school_id)
    _get_student_record(db, student_id=student_id, school_id=school_id)

    base = (
        select(AssignmentSubmission, Assignment.title)
        .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
        .where(
            AssignmentSubmission.student_id == student_id,
            Assignment.school_id == school_id,
        )
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    offset = max(page - 1, 0) * limit
    rows = db.execute(
        base.order_by(AssignmentSubmission.submitted_at.desc().nullslast(), AssignmentSubmission.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        StudentSubmissionRead(
            id=sub.id,
            assignment_id=sub.assignment_id,
            assignment_title=title,
            body=sub.body,
            status=sub.status,
            submitted_at=sub.submitted_at,
            created_at=sub.created_at,
        )
        for sub, title in rows
    ]
    return items, total


def submit_assignment(
    db: Session,
    *,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: StudentSubmissionCreate,
) -> StudentSubmissionRead:
    assert_student_portal_enabled(db, school_id)
    student = _get_student_record(db, student_id=student_id, school_id=school_id)
    assignment = _get_assignment_for_student(
        db, student=student, school_id=school_id, assignment_id=assignment_id
    )

    existing = db.scalar(
        select(AssignmentSubmission).where(
            AssignmentSubmission.student_id == student_id,
            AssignmentSubmission.assignment_id == assignment_id,
        )
    )
    now = _utcnow()
    if existing:
        if existing.status in ("submitted", "graded"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta entrega ya fue enviada",
            )
        existing.body = body.body
        existing.status = "submitted"
        existing.submitted_at = now
        submission = existing
    else:
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=student_id,
            body=body.body,
            status="submitted",
            submitted_at=now,
        )
        db.add(submission)

    db.commit()
    db.refresh(submission)
    return StudentSubmissionRead(
        id=submission.id,
        assignment_id=submission.assignment_id,
        assignment_title=assignment.title,
        body=submission.body,
        status=submission.status,
        submitted_at=submission.submitted_at,
        created_at=submission.created_at,
    )
