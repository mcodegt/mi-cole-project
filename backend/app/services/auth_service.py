from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.branding import LOGIN_PORTALS, CampusPortalBranding
from app.models.campus import Campus, MembershipCampus
from app.models.edu import Parent
from app.models.rbac import Permission, PlatformRoleAssignment, Role, RolePermission, SchoolMembership
from app.models.school import School
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    AuthPortal,
    LoginResponse,
    MeResponse,
    MembershipSummary,
    ParentMeContext,
    PlatformContext,
    StaffMeContext,
    UserInfo,
)
from app.services.plan_limits import assert_parent_portal_enabled, get_plan_limits_usage_for_school

ALGORITHM = "HS256"


class AuthError(Exception):
    def __init__(self, message: str, code: str = "auth_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _encode(payload: dict[str, Any], secret: str) -> str:
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AuthError("Token inválido o expirado", "invalid_token") from exc


def _school_permission_codes(db: Session, role_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    return sorted(db.scalars(stmt).all())


def _platform_permissions(db: Session, user_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(PlatformRoleAssignment, PlatformRoleAssignment.role_id == Role.id)
        .where(PlatformRoleAssignment.user_id == user_id, Role.scope == "platform")
        .distinct()
    )
    return sorted(db.scalars(stmt).all())


def _is_superadmin(db: Session, user_id: uuid.UUID) -> bool:
    stmt = (
        select(Role)
        .join(PlatformRoleAssignment, PlatformRoleAssignment.role_id == Role.id)
        .where(PlatformRoleAssignment.user_id == user_id, Role.code == "superadmin", Role.scope == "platform")
    )
    return db.scalar(stmt) is not None


def _user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )


def create_access_token(
    *,
    user_id: uuid.UUID,
    portal: AuthPortal,
    settings: Settings,
    sid: uuid.UUID | None = None,
    mid: uuid.UUID | None = None,
    pid: uuid.UUID | None = None,
    campus_id: uuid.UUID | None = None,
) -> str:
    expire = _utcnow() + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "access",
        "portal": portal.value,
        "exp": expire,
    }
    if sid:
        payload["sid"] = str(sid)
    if mid:
        payload["mid"] = str(mid)
    if pid:
        payload["pid"] = str(pid)
    if campus_id:
        payload["campus_id"] = str(campus_id)
    return _encode(payload, settings.jwt_secret)


def create_refresh_token_record(
    db: Session,
    *,
    user_id: uuid.UUID,
    portal: AuthPortal,
    settings: Settings,
    sid: uuid.UUID | None = None,
    mid: uuid.UUID | None = None,
    pid: uuid.UUID | None = None,
    campus_id: uuid.UUID | None = None,
    user_agent: str | None = None,
    ip: str | None = None,
) -> tuple[str, RefreshToken]:
    jti = uuid.uuid4()
    expires_at = _utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    record = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        user_agent=user_agent,
        ip=ip,
    )
    db.add(record)
    db.flush()

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "typ": "refresh",
        "jti": str(jti),
        "portal": portal.value,
        "exp": expires_at,
    }
    if sid:
        payload["sid"] = str(sid)
    if mid:
        payload["mid"] = str(mid)
    if pid:
        payload["pid"] = str(pid)
    if campus_id:
        payload["campus_id"] = str(campus_id)

    token = _encode(payload, settings.jwt_secret)
    return token, record


def revoke_refresh_token(db: Session, jti: uuid.UUID) -> None:
    record = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if record and record.revoked_at is None:
        record.revoked_at = _utcnow()


def _get_valid_refresh_record(db: Session, token: str, settings: Settings) -> tuple[dict[str, Any], RefreshToken]:
    payload = decode_token(token, settings.jwt_secret)
    if payload.get("typ") != "refresh":
        raise AuthError("Token de refresh inválido", "invalid_refresh")

    jti = uuid.UUID(payload["jti"])
    record = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if not record:
        raise AuthError("Refresh token no encontrado", "refresh_not_found")
    if record.revoked_at is not None:
        raise AuthError("Refresh token revocado", "refresh_revoked")
    if record.expires_at.replace(tzinfo=timezone.utc) <= _utcnow():
        raise AuthError("Refresh token expirado", "refresh_expired")

    return payload, record


