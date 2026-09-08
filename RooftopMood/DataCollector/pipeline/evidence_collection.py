from __future__ import annotations

import logging
from collections import defaultdict

import yaml

from collectors.kakao_blog_collector import KakaoBlogCollector
from collectors.kakao_local_collector import KakaoAPIError
from settings import BASE_DIR, settings
from utils import normalize_name, read_csv, write_csv

LOGGER = logging.getLogger(__name__)

EVIDENCE_FIELDS = [
    "cafe_id", "cafe_name", "region_code", "evidence_tag", "search_query", "title", "description",
    "source_url", "source_host", "source_kind", "is_tistory", "blogger_name", "blogger_link",
    "post_date", "relevance_score", "collected_at",
]

SUMMARY_FIELDS = [
    "cafe_id", "cafe_name", "region_code", "ROOFTOP", "SUNSET", "HAN_RIVER", "CITY", "PALACE", "FOREST",
    "TISTORY_ROOFTOP", "TISTORY_TOTAL", "total_evidence", "latest_post_date",
]

TAG_KEYWORDS = {
    "ROOFTOP": ("루프탑", "옥상", "테라스", "rooftop"),
    "SUNSET": ("노을", "일몰", "선셋", "해질"),
    "HAN_RIVER": ("한강뷰", "한강 뷰", "한강", "리버뷰"),
    "CITY": ("시티뷰", "시티 뷰", "야경", "도심", "스카이라인"),
    "PALACE": ("궁궐", "경복궁", "창덕궁", "덕수궁"),
    "FOREST": ("숲뷰", "서울숲", "숲", "남산"),
    "DISCOVERY": ("뷰", "전망", "경치"),
}


