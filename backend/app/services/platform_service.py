from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.campus import Campus
from app.models.rbac import Permission, PlatformRoleAssignment, Role, RolePermission, SchoolMembership
from app.models.school import School, SchoolProfile, SchoolSettings
from app.models.user import User
from app.schemas.platform import (
    BillingAccessMode,
    OwnerInline,
    PlatformRoleRead,
    PlatformUserCreate,
    PlatformUserRead,
    PlatformUserUpdate,
    SchoolCreate,
    SchoolRead,
    SchoolStatus,
    SchoolUpdate,
)
from app.services.auth_service import hash_password
from app.services.subscription_plan_service import validate_subscription_plan_id

SCHOOL_OWNER_PERMISSION_PREFIXES = (
    "school.campuses.",
    "school.settings.",
    "school.team.",
    "school.students.",
    "school.parents.",
    "school.subscription.",
)

PROTECTED_SCHOOL_SLUGS = frozenset({"colegio-demo"})


def _school_to_read(school: School, settings: Optional[SchoolSettings]) -> SchoolRead:
    notes = None
    currency = "GTQ"
    if settings:
        currency = settings.currency
        notes = (settings.metadata_ or {}).get("notes")
    return SchoolRead(
        id=school.id,
        name=school.name,
        slug=school.slug,
        status=SchoolStatus(school.status),
        subscription_plan_id=school.subscription_plan_id,
        billing_access_mode=BillingAccessMode(school.billing_access_mode),
        payment_reference_code=school.payment_reference_code,
        currency=currency,
        notes=notes,
        created_at=school.created_at,
        updated_at=school.updated_at,
    )


def _owner_permission_codes(db: Session) -> list[Permission]:
    return list(
        db.scalars(
            select(Permission).where(
                or_(*[Permission.code.like(f"{p}%") for p in SCHOOL_OWNER_PERMISSION_PREFIXES])
            )
        ).all()
    )


def _sync_role_permissions(db: Session, role: Role, permissions: list[Permission]) -> None:
    existing = set(
        db.scalars(select(RolePermission.permission_id).where(RolePermission.role_id == role.id)).all()
    )
    for perm in permissions:
        if perm.id not in existing:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))


def _ensure_owner_role(db: Session, school_id: uuid.UUID) -> Role:
    role = db.scalar(
        select(Role).where(Role.code == "owner", Role.scope == "school", Role.school_id == school_id)
    )
    owner_perms = _owner_permission_codes(db)
    if role:
        _sync_role_permissions(db, role, owner_perms)
        db.flush()
        return role

    role = Role(code="owner", name="Dueño", scope="school", school_id=school_id)
    db.add(role)
    db.flush()

    for perm in owner_perms:
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.flush()
    return role


