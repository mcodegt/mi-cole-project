import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.school import School, SubscriptionPlan
from app.services.plan_limits import (
    PlanLimitError,
    assert_can_add_parent,
    assert_can_add_student,
    assert_can_add_team_member,
    get_plan_limits_usage_for_school,
)
from tests.conftest import DEMO_SCHOOL_ID, staff_login
from tests.test_auth import _ensure_superadmin
from tests.test_platform import platform_headers, platform_login


PLAN_LIMITED_ID = uuid.UUID("e5000001-0000-4000-8000-000000000099")


@pytest.fixture
def limited_plan(db_session):
    from sqlalchemy import delete

    from app.models.edu import Parent, Student

    plan = SubscriptionPlan(
        id=PLAN_LIMITED_ID,
        code="test-limited",
        name="Test Limitado",
        tier="basic",
        is_active=True,
        is_public=False,
        limits={"max_team_members": 2, "max_students": 2, "max_parents": 2},
        metadata_={},
    )
    db_session.add(plan)
    school = db_session.get(School, uuid.UUID(DEMO_SCHOOL_ID))
    school.subscription_plan_id = plan.id
    db_session.execute(delete(Student).where(Student.school_id == uuid.UUID(DEMO_SCHOOL_ID)))
    db_session.execute(delete(Parent).where(Parent.school_id == uuid.UUID(DEMO_SCHOOL_ID)))
    db_session.flush()
    return plan


def _staff_headers(client: TestClient, demo_users) -> dict:
    login = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-norte",
    )
    return {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }


def test_assert_can_add_student_blocks_at_limit(db_session, limited_plan):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    from app.models.edu import Student

    for i in range(2):
        db_session.add(Student(school_id=school_id, full_name=f"Alumno {i}"))
    db_session.flush()

    with pytest.raises(PlanLimitError) as exc:
        assert_can_add_student(db_session, school_id)
    assert "2/2 estudiantes" in exc.value.detail


def test_assert_can_add_team_member(db_session, limited_plan, demo_users):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    with pytest.raises(PlanLimitError) as exc:
        assert_can_add_team_member(db_session, school_id)
    assert "miembros del equipo" in exc.value.detail


def test_assert_can_add_parent(db_session, limited_plan):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    from app.models.edu import Parent

    for i in range(2):
        db_session.add(Parent(school_id=school_id, full_name=f"Padre {i}"))
    db_session.flush()

    with pytest.raises(PlanLimitError) as exc:
        assert_can_add_parent(db_session, school_id)
    assert "2/2 padres" in exc.value.detail


def test_get_plan_limits_usage(db_session, limited_plan):
    usage = get_plan_limits_usage_for_school(db_session, uuid.UUID(DEMO_SCHOOL_ID))
    assert usage.plan is not None
    assert usage.plan.code == "test-limited"
    assert usage.usage["students"].max == 2
    assert usage.usage["students"].current == 0


def test_student_post_403_on_limit(client, demo_users, limited_plan):
    headers = _staff_headers(client, demo_users)
    for i in range(2):
        resp = client.post(
            "/api/v1/students",
            headers=headers,
            json={"full_name": f"Estudiante {i}"},
        )
        assert resp.status_code == 201, resp.text

    blocked = client.post(
        "/api/v1/students",
        headers=headers,
        json={"full_name": "Estudiante 3"},
    )
    assert blocked.status_code == 403
    assert "estudiantes" in blocked.json()["detail"]


def test_subscription_dashboard(client, demo_users, limited_plan):
    headers = _staff_headers(client, demo_users)
    resp = client.get("/api/v1/subscription/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"]["code"] == "test-limited"
    assert data["usage"]["students"]["max"] == 2


def test_platform_patch_plan_updates_limits(
    client, db_session, superadmin_credentials, demo_users, limited_plan
):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    headers = platform_headers(login["access_token"])

    patch = client.patch(
        f"/api/v1/platform/subscription-plans/{PLAN_LIMITED_ID}",
        headers=headers,
        json={"limits": {"max_students": 5, "max_team_members": 2, "max_parents": 2}},
    )
    assert patch.status_code == 200

    staff_headers = _staff_headers(client, demo_users)
    dash = client.get("/api/v1/subscription/dashboard", headers=staff_headers)
    assert dash.json()["usage"]["students"]["max"] == 5


def test_platform_list_and_create_plan(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    headers = platform_headers(login["access_token"])

    listing = client.get("/api/v1/platform/subscription-plans", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 3

    create = client.post(
        "/api/v1/platform/subscription-plans",
        headers=headers,
        json={
            "code": "custom-test",
            "name": "Custom Test",
            "limits": {"max_students": 10},
        },
    )
    assert create.status_code == 201
    assert create.json()["limits"]["max_students"] == 10


def test_no_plan_means_unlimited(db_session):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    school = db_session.get(School, school_id)
    school.subscription_plan_id = None
    db_session.flush()

    assert_can_add_student(db_session, school_id)

    usage = get_plan_limits_usage_for_school(db_session, school_id)
    assert usage.plan is None
    assert usage.usage["students"].max is None
