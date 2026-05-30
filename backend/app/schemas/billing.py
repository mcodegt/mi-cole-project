from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BillingAccessMode(str, Enum):
    full = "full"
    payment_evidence_only = "payment_evidence_only"


class BillingPeriodStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


class PaymentEvidenceKind(str, Enum):
    onboarding = "onboarding"
    monthly = "monthly"


class PaymentEvidenceReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BillingPeriodRead(BaseModel):
    id: UUID
    school_id: UUID
    period_year: int
    period_month: int
    amount_expected: Decimal
    status: BillingPeriodStatus
    due_day: int
    paid_validated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BillingDashboardInfo(BaseModel):
    billing_access_mode: BillingAccessMode
    current_period: Optional[BillingPeriodRead] = None
    has_pending_evidence: bool = False


class PaymentEvidenceRead(BaseModel):
    id: UUID
    school_id: UUID
    school_name: Optional[str] = None
    school_slug: Optional[str] = None
    billing_period_id: Optional[UUID] = None
    period_year: Optional[int] = None
    period_month: Optional[int] = None
    amount_expected: Optional[Decimal] = None
    kind: PaymentEvidenceKind
    original_filename: Optional[str] = None
    review_status: PaymentEvidenceReviewStatus
    rejection_reason: Optional[str] = None
    uploaded_by_user_id: UUID
    created_at: datetime


class PaymentEvidenceReject(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class PaymentEvidenceUploadResponse(BaseModel):
    id: UUID
    review_status: PaymentEvidenceReviewStatus
    storage_key: str
    message: str = "Comprobante recibido. Será revisado por el equipo de plataforma."
