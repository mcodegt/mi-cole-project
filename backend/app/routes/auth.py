import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.dependencies import client_ip, get_current_token_payload
from app.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    MembershipSummary,
    RefreshRequest,
    SwitchCampusRequest,
    SwitchPortalRequest,
    SwitchSchoolRequest,
)
from app.services.auth_service import (
    AuthError,
    build_me,
    change_password,
    list_staff_memberships,
    login,
    logout,
    refresh,
    switch_campus,
    switch_portal,
    switch_school,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def auth_login(
    body: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    try:
        return login(
            db,
            email=body.email.lower(),
            password=body.password,
            portal=body.portal,
            school_slug=body.school_slug,
            campus_slug=body.campus_slug,
            settings=settings,
            user_agent=request.headers.get("user-agent"),
            ip=client_ip(request),
        )
    except AuthError as exc:
        if exc.code in ("login_disabled", "portal_forbidden"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.post("/refresh", response_model=LoginResponse)
def auth_refresh(
    body: RefreshRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    try:
        return refresh(
            db,
            refresh_token=body.refresh_token,
            settings=settings,
            user_agent=request.headers.get("user-agent"),
            ip=client_ip(request),
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def auth_logout(
    body: LogoutRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    try:
        logout(db, refresh_token=body.refresh_token, settings=settings)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.get("/me", response_model=MeResponse)
def auth_me(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
) -> MeResponse:
    try:
        return build_me(db, access_payload=payload)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.get("/memberships", response_model=list[MembershipSummary])
def auth_memberships(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> list[MembershipSummary]:
    return list_staff_memberships(db, user_id)


@router.post("/switch-school", response_model=LoginResponse)
def auth_switch_school(
    body: SwitchSchoolRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    if payload.get("portal") != "staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo portal staff")
    campus_id = uuid.UUID(payload["campus_id"]) if payload.get("campus_id") else None
    try:
        return switch_school(
            db,
            user_id=uuid.UUID(payload["sub"]),
            membership_id=body.membership_id,
            campus_id=campus_id,
            settings=settings,
            user_agent=request.headers.get("user-agent"),
            ip=client_ip(request),
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc


@router.post("/switch-campus", response_model=LoginResponse)
def auth_switch_campus(
    body: SwitchCampusRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict[str, Any], Depends(get_current_token_payload)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    if payload.get("portal") != "staff" or not payload.get("mid"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo portal staff")
    try:
        return switch_campus(
            db,
            user_id=uuid.UUID(payload["sub"]),
            membership_id=uuid.UUID(payload["mid"]),
            campus_id=body.campus_id,
            settings=settings,
            user_agent=request.headers.get("user-agent"),
            ip=client_ip(request),
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc


@router.post("/switch-portal", response_model=LoginResponse)
def auth_switch_portal(
    body: SwitchPortalRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    try:
        return switch_portal(
            db,
            user_id=user_id,
            portal=body.portal,
            school_slug=body.school_slug,
            campus_slug=body.campus_slug,
            settings=settings,
            user_agent=request.headers.get("user-agent"),
            ip=client_ip(request),
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def auth_change_password(
    body: ChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    try:
        change_password(
            db,
            user_id=user_id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