def _resolve_owner_user(db: Session, *, owner_user_id: Optional[uuid.UUID], owner: Optional[OwnerInline]) -> User:
    if owner_user_id and owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use owner_user_id o owner, no ambos")
    if not owner_user_id and not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe indicar owner_user_id o owner")

    if owner_user_id:
        user = db.get(User, owner_user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario owner no encontrado")
        return user

    assert owner is not None
    existing = db.scalar(select(User).where(User.email == owner.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email del owner ya existe")
    user = User(
        email=owner.email.lower(),
        password_hash=hash_password(owner.password),
        full_name=owner.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def create_school(db: Session, body: SchoolCreate) -> SchoolRead:
    validate_subscription_plan_id(db, body.subscription_plan_id)
    owner_user = _resolve_owner_user(db, owner_user_id=body.owner_user_id, owner=body.owner)

    metadata: dict = {}
    if body.notes:
        metadata["notes"] = body.notes

    school = School(
        name=body.name,
        slug=body.slug.lower(),
        status=body.status.value,
        subscription_plan_id=body.subscription_plan_id,
        billing_access_mode=body.billing_access_mode.value,
    )
    db.add(school)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de colegio ya existe") from exc

    settings = SchoolSettings(school_id=school.id, currency=body.currency.upper(), metadata_=metadata)
    db.add(settings)
    db.flush()

    profile = SchoolProfile(school_id=school.id)
    db.add(profile)

    owner_role = _ensure_owner_role(db, school.id)

    default_campus = Campus(
        school_id=school.id,
        name="Sede principal",
        slug="sede-principal",
        campus_type="main",
        is_active=True,
    )
    db.add(default_campus)
    db.flush()

    existing_membership = db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.user_id == owner_user.id,
            SchoolMembership.school_id == school.id,
        )
    )
    if not existing_membership:
        db.add(
            SchoolMembership(
                user_id=owner_user.id,
                school_id=school.id,
                role_id=owner_role.id,
                status="active",
                all_campuses=True,
                default_campus_id=default_campus.id,
            )
        )

    db.commit()
    db.refresh(school)
    return _school_to_read(school, settings)


def update_school(db: Session, school_id: uuid.UUID, body: SchoolUpdate) -> SchoolRead:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    settings = db.get(SchoolSettings, school_id)
    if not settings:
        settings = SchoolSettings(school_id=school_id)
        db.add(settings)

    data = body.model_dump(exclude_unset=True)
    if "subscription_plan_id" in data:
        validate_subscription_plan_id(db, data["subscription_plan_id"])
    notes = data.pop("notes", None)
    currency = data.pop("currency", None)

    if "slug" in data and data["slug"]:
        data["slug"] = data["slug"].lower()
    if "status" in data and data["status"]:
        data["status"] = data["status"].value
    if "billing_access_mode" in data and data["billing_access_mode"]:
        data["billing_access_mode"] = data["billing_access_mode"].value

    for key, value in data.items():
        setattr(school, key, value)

    if currency is not None:
        settings.currency = currency.upper()
    if notes is not None:
        meta = dict(settings.metadata_ or {})
        meta["notes"] = notes
        settings.metadata_ = meta

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug de colegio ya existe") from exc

    db.refresh(school)
    return _school_to_read(school, settings)


def list_schools(
    db: Session,
    *,
    page: int,
    limit: int,
    q: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> tuple[list[SchoolRead], int]:
    stmt = select(School).join(SchoolSettings, SchoolSettings.school_id == School.id, isouter=True)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(School.name.ilike(like), School.slug.ilike(like)))
    if status_filter:
        stmt = stmt.where(School.status == status_filter)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    schools = db.scalars(stmt.order_by(School.name).offset((page - 1) * limit).limit(limit)).all()

    items = []
    for school in schools:
        settings = db.get(SchoolSettings, school.id)
        items.append(_school_to_read(school, settings))
    return items, total


def get_school(db: Session, school_id: uuid.UUID) -> SchoolRead:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")
    settings = db.get(SchoolSettings, school_id)
    return _school_to_read(school, settings)


def delete_school(db: Session, school_id: uuid.UUID, slug_confirm: str) -> None:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    if school.slug in PROTECTED_SCHOOL_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este colegio demo está protegido y no puede eliminarse",
        )

    if slug_confirm.strip().lower() != school.slug.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slug no coincide. Escriba el slug exacto para confirmar.",
        )

    db.delete(school)
    db.commit()


def create_platform_user(db: Session, body: PlatformUserCreate) -> User:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    user = User(
        email=email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        is_active=body.is_active,
    )
    db.add(user)
    db.flush()
    _set_platform_roles(db, user.id, body.platform_role_ids)
    db.commit()
    db.refresh(user)
    return user


def update_platform_user(db: Session, user_id: uuid.UUID, body: PlatformUserUpdate) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    data = body.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(user, key, value)
    if password:
        user.password_hash = hash_password(password)

    db.commit()
    db.refresh(user)
    return user


def _set_platform_roles(db: Session, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> None:
    db.execute(delete(PlatformRoleAssignment).where(PlatformRoleAssignment.user_id == user_id))
    if not role_ids:
        return
    roles = db.scalars(select(Role).where(Role.id.in_(role_ids), Role.scope == "platform")).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol platform inválido")
    for role in roles:
        db.add(PlatformRoleAssignment(user_id=user_id, role_id=role.id))


def set_platform_user_roles(db: Session, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    _set_platform_roles(db, user_id, role_ids)
    db.commit()
    db.refresh(user)
    return user


def list_platform_users(
    db: Session,
    *,
    page: int,
    limit: int,
    q: Optional[str] = None,
) -> tuple[list[User], int]:
    stmt = select(User)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    users = db.scalars(
        stmt.options(joinedload(User.platform_roles).joinedload(PlatformRoleAssignment.role))
        .order_by(User.email)
        .offset((page - 1) * limit)
        .limit(limit)
    ).unique().all()
    return users, total


def get_platform_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.platform_roles).joinedload(PlatformRoleAssignment.role))
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


def user_to_read(user: User) -> PlatformUserRead:
    roles = [
        PlatformRoleRead.model_validate(assignment.role)
        for assignment in user.platform_roles
        if assignment.role
    ]
    return PlatformUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        platform_roles=roles,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
