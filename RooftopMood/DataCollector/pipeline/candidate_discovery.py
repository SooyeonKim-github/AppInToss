from __future__ import annotations

from collections import Counter
import logging

import yaml

from collectors.kakao_local_collector import KakaoAPIError, KakaoLocalCollector
from pipeline.deduplicator import CandidateDeduplicator
from pipeline.region_resolver import RegionResolver
from settings import BASE_DIR, settings
from utils import write_csv

LOGGER = logging.getLogger(__name__)

RAW_FIELDS = [
    "source", "source_place_id", "name", "category", "phone", "address", "road_address",
    "latitude", "longitude", "search_region_code", "region_code",
    "region_resolution_source", "region_distance_m", "region_resolution_confidence",
    "source_url", "search_query", "collected_at", "naver_mapx", "naver_mapy",
]

REJECTED_FIELDS = RAW_FIELDS + ["resolved_region_code", "reject_reason"]

DEDUP_FIELDS = [
    "cafe_id", "name", "category", "phone", "address", "road_address", "latitude", "longitude",
    "region_code", "region_resolution_source", "region_distance_m", "region_resolution_confidence",
    "kakao_place_id", "kakao_url", "naver_url", "providers", "matched_queries",
    "matched_query_count", "region_query_total", "query_hit_ratio", "raw_match_count",
]


class CandidateDiscoveryPipeline:
    """Kakao Local만 사용해 서울 루프탑/뷰 카페 후보를 수집한다."""

    def __init__(self):
        if not settings.has_kakao:
            raise RuntimeError("Kakao REST API 키가 없습니다. DataCollector/.env에 KAKAO_REST_API_KEY를 설정하세요.")
        self.kakao = KakaoLocalCollector(settings.kakao_rest_api_key, settings.request_timeout_sec)
        self.deduplicator = CandidateDeduplicator()
        self.region_resolver = RegionResolver(BASE_DIR / "config" / "regions.yaml")

    def run(self) -> tuple[list[dict], list[dict]]:
        queries = self._load_queries()
        query_totals = Counter(region_code for region_code, _ in queries)
        raw: list[dict] = []
        rejected: list[dict] = []

        for region_code, query in queries:
            LOGGER.info("검색: %s [%s]", query, region_code)
            try:
                search_params = self.region_resolver.search_params(region_code)
                found = self.kakao.search(query, region_code, **search_params)
            except KakaoAPIError as exc:
                if exc.is_auth_or_permission_error:
                    raise RuntimeError(
                        "Kakao Local 인증/권한 오류입니다. "
                        f"{exc}. Kakao Developers의 카카오맵 API 사용 설정과 REST API 키를 확인하세요."
                    ) from exc
                LOGGER.exception("  Kakao 실패: %s", exc)
                continue
            except Exception as exc:
                LOGGER.exception("  Kakao 실패: %s", exc)
                continue

            kept = 0
            for row in found:
                resolution = self.region_resolver.resolve(row)
                resolved_region = str(resolution.get("region_code", "") or "")
                row.update(resolution)
                row["search_region_code"] = region_code

                if resolved_region != region_code:
                    rejected_row = dict(row)
                    rejected_row["resolved_region_code"] = resolved_region
                    rejected_row["reject_reason"] = (
                        "OUT_OF_TARGET_REGION" if resolved_region else str(resolution.get("region_resolution_source", "REGION_UNRESOLVED"))
                    )
                    rejected.append(rejected_row)
                    continue

                raw.append(row)
                kept += 1

            LOGGER.info("  Kakao: %d / 지역검증 통과: %d / 제외: %d", len(found), kept, len(found) - kept)

        if not raw:
            raise RuntimeError("Kakao Local에서 지역 검증을 통과한 후보가 없습니다. regions.yaml의 중심점/반경을 확인하세요.")

        deduped = self.deduplicator.deduplicate(raw, dict(query_totals))
        output_dir = BASE_DIR / "output"
        write_csv(output_dir / "candidates_raw.csv", raw, RAW_FIELDS)
        write_csv(output_dir / "candidates_rejected.csv", rejected, REJECTED_FIELDS)
        write_csv(output_dir / "candidates_deduped.csv", deduped, DEDUP_FIELDS)

        LOGGER.info(
            "Kakao filtered Raw=%d / Rejected=%d / Unique=%d / Duplicate hits=%d",
            len(raw),
            len(rejected),
            len(deduped),
            len(raw) - len(deduped),
        )
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
