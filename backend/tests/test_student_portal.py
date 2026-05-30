import uuid

from tests.conftest import DEMO_CAMPUS_NORTE, DEMO_SCHOOL_ID, staff_login

DEMO_STUDENT_EMAIL = "student@colegio-demo.dev"
DEMO_STUDENT_RECORD_ID = "f8000001-0000-4000-8000-000000000001"
DEMO_PASSWORD = "Demo123!"
DEMO_ASSIGNMENT_MATH = "f9000001-0000-4000-8000-000000000001"
DEMO_ASSIGNMENT_READING = "f9000001-0000-4000-8000-000000000002"
DEMO_INTERMEDIO_PLAN_ID = "e5000001-0000-4000-8000-000000000002"


def student_login(client, *, email: str = DEMO_STUDENT_EMAIL, password: str = DEMO_PASSWORD) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
            "portal": "student",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _student_headers(login: dict) -> dict:
    return {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": login["sid"],
        "X-Campus-Id": login["campus_id"],
        "X-Portal": "student",
    }


def test_student_login_success(client, demo_users):
    login = student_login(client)
    assert login["portal"] == "student"
    assert login["stid"] == DEMO_STUDENT_RECORD_ID
    assert login["sid"] == DEMO_SCHOOL_ID


def test_student_dashboard(client, demo_users):
    login = student_login(client)
    headers = _student_headers(login)

    dash = client.get("/api/v1/student/dashboard", headers=headers).json()
    assert dash["student_code"] == "EST-001"
    assert dash["school_slug"] == "colegio-demo"
    assert dash["pending_assignments_count"] >= 1


def test_student_assignments_paginated(client, demo_users):
    login = student_login(client)
    headers = _student_headers(login)

    page = client.get("/api/v1/student/assignments?page=1&limit=10", headers=headers).json()
    assert page["total"] >= 2
    assert len(page["items"]) >= 2
    titles = {a["title"] for a in page["items"]}
    assert "Tarea de Matemáticas — Fracciones" in titles


def test_student_assignment_detail(client, demo_users):
    login = student_login(client)
    headers = _student_headers(login)

    detail = client.get(
        f"/api/v1/student/assignments/{DEMO_ASSIGNMENT_READING}",
        headers=headers,
    ).json()
    assert detail["submission_status"] == "submitted"


def test_student_submit_assignment(client, demo_users):
    login = student_login(client)
    headers = _student_headers(login)

    response = client.post(
        f"/api/v1/student/assignments/{DEMO_ASSIGNMENT_MATH}/submissions",
        headers=headers,
        json={"body": "Resolví los ejercicios 1 al 10."},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "submitted"
    assert "ejercicios" in data["body"]

    duplicate = client.post(
        f"/api/v1/student/assignments/{DEMO_ASSIGNMENT_MATH}/submissions",
        headers=headers,
        json={"body": "Intento duplicado."},
    )
    assert duplicate.status_code == 409


def test_student_submissions_list(client, demo_users):
    login = student_login(client)
    headers = _student_headers(login)

    client.post(
        f"/api/v1/student/assignments/{DEMO_ASSIGNMENT_MATH}/submissions",
        headers=headers,
        json={"body": "Entrega para listado."},
    )

    page = client.get("/api/v1/student/submissions", headers=headers).json()
    assert page["total"] >= 2
    assert all(item["assignment_title"] for item in page["items"])


def test_student_portal_disabled_by_plan(client, demo_users, db_session):
    from app.models.school import School, SubscriptionPlan

    school = db_session.get(School, uuid.UUID(DEMO_SCHOOL_ID))
    plan = db_session.get(SubscriptionPlan, school.subscription_plan_id)
    original = dict(plan.limits)
    plan.limits = {**original, "features": {"parent_portal": True, "student_portal": False}}
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": DEMO_STUDENT_EMAIL,
            "password": DEMO_PASSWORD,
            "portal": "student",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert response.status_code == 403

    plan.limits = original
    db_session.flush()


def test_staff_cannot_access_student_api(client, demo_users):
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
    response = client.get("/api/v1/student/dashboard", headers=headers)
    assert response.status_code == 403
