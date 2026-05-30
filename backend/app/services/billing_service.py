from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.billing import PaymentEvidenceFile, SchoolBillingPeriod
from app.models.school import School
from app.schemas.billing import (
    BillingAccessMode,
    BillingDashboardInfo,
    BillingPeriodRead,
    BillingPeriodStatus,
    PaymentEvidenceKind,
    PaymentEvidenceRead,
    PaymentEvidenceReviewStatus,
    PaymentEvidenceUploadResponse,
)
from app.schemas.subscription import PlanFeatures, ResourceUsage, SubscriptionDashboard, SubscriptionPlanRead
from app.services.plan_limits import get_plan_limits_usage_for_school
from app.services.storage_service import StorageService, get_storage


def build_subscription_dashboard(db: Session, school_id: uuid.UUID) -> SubscriptionDashboard:
    usage = get_plan_limits_usage_for_school(db, school_id)
    billing = get_billing_dashboard_info(db, school_id)
    return SubscriptionDashboard(
        plan=usage.plan,
        usage=usage.usage,
        features=usage.features,
        billing=billing,
    )


def assert_billing_full_access(db: Session, school_id: uuid.UUID) -> None:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")
    if school.billing_access_mode == BillingAccessMode.payment_evidence_only.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido por facturación. Suba su comprobante en Suscripción.",
        )


def _period_to_read(period: SchoolBillingPeriod) -> BillingPeriodRead:
    return BillingPeriodRead(
        id=period.id,
        school_id=period.school_id,
        period_year=period.period_year,
        period_month=period.period_month,
        amount_expected=period.amount_expected,
        status=BillingPeriodStatus(period.period_status),
        due_day=period.due_day,
        paid_validated_at=period.paid_validated_at,
    )


def get_current_billing_period(db: Session, school_id: uuid.UUID) -> Optional[SchoolBillingPeriod]:
    return db.scalar(
        select(SchoolBillingPeriod)
        .where(
            SchoolBillingPeriod.school_id == school_id,
            SchoolBillingPeriod.period_status.in_(("pending", "overdue")),
        )
        .order_by(SchoolBillingPeriod.period_year.desc(), SchoolBillingPeriod.period_month.desc())
        .limit(1)
    )


def get_billing_dashboard_info(db: Session, school_id: uuid.UUID) -> BillingDashboardInfo:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")

    period = get_current_billing_period(db, school_id)
    pending_evidence = db.scalar(
        select(PaymentEvidenceFile.id)
        .where(
            PaymentEvidenceFile.school_id == school_id,
            PaymentEvidenceFile.evidence_status == "pending",
        )
        .limit(1)
    )

    return BillingDashboardInfo(
        billing_access_mode=BillingAccessMode(school.billing_access_mode),
        current_period=_period_to_read(period) if period else None,
        has_pending_evidence=pending_evidence is not None,
    )


