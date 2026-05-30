from __future__ import annotations

import logging
import secrets
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, assert_campus_access
from app.models.campus import Campus
from app.models.edu import Parent, Student, StudentParent
from app.models.school import School
from app.models.user import User
from app.schemas.auth import AuthPortal
from app.schemas.invite import PortalInviteRequest, PortalInviteResponse
from app.services.auth_service import hash_password
from app.services.edu_service import get_parent, get_student
from app.services.plan_limits import assert_parent_portal_enabled, assert_student_portal_enabled

logger = logging.getLogger(__name__)


def _generate_temp_password() -> str:
    return secrets.token_urlsafe(10)


def _resolve_campus(
    db: Session,
    *,
    school: School,
    campus_slug: Optional[str],
    fallback_campus_id: Optional[uuid.UUID],
) -> Campus:
    if campus_slug:
        campus = db.scalar(
            select(Campus).where(
                Campus.school_id == school.id,
                Campus.slug == campus_slug.lower(),
                Campus.is_active.is_(True),
            )
        )
        if not campus:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
        return campus

    if fallback_campus_id:
        campus = db.get(Campus, fallback_campus_id)
        if campus and campus.school_id == school.id and campus.is_active:
            return campus

    campus = db.scalar(
        select(Campus)
        .where(Campus.school_id == school.id, Campus.is_active.is_(True))
        .order_by(Campus.name)
        .limit(1)
    )
    if not campus:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El colegio no tiene sedes activas")
    return campus


def _parent_default_campus_id(db: Session, parent_id: uuid.UUID) -> Optional[uuid.UUID]:
    return db.scalar(
        select(Student.campus_id)
        .join(StudentParent, StudentParent.student_id == Student.id)
        .where(StudentParent.parent_id == parent_id, Student.campus_id.isnot(None))
        .limit(1)
    )


def _ensure_user_for_invite(
    db: Session,
    *,
    email: str,
    full_name: str,
    temp_password: str,
) -> tuple[User, bool]:
    normalized = email.lower()
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing:
        if not existing.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario inactivo con ese email")
        existing.password_hash = hash_password(temp_password)
        existing.must_change_password = True
        existing.full_name = full_name
        return existing, False

    user = User(
        email=normalized,
        password_hash=hash_password(temp_password),
        full_name=full_name,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    return user, True


def _assert_parent_not_linked_elsewhere(
    db: Session, *, school_id: uuid.UUID, user_id: uuid.UUID, parent_id: uuid.UUID
) -> None:
    other = db.scalar(
        select(Parent).where(
            Parent.school_id == school_id,
            Parent.user_id == user_id,
            Parent.id != parent_id,
        )
    )
    if other:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya está vinculado a otro padre en este colegio",
        )


def _assert_student_not_linked_elsewhere(
    db: Session, *, school_id: uuid.UUID, user_id: uuid.UUID, student_id: uuid.UUID
) -> None:
    other = db.scalar(
        select(Student).where(
            Student.school_id == school_id,
            Student.user_id == user_id,
            Student.id != student_id,
        )
    )
    if other:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya está vinculado a otro estudiante en este colegio",
        )


def invite_parent(
    db: Session,
    ctx: AuthzContext,
    *,
    parent_id: uuid.UUID,
    body: PortalInviteRequest,
) -> PortalInviteResponse:
    assert_parent_portal_enabled(db, ctx.school_id)
    parent = get_parent(db, ctx, parent_id)
    if parent.parent_status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Padre inactivo")
    if parent.user_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Padre ya tiene acceso al portal")

    school = db.get(School, ctx.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    campus = _resolve_campus(
        db,
        school=school,
        campus_slug=body.campus_slug,
        fallback_campus_id=_parent_default_campus_id(db, parent.id),
    )
    assert_campus_access(ctx, campus.id, db=db)

    temp_password = _generate_temp_password()
    user, created = _ensure_user_for_invite(
        db,
        email=body.email,
        full_name=parent.full_name,
        temp_password=temp_password,
    )
    _assert_parent_not_linked_elsewhere(db, school_id=school.id, user_id=user.id, parent_id=parent.id)

    parent.user_id = user.id
    if not parent.email:
        parent.email = body.email.lower()

    login_path = f"/login/parent/{school.slug}/{campus.slug}"
    logger.info(
        "[INVITE] Padre %s (%s) — contraseña temporal: %s — login: %s",
        parent.full_name,
        body.email,
        temp_password,
        login_path,
    )
    print(f"[INVITE] Padre {body.email} → {login_path} | contraseña temporal: {temp_password}")

    db.commit()

    return PortalInviteResponse(
        email=body.email.lower(),
        portal=AuthPortal.parent.value,
        login_path=login_path,
        temporary_password=temp_password,
        user_created=created,
        must_change_password=True,
        message="Invitación creada. Comparte el enlace de login y la contraseña temporal.",
    )


def invite_student(
    db: Session,
    ctx: AuthzContext,
    *,
    student_id: uuid.UUID,
    body: PortalInviteRequest,
) -> PortalInviteResponse:
    assert_student_portal_enabled(db, ctx.school_id)
    student = get_student(db, ctx, student_id)
    if student.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estudiante inactivo")
    if student.user_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Estudiante ya tiene acceso al portal")
    if student.campus_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante debe tener sede asignada para invitar al portal",
        )

    school = db.get(School, ctx.school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    campus = _resolve_campus(
        db,
        school=school,
        campus_slug=body.campus_slug,
        fallback_campus_id=student.campus_id,
    )
    if campus.id != student.campus_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sede indicada no coincide con la del estudiante",
        )
    assert_campus_access(ctx, campus.id, db=db)

    temp_password = _generate_temp_password()
    user, created = _ensure_user_for_invite(
        db,
        email=body.email,
        full_name=student.full_name,
        temp_password=temp_password,
    )
    _assert_student_not_linked_elsewhere(db, school_id=school.id, user_id=user.id, student_id=student.id)

    student.user_id = user.id

    login_path = f"/login/student/{school.slug}/{campus.slug}"
    logger.info(
        "[INVITE] Estudiante %s (%s) — contraseña temporal: %s — login: %s",
        student.full_name,
        body.email,
        temp_password,
        login_path,
    )
    print(f"[INVITE] Estudiante {body.email} → {login_path} | contraseña temporal: {temp_password}")

    db.commit()

    return PortalInviteResponse(
        email=body.email.lower(),
        portal=AuthPortal.student.value,
        login_path=login_path,
        temporary_password=temp_password,
        user_created=created,
        must_change_password=True,
        message="Invitación creada. Comparte el enlace de login y la contraseña temporal.",
    )
