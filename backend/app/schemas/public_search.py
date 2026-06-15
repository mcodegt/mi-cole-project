from __future__ import annotations

from pydantic import BaseModel, Field


class PublicCampusSearchItem(BaseModel):
    slug: str
    name: str


class PublicSchoolSearchItem(BaseModel):
    slug: str
    name: str
    campuses: list[PublicCampusSearchItem]


class PublicSchoolSearchResponse(BaseModel):
    items: list[PublicSchoolSearchItem]
    total: int = Field(ge=0)
