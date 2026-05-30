from tests.conftest import staff_login
from tests.test_auth import _ensure_superadmin


def platform_login(client, credentials):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": credentials["email"],
            "password": credentials["password"],
            "portal": "platform",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def platform_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Portal": "platform",
    }


def test_superadmin_lists_schools(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    response = client.get(
        "/api/v1/platform/schools",
        headers=platform_headers(login["access_token"]),
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


def test_superadmin_creates_school_and_owner_logs_in(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    headers = platform_headers(login["access_token"])

    create = client.post(
        "/api/v1/platform/schools",
        headers=headers,
        json={
            "name": "Colegio Nuevo",
            "slug": "colegio-nuevo-test",
            "owner": {
                "email": "owner-nuevo@test.dev",
                "password": "Owner123!",
                "full_name": "Dueño Nuevo",
            },
        },
    )
    assert create.status_code == 201, create.text
    school = create.json()
    assert school["slug"] == "colegio-nuevo-test"
    assert school["status"] == "active"

    staff = staff_login(
        client,
        email="owner-nuevo@test.dev",
        password="Owner123!",
        school_slug="colegio-nuevo-test",
        campus_slug="sede-principal",
    )
    assert staff["portal"] == "staff"
    assert staff["sid"] == school["id"]
    assert staff["campus_id"] is not None


def test_staff_403_on_platform_schools(client, demo_users):
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
    response = client.get("/api/v1/platform/schools", headers=headers)
    assert response.status_code == 403


def test_superadmin_creates_platform_user(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    headers = platform_headers(login["access_token"])

    response = client.post(
        "/api/v1/platform/users",
        headers=headers,
        json={
            "email": "support@test.dev",
            "password": "Support123!",
            "full_name": "Soporte Test",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "support@test.dev"
    assert data["is_active"] is True


def test_superadmin_patches_school(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)
    login = platform_login(client, superadmin_credentials)
    headers = platform_headers(login["access_token"])

    create = client.post(
        "/api/v1/platform/schools",
        headers=headers,
        json={
            "name": "Colegio Patch",
            "slug": "colegio-patch-test",
            "owner": {
                "email": "owner-patch@test.dev",
                "password": "Owner123!",
                "full_name": "Dueño Patch",
            },
            "notes": "Nota inicial",
        },
    )
    assert create.status_code == 201
    school_id = create.json()["id"]

    patch = client.patch(
        f"/api/v1/platform/schools/{school_id}",
        headers=headers,
        json={"status": "trial", "notes": "En prueba"},
    )
    assert patch.status_code == 200
    updated = patch.json()
    assert updated["status"] == "trial"
    assert updated["notes"] == "En prueba"
