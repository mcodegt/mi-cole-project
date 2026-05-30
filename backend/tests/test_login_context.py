import io

from tests.conftest import DEMO_CAMPUS_NORTE, DEMO_CAMPUS_SUR, staff_login


def test_login_context_three_portals_norte(client):
    base = {
        "school_slug": "colegio-demo",
        "campus_slug": "sede-norte",
    }
    staff = client.get("/api/v1/public/login-context", params={**base, "portal": "staff"})
    parent = client.get("/api/v1/public/login-context", params={**base, "portal": "parent"})
    student = client.get("/api/v1/public/login-context", params={**base, "portal": "student"})

    assert staff.status_code == 200
    assert parent.status_code == 200
    assert student.status_code == 200

    titles = {
        staff.json()["branding"]["login_title"],
        parent.json()["branding"]["login_title"],
        student.json()["branding"]["login_title"],
    }
    assert titles == {
        "Personal — Sede Norte",
        "Padres — Sede Norte",
        "Estudiantes — Sede Norte",
    }
    assert staff.json()["login_path"] == "/login/staff/colegio-demo/sede-norte"


def test_login_context_disabled_portal_404(client):
    response = client.get(
        "/api/v1/public/login-context",
        params={
            "school_slug": "colegio-demo",
            "campus_slug": "sede-sur",
            "portal": "parent",
        },
    )
    assert response.status_code == 404


def test_staff_login_blocked_when_portal_disabled(client, demo_users):
    client.patch(
        f"/api/v1/campuses/{DEMO_CAMPUS_NORTE}/portal-branding/staff",
        headers=_owner_headers(client, demo_users),
        json={"login_enabled": False},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": demo_users["owner"]["email"],
            "password": demo_users["owner"]["password"],
            "portal": "staff",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert response.status_code == 403


def test_owner_patch_portal_branding(client, demo_users):
    response = client.patch(
        f"/api/v1/campuses/{DEMO_CAMPUS_NORTE}/portal-branding/parent",
        headers=_owner_headers(client, demo_users),
        json={
            "login_title": "Familias Norte",
            "primary_color_hex": "#ff00aa",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["login_title"] == "Familias Norte"
    assert data["primary_color_hex"] == "#ff00aa"

    ctx = client.get(
        "/api/v1/public/login-context",
        params={
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
            "portal": "parent",
        },
    )
    assert ctx.status_code == 200
    assert ctx.json()["branding"]["login_title"] == "Familias Norte"
    assert ctx.json()["branding"]["primary_color_hex"] == "#ff00aa"


def test_campus_access_links(client, demo_users):
    response = client.get(
        f"/api/v1/campuses/{DEMO_CAMPUS_NORTE}/access-links",
        headers=_owner_headers(client, demo_users),
    )
    assert response.status_code == 200
    links = response.json()
    assert links["staff"] == "/login/staff/colegio-demo/sede-norte"
    assert links["parent"] == "/login/parent/colegio-demo/sede-norte"
    assert links["student"] == "/login/student/colegio-demo/sede-norte"


def test_upload_portal_logo(client, demo_users, tmp_path, monkeypatch):
    from app.config import get_settings
    from app.services import storage_service

    monkeypatch.setattr(
        storage_service,
        "get_storage",
        lambda: storage_service.StorageService(root=tmp_path),
    )
    get_settings.cache_clear()

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = client.post(
        f"/api/v1/campuses/{DEMO_CAMPUS_NORTE}/portal-branding/staff/logo",
        headers=_owner_headers(client, demo_users),
        files={"file": ("logo.png", io.BytesIO(png), "image/png")},
    )
    assert response.status_code == 200
    logo_url = response.json()["logo_url"]
    assert logo_url and "branding-file?key=" in logo_url

    file_resp = client.get(logo_url)
    assert file_resp.status_code == 200


def _owner_headers(client, demo_users):
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