def set_school_billing_restricted(db: Session, school_id: uuid.UUID, *, restricted: bool) -> School:
    school = db.get(School, school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colegio no encontrado")
    school.billing_access_mode = (
        BillingAccessMode.payment_evidence_only.value
        if restricted
        else BillingAccessMode.full.value
    )
    db.commit()
    db.refresh(school)
    return school


async def upload_payment_evidence(
    db: Session,
    *,
    school_id: uuid.UUID,
    user_id: uuid.UUID,
    file: UploadFile,
    billing_period_id: Optional[uuid.UUID] = None,
    kind: PaymentEvidenceKind = PaymentEvidenceKind.monthly,
    storage: Optional[StorageService] = None,
) -> PaymentEvidenceUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo requerido")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo demasiado grande (máx. 10 MB)")

    period = None
    if billing_period_id:
        period = db.get(SchoolBillingPeriod, billing_period_id)
        if not period or period.school_id != school_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Período inválido")
    else:
        period = get_current_billing_period(db, school_id)

    storage = storage or get_storage()
    key = storage.put(content=content, school_id=school_id, filename=file.filename)

    evidence = PaymentEvidenceFile(
        school_id=school_id,
        billing_period_id=period.id if period else None,
        kind=kind.value,
        storage_key=key,
        original_filename=file.filename,
        evidence_status="pending",
        uploaded_by_user_id=user_id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return PaymentEvidenceUploadResponse(
        id=evidence.id,
        review_status=PaymentEvidenceReviewStatus.pending,
        storage_key=key,
    )


def list_pending_evidence_queue(
    db: Session, *, page: int = 1, limit: int = 25
) -> tuple[list[PaymentEvidenceRead], int]:
    base = (
        select(PaymentEvidenceFile, School, SchoolBillingPeriod)
        .join(School, School.id == PaymentEvidenceFile.school_id)
        .outerjoin(SchoolBillingPeriod, SchoolBillingPeriod.id == PaymentEvidenceFile.billing_period_id)
        .where(PaymentEvidenceFile.evidence_status == "pending")
        .order_by(PaymentEvidenceFile.created_at.asc())
    )
    total = db.scalar(
        select(func.count())
        .select_from(PaymentEvidenceFile)
        .where(PaymentEvidenceFile.evidence_status == "pending")
    ) or 0
    rows = db.execute(base.offset((page - 1) * limit).limit(limit)).all()
    items = []
    for evidence, school, period in rows:
        items.append(
            PaymentEvidenceRead(
                id=evidence.id,
                school_id=evidence.school_id,
                school_name=school.name,
                school_slug=school.slug,
                billing_period_id=evidence.billing_period_id,
                period_year=period.period_year if period else None,
                period_month=period.period_month if period else None,
                amount_expected=period.amount_expected if period else None,
                kind=PaymentEvidenceKind(evidence.kind),
                original_filename=evidence.original_filename,
                review_status=PaymentEvidenceReviewStatus(evidence.evidence_status),
                rejection_reason=evidence.rejection_reason,
                uploaded_by_user_id=evidence.uploaded_by_user_id,
                created_at=evidence.created_at,
            )
        )
    return items, total


def approve_payment_evidence(
    db: Session, evidence_id: uuid.UUID, reviewer_user_id: uuid.UUID
) -> PaymentEvidenceRead:
    evidence = db.get(PaymentEvidenceFile, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")
    if evidence.evidence_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comprobante ya revisado")

    now = datetime.now(timezone.utc)
    evidence.evidence_status = "approved"
    evidence.reviewed_by_user_id = reviewer_user_id
    evidence.reviewed_at = now

    school = db.get(School, evidence.school_id)
    if school:
        school.billing_access_mode = BillingAccessMode.full.value
        if school.status != "active":
            school.status = "active"

    if evidence.billing_period_id:
        period = db.get(SchoolBillingPeriod, evidence.billing_period_id)
        if period:
            period.period_status = "paid"
            period.paid_validated_at = now
            period.validated_by_user_id = reviewer_user_id

    db.commit()
    db.refresh(evidence)
    return _evidence_to_read(db, evidence)


def reject_payment_evidence(
    db: Session, evidence_id: uuid.UUID, reviewer_user_id: uuid.UUID, reason: str
) -> PaymentEvidenceRead:
    evidence = db.get(PaymentEvidenceFile, evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")
    if evidence.evidence_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comprobante ya revisado")

    now = datetime.now(timezone.utc)
    evidence.evidence_status = "rejected"
    evidence.rejection_reason = reason
    evidence.reviewed_by_user_id = reviewer_user_id
    evidence.reviewed_at = now
    db.commit()
    db.refresh(evidence)
    return _evidence_to_read(db, evidence)


def _evidence_to_read(db: Session, evidence: PaymentEvidenceFile) -> PaymentEvidenceRead:
    school = db.get(School, evidence.school_id)
    period = db.get(SchoolBillingPeriod, evidence.billing_period_id) if evidence.billing_period_id else None
    return PaymentEvidenceRead(
        id=evidence.id,
        school_id=evidence.school_id,
        school_name=school.name if school else None,
        school_slug=school.slug if school else None,
        billing_period_id=evidence.billing_period_id,
        period_year=period.period_year if period else None,
        period_month=period.period_month if period else None,
        amount_expected=period.amount_expected if period else None,
        kind=PaymentEvidenceKind(evidence.kind),
        original_filename=evidence.original_filename,
        review_status=PaymentEvidenceReviewStatus(evidence.evidence_status),
        rejection_reason=evidence.rejection_reason,
        uploaded_by_user_id=evidence.uploaded_by_user_id,
        created_at=evidence.created_at,
    )
