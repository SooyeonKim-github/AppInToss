from pipeline.deduplicator import CandidateDeduplicator


def test_same_kakao_id_is_merged():
    rows = [
        {"source": "KAKAO", "source_place_id": "1", "name": "테스트카페", "road_address": "서울 용산구 1", "latitude": "37.5", "longitude": "126.9", "region_code": "A", "search_query": "q1"},
        {"source": "KAKAO", "source_place_id": "1", "name": "테스트 카페", "road_address": "서울 용산구 1", "latitude": "37.5", "longitude": "126.9", "region_code": "A", "search_query": "q2"},
    ]
    result = CandidateDeduplicator().deduplicate(rows)
    assert len(result) == 1
    assert result[0]["raw_match_count"] == 2


def test_cross_provider_name_address_is_merged():
    rows = [
        {"source": "KAKAO", "source_place_id": "1", "name": "ABC 카페", "road_address": "서울 마포구 월드컵로 1", "latitude": "37.5", "longitude": "126.9", "region_code": "A", "search_query": "q1", "source_url": "k"},
        {"source": "NAVER", "source_place_id": "", "name": "ABC카페", "road_address": "서울특별시 마포구 월드컵로 1", "latitude": "37.5", "longitude": "126.9", "region_code": "A", "search_query": "q2", "source_url": "n"},
    ]
    result = CandidateDeduplicator().deduplicate(rows)
    assert len(result) == 1
    assert result[0]["providers"] == "KAKAO|NAVER"
