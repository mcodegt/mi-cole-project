import uuid

from tests.conftest import DEMO_CAMPUS_NORTE, DEMO_SCHOOL_ID, staff_login

DEMO_PARENT_EMAIL = "parent@colegio-demo.dev"
DEMO_PARENT_ID = "f8000004-0000-4000-8000-000000000001"
DEMO_PASSWORD = "Demo123!"
DEMO_CHILD_1 = "f8000001-0000-4000-8000-000000000001"
DEMO_CHILD_2 = "f8000001-0000-4000-8000-000000000002"
DEMO_CHILD_FOREIGN = "f8000001-0000-4000-8000-000000000010"


def parent_login(client, *, email: str = DEMO_PARENT_EMAIL, password: str = DEMO_PASSWORD) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
            "portal": "parent",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _parent_headers(login: dict) -> dict:
    return {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": login["sid"],
        "X-Campus-Id": login["campus_id"],
        "X-Portal": "parent",
    }


def test_parent_login_success(client, demo_users):
    login = parent_login(client)
    assert login["portal"] == "parent"
    assert login["pid"] == DEMO_PARENT_ID
    assert login["sid"] == DEMO_SCHOOL_ID


def test_parent_sees_only_linked_children(client, demo_users):
    login = parent_login(client)
    headers = _parent_headers(login)

    children = client.get("/api/v1/parent/children", headers=headers).json()
    assert len(children) == 3
    ids = {c["id"] for c in children}
    assert DEMO_CHILD_1 in ids
    assert DEMO_CHILD_2 in ids
    assert DEMO_CHILD_FOREIGN not in ids


def test_parent_dashboard(client, demo_users):
    login = parent_login(client)
    headers = _parent_headers(login)

    dash = client.get("/api/v1/parent/dashboard", headers=headers).json()
    assert dash["children_count"] == 3
    assert dash["school_slug"] == "colegio-demo"
    assert dash["parent_name"] == "Padre Demo"


def test_parent_assignments_for_child(client, demo_users):
    login = parent_login(client)
    headers = _parent_headers(login)

    assignments = client.get(
        f"/api/v1/parent/assignments?student_id={DEMO_CHILD_1}",
        headers=headers,
    ).json()
    assert len(assignments) >= 2
    titles = {a["title"] for a in assignments}
    assert "Tarea de Matemáticas — Fracciones" in titles


def test_parent_foreign_student_forbidden(client, demo_users):
    login = parent_login(client)
    headers = _parent_headers(login)

    response = client.get(
        f"/api/v1/parent/assignments?student_id={DEMO_CHILD_FOREIGN}",
        headers=headers,
    )
    assert response.status_code == 403


def test_parent_portal_disabled_by_plan(client, demo_users, db_session):
    from app.models.school import School, SubscriptionPlan

    school = db_session.get(School, uuid.UUID(DEMO_SCHOOL_ID))
    plan = db_session.get(SubscriptionPlan, school.subscription_plan_id)
    original = dict(plan.limits)
    plan.limits = {**original, "features": {"parent_portal": False, "student_portal": False}}
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": DEMO_PARENT_EMAIL,
            "password": DEMO_PASSWORD,
            "portal": "parent",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert response.status_code == 403

    plan.limits = original
    db_session.flush()


def test_staff_cannot_access_parent_api(client, demo_users):
    login = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-norte",
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }
    response = client.get("/api/v1/parent/dashboard", headers=headers)
    assert response.status_code == 403
