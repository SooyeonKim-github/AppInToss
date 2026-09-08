from __future__ import annotations

import logging
from collections import defaultdict

import yaml

from collectors.naver_blog_collector import NaverBlogCollector
from settings import BASE_DIR, settings
from utils import normalize_name, read_csv, write_csv

LOGGER = logging.getLogger(__name__)

EVIDENCE_FIELDS = [
    "cafe_id", "cafe_name", "region_code", "evidence_tag", "search_query", "title", "description",
    "source_url", "blogger_name", "blogger_link", "post_date", "relevance_score", "collected_at",
]

SUMMARY_FIELDS = [
    "cafe_id", "cafe_name", "region_code", "ROOFTOP", "SUNSET", "HAN_RIVER", "CITY", "PALACE", "FOREST",
    "total_evidence", "latest_post_date",
]


class EvidenceCollectionPipeline:
    def __init__(self):
        if not settings.has_naver:
            raise RuntimeError(
                "NAVER API HUB 키가 없습니다. DataCollector/.env에 "
                "NAVER_API_HUB_CLIENT_ID/SECRET을 설정하세요."
            )
        self.collector = NaverBlogCollector(
            settings.naver_client_id,
            settings.naver_client_secret,
            settings.request_timeout_sec,
            settings.naver_api_hub_base_url,
        )

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
            LOGGER.info("[%d/%d] Evidence: %s", idx, len(candidates), cafe_name)
            seen_links: set[tuple[str, str]] = set()

            for tag, queries in templates.items():
                for template in queries:
                    query = template.format(name=cafe_name)
                    try:
                        results = self.collector.search(query, display=settings.naver_blog_display)
                    except Exception as exc:
                        LOGGER.exception("  Blog 검색 실패 [%s]: %s", query, exc)
                        continue

                    for item in results:
                        dedupe_key = (tag, item["link"])
                        if not item["link"] or dedupe_key in seen_links:
                            continue
                        seen_links.add(dedupe_key)
                        relevance = self._relevance_score(cafe_name, query, item["title"], item["description"])
                        evidence_rows.append(
                            {
                                "cafe_id": cafe_id,
                                "cafe_name": cafe_name,
                                "region_code": cafe.get("region_code", ""),
                                "evidence_tag": tag,
                                "search_query": query,
                                "title": item["title"],
                                "description": item["description"],
                                "source_url": item["link"],
                                "blogger_name": item["blogger_name"],
                                "blogger_link": item["blogger_link"],
                                "post_date": item["post_date"],
                                "relevance_score": relevance,
                                "collected_at": item["collected_at"],
                            }
                        )

        summaries = self._build_summary(candidates, evidence_rows)
        output_dir = BASE_DIR / "output"
        write_csv(output_dir / "cafe_evidences.csv", evidence_rows, EVIDENCE_FIELDS)
        write_csv(output_dir / "evidence_summary.csv", summaries, SUMMARY_FIELDS)
        LOGGER.info("Evidence rows=%d", len(evidence_rows))
        return evidence_rows, summaries

    @staticmethod
    def _load_templates() -> dict[str, list[str]]:
        payload = yaml.safe_load((BASE_DIR / "config" / "evidence_queries.yaml").read_text(encoding="utf-8"))
        return payload.get("query_templates", {})

    @staticmethod
    def _relevance_score(cafe_name: str, query: str, title: str, description: str) -> int:
        haystack = normalize_name(f"{title} {description}")
        cafe_key = normalize_name(cafe_name)
        score = 0
        if cafe_key and cafe_key in haystack:
            score += 60
        keywords = ["루프탑", "옥상", "테라스", "노을", "일몰", "한강", "시티", "야경", "궁궐", "경복궁", "창덕궁", "숲", "서울숲", "남산"]
        query_keywords = [kw for kw in keywords if kw in query]
        text = f"{title} {description}"
        if any(kw in text for kw in query_keywords):
            score += 30
        if "서울" in text or "카페" in text:
            score += 10
        return min(score, 100)

    @staticmethod
    def _build_summary(candidates: list[dict], rows: list[dict]) -> list[dict]:
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        latest: dict[str, str] = defaultdict(str)
        for row in rows:
            if int(row.get("relevance_score", 0)) < 60:
                continue
            cafe_id = row["cafe_id"]
            tag = row["evidence_tag"]
            counts[cafe_id][tag] += 1
            post_date = row.get("post_date", "")
            if post_date > latest[cafe_id]:
                latest[cafe_id] = post_date

        summaries: list[dict] = []
        for cafe in candidates:
            cafe_id = cafe["cafe_id"]
            tag_counts = counts[cafe_id]
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
                    "total_evidence": sum(tag_counts.values()),
                    "latest_post_date": latest.get(cafe_id, ""),
                }
            )
        return summaries
