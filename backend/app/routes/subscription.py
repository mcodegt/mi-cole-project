from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.authz import AuthzContext, require_permission, require_portal
from app.database import get_db
from app.schemas.auth import AuthPortal
from app.schemas.billing import PaymentEvidenceKind, PaymentEvidenceUploadResponse
from app.schemas.subscription import SubscriptionDashboard
from app.services.billing_service import build_subscription_dashboard, upload_payment_evidence

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("/dashboard", response_model=SubscriptionDashboard)
def subscription_dashboard(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_portal(AuthPortal.staff)),
    _: AuthzContext = Depends(require_permission("school.subscription.read")),
) -> SubscriptionDashboard:
    return build_subscription_dashboard(db, ctx.school_id)


@router.post("/payment-evidence", response_model=PaymentEvidenceUploadResponse, status_code=201)
async def upload_payment_evidence_route(
    file: UploadFile = File(...),
    billing_period_id: Optional[UUID] = Form(None),
    kind: PaymentEvidenceKind = Form(PaymentEvidenceKind.monthly),
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_portal(AuthPortal.staff)),
    _: AuthzContext = Depends(require_permission("school.subscription.write")),
) -> PaymentEvidenceUploadResponse:
    return await upload_payment_evidence(
        db,
        school_id=ctx.school_id,
        user_id=ctx.user_id,
        file=file,
        billing_period_id=billing_period_id,
        kind=kind,
    )
