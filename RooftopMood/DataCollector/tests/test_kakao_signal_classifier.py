from analyzers.kakao_signal_classifier import KakaoSignalClassifier


def test_kakao_signal_classifier_detects_rooftop_and_han_river_view():
    cafe = {
        "cafe_id": "1",
        "name": "테스트카페",
        "category": "음식점 > 카페",
        "region_code": "YEOUIDO",
        "matched_queries": "여의도 루프탑 카페|여의도 한강뷰 카페|여의도 노을 카페",
        "raw_match_count": "3",
    }

    result = KakaoSignalClassifier().classify(cafe)

    assert result["rooftop_status"] == "PROBABLE"
    assert result["rooftop_confidence"] >= 0.6
    assert result["han_river_score"] >= 3
    assert result["han_river_confidence"] >= 0.65


def test_kakao_signal_classifier_confirms_repeated_rooftop_hits():
    cafe = {
        "cafe_id": "2",
        "name": "옥상정원",
        "category": "카페",
        "region_code": "SEONGSU",
        "matched_queries": "성수 루프탑 카페|성수 옥상 카페|성수 서울숲뷰 카페",
        "raw_match_count": "3",
    }

    result = KakaoSignalClassifier().classify(cafe)

    assert result["rooftop_status"] == "CONFIRMED"
    assert result["forest_score"] >= 3


def test_generic_view_query_does_not_fake_specific_view():
    cafe = {
        "cafe_id": "3",
        "name": "일반카페",
        "category": "카페",
        "region_code": "ITAEWON",
        "matched_queries": "이태원 뷰 좋은 카페",
        "raw_match_count": "1",
    }

    result = KakaoSignalClassifier().classify(cafe)

    assert result["rooftop_status"] == "REJECT"
    assert result["han_river_score"] == 0
    assert result["city_score"] == 0
    assert result["palace_score"] == 0
    assert result["forest_score"] == 0
