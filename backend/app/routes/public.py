from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.branding import LoginContextResponse, LoginPortal
from app.schemas.public_search import PublicSchoolSearchResponse
from app.services.branding_service import get_login_context
from app.services.public_search_service import search_schools_for_login
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


@router.get("/schools/search", response_model=PublicSchoolSearchResponse)
def schools_search(
    q: str = Query("", max_length=120),
    limit: int = Query(20, ge=1, le=20),
    db: Session = Depends(get_db),
) -> PublicSchoolSearchResponse:
    return search_schools_for_login(db, q=q, limit=limit)


@router.get("/branding-file")
def branding_file(key: str = Query(..., min_length=1)) -> FileResponse:
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    path = storage.resolve_path(key)
    return FileResponse(path)
