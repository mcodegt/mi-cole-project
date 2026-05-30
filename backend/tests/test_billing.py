import io
import uuid

from app.models.billing import PaymentEvidenceFile
from app.services.billing_service import set_school_billing_restricted
from tests.conftest import DEMO_SCHOOL_ID, staff_login
from tests.test_auth import _ensure_superadmin
from tests.test_platform import platform_headers, platform_login


def _staff_headers(client, demo_users):
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


def test_restricted_school_blocks_students(client, demo_users, db_session):
    set_school_billing_restricted(db_session, uuid.UUID(DEMO_SCHOOL_ID), restricted=True)
    headers = _staff_headers(client, demo_users)

    blocked = client.get("/api/v1/students", headers=headers)
    assert blocked.status_code == 403
    assert "facturación" in blocked.json()["detail"].lower()

    allowed = client.get("/api/v1/subscription/dashboard", headers=headers)
    assert allowed.status_code == 200
    assert allowed.json()["billing"]["billing_access_mode"] == "payment_evidence_only"


def test_billing_queue_pagination(client, demo_users, db_session, superadmin_credentials):
    owner_headers = _staff_headers(client, demo_users)
    client.post(
        "/api/v1/subscription/payment-evidence",
        headers=owner_headers,
        files={"file": ("pag.pdf", io.BytesIO(b"pdf"), "application/pdf")},
    )

    _ensure_superadmin(db_session, superadmin_credentials)
    platform = platform_login(client, superadmin_credentials)
    p_headers = platform_headers(platform["access_token"])

    page = client.get("/api/v1/platform/billing/queue?page=1&limit=25", headers=p_headers)
    assert page.status_code == 200
    data = page.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 25


def test_upload_and_approve_restores_access(client, demo_users, db_session, superadmin_credentials):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    set_school_billing_restricted(db_session, school_id, restricted=True)
    owner_headers = _staff_headers(client, demo_users)

    upload = client.post(
        "/api/v1/subscription/payment-evidence",
        headers=owner_headers,
        files={"file": ("comprobante.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"kind": "monthly"},
    )
    assert upload.status_code == 201, upload.text
    evidence_id = upload.json()["id"]

    _ensure_superadmin(db_session, superadmin_credentials)
    platform = platform_login(client, superadmin_credentials)
    p_headers = platform_headers(platform["access_token"])

    queue = client.get("/api/v1/platform/billing/queue", headers=p_headers)
    assert queue.status_code == 200
    assert any(item["id"] == evidence_id for item in queue.json()["items"])

    approve = client.post(
        f"/api/v1/platform/billing/evidence/{evidence_id}/approve",
        headers=p_headers,
    )
    assert approve.status_code == 200
    assert approve.json()["review_status"] == "approved"

    students = client.get("/api/v1/students", headers=owner_headers)
    assert students.status_code == 200

    dash = client.get("/api/v1/subscription/dashboard", headers=owner_headers)
    assert dash.json()["billing"]["billing_access_mode"] == "full"


def test_reject_evidence_with_reason(client, demo_users, db_session, superadmin_credentials):
    school_id = uuid.UUID(DEMO_SCHOOL_ID)
    owner_headers = _staff_headers(client, demo_users)

    upload = client.post(
        "/api/v1/subscription/payment-evidence",
        headers=owner_headers,
        files={"file": ("rechazo.pdf", io.BytesIO(b"data"), "application/pdf")},
    )
    assert upload.status_code == 201
    evidence_id = upload.json()["id"]

    _ensure_superadmin(db_session, superadmin_credentials)
    platform = platform_login(client, superadmin_credentials)
    p_headers = platform_headers(platform["access_token"])

    reject = client.post(
        f"/api/v1/platform/billing/evidence/{evidence_id}/reject",
        headers=p_headers,
        json={"reason": "Monto no coincide con el período"},
    )
    assert reject.status_code == 200
    assert reject.json()["review_status"] == "rejected"
    assert reject.json()["rejection_reason"] == "Monto no coincide con el período"

    evidence = db_session.get(PaymentEvidenceFile, uuid.UUID(evidence_id))
    assert evidence.evidence_status == "rejected"
