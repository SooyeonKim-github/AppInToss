from pipeline.evidence_collection import EvidenceCollectionPipeline


def test_relevance_score_prefers_cafe_and_keyword():
    score = EvidenceCollectionPipeline._relevance_score(
        "무드카페",
        "무드카페 루프탑",
        "무드카페 루프탑 후기",
        "서울에서 노을이 예쁜 루프탑 카페",
    )
    assert score >= 90
