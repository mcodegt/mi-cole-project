from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.branding import LoginContextResponse, LoginPortal
from app.services.branding_service import get_login_context
from app.services.storage_service import get_storage

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/login-context", response_model=LoginContextResponse)
def login_context(
    school_slug: str = Query(..., min_length=1),
    campus_slug: str = Query(..., min_length=1),
    portal: LoginPortal = Query(...),
    db: Session = Depends(get_db),
) -> LoginContextResponse:
    return get_login_context(
        db, school_slug=school_slug, campus_slug=campus_slug, portal=portal
    )


@router.get("/branding-file")
def branding_file(key: str = Query(..., min_length=1)) -> FileResponse:
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    path = storage.resolve_path(key)
    return FileResponse(path)
