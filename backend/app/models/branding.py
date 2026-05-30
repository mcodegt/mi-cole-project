from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

LOGIN_PORTALS = ("staff", "parent", "student")


class CampusPortalBranding(Base):
    __tablename__ = "campus_portal_branding"

    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campuses.id", ondelete="CASCADE"), primary_key=True
    )
    portal: Mapped[str] = mapped_column(String(16), primary_key=True)
    login_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    logo_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    login_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    login_subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_color_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
