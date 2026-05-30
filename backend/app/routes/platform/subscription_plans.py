from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_platform_permission
from app.database import get_db
from app.schemas.campus import PaginatedResponse
from app.schemas.subscription import SubscriptionPlanCreate, SubscriptionPlanRead, SubscriptionPlanUpdate
from app.services.subscription_plan_service import (
    create_subscription_plan,
    get_subscription_plan,
    list_subscription_plans,
    update_subscription_plan,
)

router = APIRouter(prefix="/subscription-plans", tags=["platform-subscription-plans"])


@router.get("", response_model=PaginatedResponse[SubscriptionPlanRead])
def list_plans(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.plans.manage")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    q: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
) -> PaginatedResponse[SubscriptionPlanRead]:
    items, total = list_subscription_plans(db, page=page, limit=limit, q=q, is_active=is_active)
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=SubscriptionPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    body: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.plans.manage")),
) -> SubscriptionPlanRead:
    return create_subscription_plan(db, body)


@router.get("/{plan_id}", response_model=SubscriptionPlanRead)
def get_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.plans.manage")),
) -> SubscriptionPlanRead:
    return get_subscription_plan(db, plan_id)


@router.patch("/{plan_id}", response_model=SubscriptionPlanRead)
def patch_plan(
    plan_id: UUID,
    body: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.plans.manage")),
) -> SubscriptionPlanRead:
    return update_subscription_plan(db, plan_id, body)
