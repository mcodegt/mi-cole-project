from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, FrozenSet, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_token_payload
from app.database import get_db
from app.models.campus import Campus, MembershipCampus
from app.models.edu import Parent, Student
from app.models.rbac import Permission, PlatformRoleAssignment, Role, RolePermission, SchoolMembership
from app.models.school import School
from app.schemas.auth import AuthPortal
from app.services.plan_limits import assert_parent_portal_enabled, assert_student_portal_enabled


@dataclass(frozen=True)
class AuthzContext:
    user_id: UUID
    portal: AuthPortal
    school_id: Optional[UUID]
    membership_id: Optional[UUID]
    parent_id: Optional[UUID]
    student_id: Optional[UUID]
    campus_id: Optional[UUID]
    permissions: FrozenSet[str]
    all_campuses: bool
    allowed_campus_ids: FrozenSet[UUID]


def _platform_permissions(db: Session, user_id: UUID) -> frozenset[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(PlatformRoleAssignment, PlatformRoleAssignment.role_id == Role.id)
        .where(PlatformRoleAssignment.user_id == user_id, Role.scope == "platform")
        .distinct()
    )
    return frozenset(db.scalars(stmt).all())


def _school_permissions(db: Session, role_id: UUID) -> frozenset[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    return frozenset(db.scalars(stmt).all())


def _membership_campus_ids(db: Session, membership_id: UUID) -> frozenset[UUID]:
    stmt = select(MembershipCampus.campus_id).where(MembershipCampus.membership_id == membership_id)
    return frozenset(db.scalars(stmt).all())


def assert_campus_access(ctx: AuthzContext, campus_id: UUID, *, db: Optional[Session] = None) -> None:
    if ctx.portal != AuthPortal.staff or ctx.school_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso staff requerido")

    if db is not None:
        campus = db.get(Campus, campus_id)
        if not campus or campus.school_id != ctx.school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sede no pertenece al colegio")

    if ctx.all_campuses:
        return

    if campus_id not in ctx.allowed_campus_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a esta sede")


def build_authz_context(
    db: Session,
    *,
    token: dict,
    x_school_id: Optional[str] = None,
    x_campus_id: Optional[str] = None,
    x_portal: Optional[str] = None,
) -> AuthzContext:
    try:
        portal = AuthPortal(token.get("portal", AuthPortal.platform.value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Portal inválido") from exc

    if x_portal and x_portal != portal.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="X-Portal no coincide con el token")

    user_id = UUID(token["sub"])
    token_sid = UUID(token["sid"]) if token.get("sid") else None
    token_mid = UUID(token["mid"]) if token.get("mid") else None
    token_campus = UUID(token["campus_id"]) if token.get("campus_id") else None

    if portal == AuthPortal.platform:
        return AuthzContext(
            user_id=user_id,
            portal=portal,
            school_id=None,
            membership_id=None,
            parent_id=None,
            student_id=None,
            campus_id=None,
            permissions=_platform_permissions(db, user_id),
            all_campuses=True,
            allowed_campus_ids=frozenset(),
        )

    if portal == AuthPortal.parent:
        if not token_sid or not token.get("pid"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token parent sin contexto")
        pid = UUID(token["pid"])
        effective_sid = UUID(x_school_id) if x_school_id else token_sid
        if effective_sid != token_sid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="X-School-Id no coincide con el token"
            )
        parent = db.get(Parent, pid)
        if not parent or parent.user_id != user_id or parent.school_id != token_sid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso padre inválido")
        assert_parent_portal_enabled(db, token_sid)
        effective_campus = UUID(x_campus_id) if x_campus_id else token_campus
        if effective_campus is not None:
            campus = db.get(Campus, effective_campus)
            if not campus or campus.school_id != token_sid:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sede no pertenece al colegio")
        return AuthzContext(
            user_id=user_id,
            portal=portal,
            school_id=token_sid,
            membership_id=None,
            parent_id=pid,
            student_id=None,
            campus_id=effective_campus,
            permissions=frozenset(
                ("parent.dashboard.read", "parent.children.read", "parent.assignments.read")
            ),
            all_campuses=True,
            allowed_campus_ids=frozenset(),
        )

    if portal == AuthPortal.student:
        if not token_sid or not token.get("stid"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token student sin contexto")
        stid = UUID(token["stid"])
        effective_sid = UUID(x_school_id) if x_school_id else token_sid
        if effective_sid != token_sid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="X-School-Id no coincide con el token"
            )
        student = db.get(Student, stid)
        if not student or student.user_id != user_id or student.school_id != token_sid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso estudiante inválido")
        assert_student_portal_enabled(db, token_sid)
        effective_campus = UUID(x_campus_id) if x_campus_id else token_campus
        if effective_campus is not None:
            campus = db.get(Campus, effective_campus)
            if not campus or campus.school_id != token_sid:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sede no pertenece al colegio")
        return AuthzContext(
            user_id=user_id,
            portal=portal,
            school_id=token_sid,
            membership_id=None,
            parent_id=None,
            student_id=stid,
            campus_id=effective_campus,
            permissions=frozenset(
                (
                    "student.dashboard.read",
                    "student.assignments.read",
                    "student.submissions.read",
                    "student.submissions.write",
                )
            ),
            all_campuses=True,
            allowed_campus_ids=frozenset(),
        )

    if portal != AuthPortal.staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Portal {portal.value} no soportado aún")

    if not token_sid or not token_mid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token staff sin contexto de colegio")

    effective_sid = UUID(x_school_id) if x_school_id else token_sid
    if effective_sid != token_sid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="X-School-Id no coincide con el token")

    membership = db.get(SchoolMembership, token_mid)
    if not membership or membership.user_id != user_id or membership.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membresía staff inválida")
    if membership.school_id != token_sid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membresía no pertenece al colegio del token")

    permissions = _school_permissions(db, membership.role_id)
    allowed = _membership_campus_ids(db, membership.id)
    all_campuses = membership.all_campuses

    effective_campus = UUID(x_campus_id) if x_campus_id else token_campus
    if effective_campus is not None:
        ctx = AuthzContext(
            user_id=user_id,
            portal=portal,
            school_id=token_sid,
            membership_id=token_mid,
            parent_id=None,
            student_id=None,
            campus_id=effective_campus,
            permissions=permissions,
            all_campuses=all_campuses,
            allowed_campus_ids=allowed,
        )
        assert_campus_access(ctx, effective_campus, db=db)
    else:
        ctx = AuthzContext(
            user_id=user_id,
            portal=portal,
            school_id=token_sid,
            membership_id=token_mid,
            parent_id=None,
            student_id=None,
            campus_id=None,
            permissions=permissions,
            all_campuses=all_campuses,
            allowed_campus_ids=allowed,
        )

    return ctx


def get_authz_context(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[dict, Depends(get_current_token_payload)],
    x_school_id: Annotated[Optional[str], Header(alias="X-School-Id")] = None,
    x_campus_id: Annotated[Optional[str], Header(alias="X-Campus-Id")] = None,
    x_portal: Annotated[Optional[str], Header(alias="X-Portal")] = None,
) -> AuthzContext:
    return build_authz_context(
        db,
        token=token,
        x_school_id=x_school_id,
        x_campus_id=x_campus_id,
        x_portal=x_portal,
    )


def require_portal(required: AuthPortal):
    def dependency(ctx: Annotated[AuthzContext, Depends(get_authz_context)]) -> AuthzContext:
        if ctx.portal != required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere portal {required.value}",
            )
        return ctx

    return dependency