def _assert_membership_campus_access(db: Session, membership: SchoolMembership, campus_id: uuid.UUID) -> None:
    campus = db.get(Campus, campus_id)
    if not campus or campus.school_id != membership.school_id or not campus.is_active:
        raise AuthError("Sede no válida", "campus_not_found")
    if membership.all_campuses:
        return
    link = db.scalar(
        select(MembershipCampus).where(
            MembershipCampus.membership_id == membership.id,
            MembershipCampus.campus_id == campus_id,
        )
    )
    if not link:
        raise AuthError("Sin acceso a esta sede", "campus_forbidden")


def login(
    db: Session,
    *,
    email: str,
    password: str,
    portal: AuthPortal,
    school_slug: str | None = None,
    campus_slug: str | None = None,
    settings: Settings | None = None,
    user_agent: str | None = None,
    ip: str | None = None,
) -> LoginResponse:
    settings = settings or get_settings()
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active:
        raise AuthError("Credenciales inválidas", "invalid_credentials")
    if not verify_password(password, user.password_hash):
        raise AuthError("Credenciales inválidas", "invalid_credentials")

    sid: uuid.UUID | None = None
    mid: uuid.UUID | None = None
    pid: uuid.UUID | None = None
    campus_id: uuid.UUID | None = None
    platform_ctx: PlatformContext | None = None

    if portal == AuthPortal.platform:
        if not _is_superadmin(db, user.id):
            raise AuthError("Sin acceso al portal platform", "portal_forbidden")
        perms = _platform_permissions(db, user.id)
        platform_ctx = PlatformContext(is_superadmin=True, permissions=perms)
    elif portal == AuthPortal.staff:
        if not school_slug:
            raise AuthError("school_slug requerido para portal staff", "school_slug_required")
        school = db.scalar(select(School).where(School.slug == school_slug.lower()))
        if not school:
            raise AuthError("Colegio no encontrado", "school_not_found")
        membership = db.scalar(
            select(SchoolMembership).where(
                SchoolMembership.user_id == user.id,
                SchoolMembership.school_id == school.id,
                SchoolMembership.status == "active",
            )
        )
        if not membership:
            raise AuthError("Sin membresía staff en este colegio", "portal_forbidden")
        sid = membership.school_id
        mid = membership.id
        if campus_slug:
            campus = db.scalar(
                select(Campus).where(
                    Campus.school_id == school.id,
                    Campus.slug == campus_slug.lower(),
                    Campus.is_active.is_(True),
                )
            )
            if not campus:
                raise AuthError("Sede no encontrada", "campus_not_found")
            _assert_membership_campus_access(db, membership, campus.id)
            campus_id = campus.id
            if portal.value in LOGIN_PORTALS:
                branding = db.get(CampusPortalBranding, {"campus_id": campus.id, "portal": portal.value})
                if branding is not None and not branding.login_enabled:
                    raise AuthError(
                        "Login deshabilitado para este portal en esta sede",
                        "login_disabled",
                    )
    elif portal == AuthPortal.parent:
        if not school_slug or not campus_slug:
            raise AuthError("school_slug y campus_slug requeridos para portal parent", "school_slug_required")
        school = db.scalar(select(School).where(School.slug == school_slug.lower()))
        if not school:
            raise AuthError("Colegio no encontrado", "school_not_found")
        usage = get_plan_limits_usage_for_school(db, school.id)
        if not usage.features.parent_portal:
            raise AuthError("Portal de padres no incluido en el plan", "portal_forbidden")
        parent = db.scalar(
            select(Parent).where(
                Parent.user_id == user.id,
                Parent.school_id == school.id,
                Parent.parent_status == "active",
            )
        )
        if not parent:
            raise AuthError("Sin cuenta de padre en este colegio", "portal_forbidden")
        campus = db.scalar(
            select(Campus).where(
                Campus.school_id == school.id,
                Campus.slug == campus_slug.lower(),
                Campus.is_active.is_(True),
            )
        )
        if not campus:
            raise AuthError("Sede no encontrada", "campus_not_found")
        branding = db.get(CampusPortalBranding, {"campus_id": campus.id, "portal": portal.value})
        if branding is not None and not branding.login_enabled:
            raise AuthError(
                "Login deshabilitado para este portal en esta sede",
                "login_disabled",
            )
        sid = school.id
        pid = parent.id
        campus_id = campus.id
    elif portal == AuthPortal.student:
        raise AuthError(f"Portal {portal.value} no disponible aún (fase 11)", "portal_not_implemented")
    else:
        raise AuthError(f"Portal {portal.value} no soportado", "portal_not_implemented")

    user.last_login_at = _utcnow()
    access = create_access_token(
        user_id=user.id,
        portal=portal,
        settings=settings,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
    )
    refresh, _ = create_refresh_token_record(
        db,
        user_id=user.id,
        portal=portal,
        settings=settings,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
        user_agent=user_agent,
        ip=ip,
    )
    db.commit()

    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_info(user),
        portal=portal,
        platform=platform_ctx,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
    )


