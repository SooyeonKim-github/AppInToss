from analyzers.kakao_signal_classifier import KakaoSignalClassifier


def test_local_plus_blog_evidence_can_be_strong_probable():
    cafe = {
        "cafe_id": "1",
        "name": "테스트카페",
        "category": "음식점 > 카페",
        "region_code": "YEOUIDO",
        "latitude": "37.5300",
        "longitude": "126.9250",
        "matched_queries": "여의도 루프탑 카페|여의도 한강뷰 카페|여의도 노을 카페",
        "matched_query_count": "3",
        "region_query_total": "3",
        "query_hit_ratio": "1.0",
    }
    evidence = {
        "ROOFTOP": "2",
        "HAN_RIVER": "2",
        "SUNSET": "1",
        "TISTORY_ROOFTOP": "1",
        "TISTORY_TOTAL": "2",
    }

    result = KakaoSignalClassifier().classify(cafe, evidence)

    assert result["rooftop_status"] == "STRONG_PROBABLE"
    assert result["rooftop_confidence"] >= 0.72
    assert result["han_river_score"] >= 4
    assert result["han_river_confidence"] >= 0.6


def test_repeated_local_hits_never_auto_confirm():
    cafe = {
        "cafe_id": "2",
        "name": "옥상정원",
        "category": "카페",
        "region_code": "SEONGSU",
        "latitude": "37.545",
        "longitude": "127.045",
        "matched_queries": "성수 루프탑 카페|성수 옥상 카페|성수 서울숲뷰 카페",
        "matched_query_count": "3",
        "region_query_total": "4",
        "query_hit_ratio": "0.75",
    }

    result = KakaoSignalClassifier().classify(cafe, {})

    assert result["rooftop_status"] == "PROBABLE"
    assert result["rooftop_status"] != "CONFIRMED"


def test_single_local_rooftop_hit_without_blog_stays_review():
    cafe = {
        "cafe_id": "3",
        "name": "일반카페",
        "category": "카페",
        "region_code": "HANNAM",
        "matched_queries": "한남 루프탑 카페",
        "matched_query_count": "1",
        "region_query_total": "3",
        "query_hit_ratio": "0.333",
    }

    result = KakaoSignalClassifier().classify(cafe, {})

    assert result["rooftop_status"] == "REVIEW"
    assert result["rooftop_confidence"] < 0.5


def test_generic_view_query_does_not_fake_specific_view():
    cafe = {
        "cafe_id": "4",
        "name": "일반카페",
        "category": "카페",
        "region_code": "ITAEWON",
        "matched_queries": "이태원 뷰 좋은 카페",
        "matched_query_count": "1",
        "region_query_total": "3",
        "query_hit_ratio": "0.333",
    }

    result = KakaoSignalClassifier().classify(cafe, {})

    assert result["rooftop_status"] == "REJECT"
    assert result["han_river_score"] == 0
    assert result["city_score"] == 0
    assert result["palace_score"] == 0
    assert result["forest_score"] == 0


def test_signal_summary_tracks_independent_query_families_and_blog_counts():
    cafe = {
        "cafe_id": "5",
        "name": "테스트",
        "region_code": "YEOUIDO",
        "matched_queries": "여의도 루프탑 카페|여의도 한강뷰 카페|여의도 노을 카페",
        "matched_query_count": "3",
        "region_query_total": "3",
        "query_hit_ratio": "1.0",
    }
    evidence = {"ROOFTOP": "2", "HAN_RIVER": "1", "TISTORY_ROOFTOP": "1", "TISTORY_TOTAL": "1"}

    summary = KakaoSignalClassifier().signal_summary(cafe, evidence)

    assert summary["query_family_count"] == 3
    assert summary["query_families"] == "HAN_RIVER|ROOFTOP|SUNSET"
    assert summary["blog_rooftop_evidence"] == 2
    assert summary["tistory_rooftop_evidence"] == 1
