from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_has_fixed_brand_copy():
    response = client.get("/api/v1/home")
    assert response.status_code == 200
    body = response.json()
    assert body["app"]["name"] == "루프탑무드"
    assert body["app"]["description"] == "노을이 예쁜 서울 루프탑 카페를 찾아드려요."
    assert len(body["views"]) == 4
    assert "weather" in body["sunset"]
    assert body["sunset"]["weather"]["source"] == "MOCK"


def test_regions_are_dynamic():
    response = client.get("/api/v1/views/HAN_RIVER/regions")
    assert response.status_code == 200
    assert response.json()["regions"]


def test_recommendation_flow():
    regions = client.get("/api/v1/views/HAN_RIVER/regions").json()["regions"]
    region = regions[0]["code"]
    response = client.get(
        "/api/v1/recommendations",
        params={"view": "HAN_RIVER", "region": region},
    )
    assert response.status_code == 200
    items = response.json()["recommendations"]
    assert len(items) <= 3
    if items:
        item = items[0]
        assert "todaySunsetInfo" in item
        assert "bestTime" in item["todaySunsetInfo"]
        assert "노을" not in item["viewDescription"]


def test_sunset_best():
    response = client.get("/api/v1/recommendations/sunset-best")
    assert response.status_code == 200
    assert response.json()["recommendation"]["score"] >= 0


def test_cafe_detail_separates_static_view_and_today_sunset():
    response = client.get("/api/v1/cafes/1")
    assert response.status_code == 200
    body = response.json()
    assert "cafe" in body
    assert "todaySunsetInfo" in body
    assert "노을" not in body["cafe"]["viewDescription"]
    assert body["todaySunsetInfo"]["position"] in {"FRONT", "RIGHT", "LEFT", "OUT_OF_VIEW", "UNKNOWN"}
