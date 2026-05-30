import pytest
from sqlalchemy import func, select

from app.models.campus import Campus
from app.models.edu import Student
from app.models.school import School
from app.services.scale_seed import reset_scale_data, seed_bulk_students
from tests.conftest import DEMO_OWNER_EMAIL, staff_login


def test_scale_seed_distributes_across_schools_and_campuses(db_session):
    reset_scale_data(db_session, slug_prefix="test-scale")

    result = seed_bulk_students(
        db_session,
        count=200,
        schools=4,
        campuses_per_school=2,
        slug_prefix="test-scale",
        reset=False,
        link_demo_owner=False,
    )

    assert result.students == 200
    assert result.schools == 4
    assert result.campuses == 8
    assert sum(result.per_school) == 200
    assert all(n == 50 for n in result.per_school)

    schools = db_session.scalars(
        select(School).where(School.slug.like("test-scale-%")).order_by(School.slug)
    ).all()
    assert len(schools) == 4

    for school in schools:
        campus_ids = set(
            db_session.scalars(select(Campus.id).where(Campus.school_id == school.id)).all()
        )
        total = db_session.scalar(
            select(func.count()).select_from(Student).where(Student.school_id == school.id)
        )
        assert total == 50
        used_campuses = set(
            db_session.scalars(
                select(Student.campus_id).where(Student.school_id == school.id).distinct()
            ).all()
        )
        assert used_campuses.issubset(campus_ids)
        assert len(used_campuses) == 2

    reset_scale_data(db_session, slug_prefix="test-scale")


def test_scale_school_isolation_in_api(client, demo_users, db_session):
    reset_scale_data(db_session, slug_prefix="test-scale")

    seed_bulk_students(
        db_session,
        count=80,
        schools=2,
        campuses_per_school=2,
        slug_prefix="test-scale",
        reset=False,
        link_demo_owner=True,
        demo_owner_email=DEMO_OWNER_EMAIL,
    )

    schools = db_session.scalars(
        select(School).where(School.slug.like("test-scale-%")).order_by(School.slug)
    ).all()
    assert len(schools) == 2

    campus_id = db_session.scalar(select(Campus.id).where(Campus.school_id == schools[0].id))
    login = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-1",
        school_slug=schools[0].slug,
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": str(schools[0].id),
        "X-Campus-Id": str(campus_id),
        "X-Portal": "staff",
    }

    page = client.get("/api/v1/students?page=1&limit=25", headers=headers).json()
    assert page["total"] == 40
    assert len(page["items"]) == 25
    for item in page["items"]:
        assert item["school_id"] == str(schools[0].id)

    campus_id_2 = db_session.scalar(select(Campus.id).where(Campus.school_id == schools[1].id))
    login2 = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-1",
        school_slug=schools[1].slug,
    )
    headers_other = {
        "Authorization": f"Bearer {login2['access_token']}",
        "X-School-Id": str(schools[1].id),
        "X-Campus-Id": str(campus_id_2),
        "X-Portal": "staff",
    }
    page_other = client.get("/api/v1/students?page=1&limit=25", headers=headers_other).json()
    assert page_other["total"] == 40
    for item in page_other["items"]:
        assert item["school_id"] == str(schools[1].id)

    reset_scale_data(db_session, slug_prefix="test-scale")


@pytest.mark.slow
def test_scale_pagination_page_n(client, demo_users, db_session):
    reset_scale_data(db_session, slug_prefix="test-scale")

    seed_bulk_students(
        db_session,
        count=500,
        schools=5,
        campuses_per_school=2,
        slug_prefix="test-scale",
        reset=False,
        link_demo_owner=True,
        demo_owner_email=DEMO_OWNER_EMAIL,
    )

    school = db_session.scalar(select(School).where(School.slug == "test-scale-01"))
    campus_id = db_session.scalar(select(Campus.id).where(Campus.school_id == school.id))

    login = staff_login(
        client,
        email=demo_users["owner"]["email"],
        password=demo_users["owner"]["password"],
        campus_slug="sede-1",
        school_slug=school.slug,
    )
    headers = {
        "Authorization": f"Bearer {login['access_token']}",
        "X-School-Id": str(school.id),
        "X-Campus-Id": str(campus_id),
        "X-Portal": "staff",
    }

    page1 = client.get("/api/v1/students?page=1&limit=25", headers=headers).json()
    page2 = client.get("/api/v1/students?page=2&limit=25", headers=headers).json()
    assert page1["total"] == 100
    assert len(page1["items"]) == 25
    assert len(page2["items"]) == 25
    assert page1["items"][0]["id"] != page2["items"][0]["id"]

    reset_scale_data(db_session, slug_prefix="test-scale")
