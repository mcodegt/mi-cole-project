from tests.conftest import staff_login


def test_owner_lists_campuses(client, demo_users):
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
    response = client.get("/api/v1/campuses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    slugs = {item["slug"] for item in data["items"]}
    assert slugs == {"sede-norte", "sede-sur"}


def test_operator_only_sees_assigned_campus(client, demo_users):
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
    response = client.get("/api/v1/campuses", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["slug"] == "sede-norte"


def test_operator_403_on_foreign_campus(client, demo_users):
    login = staff_login(
        client,
        email=demo_users["operator"]["email"],
        password=demo_users["operator"]["password"],
        campus_slug="sede-norte",
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_sur"],
        "X-Portal": "staff",
    }
    response = client.get(f"/api/v1/campuses/{demo_users['campus_sur']}", headers=headers)
    assert response.status_code == 403


def test_operator_cannot_create_campus(client, demo_users):
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
    response = client.post(
        "/api/v1/campuses",
        headers=headers,
        json={"name": "Sede Este", "slug": "sede-este"},
    )
    assert response.status_code == 403


def test_wrong_x_school_id_403(client, demo_users):
    login = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-norte",
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": "00000000-0000-4000-8000-000000000099",
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }
    response = client.get("/api/v1/campuses", headers=headers)
    assert response.status_code == 403


def test_owner_can_create_campus(client, demo_users):
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
    response = client.post(
        "/api/v1/campuses",
        headers=headers,
        json={"name": "Sede Este", "slug": "sede-este", "campus_type": "annex"},
    )
    assert response.status_code == 201
    assert response.json()["slug"] == "sede-este"
