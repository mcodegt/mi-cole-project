import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import get_db
from app.main import create_app
from app.services.auth_service import hash_password

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://micole:micole@localhost:5432/micole_test",
)

DEMO_SCHOOL_ID = "d4000001-0000-4000-8000-000000000001"
DEMO_CAMPUS_NORTE = "d4000002-0000-4000-8000-000000000001"
DEMO_CAMPUS_SUR = "d4000002-0000-4000-8000-000000000002"
DEMO_OWNER_EMAIL = "owner@colegio-demo.dev"
DEMO_OPERATOR_EMAIL = "operator@colegio-demo.dev"
DEMO_PASSWORD = "Demo123!"


def _resolve_sql_dir() -> Path:
    env = os.environ.get("MICOLE_SQL_DIR")
    if env:
        return Path(env)
    docs = Path(__file__).resolve().parents[3] / "mi-cole-docs" / "sql"
    if docs.is_dir():
        return docs
    return Path(__file__).resolve().parent.parent / "sql"


def _all_sql_files(sql_dir: Path) -> list[Path]:
    files = sorted(sql_dir.glob("*.sql"))
    migrations = sorted((sql_dir / "migrations").glob("*.sql"))
    return files + migrations


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    sql_dir = _resolve_sql_dir()
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        for path in _all_sql_files(sql_dir):
            conn.execute(text(path.read_text(encoding="utf-8")))
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def superadmin_credentials():
    settings = get_settings()
    return {
        "email": settings.superadmin_email,
        "password": settings.superadmin_password,
    }


@pytest.fixture
def demo_users(db_session: Session):
    import uuid

    from app.models.campus import Campus, MembershipCampus
    from app.models.edu import Parent, Student, StudentParent
    from app.models.rbac import Role, SchoolMembership
    from app.models.user import User

    from app.models.school import School

    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    school = db_session.get(School, school_id)
    school.subscription_plan_id = uuid.UUID("e5000001-0000-4000-8000-000000000002")
    campus_norte = db_session.get(Campus, uuid.UUID(DEMO_CAMPUS_NORTE))
    owner_role = db_session.get(Role, uuid.UUID("d4000003-0000-4000-8000-000000000001"))
    operator_role = db_session.get(Role, uuid.UUID("d4000003-0000-4000-8000-000000000003"))

    specs = (
        (DEMO_OWNER_EMAIL, "Dueño Demo", owner_role, True),
        (DEMO_OPERATOR_EMAIL, "Operador Demo", operator_role, False),
    )
    for email, name, role, all_campuses in specs:
        user = User(
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name=name,
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        membership = SchoolMembership(
            user_id=user.id,
            school_id=school_id,
            role_id=role.id,
            status="active",
            all_campuses=all_campuses,
            default_campus_id=campus_norte.id,
        )
        db_session.add(membership)
        db_session.flush()
        if not all_campuses:
            db_session.add(MembershipCampus(membership_id=membership.id, campus_id=campus_norte.id))

    parent_user = User(
        email="parent@colegio-demo.dev",
        password_hash=hash_password(DEMO_PASSWORD),
        full_name="Padre Demo",
        is_active=True,
    )
    db_session.add(parent_user)
    db_session.flush()
    parent = Parent(
        id=uuid.UUID("f8000004-0000-4000-8000-000000000001"),
        school_id=school_id,
        user_id=parent_user.id,
        full_name="Padre Demo",
        email="parent@colegio-demo.dev",
        relation_type="father",
        parent_status="active",
    )
    db_session.add(parent)
    db_session.flush()
    for student_id in (
        "f8000001-0000-4000-8000-000000000001",
        "f8000001-0000-4000-8000-000000000002",
        "f8000001-0000-4000-8000-000000000003",
    ):
        sid = uuid.UUID(student_id)
        if db_session.get(Student, sid) is None:
            continue
        exists = db_session.get(StudentParent, {"student_id": sid, "parent_id": parent.id})
        if not exists:
            db_session.add(StudentParent(student_id=sid, parent_id=parent.id))

    student_user = User(
        email="student@colegio-demo.dev",
        password_hash=hash_password(DEMO_PASSWORD),
        full_name="Estudiante Demo 1",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.flush()
    student = db_session.get(Student, uuid.UUID("f8000001-0000-4000-8000-000000000001"))
    if student:
        student.user_id = student_user.id

    db_session.flush()
    return {
        "owner": {"email": DEMO_OWNER_EMAIL, "password": DEMO_PASSWORD},
        "operator": {"email": DEMO_OPERATOR_EMAIL, "password": DEMO_PASSWORD},
        "parent": {"email": "parent@colegio-demo.dev", "password": DEMO_PASSWORD},
        "student": {"email": "student@colegio-demo.dev", "password": DEMO_PASSWORD},
        "school_id": DEMO_SCHOOL_ID,
        "campus_norte": DEMO_CAMPUS_NORTE,
        "campus_sur": DEMO_CAMPUS_SUR,
        "parent_id": "f8000004-0000-4000-8000-000000000001",
        "student_id": "f8000001-0000-4000-8000-000000000001",
    }


def staff_login(
    client: TestClient,
    *,
    email: str,
    password: str,
    campus_slug: str,
    school_slug: str = "colegio-demo",
) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
            "portal": "staff",
            "school_slug": school_slug,
            "campus_slug": campus_slug,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()
