"""Seed de volumen para pruebas de paginación multi-colegio / multi-sede."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.campus import Campus
from app.models.edu import Student
from app.models.rbac import SchoolMembership
from app.models.school import School, SchoolProfile, SchoolSettings
from app.models.user import User
from app.services.platform_service import _ensure_owner_role

SCALE_NAMESPACE = uuid.UUID("e9000000-0000-4000-8000-000000000001")
ADVANCED_PLAN_ID = uuid.UUID("e5000001-0000-4000-8000-000000000003")
DEFAULT_SLUG_PREFIX = "scale-colegio"
BATCH_SIZE = 500


@dataclass(frozen=True)
class ScaleSeedResult:
    schools: int
    campuses: int
    students: int
    per_school: list[int]


def _scale_id(label: str) -> uuid.UUID:
    return uuid.uuid5(SCALE_NAMESPACE, label)


def _school_slug(prefix: str, index: int) -> str:
    return f"{prefix}-{index:02d}"


def reset_scale_data(db: Session, *, slug_prefix: str = DEFAULT_SLUG_PREFIX) -> int:
    """Elimina colegios scale-* (cascade: sedes, estudiantes, roles)."""
    school_ids = db.scalars(
        select(School.id).where(School.slug.like(f"{slug_prefix}-%"))
    ).all()
    if not school_ids:
        return 0
    db.execute(delete(School).where(School.id.in_(school_ids)))
    db.commit()
    return len(school_ids)


def _existing_scale_schools(db: Session, slug_prefix: str) -> list[School]:
    return list(
        db.scalars(
            select(School).where(School.slug.like(f"{slug_prefix}-%")).order_by(School.slug)
        ).all()
    )


def _distribute(count: int, slots: int) -> list[int]:
    base, remainder = divmod(count, slots)
    return [base + (1 if i < remainder else 0) for i in range(slots)]


def seed_bulk_students(
    db: Session,
    *,
    count: int = 10_000,
    schools: int = 10,
    campuses_per_school: int = 2,
    slug_prefix: str = DEFAULT_SLUG_PREFIX,
    reset: bool = False,
    link_demo_owner: bool = True,
    demo_owner_email: str | None = None,
) -> ScaleSeedResult:
    if count < 1:
        raise ValueError("count debe ser >= 1")
    if schools < 1:
        raise ValueError("schools debe ser >= 1")
    if campuses_per_school < 1:
        raise ValueError("campuses_per_school debe ser >= 1")

    per_school_max = max(_distribute(count, schools))
    if per_school_max > 2000:
        raise ValueError(
            f"Con {schools} colegios y plan Avanzado (max 2000 estudiantes), "
            f"count={count} excede el límite (~{per_school_max} por colegio). "
            "Aumenta --schools o reduce --count."
        )

    existing = _existing_scale_schools(db, slug_prefix)
    if existing and not reset:
        raise RuntimeError(
            f"Ya existen {len(existing)} colegios con prefijo '{slug_prefix}-*'. "
            "Usa --reset para regenerar."
        )

    if reset:
        reset_scale_data(db, slug_prefix=slug_prefix)

    total_slots = schools * campuses_per_school
    slot_counts = _distribute(count, total_slots)

    demo_owner: User | None = None
    if link_demo_owner:
        if not demo_owner_email:
            raise ValueError("demo_owner_email requerido cuando link_demo_owner=True")
        demo_owner = db.scalar(select(User).where(User.email == demo_owner_email.lower()))
        if not demo_owner:
            raise RuntimeError(f"Usuario demo owner no encontrado: {demo_owner_email}")

    campus_rows: list[tuple[School, Campus, int]] = []
    per_school_totals: list[int] = []
    slot_idx = 0

    for school_idx in range(1, schools + 1):
        slug = _school_slug(slug_prefix, school_idx)
        school = School(
            id=_scale_id(f"school:{slug}"),
            name=f"Colegio Scale {school_idx:02d}",
            slug=slug,
            status="active",
            subscription_plan_id=ADVANCED_PLAN_ID,
            billing_access_mode="full",
        )
        db.add(school)
        db.flush()

        db.add(SchoolSettings(school_id=school.id, currency="GTQ", metadata_={"scale_seed": True}))
        db.flush()
        db.add(SchoolProfile(school_id=school.id))

        owner_role = _ensure_owner_role(db, school.id)

        if demo_owner:
            db.add(
                SchoolMembership(
                    user_id=demo_owner.id,
                    school_id=school.id,
                    role_id=owner_role.id,
                    status="active",
                    all_campuses=True,
                )
            )

        school_total = 0
        for campus_idx in range(1, campuses_per_school + 1):
            campus_slug = f"sede-{campus_idx}"
            campus = Campus(
                id=_scale_id(f"campus:{slug}:{campus_slug}"),
                school_id=school.id,
                name=f"Sede {campus_idx}",
                slug=campus_slug,
                campus_type="main" if campus_idx == 1 else "annex",
                is_active=True,
            )
            db.add(campus)
            db.flush()

            n = slot_counts[slot_idx]
            slot_idx += 1
            school_total += n
            if n:
                campus_rows.append((school, campus, n))

        per_school_totals.append(school_total)

    db.commit()

    global_seq = 0
    inserted = 0
    batch: list[dict] = []
    current_school_id: uuid.UUID | None = None
    local_seq = 0
    school_num = 0

    for school, campus, n in campus_rows:
        if school.id != current_school_id:
            current_school_id = school.id
            local_seq = 0
            school_num = int(school.slug.rsplit("-", 1)[-1])
        for _ in range(n):
            global_seq += 1
            local_seq += 1
            batch.append(
                {
                    "id": _scale_id(f"student:{global_seq:06d}"),
                    "school_id": school.id,
                    "campus_id": campus.id,
                    "code": f"SC{school_num:02d}-{local_seq:05d}",
                    "full_name": f"Estudiante {school.name} {local_seq:05d}",
                    "status": "inactive" if global_seq % 20 == 0 else "active",
                }
            )
            if len(batch) >= BATCH_SIZE:
                db.bulk_insert_mappings(Student, batch)
                db.commit()
                inserted += len(batch)
                batch.clear()

    if batch:
        db.bulk_insert_mappings(Student, batch)
        db.commit()
        inserted += len(batch)

    return ScaleSeedResult(
        schools=schools,
        campuses=schools * campuses_per_school,
        students=inserted,
        per_school=per_school_totals,
    )


def count_scale_students(db: Session, *, slug_prefix: str = DEFAULT_SLUG_PREFIX) -> int:
    school_ids = db.scalars(
        select(School.id).where(School.slug.like(f"{slug_prefix}-%"))
    ).all()
    if not school_ids:
        return 0
    return db.scalar(
        select(func.count()).select_from(Student).where(Student.school_id.in_(school_ids))
    ) or 0
