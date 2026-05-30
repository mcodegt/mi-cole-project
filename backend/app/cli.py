import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models.campus import Campus, MembershipCampus
from app.models.edu import Parent, Student, StudentParent
from app.models.rbac import PlatformRoleAssignment, Role, SchoolMembership
from app.models.school import School
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.scale_seed import DEFAULT_SLUG_PREFIX, reset_scale_data, seed_bulk_students


def _resolve_sql_dir() -> Path:
    env = os.environ.get("MICOLE_SQL_DIR")
    if env:
        return Path(env)
    p = Path(__file__).resolve()
    if len(p.parents) > 3:
        docs_sql = p.parents[3] / "mi-cole-docs" / "sql"
        if docs_sql.is_dir():
            return docs_sql
    return p.parent.parent / "sql"


SQL_DIR = _resolve_sql_dir()


def apply_sql_files() -> None:
    files = sorted(SQL_DIR.glob("*.sql"))
    if not files:
        print("No SQL files found.", file=sys.stderr)
        sys.exit(1)

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users')")
        ).scalar()
        if exists:
            print("Schema already applied, skipping SQL.")
            return

    with engine.begin() as conn:
        for path in files:
            print(f"Applying {path.name}...")
            conn.execute(text(path.read_text(encoding="utf-8")))
    print("SQL applied.")


def seed_superadmin() -> None:
    settings = get_settings()
    db: Session = SessionLocal()
    try:
        role = db.scalar(select(Role).where(Role.code == "superadmin", Role.scope == "platform"))
        if not role:
            print("Rol superadmin no encontrado. Ejecuta apply-sql primero.", file=sys.stderr)
            sys.exit(1)

        email = settings.superadmin_email.lower()
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.password_hash = hash_password(settings.superadmin_password)
            user.full_name = settings.superadmin_name
            user.is_active = True
            print(f"Superadmin actualizado: {email}")
        else:
            user = User(
                email=email,
                password_hash=hash_password(settings.superadmin_password),
                full_name=settings.superadmin_name,
                is_active=True,
            )
            db.add(user)
            db.flush()
            print(f"Superadmin creado: {email}")

        existing = db.scalar(
            select(PlatformRoleAssignment).where(
                PlatformRoleAssignment.user_id == user.id,
                PlatformRoleAssignment.role_id == role.id,
            )
        )
        if not existing:
            db.add(PlatformRoleAssignment(user_id=user.id, role_id=role.id))

        db.commit()
    finally:
        db.close()


DEMO_SCHOOL_ID = "d4000001-0000-4000-8000-000000000001"
DEMO_CAMPUS_NORTE = "d4000002-0000-4000-8000-000000000001"
DEMO_OWNER_ROLE = "d4000003-0000-4000-8000-000000000001"
DEMO_OPERATOR_ROLE = "d4000003-0000-4000-8000-000000000003"
DEMO_OWNER_EMAIL = "owner@colegio-demo.dev"
DEMO_OPERATOR_EMAIL = "operator@colegio-demo.dev"
DEMO_PARENT_EMAIL = "parent@colegio-demo.dev"
DEMO_PARENT_ID = "f8000004-0000-4000-8000-000000000001"
DEMO_STUDENT_EMAIL = "student@colegio-demo.dev"
DEMO_STUDENT_RECORD_ID = "f8000001-0000-4000-8000-000000000001"
DEMO_INTERMEDIO_PLAN_ID = "e5000001-0000-4000-8000-000000000002"
DEMO_CHILD_STUDENT_IDS = (
    "f8000001-0000-4000-8000-000000000001",
    "f8000001-0000-4000-8000-000000000002",
    "f8000001-0000-4000-8000-000000000003",
)
DEMO_PASSWORD = "Demo123!"


