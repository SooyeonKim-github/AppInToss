from __future__ import annotations

import logging

import yaml

from collectors.kakao_local_collector import KakaoAPIError, KakaoLocalCollector
from pipeline.deduplicator import CandidateDeduplicator
from settings import BASE_DIR, settings
from utils import write_csv

LOGGER = logging.getLogger(__name__)

RAW_FIELDS = [
    "source", "source_place_id", "name", "category", "phone", "address", "road_address",
    "latitude", "longitude", "region_code", "source_url", "search_query", "collected_at",
    "naver_mapx", "naver_mapy",
]

DEDUP_FIELDS = [
    "cafe_id", "name", "category", "phone", "address", "road_address", "latitude", "longitude",
    "region_code", "kakao_place_id", "kakao_url", "naver_url", "providers", "matched_queries",
    "raw_match_count",
]


class CandidateDiscoveryPipeline:
    """Kakao Local만 사용해 서울 루프탑/뷰 카페 후보를 수집한다."""

    def __init__(self):
        if not settings.has_kakao:
            raise RuntimeError("Kakao REST API 키가 없습니다. DataCollector/.env에 KAKAO_REST_API_KEY를 설정하세요.")
        self.kakao = KakaoLocalCollector(settings.kakao_rest_api_key, settings.request_timeout_sec)
        self.deduplicator = CandidateDeduplicator()

    def run(self) -> tuple[list[dict], list[dict]]:
        queries = self._load_queries()
        raw: list[dict] = []

        for region_code, query in queries:
            LOGGER.info("검색: %s [%s]", query, region_code)
            try:
                found = self.kakao.search(query, region_code)
                raw.extend(found)
                LOGGER.info("  Kakao: %d", len(found))
            except KakaoAPIError as exc:
                if exc.is_auth_or_permission_error:
                    raise RuntimeError(
                        "Kakao Local 인증/권한 오류입니다. "
                        f"{exc}. Kakao Developers의 REST API 키 활성화/호출 허용 IP를 확인하세요."
                    ) from exc
                LOGGER.exception("  Kakao 실패: %s", exc)
            except Exception as exc:
                LOGGER.exception("  Kakao 실패: %s", exc)

        if not raw:
            raise RuntimeError("Kakao Local에서 수집된 후보가 없습니다. API 키/쿼터/검색어를 확인하세요.")

        deduped = self.deduplicator.deduplicate(raw)
        output_dir = BASE_DIR / "output"
        write_csv(output_dir / "candidates_raw.csv", raw, RAW_FIELDS)
        write_csv(output_dir / "candidates_deduped.csv", deduped, DEDUP_FIELDS)

        LOGGER.info("Kakao Raw=%d / Unique=%d / Duplicate hits=%d", len(raw), len(deduped), len(raw) - len(deduped))
        return raw, deduped

    @staticmethod
    def _load_queries() -> list[tuple[str, str]]:
        path = BASE_DIR / "config" / "search_queries.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        rows: list[tuple[str, str]] = []
        for block in payload.get("queries", []):
            region = block["region"]
            for term in block.get("terms", []):
                rows.append((region, term))
        return rows
