def test_public_school_search_finds_demo(client):
    response = client.get("/api/v1/public/schools/search", params={"q": "demo"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    slugs = {item["slug"] for item in data["items"]}
    assert "colegio-demo" in slugs
    demo = next(item for item in data["items"] if item["slug"] == "colegio-demo")
    campus_slugs = {campus["slug"] for campus in demo["campuses"]}
    assert "sede-norte" in campus_slugs


def test_public_school_search_requires_min_length(client):
    response = client.get("/api/v1/public/schools/search", params={"q": "a"})
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_public_school_search_no_auth_required(client):
    response = client.get("/api/v1/public/schools/search", params={"q": "colegio"})
    assert response.status_code == 200