def require_permission(code: str):
    def dependency(ctx: Annotated[AuthzContext, Depends(get_authz_context)]) -> AuthzContext:
        if code not in ctx.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {code}",
            )
        return ctx

    return dependency


def require_platform_permission(code: str):
    def dependency(ctx: Annotated[AuthzContext, Depends(get_authz_context)]) -> AuthzContext:
        if ctx.portal != AuthPortal.platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere portal {AuthPortal.platform.value}",
            )
        if code not in ctx.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {code}",
            )
        return ctx

    return dependency


def require_parent_portal():
    portal_dep = require_portal(AuthPortal.parent)

    def dependency(
        ctx: AuthzContext = Depends(portal_dep),
    ) -> AuthzContext:
        if ctx.parent_id is None or ctx.school_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contexto padre requerido")
        return ctx

    return dependency


StaffAuthz = Annotated[AuthzContext, Depends(require_portal(AuthPortal.staff))]
ParentAuthz = Annotated[AuthzContext, Depends(require_parent_portal())]


def require_student_portal():
    portal_dep = require_portal(AuthPortal.student)

    def dependency(
        ctx: AuthzContext = Depends(portal_dep),
    ) -> AuthzContext:
        if ctx.student_id is None or ctx.school_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contexto estudiante requerido")
        return ctx

    return dependency


StudentAuthz = Annotated[AuthzContext, Depends(require_student_portal())]


def require_staff_with_billing(permission: str):
    """Permiso staff + colegio con billing_access_mode full."""
    permission_dep = require_permission(permission)

    def dependency(
        ctx: AuthzContext = Depends(permission_dep),
        db: Session = Depends(get_db),
    ) -> AuthzContext:
        from app.services.billing_service import assert_billing_full_access

        assert_billing_full_access(db, ctx.school_id)
        return ctx

    return dependency
