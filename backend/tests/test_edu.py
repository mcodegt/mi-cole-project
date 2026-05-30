import uuid

from tests.conftest import DEMO_CAMPUS_SUR, DEMO_SCHOOL_ID, staff_login


def _staff_headers(client, demo_users, *, as_operator: bool = False) -> dict:
    user = demo_users["operator"] if as_operator else demo_users["owner"]
    login = staff_login(
        client,
        email=user["email"],
        password=user["password"],
        campus_slug="sede-norte",
    )
    return {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }


def test_owner_lists_all_demo_students(client, demo_users):
    headers = _staff_headers(client, demo_users)
    response = client.get("/api/v1/students", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 48
    assert len(data["items"]) == 25


def test_owner_students_pagination(client, demo_users):
    headers = _staff_headers(client, demo_users)
    page1 = client.get("/api/v1/students?page=1&limit=25", headers=headers).json()
    page2 = client.get("/api/v1/students?page=2&limit=25", headers=headers).json()
    assert page1["total"] == 48
    assert len(page1["items"]) == 25
    assert len(page2["items"]) == 23


def test_operator_only_sees_norte_students(client, demo_users, db_session):
    from app.models.edu import Student

    db_session.add(
        Student(
            school_id=uuid.UUID(DEMO_SCHOOL_ID),
            campus_id=uuid.UUID(DEMO_CAMPUS_SUR),
            full_name="Estudiante Sur Aislado",
            status="active",
        )
    )
    db_session.flush()

    headers = _staff_headers(client, demo_users, as_operator=True)
    response = client.get("/api/v1/students", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 48
    for item in data["items"]:
        assert item["campus_id"] == demo_users["campus_norte"]


def test_subscription_dashboard_shows_48_of_50(client, demo_users):
    headers = _staff_headers(client, demo_users)
    response = client.get("/api/v1/subscription/dashboard", headers=headers)
    assert response.status_code == 200
    usage = response.json()["usage"]
    assert usage["students"]["current"] == 48
    assert usage["students"]["max"] == 50
    assert response.json()["billing"]["billing_access_mode"] == "full"


def test_parent_without_user_id_listed(client, demo_users):
    headers = _staff_headers(client, demo_users)
    response = client.get("/api/v1/parents", headers=headers)
    assert response.status_code == 200
    emails = [p.get("email") for p in response.json()["items"]]
    assert "padre-sin-login@demo.dev" in emails


def test_owner_lists_team_memberships(client, demo_users):
    headers = _staff_headers(client, demo_users)
    response = client.get("/api/v1/team/memberships", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 2


def test_owner_creates_team_member(client, demo_users, db_session):
    from app.models.rbac import Role

    operator_role = db_session.get(Role, uuid.UUID("d4000003-0000-4000-8000-000000000003"))
    headers = _staff_headers(client, demo_users)
    response = client.post(
        "/api/v1/team/memberships",
        headers=headers,
        json={
            "role_id": str(operator_role.id),
            "member": {
                "email": "nuevo-staff@test.dev",
                "password": "Staff123!",
                "full_name": "Nuevo Staff",
            },
            "all_campuses": False,
            "campus_ids": [demo_users["campus_norte"]],
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_email"] == "nuevo-staff@test.dev"
    assert demo_users["campus_norte"] in data["campus_ids"]


def test_operator_cannot_create_team_member(client, demo_users):
    headers = _staff_headers(client, demo_users, as_operator=True)
    response = client.post(
        "/api/v1/team/memberships",
        headers=headers,
        json={"role_id": "00000000-0000-4000-8000-000000000001"},
    )
    assert response.status_code == 403


def test_crud_student(client, demo_users):
    headers = _staff_headers(client, demo_users)
    create = client.post(
        "/api/v1/students",
        headers=headers,
        json={"full_name": "Nuevo Alumno", "campus_id": demo_users["campus_norte"]},
    )
    assert create.status_code == 201
    student_id = create.json()["id"]

    get_one = client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert get_one.status_code == 200

    patch = client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={"full_name": "Alumno Actualizado"},
    )
    assert patch.status_code == 200
    assert patch.json()["full_name"] == "Alumno Actualizado"

    delete = client.delete(f"/api/v1/students/{student_id}", headers=headers)
    assert delete.status_code == 204
