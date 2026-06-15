from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.campus import Campus
from app.models.school import School
from app.schemas.public_search import (
    PublicCampusSearchItem,
    PublicSchoolSearchItem,
    PublicSchoolSearchResponse,
)

PUBLIC_LOGIN_SCHOOL_STATUSES = ("active", "trial")
DEFAULT_SEARCH_LIMIT = 20
MIN_QUERY_LENGTH = 2


def search_schools_for_login(
    db: Session,
    *,
    q: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> PublicSchoolSearchResponse:
    query = q.strip()
    if len(query) < MIN_QUERY_LENGTH:
        return PublicSchoolSearchResponse(items=[], total=0)

    safe_limit = max(1, min(limit, DEFAULT_SEARCH_LIMIT))
    like = f"%{query}%"
    schools = db.scalars(
        select(School)
        .where(School.status.in_(PUBLIC_LOGIN_SCHOOL_STATUSES))
        .where(or_(School.name.ilike(like), School.slug.ilike(like)))
        .order_by(School.name)
        .limit(safe_limit)
    ).all()

    items: list[PublicSchoolSearchItem] = []
    for school in schools:
        campuses = db.scalars(
            select(Campus)
            .where(
                Campus.school_id == school.id,
                Campus.is_active.is_(True),
            )
            .order_by(Campus.name)
        ).all()
        if not campuses:
            continue
        items.append(
            PublicSchoolSearchItem(
                slug=school.slug,
                name=school.name,
                campuses=[
                    PublicCampusSearchItem(slug=campus.slug, name=campus.name) for campus in campuses
                ],
            )
        )

    return PublicSchoolSearchResponse(items=items, total=len(items))
