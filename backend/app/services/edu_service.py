from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, assert_campus_access
from app.models.campus import Campus
from app.models.edu import Parent, Student, StudentParent
from app.schemas.edu import ParentCreate, ParentRead, ParentRelationship, ParentStatus, StudentCreate, StudentRead
from app.schemas.edu_updates import ParentUpdate, StudentParentLink, StudentUpdate
from app.services.plan_limits import assert_can_add_parent, assert_can_add_student


def parent_to_read(parent: Parent) -> ParentRead:
    return ParentRead(
        id=parent.id,
        school_id=parent.school_id,
        full_name=parent.full_name,
        email=parent.email,
        phone=parent.phone,
        relationship=ParentRelationship(parent.relation_type),
        status=ParentStatus(parent.parent_status),
        portal_access=parent.user_id is not None,
    )


def student_to_read(student: Student) -> StudentRead:
    return StudentRead(
        id=student.id,
        school_id=student.school_id,
        campus_id=student.campus_id,
        full_name=student.full_name,
        code=student.code,
        status=student.status,
        portal_access=student.user_id is not None,
    )


def _validate_campus(db: Session, ctx: AuthzContext, campus_id: Optional[uuid.UUID]) -> None:
    if campus_id is None:
        return
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sede inválida")
    assert_campus_access(ctx, campus_id, db=db)


def _students_base_query(ctx: AuthzContext):
    stmt = select(Student).where(Student.school_id == ctx.school_id)
    if not ctx.all_campuses:
        if not ctx.allowed_campus_ids:
            return stmt.where(Student.id.is_(None))
        return stmt.where(Student.campus_id.in_(ctx.allowed_campus_ids))
    return stmt


def list_students(
    db: Session,
    ctx: AuthzContext,
    *,
    page: int,
    limit: int,
    campus_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
) -> tuple[list[Student], int]:
    stmt = _students_base_query(ctx)
    if campus_id is not None:
        _validate_campus(db, ctx, campus_id)
        stmt = stmt.where(Student.campus_id == campus_id)
    if status_filter:
        stmt = stmt.where(Student.status == status_filter)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Student.full_name.ilike(like), Student.code.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Student.full_name).offset((page - 1) * limit).limit(limit)
    ).all()
    return rows, total


def get_student(db: Session, ctx: AuthzContext, student_id: uuid.UUID) -> Student:
    student = db.get(Student, student_id)
    if not student or student.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estudiante no encontrado")
    if student.campus_id is not None:
        assert_campus_access(ctx, student.campus_id, db=db)
    elif not ctx.all_campuses:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este estudiante")
    return student


def create_student(db: Session, ctx: AuthzContext, body: StudentCreate) -> StudentRead:
    assert_can_add_student(db, ctx.school_id)
    _validate_campus(db, ctx, body.campus_id)

    student = Student(
        school_id=ctx.school_id,
        campus_id=body.campus_id,
        full_name=body.full_name,
        code=body.code,
        status=body.status.value,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student_to_read(student)


def update_student(
    db: Session, ctx: AuthzContext, student_id: uuid.UUID, body: StudentUpdate
) -> StudentRead:
    student = get_student(db, ctx, student_id)
    data = body.model_dump(exclude_unset=True)
    if "campus_id" in data:
        _validate_campus(db, ctx, data["campus_id"])
    for key, value in data.items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student_to_read(student)


def delete_student(db: Session, ctx: AuthzContext, student_id: uuid.UUID) -> None:
    student = get_student(db, ctx, student_id)
    db.execute(delete(StudentParent).where(StudentParent.student_id == student.id))
    db.delete(student)
    db.commit()


def link_student_parent(
    db: Session, ctx: AuthzContext, student_id: uuid.UUID, body: StudentParentLink
) -> None:
    student = get_student(db, ctx, student_id)
    parent = db.get(Parent, body.parent_id)
    if not parent or parent.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Padre no encontrado")
    existing = db.get(StudentParent, {"student_id": student.id, "parent_id": parent.id})
    if existing:
        return
    db.add(StudentParent(student_id=student.id, parent_id=parent.id))
    db.commit()


def list_parents(
    db: Session,
    ctx: AuthzContext,
    *,
    page: int,
    limit: int,
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
) -> tuple[list[Parent], int]:
    stmt = select(Parent).where(Parent.school_id == ctx.school_id)
    if status_filter:
        stmt = stmt.where(Parent.parent_status == status_filter)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Parent.full_name.ilike(like), Parent.email.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Parent.full_name).offset((page - 1) * limit).limit(limit)
    ).all()
    return rows, total


def get_parent(db: Session, ctx: AuthzContext, parent_id: uuid.UUID) -> Parent:
    parent = db.get(Parent, parent_id)
    if not parent or parent.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Padre no encontrado")
    return parent


def create_parent(db: Session, ctx: AuthzContext, body: ParentCreate) -> ParentRead:
    assert_can_add_parent(db, ctx.school_id)
    parent = Parent(
        school_id=ctx.school_id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        relation_type=body.relationship.value,
        parent_status=body.status.value,
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent_to_read(parent)


def update_parent(
    db: Session, ctx: AuthzContext, parent_id: uuid.UUID, body: ParentUpdate
) -> ParentRead:
    parent = get_parent(db, ctx, parent_id)
    data = body.model_dump(exclude_unset=True)
    if "relationship" in data and data["relationship"] is not None:
        rel = data.pop("relationship")
        data["relation_type"] = rel.value if hasattr(rel, "value") else rel
    if "status" in data and data["status"] is not None:
        st = data.pop("status")
        data["parent_status"] = st.value if hasattr(st, "value") else st
    for key, value in data.items():
        setattr(parent, key, value)
    db.commit()
    db.refresh(parent)
    return parent_to_read(parent)


def delete_parent(db: Session, ctx: AuthzContext, parent_id: uuid.UUID) -> None:
    parent = get_parent(db, ctx, parent_id)
    db.execute(delete(StudentParent).where(StudentParent.parent_id == parent.id))
    db.delete(parent)
    db.commit()
