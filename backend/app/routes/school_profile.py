from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.authz import AuthzContext, require_permission, require_staff_with_billing
from app.database import get_db
from app.schemas.school_profile import SchoolProfileRead, SchoolProfileUpdate
from app.services.school_profile_service import (
    get_school_profile,
    update_school_profile,
    upload_school_logo,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/school", tags=["school"])


@router.get("/profile", response_model=SchoolProfileRead)
def read_school_profile(
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_permission("school.settings.read")),
) -> SchoolProfileRead:
    return get_school_profile(db, ctx)


@router.patch("/profile", response_model=SchoolProfileRead)
def patch_school_profile(
    body: SchoolProfileUpdate,
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.settings.write")),
) -> SchoolProfileRead:
    return update_school_profile(db, ctx, body)


@router.post("/profile/logo", response_model=SchoolProfileRead)
async def post_school_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: AuthzContext = Depends(require_staff_with_billing("school.settings.write")),
) -> SchoolProfileRead:
    return await upload_school_logo(db, ctx, file)
