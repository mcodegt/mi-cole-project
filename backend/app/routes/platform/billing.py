from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_platform_permission
from app.database import get_db
from app.schemas.billing import PaymentEvidenceRead, PaymentEvidenceReject
from app.schemas.campus import PaginatedResponse
from app.services.billing_service import (
    approve_payment_evidence,
    list_pending_evidence_queue,
    reject_payment_evidence,
)

router = APIRouter(prefix="/billing", tags=["platform-billing"])


@router.get("/queue", response_model=PaginatedResponse[PaymentEvidenceRead])
def billing_queue(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.billing.review")),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
) -> PaginatedResponse[PaymentEvidenceRead]:
    items, total = list_pending_evidence_queue(db, page=page, limit=limit)
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("/evidence/{evidence_id}/approve", response_model=PaymentEvidenceRead)
def approve_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.billing.review")),
) -> PaymentEvidenceRead:
    return approve_payment_evidence(db, evidence_id, ctx.user_id)


@router.post("/evidence/{evidence_id}/reject", response_model=PaymentEvidenceRead)
def reject_evidence(
    evidence_id: UUID,
    body: PaymentEvidenceReject,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_platform_permission("platform.billing.review")),
) -> PaymentEvidenceRead:
    return reject_payment_evidence(db, evidence_id, ctx.user_id, body.reason)