def refresh(
    db: Session,
    *,
    refresh_token: str,
    settings: Settings | None = None,
    user_agent: str | None = None,
    ip: str | None = None,
) -> LoginResponse:
    settings = settings or get_settings()
    payload, old_record = _get_valid_refresh_record(db, refresh_token, settings)

    user = db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("Usuario inactivo", "user_inactive")

    portal = AuthPortal(payload.get("portal", AuthPortal.platform.value))
    sid = uuid.UUID(payload["sid"]) if payload.get("sid") else None
    mid = uuid.UUID(payload["mid"]) if payload.get("mid") else None
    pid = uuid.UUID(payload["pid"]) if payload.get("pid") else None
    campus_id = uuid.UUID(payload["campus_id"]) if payload.get("campus_id") else None

    revoke_refresh_token(db, old_record.jti)

    platform_ctx: PlatformContext | None = None
    if portal == AuthPortal.platform:
        platform_ctx = PlatformContext(
            is_superadmin=_is_superadmin(db, user.id),
            permissions=_platform_permissions(db, user.id),
        )

    access = create_access_token(
        user_id=user.id,
        portal=portal,
        settings=settings,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
    )
    new_refresh, _ = create_refresh_token_record(
        db,
        user_id=user.id,
        portal=portal,
        settings=settings,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
        user_agent=user_agent,
        ip=ip,
    )
    db.commit()

    return LoginResponse(
        access_token=access,
        refresh_token=new_refresh,
        user=_user_info(user),
        portal=portal,
        platform=platform_ctx,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
    )


