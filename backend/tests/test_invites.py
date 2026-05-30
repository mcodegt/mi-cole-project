import uuid

from tests.conftest import DEMO_CAMPUS_NORTE, DEMO_PASSWORD, DEMO_SCHOOL_ID, staff_login

DEMO_PARENT_NO_LOGIN = "f8000003-0000-4000-8000-000000000001"
DEMO_STUDENT_2 = "f8000001-0000-4000-8000-000000000002"
DEMO_BASICO_PLAN_ID = "e5000001-0000-4000-8000-000000000001"


def _staff_headers(client, demo_users) -> dict:
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


def test_invite_parent_and_login(client, demo_users):
    headers = _staff_headers(client, demo_users)
    email = "padre-invitado@colegio-demo.dev"

    invite = client.post(
        f"/api/v1/parents/{DEMO_PARENT_NO_LOGIN}/invite",
        headers=headers,
        json={"email": email},
    )
    assert invite.status_code == 201, invite.text
    data = invite.json()
    assert data["portal"] == "parent"
    assert "/login/parent/colegio-demo/sede-norte" in data["login_path"]
    assert data["temporary_password"]

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": data["temporary_password"],
            "portal": "parent",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["must_change_password"] is True


def test_invite_parent_already_linked(client, demo_users):
    headers = _staff_headers(client, demo_users)

    response = client.post(
        f"/api/v1/parents/{demo_users['parent_id']}/invite",
        headers=headers,
        json={"email": "otro@colegio-demo.dev"},
    )
    assert response.status_code == 409


def test_invite_student_and_login(client, demo_users):
    headers = _staff_headers(client, demo_users)
    email = "estudiante-invitado@colegio-demo.dev"

    invite = client.post(
        f"/api/v1/students/{DEMO_STUDENT_2}/invite",
        headers=headers,
        json={"email": email},
    )
    assert invite.status_code == 201, invite.text
    data = invite.json()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": data["temporary_password"],
            "portal": "student",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert login.status_code == 200, login.text


def test_invite_student_blocked_when_portal_off(client, demo_users, db_session):
    from app.models.school import School, SubscriptionPlan

    school = db_session.get(School, uuid.UUID(DEMO_SCHOOL_ID))
    school.subscription_plan_id = uuid.UUID(DEMO_BASICO_PLAN_ID)
    db_session.flush()

    headers = _staff_headers(client, demo_users)
    response = client.post(
        f"/api/v1/students/{DEMO_STUDENT_2}/invite",
        headers=headers,
        json={"email": "bloqueado@colegio-demo.dev"},
    )
    assert response.status_code == 403


def test_change_password_clears_flag(client, demo_users):
    headers = _staff_headers(client, demo_users)
    email = "cambio-clave@colegio-demo.dev"

    invite = client.post(
        f"/api/v1/parents/{DEMO_PARENT_NO_LOGIN}/invite",
        headers=headers,
        json={"email": email},
    )
    temp = invite.json()["temporary_password"]

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": temp,
            "portal": "parent",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    ).json()

    auth_headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": login["sid"],
        "X-Campus-Id": login["campus_id"],
        "X-Portal": "parent",
    }
    change = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={"current_password": temp, "new_password": "NuevaClave123!"},
    )
    assert change.status_code == 204

    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    assert me["user"]["must_change_password"] is False


def test_switch_portal_staff_to_parent(client, demo_users, db_session):
    from sqlalchemy import select

    from app.models.edu import Parent
    from app.models.user import User

    owner = db_session.scalar(select(User).where(User.email == demo_users["owner"]["email"]))
    parent = Parent(
        school_id=uuid.UUID(DEMO_SCHOOL_ID),
        user_id=owner.id,
        full_name="Owner como padre",
        email=demo_users["owner"]["email"],
        relation_type="guardian",
        parent_status="active",
    )
    db_session.add(parent)
    db_session.flush()

    staff_login_data = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-norte",
    )
    auth_headers = {
        "Authorization": f"Bearer {staff_login_data['access_token']}",
        "X-School-Id": demo_users["school_id"],
        "X-Campus-Id": demo_users["campus_norte"],
        "X-Portal": "staff",
    }

    switch = client.post(
        "/api/v1/auth/switch-portal",
        headers=auth_headers,
        json={
            "portal": "parent",
            "school_slug": "colegio-demo",
            "campus_slug": "sede-norte",
        },
    )
    assert switch.status_code == 200, switch.text
    assert switch.json()["portal"] == "parent"
    assert "parent" in switch.json()["portals"]
