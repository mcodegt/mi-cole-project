from app.services.auth_service import hash_password
from sqlalchemy import select

from app.models.rbac import PlatformRoleAssignment, Role
from app.models.user import User


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_superadmin(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": superadmin_credentials["email"],
            "password": superadmin_credentials["password"],
            "portal": "platform",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["portal"] == "platform"
    assert data["platform"]["is_superadmin"] is True
    assert "platform.schools.manage" in data["platform"]["permissions"]


def test_me_and_refresh_rotation(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": superadmin_credentials["email"],
            "password": superadmin_credentials["password"],
            "portal": "platform",
        },
    ).json()
    access = login["access_token"]
    refresh_token = login["refresh_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == superadmin_credentials["email"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != refresh_token

    old_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert old_refresh.status_code == 401

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout.status_code == 204

    after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert after_logout.status_code == 401


def test_login_invalid_credentials(client, db_session, superadmin_credentials):
    _ensure_superadmin(db_session, superadmin_credentials)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": superadmin_credentials["email"],
            "password": "wrong-password",
            "portal": "platform",
        },
    )
    assert response.status_code == 401


def _ensure_superadmin(db_session, credentials):
    role = db_session.scalar(select(Role).where(Role.code == "superadmin", Role.scope == "platform"))
    email = credentials["email"].lower()
    user = db_session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(credentials["password"]),
            full_name="Super Admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
    if role:
        existing = db_session.scalar(
            select(PlatformRoleAssignment).where(
                PlatformRoleAssignment.user_id == user.id,
                PlatformRoleAssignment.role_id == role.id,
            )
        )
        if not existing:
            db_session.add(PlatformRoleAssignment(user_id=user.id, role_id=role.id))
    db_session.flush()