def logout(db: Session, *, refresh_token: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    payload, record = _get_valid_refresh_record(db, refresh_token, settings)
    revoke_refresh_token(db, record.jti)
    db.commit()


def _staff_me_context(db: Session, *, school_id: uuid.UUID, membership_id: uuid.UUID) -> StaffMeContext:
    school = db.get(School, school_id)
    membership = db.get(SchoolMembership, membership_id)
    if not school or not membership or membership.school_id != school_id:
        raise AuthError("Contexto staff inválido", "staff_context_invalid")
    role = db.get(Role, membership.role_id)
    return StaffMeContext(
        school_id=school.id,
        school_slug=school.slug,
        school_name=school.name,
        billing_access_mode=school.billing_access_mode,
        permissions=_school_permission_codes(db, membership.role_id),
        all_campuses=membership.all_campuses,
    )


def _parent_me_context(
    db: Session, *, school_id: uuid.UUID, parent_id: uuid.UUID, campus_id: uuid.UUID | None
) -> ParentMeContext:
    school = db.get(School, school_id)
    parent = db.get(Parent, parent_id)
    if not school or not parent or parent.school_id != school_id:
        raise AuthError("Contexto parent inválido", "parent_context_invalid")
    campus_name = None
    if campus_id:
        campus = db.get(Campus, campus_id)
        campus_name = campus.name if campus else None
    return ParentMeContext(
        parent_id=parent.id,
        school_id=school.id,
        school_slug=school.slug,
        school_name=school.name,
        campus_name=campus_name,
    )


def build_me(db: Session, *, access_payload: dict[str, Any]) -> MeResponse:
    user_id = uuid.UUID(access_payload["sub"])
    user = db.get(User, user_id)
    if not user:
        raise AuthError("Usuario no encontrado", "user_not_found")

    portal = AuthPortal(access_payload.get("portal", AuthPortal.platform.value))
    sid = uuid.UUID(access_payload["sid"]) if access_payload.get("sid") else None
    mid = uuid.UUID(access_payload["mid"]) if access_payload.get("mid") else None
    pid = uuid.UUID(access_payload["pid"]) if access_payload.get("pid") else None
    campus_id = uuid.UUID(access_payload["campus_id"]) if access_payload.get("campus_id") else None

    platform_ctx: PlatformContext | None = None
    staff_ctx: StaffMeContext | None = None
    parent_ctx: ParentMeContext | None = None
    if portal == AuthPortal.platform:
        platform_ctx = PlatformContext(
            is_superadmin=_is_superadmin(db, user.id),
            permissions=_platform_permissions(db, user.id),
        )
    elif portal == AuthPortal.staff and sid and mid:
        staff_ctx = _staff_me_context(db, school_id=sid, membership_id=mid)
    elif portal == AuthPortal.parent and sid and pid:
        parent_ctx = _parent_me_context(db, school_id=sid, parent_id=pid, campus_id=campus_id)

    return MeResponse(
        user=_user_info(user),
        portal=portal,
        platform=platform_ctx,
        staff=staff_ctx,
        parent=parent_ctx,
        sid=sid,
        mid=mid,
        pid=pid,
        campus_id=campus_id,
    )


def list_staff_memberships(db: Session, user_id: uuid.UUID) -> list[MembershipSummary]:
    stmt = (
        select(SchoolMembership, School, Role)
        .join(School, School.id == SchoolMembership.school_id)
        .join(Role, Role.id == SchoolMembership.role_id)
        .where(SchoolMembership.user_id == user_id, SchoolMembership.status == "active")
        .order_by(School.name)
    )
    rows = db.execute(stmt).all()
    return [
        MembershipSummary(
            membership_id=m.id,
            school_id=s.id,
            school_slug=s.slug,
            school_name=s.name,
            role_code=r.code,
            all_campuses=m.all_campuses,
        )
        for m, s, r in rows
    ]


def _issue_staff_tokens(
    db: Session,
    *,
    user: User,
    membership: SchoolMembership,
    campus_id: uuid.UUID | None,
    settings: Settings,
    user_agent: str | None = None,
    ip: str | None = None,
) -> LoginResponse:
    access = create_access_token(
        user_id=user.id,
        portal=AuthPortal.staff,
        settings=settings,
        sid=membership.school_id,
        mid=membership.id,
        campus_id=campus_id,
    )
    refresh, _ = create_refresh_token_record(
        db,
        user_id=user.id,
        portal=AuthPortal.staff,
        settings=settings,
        sid=membership.school_id,
        mid=membership.id,
        user_agent=user_agent,
        ip=ip,
    )
    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_info(user),
        portal=AuthPortal.staff,
        sid=membership.school_id,
        mid=membership.id,
        campus_id=campus_id,
    )


def switch_school(
    db: Session,
    *,
    user_id: uuid.UUID,
    membership_id: uuid.UUID,
    campus_id: uuid.UUID | None,
    settings: Settings | None = None,
    user_agent: str | None = None,
    ip: str | None = None,
) -> LoginResponse:
    settings = settings or get_settings()
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthError("Usuario inactivo", "user_inactive")
    membership = db.get(SchoolMembership, membership_id)
    if not membership or membership.user_id != user_id or membership.status != "active":
        raise AuthError("Membresía no encontrada", "membership_not_found")
    if campus_id is not None:
        campus = db.get(Campus, campus_id)
        if not campus or campus.school_id != membership.school_id:
            raise AuthError("Sede no encontrada", "campus_not_found")
        _assert_membership_campus_access(db, membership, campus_id)
    response = _issue_staff_tokens(
        db,
        user=user,
        membership=membership,
        campus_id=campus_id,
        settings=settings,
        user_agent=user_agent,
        ip=ip,
    )
    db.commit()
    return response


def switch_campus(
    db: Session,
    *,
    user_id: uuid.UUID,
    membership_id: uuid.UUID,
    campus_id: uuid.UUID,
    settings: Settings | None = None,
    user_agent: str | None = None,
    ip: str | None = None,
) -> LoginResponse:
    return switch_school(
        db,
        user_id=user_id,
        membership_id=membership_id,
        campus_id=campus_id,
        settings=settings,
        user_agent=user_agent,
        ip=ip,
    )