def seed_demo() -> None:
    """Usuarios demo tras migrations/004_seed_demo_school.sql."""
    import uuid

    db: Session = SessionLocal()
    try:
        school = db.get(School, uuid.UUID(DEMO_SCHOOL_ID))
        if not school:
            print("Colegio demo no encontrado. Ejecuta migrations/004_seed_demo_school.sql.", file=sys.stderr)
            sys.exit(1)

        school.subscription_plan_id = uuid.UUID(DEMO_INTERMEDIO_PLAN_ID)

        owner_role = db.get(Role, uuid.UUID(DEMO_OWNER_ROLE))
        operator_role = db.get(Role, uuid.UUID(DEMO_OPERATOR_ROLE))
        campus_norte = db.get(Campus, uuid.UUID(DEMO_CAMPUS_NORTE))

        for email, name, role, all_campuses, campus_links in (
            (DEMO_OWNER_EMAIL, "Dueño Demo", owner_role, True, []),
            (DEMO_OPERATOR_EMAIL, "Operador Demo", operator_role, False, [campus_norte]),
        ):
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    email=email,
                    password_hash=hash_password(DEMO_PASSWORD),
                    full_name=name,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"Usuario creado: {email}")
            else:
                user.password_hash = hash_password(DEMO_PASSWORD)
                print(f"Usuario actualizado: {email}")

            membership = db.scalar(
                select(SchoolMembership).where(
                    SchoolMembership.user_id == user.id,
                    SchoolMembership.school_id == school.id,
                )
            )
            if not membership:
                membership = SchoolMembership(
                    user_id=user.id,
                    school_id=school.id,
                    role_id=role.id,
                    status="active",
                    all_campuses=all_campuses,
                    default_campus_id=campus_norte.id if campus_links else None,
                )
                db.add(membership)
                db.flush()
            else:
                membership.role_id = role.id
                membership.all_campuses = all_campuses
                membership.status = "active"

            if not all_campuses and campus_links:
                for campus in campus_links:
                    if campus is None:
                        continue
                    exists = db.scalar(
                        select(MembershipCampus).where(
                            MembershipCampus.membership_id == membership.id,
                            MembershipCampus.campus_id == campus.id,
                        )
                    )
                    if not exists:
                        db.add(MembershipCampus(membership_id=membership.id, campus_id=campus.id))

        parent_user = db.scalar(select(User).where(User.email == DEMO_PARENT_EMAIL))
        if not parent_user:
            parent_user = User(
                email=DEMO_PARENT_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Padre Demo",
                is_active=True,
            )
            db.add(parent_user)
            db.flush()
            print(f"Usuario creado: {DEMO_PARENT_EMAIL}")
        else:
            parent_user.password_hash = hash_password(DEMO_PASSWORD)
            print(f"Usuario actualizado: {DEMO_PARENT_EMAIL}")

        parent = db.get(Parent, uuid.UUID(DEMO_PARENT_ID))
        if not parent:
            parent = Parent(
                id=uuid.UUID(DEMO_PARENT_ID),
                school_id=school.id,
                user_id=parent_user.id,
                full_name="Padre Demo",
                email=DEMO_PARENT_EMAIL,
                relation_type="father",
                parent_status="active",
            )
            db.add(parent)
            db.flush()
        else:
            parent.user_id = parent_user.id
            parent.full_name = "Padre Demo"
            parent.email = DEMO_PARENT_EMAIL
            parent.parent_status = "active"

        for student_id in DEMO_CHILD_STUDENT_IDS:
            exists = db.get(
                StudentParent,
                {"student_id": uuid.UUID(student_id), "parent_id": parent.id},
            )
            if not exists:
                db.add(StudentParent(student_id=uuid.UUID(student_id), parent_id=parent.id))

        student_user = db.scalar(select(User).where(User.email == DEMO_STUDENT_EMAIL))
        if not student_user:
            student_user = User(
                email=DEMO_STUDENT_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Estudiante Demo 1",
                is_active=True,
            )
            db.add(student_user)
            db.flush()
            print(f"Usuario creado: {DEMO_STUDENT_EMAIL}")
        else:
            student_user.password_hash = hash_password(DEMO_PASSWORD)
            print(f"Usuario actualizado: {DEMO_STUDENT_EMAIL}")

        student = db.get(Student, uuid.UUID(DEMO_STUDENT_RECORD_ID))
        if not student:
            print(
                f"Registro estudiante {DEMO_STUDENT_RECORD_ID} no encontrado. "
                "Ejecuta migrations/008_seed_demo_students.sql.",
                file=sys.stderr,
            )
            sys.exit(1)
        student.user_id = student_user.id

        db.commit()
        print("Seed demo listo.")
        print(f"  Owner:    {DEMO_OWNER_EMAIL} / {DEMO_PASSWORD}")
        print(f"  Operator: {DEMO_OPERATOR_EMAIL} / {DEMO_PASSWORD} (solo sede-norte)")
        print(f"  Parent:   {DEMO_PARENT_EMAIL} / {DEMO_PASSWORD} (3 hijos en sede-norte)")
        print(f"  Student:  {DEMO_STUDENT_EMAIL} / {DEMO_PASSWORD} (EST-001, sede-norte)")
    finally:
        db.close()


