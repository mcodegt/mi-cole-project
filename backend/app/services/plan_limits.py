from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.edu import Parent, Student
from app.models.rbac import SchoolMembership
from app.models.school import School, SubscriptionPlan
from app.schemas.subscription import PlanFeatures, PlanLimits, PlanTier, PlanUsageSummary, ResourceUsage, SubscriptionPlanRead


class PlanLimitError(HTTPException):
    def __init__(self, *, resource_label: str, current: int, maximum: int, plan_name: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{current}/{maximum} {resource_label} del plan {plan_name}",
        )


def _parse_limits(raw: dict) -> PlanLimits:
    return PlanLimits.model_validate(raw or {})


def _parse_features(limits: PlanLimits) -> PlanFeatures:
    return limits.features or PlanFeatures()


def get_school_plan(db: Session, school_id: uuid.UUID) -> Optional[SubscriptionPlan]:
    school = db.get(School, school_id)
    if not school or not school.subscription_plan_id:
        return None
    return db.get(SubscriptionPlan, school.subscription_plan_id)


def _numeric_limit(limits: PlanLimits, key: str) -> Optional[int]:
    value = getattr(limits, key, None)
    if value is None:
        return None
    return int(value)


def count_team_members(db: Session, school_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(SchoolMembership).where(
        SchoolMembership.school_id == school_id,
        SchoolMembership.status == "active",
    )
    return db.scalar(stmt) or 0


def count_students(db: Session, school_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Student).where(Student.school_id == school_id)
    return db.scalar(stmt) or 0


def count_parents(db: Session, school_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Parent).where(Parent.school_id == school_id)
    return db.scalar(stmt) or 0


def _assert_under_limit(
    *,
    current: int,
    maximum: Optional[int],
    resource_label: str,
    plan_name: str,
) -> None:
    if maximum is None:
        return
    if current >= maximum:
        raise PlanLimitError(
            resource_label=resource_label,
            current=current,
            maximum=maximum,
            plan_name=plan_name,
        )


def assert_can_add_team_member(db: Session, school_id: uuid.UUID) -> None:
    plan = get_school_plan(db, school_id)
    if not plan:
        return
    limits = _parse_limits(plan.limits)
    maximum = _numeric_limit(limits, "max_team_members")
    current = count_team_members(db, school_id)
    _assert_under_limit(
        current=current,
        maximum=maximum,
        resource_label="miembros del equipo",
        plan_name=plan.name,
    )


def assert_can_add_student(db: Session, school_id: uuid.UUID) -> None:
    plan = get_school_plan(db, school_id)
    if not plan:
        return
    limits = _parse_limits(plan.limits)
    maximum = _numeric_limit(limits, "max_students")
    current = count_students(db, school_id)
    _assert_under_limit(
        current=current,
        maximum=maximum,
        resource_label="estudiantes",
        plan_name=plan.name,
    )


def assert_can_add_parent(db: Session, school_id: uuid.UUID) -> None:
    plan = get_school_plan(db, school_id)
    if not plan:
        return
    limits = _parse_limits(plan.limits)
    maximum = _numeric_limit(limits, "max_parents")
    current = count_parents(db, school_id)
    _assert_under_limit(
        current=current,
        maximum=maximum,
        resource_label="padres",
        plan_name=plan.name,
    )


def _plan_to_read(plan: SubscriptionPlan) -> SubscriptionPlanRead:
    limits = _parse_limits(plan.limits)
    return SubscriptionPlanRead(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        tier=PlanTier(plan.tier),
        is_active=plan.is_active,
        is_public=plan.is_public,
        limits=limits,
        metadata=plan.metadata_ or {},
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def get_plan_limits_usage_for_school(db: Session, school_id: uuid.UUID) -> PlanUsageSummary:
    plan = get_school_plan(db, school_id)
    limits = _parse_limits(plan.limits) if plan else PlanLimits()
    features = _parse_features(limits)

    usage: dict[str, ResourceUsage] = {
        "team_members": ResourceUsage(
            current=count_team_members(db, school_id),
            max=_numeric_limit(limits, "max_team_members"),
        ),
        "students": ResourceUsage(
            current=count_students(db, school_id),
            max=_numeric_limit(limits, "max_students"),
        ),
        "parents": ResourceUsage(
            current=count_parents(db, school_id),
            max=_numeric_limit(limits, "max_parents"),
        ),
    }

    return PlanUsageSummary(
        plan=_plan_to_read(plan) if plan else None,
        usage=usage,
        features=features,
    )


def assert_parent_portal_enabled(db: Session, school_id: uuid.UUID) -> None:
    usage = get_plan_limits_usage_for_school(db, school_id)
    if not usage.features.parent_portal:
        plan_name = usage.plan.name if usage.plan else "sin plan"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Portal de padres no incluido en el plan {plan_name}",
        )


def assert_student_portal_enabled(db: Session, school_id: uuid.UUID) -> None:
    usage = get_plan_limits_usage_for_school(db, school_id)
    if not usage.features.student_portal:
        plan_name = usage.plan.name if usage.plan else "sin plan"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Portal de estudiantes no incluido en el plan {plan_name}",
        )
