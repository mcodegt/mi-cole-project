from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.billing import BillingDashboardInfo


class PlanTier(str, Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    custom = "custom"


class PlanFeatures(BaseModel):
    parent_portal: bool = False
    student_portal: bool = False
    reports_advanced: bool = False

    model_config = {"extra": "allow"}


class PlanLimits(BaseModel):
    """Clave ausente o null = sin límite numérico para ese recurso."""

    max_team_members: Optional[int] = Field(default=None, ge=0)
    max_students: Optional[int] = Field(default=None, ge=0)
    max_parents: Optional[int] = Field(default=None, ge=0)
    features: PlanFeatures = Field(default_factory=PlanFeatures)

    model_config = {"extra": "allow"}


class PlanMetadata(BaseModel):
    monthly_price_gtq: Optional[float] = None
    display_order: Optional[int] = None

    model_config = {"extra": "allow"}


class SubscriptionPlanCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=128)
    tier: PlanTier = PlanTier.basic
    is_active: bool = True
    is_public: bool = True
    limits: PlanLimits = Field(default_factory=PlanLimits)
    metadata: PlanMetadata = Field(default_factory=PlanMetadata)


class SubscriptionPlanUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    tier: Optional[PlanTier] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    limits: Optional[PlanLimits] = None
    metadata: Optional[PlanMetadata] = None


class SubscriptionPlanRead(BaseModel):
    id: UUID
    code: str
    name: str
    tier: PlanTier
    is_active: bool
    is_public: bool
    limits: PlanLimits
    metadata: PlanMetadata
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResourceUsage(BaseModel):
    current: int
    max: Optional[int] = None


class PlanUsageSummary(BaseModel):
    plan: Optional[SubscriptionPlanRead] = None
    usage: dict[str, ResourceUsage]
    features: PlanFeatures = Field(default_factory=PlanFeatures)


class SubscriptionDashboard(PlanUsageSummary):
    billing: BillingDashboardInfo
