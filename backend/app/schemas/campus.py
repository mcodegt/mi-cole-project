from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class CampusType(str, Enum):
    main = "main"
    annex = "annex"
    kindergarten = "kindergarten"
    administrative = "administrative"
    other = "other"


class CampusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    campus_type: CampusType = CampusType.main
    is_active: bool = True
    address: Optional[str] = None


class CampusUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    campus_type: Optional[CampusType] = None
    is_active: Optional[bool] = None
    address: Optional[str] = None


class CampusRead(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    slug: str
    campus_type: CampusType
    is_active: bool
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