class EvidenceCollectionPipeline:
    """Kakao Daum Blog Search로 루프탑/뷰 후기 근거를 수집한다.

    Tistory 결과는 별도 표기해 가중치를 줄 수 있지만, Daum 검색의 다른 블로그 결과도
    버리지 않고 보조 Evidence로 보존한다.
    """

    def __init__(self):
        if not settings.has_kakao:
            raise RuntimeError("Kakao REST API 키가 없습니다. DataCollector/.env에 KAKAO_REST_API_KEY를 설정하세요.")
        self.collector = KakaoBlogCollector(settings.kakao_rest_api_key, settings.request_timeout_sec)
        self.region_names = self._load_region_names()

    def run(self, limit: int | None = None) -> tuple[list[dict], list[dict]]:
        candidates_path = BASE_DIR / "output" / "candidates_deduped.csv"
        if not candidates_path.exists():
            raise FileNotFoundError("candidates_deduped.csv가 없습니다. 먼저 `python main.py discover`를 실행하세요.")

        candidates = read_csv(candidates_path)
        if limit:
            candidates = candidates[:limit]

        templates = self._load_templates()
        evidence_rows: list[dict] = []

        for idx, cafe in enumerate(candidates, start=1):
            cafe_id = cafe["cafe_id"]
            cafe_name = cafe["name"]
            region_name = self.region_names.get(cafe.get("region_code", ""), "")
            LOGGER.info("[%d/%d] Kakao Blog Evidence: %s", idx, len(candidates), cafe_name)
            seen_links: set[tuple[str, str]] = set()

            for tag, queries in templates.items():
                for template in queries:
                    query = template.format(name=cafe_name, region=region_name)
                    try:
                        results = self.collector.search(
                            query,
                            size=settings.kakao_blog_display,
                            max_pages=settings.kakao_blog_max_pages,
                        )
                    except KakaoAPIError as exc:
                        if exc.is_auth_or_permission_error:
                            raise RuntimeError(
                                "Kakao Daum Blog Search 인증/권한 오류입니다. "
                                f"{exc}. Kakao Developers의 REST API 키/서비스 설정을 확인하세요."
                            ) from exc
                        LOGGER.exception("  Daum Blog 검색 실패 [%s]: %s", query, exc)
                        continue
                    except Exception as exc:
                        LOGGER.exception("  Daum Blog 검색 실패 [%s]: %s", query, exc)
                        continue

                    for item in results:
                        link = item["link"]
                        dedupe_key = (tag, link)
                        if not link or dedupe_key in seen_links:
                            continue
                        seen_links.add(dedupe_key)
                        relevance = self._relevance_score(
                            cafe_name,
                            region_name,
                            tag,
                            item["title"],
                            item["description"],
                            bool(item.get("is_tistory")),
                        )
                        evidence_rows.append(
                            {
                                "cafe_id": cafe_id,
                                "cafe_name": cafe_name,
                                "region_code": cafe.get("region_code", ""),
                                "evidence_tag": tag,
                                "search_query": query,
                                "title": item["title"],
                                "description": item["description"],
                                "source_url": link,
                                "source_host": item.get("source_host", ""),
                                "source_kind": item.get("source_kind", "DAUM_BLOG"),
                                "is_tistory": item.get("is_tistory", 0),
                                "blogger_name": item.get("blogger_name", ""),
                                "blogger_link": item.get("blogger_link", ""),
                                "post_date": item.get("post_date", ""),
                                "relevance_score": relevance,
                                "collected_at": item.get("collected_at", ""),
                            }
                        )

        summaries = self._build_summary(candidates, evidence_rows)
        output_dir = BASE_DIR / "output"
        write_csv(output_dir / "cafe_evidences.csv", evidence_rows, EVIDENCE_FIELDS)
        write_csv(output_dir / "evidence_summary.csv", summaries, SUMMARY_FIELDS)
        LOGGER.info(
            "Kakao Blog evidence rows=%d | tistory=%d",
            len(evidence_rows),
            sum(int(row.get("is_tistory", 0) or 0) == 1 for row in evidence_rows),
        )
        return evidence_rows, summaries

    @staticmethod
    def _load_templates() -> dict[str, list[str]]:
        payload = yaml.safe_load((BASE_DIR / "config" / "evidence_queries.yaml").read_text(encoding="utf-8"))
        return payload.get("query_templates", {})

    @staticmethod
    def _load_region_names() -> dict[str, str]:
        payload = yaml.safe_load((BASE_DIR / "config" / "regions.yaml").read_text(encoding="utf-8")) or {}
        return {
            code: str(config.get("name", code))
            for code, config in (payload.get("regions") or {}).items()
        }

    @staticmethod
    def _relevance_score(
        cafe_name: str,
        region_name: str,
        tag: str,
        title: str,
        description: str,
        is_tistory: bool,
    ) -> int:
        text = f"{title} {description}".strip()
        haystack = normalize_name(text)
        cafe_key = normalize_name(cafe_name)
        score = 0
        if cafe_key and cafe_key in haystack:
            score += 55
        if region_name and region_name.replace("·", "") in text.replace("·", ""):
            score += 10
        if any(keyword in text.lower() for keyword in TAG_KEYWORDS.get(tag, ())):
            score += 25
        if is_tistory:
            score += 5
        if "카페" in text or "서울" in text:
            score += 5
        return min(score, 100)

    @staticmethod
    def _build_summary(candidates: list[dict], rows: list[dict]) -> list[dict]:
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        tistory_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        latest: dict[str, str] = defaultdict(str)
        seen_sources: dict[str, set[tuple[str, str]]] = defaultdict(set)

        for row in rows:
            if int(row.get("relevance_score", 0) or 0) < 60:
                continue
            cafe_id = row["cafe_id"]
            tag = row["evidence_tag"]
            source_key = (tag, row.get("source_url", ""))
            if source_key in seen_sources[cafe_id]:
                continue
            seen_sources[cafe_id].add(source_key)
            counts[cafe_id][tag] += 1
            if int(row.get("is_tistory", 0) or 0) == 1:
                tistory_counts[cafe_id][tag] += 1
            post_date = row.get("post_date", "")
            if post_date > latest[cafe_id]:
                latest[cafe_id] = post_date

        summaries: list[dict] = []
        for cafe in candidates:
            cafe_id = cafe["cafe_id"]
            tag_counts = counts[cafe_id]
            tistory = tistory_counts[cafe_id]
            summaries.append(
                {
                    "cafe_id": cafe_id,
                    "cafe_name": cafe["name"],
                    "region_code": cafe.get("region_code", ""),
                    "ROOFTOP": tag_counts.get("ROOFTOP", 0),
                    "SUNSET": tag_counts.get("SUNSET", 0),
                    "HAN_RIVER": tag_counts.get("HAN_RIVER", 0),
                    "CITY": tag_counts.get("CITY", 0),
                    "PALACE": tag_counts.get("PALACE", 0),
                    "FOREST": tag_counts.get("FOREST", 0),
                    "TISTORY_ROOFTOP": tistory.get("ROOFTOP", 0),
                    "TISTORY_TOTAL": sum(tistory.values()),
                    "total_evidence": sum(tag_counts.values()),
                    "latest_post_date": latest.get(cafe_id, ""),
                }
            )
        return summaries
