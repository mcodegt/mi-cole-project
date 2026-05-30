from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.school import SubscriptionPlan
from app.schemas.subscription import (
    PlanLimits,
    PlanMetadata,
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
)
from app.services.plan_limits import _plan_to_read


def _metadata_to_dict(meta: PlanMetadata) -> dict:
    return meta.model_dump(exclude_none=True)


def create_subscription_plan(db: Session, body: SubscriptionPlanCreate) -> SubscriptionPlanRead:
    plan = SubscriptionPlan(
        code=body.code.lower(),
        name=body.name,
        tier=body.tier.value,
        is_active=body.is_active,
        is_public=body.is_public,
        limits=body.limits.model_dump(),
        metadata_=_metadata_to_dict(body.metadata),
    )
    db.add(plan)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de plan ya existe") from exc
    db.refresh(plan)
    return _plan_to_read(plan)


def update_subscription_plan(
    db: Session, plan_id: uuid.UUID, body: SubscriptionPlanUpdate
) -> SubscriptionPlanRead:
    plan = db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")

    data = body.model_dump(exclude_unset=True)
    limits = data.pop("limits", None)
    metadata = data.pop("metadata", None)

    if "code" in data and data["code"]:
        data["code"] = data["code"].lower()
    if "tier" in data and data["tier"]:
        data["tier"] = data["tier"].value

    for key, value in data.items():
        setattr(plan, key, value)

    if limits is not None:
        plan.limits = limits.model_dump() if isinstance(limits, PlanLimits) else limits
    if metadata is not None:
        plan.metadata_ = _metadata_to_dict(metadata) if isinstance(metadata, PlanMetadata) else metadata

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Código de plan ya existe") from exc
    db.refresh(plan)
    return _plan_to_read(plan)


def get_subscription_plan(db: Session, plan_id: uuid.UUID) -> SubscriptionPlanRead:
    plan = db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    return _plan_to_read(plan)


def list_subscription_plans(
    db: Session,
    *,
    page: int,
    limit: int,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> tuple[list[SubscriptionPlanRead], int]:
    stmt = select(SubscriptionPlan)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(SubscriptionPlan.name.ilike(like), SubscriptionPlan.code.ilike(like)))
    if is_active is not None:
        stmt = stmt.where(SubscriptionPlan.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    plans = db.scalars(
        stmt.order_by(SubscriptionPlan.name).offset((page - 1) * limit).limit(limit)
    ).all()
    return [_plan_to_read(p) for p in plans], total


def validate_subscription_plan_id(db: Session, plan_id: Optional[uuid.UUID]) -> None:
    if plan_id is None:
        return
    plan = db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan de suscripción inválido")