def seed_bulk_students_cmd(
    *,
    count: int,
    schools: int,
    campuses_per_school: int,
    slug_prefix: str,
    reset: bool,
    link_demo_owner: bool,
) -> None:
    db: Session = SessionLocal()
    try:
        if reset:
            removed = reset_scale_data(db, slug_prefix=slug_prefix)
            if removed:
                print(f"Eliminados {removed} colegios scale ({slug_prefix}-*).")

        result = seed_bulk_students(
            db,
            count=count,
            schools=schools,
            campuses_per_school=campuses_per_school,
            slug_prefix=slug_prefix,
            reset=False,
            link_demo_owner=link_demo_owner,
            demo_owner_email=DEMO_OWNER_EMAIL if link_demo_owner else None,
        )
        print("Seed bulk estudiantes listo.")
        print(f"  Colegios:   {result.schools} ({slug_prefix}-01 … {slug_prefix}-{result.schools:02d})")
        print(f"  Sedes:      {result.campuses} ({campuses_per_school} por colegio)")
        print(f"  Estudiantes: {result.students:,} total")
        for i, n in enumerate(result.per_school, start=1):
            print(f"    {slug_prefix}-{i:02d}: {n:,}")
        if link_demo_owner:
            print(f"  Owner vinculado: {DEMO_OWNER_EMAIL} (all_campuses en cada colegio scale)")
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("apply-sql", help=f"Aplicar 001/002 desde {SQL_DIR}")
    sub.add_parser("seed-superadmin", help="Crear o actualizar usuario superadmin")
    sub.add_parser("seed-demo", help="Usuarios owner/operator del colegio demo")

    bulk = sub.add_parser(
        "seed-bulk-students",
        help="Generar estudiantes de prueba repartidos en varios colegios y sedes",
    )
    bulk.add_argument("--count", type=int, default=10_000, help="Total de estudiantes (default: 10000)")
    bulk.add_argument("--schools", type=int, default=10, help="Cantidad de colegios (default: 10)")
    bulk.add_argument(
        "--campuses-per-school",
        type=int,
        default=2,
        help="Sedes por colegio (default: 2)",
    )
    bulk.add_argument(
        "--slug-prefix",
        default=DEFAULT_SLUG_PREFIX,
        help=f"Prefijo slug colegios (default: {DEFAULT_SLUG_PREFIX})",
    )
    bulk.add_argument("--reset", action="store_true", help="Borrar colegios scale-* antes de generar")
    bulk.add_argument(
        "--no-link-demo-owner",
        action="store_true",
        help="No vincular owner@colegio-demo.dev a los colegios scale",
    )

    args = parser.parse_args()
    if args.command == "apply-sql":
        apply_sql_files()
    elif args.command == "seed-superadmin":
        seed_superadmin()
    elif args.command == "seed-demo":
        seed_demo()
    elif args.command == "seed-bulk-students":
        seed_bulk_students_cmd(
            count=args.count,
            schools=args.schools,
            campuses_per_school=args.campuses_per_school,
            slug_prefix=args.slug_prefix,
            reset=args.reset,
            link_demo_owner=not args.no_link_demo_owner,
        )


if __name__ == "__main__":
    main()
