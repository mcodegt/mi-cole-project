from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.authz import AuthzContext, assert_campus_access
from app.models.campus import Campus, MembershipCampus
from app.models.rbac import Role, SchoolMembership
from app.models.user import User
from app.schemas.team import (
    MembershipStatus,
    TeamMemberInline,
    TeamMembershipCreate,
    TeamMembershipRead,
    TeamMembershipUpdate,
)
from app.services.auth_service import hash_password
from app.services.plan_limits import assert_can_add_team_member


def _membership_to_read(db: Session, membership: SchoolMembership) -> TeamMembershipRead:
    role = membership.role or db.get(Role, membership.role_id)
    user = membership.user or db.get(User, membership.user_id)
    campus_ids = [
        row
        for row in db.scalars(
            select(MembershipCampus.campus_id).where(MembershipCampus.membership_id == membership.id)
        ).all()
    ]
    return TeamMembershipRead(
        id=membership.id,
        user_id=membership.user_id,
        user_email=user.email if user else "",
        user_full_name=user.full_name if user else "",
        role_id=membership.role_id,
        role_code=role.code if role else "",
        role_name=role.name if role else "",
        status=MembershipStatus(membership.status),
        all_campuses=membership.all_campuses,
        campus_ids=campus_ids,
        default_campus_id=membership.default_campus_id,
    )


def _resolve_user(db: Session, *, user_id: Optional[uuid.UUID], member: Optional[TeamMemberInline]) -> User:
    if user_id and member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use user_id o member, no ambos")
    if not user_id and not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar user_id o member")

    if user_id:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    assert member is not None
    email = member.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")
    user = User(
        email=email,
        password_hash=hash_password(member.password),
        full_name=member.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _validate_role(db: Session, ctx: AuthzContext, role_id: uuid.UUID) -> Role:
    role = db.get(Role, role_id)
    if not role or role.scope != "school" or role.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido")
    return role


def _validate_campuses(
    db: Session, ctx: AuthzContext, *, campus_ids: list[uuid.UUID], all_campuses: bool
) -> None:
    if all_campuses:
        return
    if not campus_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Indique campus_ids cuando all_campuses es false",
        )
    for campus_id in campus_ids:
        campus = db.get(Campus, campus_id)
        if not campus or campus.school_id != ctx.school_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sede inválida")
        assert_campus_access(ctx, campus_id, db=db)


def _set_membership_campuses(db: Session, membership_id: uuid.UUID, campus_ids: list[uuid.UUID]) -> None:
    db.execute(delete(MembershipCampus).where(MembershipCampus.membership_id == membership_id))
    for campus_id in campus_ids:
        db.add(MembershipCampus(membership_id=membership_id, campus_id=campus_id))


def list_team_memberships(
    db: Session,
    ctx: AuthzContext,
    *,
    page: int,
    limit: int,
    q: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> tuple[list[TeamMembershipRead], int]:
    stmt = (
        select(SchoolMembership)
        .where(SchoolMembership.school_id == ctx.school_id)
        .options(joinedload(SchoolMembership.user), joinedload(SchoolMembership.role))
    )
    if status_filter:
        stmt = stmt.where(SchoolMembership.status == status_filter)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.join(User, User.id == SchoolMembership.user_id).where(
            or_(User.email.ilike(like), User.full_name.ilike(like))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(SchoolMembership.created_at.desc()).offset((page - 1) * limit).limit(limit)
    ).unique().all()
    return [_membership_to_read(db, m) for m in rows], total


def get_team_membership(db: Session, ctx: AuthzContext, membership_id: uuid.UUID) -> TeamMembershipRead:
    membership = db.scalar(
        select(SchoolMembership)
        .where(SchoolMembership.id == membership_id, SchoolMembership.school_id == ctx.school_id)
        .options(joinedload(SchoolMembership.user), joinedload(SchoolMembership.role))
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    return _membership_to_read(db, membership)


def create_team_membership(
    db: Session, ctx: AuthzContext, body: TeamMembershipCreate
) -> TeamMembershipRead:
    assert_can_add_team_member(db, ctx.school_id)
    _validate_role(db, ctx, body.role_id)
    _validate_campuses(db, ctx, campus_ids=body.campus_ids, all_campuses=body.all_campuses)

    user = _resolve_user(db, user_id=body.user_id, member=body.member)
    existing = db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.user_id == user.id,
            SchoolMembership.school_id == ctx.school_id,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ya es miembro del colegio")

    if body.default_campus_id and not body.all_campuses:
        if body.default_campus_id not in body.campus_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="default_campus_id debe estar en campus_ids")

    membership = SchoolMembership(
        user_id=user.id,
        school_id=ctx.school_id,
        role_id=body.role_id,
        status=body.status.value,
        all_campuses=body.all_campuses,
        default_campus_id=body.default_campus_id,
    )
    db.add(membership)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membresía duplicada") from exc

    if not body.all_campuses:
        _set_membership_campuses(db, membership.id, body.campus_ids)

    db.commit()
    db.refresh(membership)
    return get_team_membership(db, ctx, membership.id)


def update_team_membership(
    db: Session, ctx: AuthzContext, membership_id: uuid.UUID, body: TeamMembershipUpdate
) -> TeamMembershipRead:
    membership = db.get(SchoolMembership, membership_id)
    if not membership or membership.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")

    data = body.model_dump(exclude_unset=True)
    campus_ids = data.pop("campus_ids", None)

    if "role_id" in data and data["role_id"]:
        _validate_role(db, ctx, data["role_id"])
    if "status" in data and data["status"]:
        data["status"] = data["status"].value

    all_campuses = data.get("all_campuses", membership.all_campuses)
    if campus_ids is not None or "all_campuses" in data:
        effective_campuses = campus_ids if campus_ids is not None else [
            row
            for row in db.scalars(
                select(MembershipCampus.campus_id).where(MembershipCampus.membership_id == membership.id)
            ).all()
        ]
        _validate_campuses(db, ctx, campus_ids=effective_campuses, all_campuses=all_campuses)

    for key, value in data.items():
        setattr(membership, key, value)

    if campus_ids is not None or "all_campuses" in data:
        if membership.all_campuses:
            db.execute(delete(MembershipCampus).where(MembershipCampus.membership_id == membership.id))
        elif campus_ids is not None:
            _set_membership_campuses(db, membership.id, campus_ids)

    db.commit()
    return get_team_membership(db, ctx, membership.id)


def delete_team_membership(db: Session, ctx: AuthzContext, membership_id: uuid.UUID) -> None:
    membership = db.get(SchoolMembership, membership_id)
    if not membership or membership.school_id != ctx.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    if membership.id == ctx.membership_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede eliminar su propia membresía")
    db.execute(delete(MembershipCampus).where(MembershipCampus.membership_id == membership.id))
    db.delete(membership)
    db.commit()
