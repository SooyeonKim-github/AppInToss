from collectors.kakao_blog_collector import KakaoBlogCollector


def test_tistory_result_is_identified_and_cleaned():
    item = {
        "title": "<b>루프탑</b> 후기",
        "contents": "성수 <b>옥상</b> 테라스",
        "url": "https://rooftop-review.tistory.com/123",
        "blogname": "테스트 블로그",
        "datetime": "2026-09-08T12:34:56.000+09:00",
    }

    result = KakaoBlogCollector._normalize(item)

    assert result["title"] == "루프탑 후기"
    assert result["description"] == "성수 옥상 테라스"
    assert result["source_kind"] == "TISTORY"
    assert result["is_tistory"] == 1
    assert result["post_date"] == "20260908"


def test_non_tistory_blog_is_kept_as_secondary_evidence():
    item = {
        "title": "카페 후기",
        "contents": "한강뷰가 보여요",
        "url": "https://example.com/post/1",
        "blogname": "외부 블로그",
        "datetime": "2026-09-01T00:00:00.000+09:00",
    }

    result = KakaoBlogCollector._normalize(item)

    assert result["source_kind"] == "DAUM_BLOG"
    assert result["is_tistory"] == 0
