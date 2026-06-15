from __future__ import annotations

import io

from tests.conftest import staff_login


def test_owner_reads_school_profile(client, demo_users):
    headers = _owner_headers(client, demo_users)
    response = client.get("/api/v1/school/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["school_name"] == "Colegio Demo"
    assert data["sidebar_color"].startswith("#")
    assert data["sidebar_text_color"].startswith("#")
    assert data["suggested_text_color"].startswith("#")


def test_owner_updates_sidebar_suggests_text_color(client, demo_users):
    headers = _owner_headers(client, demo_users)
    response = client.patch(
        "/api/v1/school/profile",
        headers=headers,
        json={"sidebar_color": "#ffffff"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sidebar_color"] == "#ffffff"
    assert data["sidebar_text_color"] == "#0f172a"
    assert data["suggested_text_color"] == "#0f172a"


def test_operator_forbidden_on_school_profile_write(client, demo_users):
    login = staff_login(
        client,
        email=demo_users["operator"]["email"],
        password=demo_users["operator"]["password"],
        campus_slug="sede-norte",
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }
    response = client.patch(
        "/api/v1/school/profile",
        headers=headers,
        json={"sidebar_color": "#112233"},
    )
    assert response.status_code == 403


def test_upload_school_logo(client, demo_users, tmp_path, monkeypatch):
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
    headers = _owner_headers(client, demo_users)
    response = client.post(
        "/api/v1/school/profile/logo",
        headers=headers,
        files={"file": ("logo.png", io.BytesIO(png), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["logo_url"] and "branding-file?key=" in response.json()["logo_url"]


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
