from pipeline.evidence_collection import EvidenceCollectionPipeline


def test_relevance_score_prefers_cafe_region_keyword_and_tistory():
    score = EvidenceCollectionPipeline._relevance_score(
        "무드카페",
        "성수",
        "ROOFTOP",
        "무드카페 성수 루프탑 후기",
        "서울에서 노을이 예쁜 루프탑 카페",
        True,
    )
    assert score >= 90
