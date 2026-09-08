from datetime import date
from pathlib import Path

from analyzers.other_view_discovery import OtherViewDiscovery
from analyzers.rooftop_classifier import RooftopClassifier
from analyzers.view_classifier import ViewClassifier
from analyzers.description_generator import TemplateDescriptionGenerator
from analyzers.view_feature_extractor import ViewFeatureExtractor
from analyzers.solar_geometry import SolarGeometryCalculator
from analyzers.sunset_direction_analyzer import SunsetDirectionAnalyzer
from analyzers.view_direction_estimator import ViewDirectionEstimator

BASE = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 9, 8)


def _row(url, title, description, post_date="20260801", relevance=100):
    return {
        "cafe_id": "c1",
        "source_url": url,
        "title": title,
        "description": description,
        "post_date": post_date,
        "relevance_score": relevance,
    }


def test_rooftop_confirmed_with_multiple_recent_sources():
    rows = [
        _row("u1", "루프탑 카페 후기", "옥상 루프탑에서 노을을 봤어요"),
        _row("u2", "서울 카페", "루프탑 테라스 좌석이 있어요"),
        _row("u3", "데이트 카페", "옥상 공간이 탁 트여 있어요"),
    ]
    result = RooftopClassifier(BASE / "config" / "rooftop_keywords.yaml", AS_OF).classify(
        {"cafe_id": "c1", "name": "테스트"}, rows
    )
    assert result["rooftop_status"] == "CONFIRMED"
    assert result["rooftop_confidence"] >= 0.6


def test_recent_rooftop_closure_rejects_when_not_outweighed():
    rows = [
        _row("u1", "예전 후기", "루프탑이 있었어요", "20230101"),
        _row("u2", "최근 후기", "현재 루프탑 폐쇄로 옥상 이용 불가", "20260815"),
    ]
    result = RooftopClassifier(BASE / "config" / "rooftop_keywords.yaml", AS_OF).classify(
        {"cafe_id": "c1", "name": "테스트"}, rows
    )
    assert result["rooftop_status"] == "REJECT"
    assert result["rooftop_recent_negative"] == 1


def test_view_classifier_scores_han_river_and_city():
    rows = [
        _row("u1", "한강뷰 루프탑", "한강이 정면으로 보이고 서울 야경도 예뻐요"),
        _row("u2", "리버뷰 카페", "한강뷰와 도심 스카이라인이 함께 보여요"),
        _row("u3", "야경 카페", "도심뷰가 탁 트여 있어요"),
    ]
    result = ViewClassifier(BASE / "config" / "view_keywords.yaml", AS_OF).classify(
        {"cafe_id": "c1", "name": "테스트"}, rows
    )
    assert result["han_river_score"] >= 3
    assert result["city_score"] >= 3


def test_other_view_discovery_finds_repeated_landmark_views():
    rows = [
        _row("u1", "남산타워뷰 카페", "N서울타워가 잘 보여요"),
        {**_row("u2", "서울 카페", "남산타워 야경이 보여요"), "cafe_id": "c2"},
        {**_row("u3", "성곽뷰 카페", "한양도성이 내려다보여요"), "cafe_id": "c3"},
    ]
    result = OtherViewDiscovery().discover(rows)
    by_name = {row["view_candidate"]: row for row in result}
    assert by_name["남산타워"]["cafe_count"] == 2
    assert by_name["남산타워"]["suggested_action"] == "REVIEW_FOR_CATEGORY"


def test_view_feature_extractor_detects_right_sunset_and_front_hanriver():
    classification = {
        "han_river_score": 5,
        "han_river_confidence": 0.91,
        "city_score": 2,
        "city_confidence": 0.6,
        "palace_score": 0,
        "palace_confidence": 0.2,
        "forest_score": 0,
        "forest_confidence": 0.2,
    }
    rows = [
        _row("u1", "한강뷰 루프탑", "한강이 정면으로 넓게 펼쳐져요. 해질 무렵 오른쪽으로 노을이 내려와요."),
        _row("u2", "노을 명소", "정면 한강뷰가 탁 트여 있고 오른편으로 노을이 보여요."),
    ]
    features = ViewFeatureExtractor().extract(classification, rows)
    assert features["main_view"] == "HAN_RIVER"
    assert features["view_position"] == "FRONT"
    assert features["openness"] == "OPEN"
    assert features["sunset_position"] == "RIGHT"
    assert features["sunset_position_confidence"] >= 0.55


def test_description_generator_creates_static_view_sentence_only():
    features = {
        "main_view": "HAN_RIVER",
        "main_view_score": 5,
        "main_view_confidence": 0.91,
        "view_position": "FRONT",
        "openness": "OPEN",
        "sunset_visible": 1,
        "sunset_position": "RIGHT",
        "sunset_position_confidence": 1.0,
    }
    result = TemplateDescriptionGenerator().generate(features, "CONFIRMED")
    assert result["view_description"] == "한강이 정면으로 넓게 펼쳐지는 탁 트인 루프탑이에요."
    assert "노을" not in result["view_description"]
    assert "오른쪽" not in result["view_description"]
    assert result["description_review_required"] == 0


def test_description_generator_never_embeds_dynamic_sunset_direction():
    features = {
        "main_view": "CITY",
        "main_view_score": 4,
        "main_view_confidence": 0.82,
        "view_position": "UNKNOWN",
        "openness": "OPEN",
        "sunset_visible": 1,
        "sunset_position": "LEFT",
        "sunset_position_confidence": 0.95,
    }
    result = TemplateDescriptionGenerator().generate(features, "CONFIRMED")
    assert result["view_description"] == "서울 도심이 시원하게 내려다보이는 루프탑이에요."
    assert "노을" not in result["view_description"]
    assert "왼쪽" not in result["view_description"]


def test_solar_geometry_seoul_september_sunset():
    result = SolarGeometryCalculator.calculate(date(2026, 9, 8), 37.5665, 126.9780)
    assert result.sunset_time in {"18:52", "18:53"}
    assert 276 <= result.sunset_azimuth_deg <= 280


def test_sunset_direction_front_right_left():
    analyzer = SunsetDirectionAnalyzer()
    candidate = {"latitude": 37.5665, "longitude": 126.9780}
    target = date(2026, 9, 8)

    front = analyzer.analyze(candidate, {"view_direction_deg": 270, "view_direction_confidence": 0.9}, target)
    assert front["sunset_position"] == "FRONT"
    assert front["sunset_alignment_score"] > 90

    right = analyzer.analyze(candidate, {"view_direction_deg": 210, "view_direction_confidence": 0.9}, target)
    assert right["sunset_position"] == "RIGHT"

    left = analyzer.analyze(candidate, {"view_direction_deg": 330, "view_direction_confidence": 0.9}, target)
    assert left["sunset_position"] == "LEFT"


def test_view_direction_estimator_han_river_geometry():
    estimator = ViewDirectionEstimator()
    candidate = {"latitude": 37.556, "longitude": 126.902}
    features = {"main_view": "HAN_RIVER", "landmarks": ""}
    result = estimator.estimate(candidate, features, [])
    assert result["view_direction_source"] == "HAN_RIVER_GEOMETRY"
    assert result["view_direction_target"] == "한강"
    assert 120 <= float(result["view_direction_deg"]) <= 220
