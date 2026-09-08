from __future__ import annotations

import logging

import yaml

from collectors.kakao_local_collector import KakaoLocalCollector
from collectors.naver_local_collector import NaverLocalCollector
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
    def __init__(self):
        self.kakao = KakaoLocalCollector(settings.kakao_rest_api_key, settings.request_timeout_sec) if settings.has_kakao else None
        self.naver = NaverLocalCollector(settings.naver_client_id, settings.naver_client_secret, settings.request_timeout_sec) if settings.has_naver else None
        self.deduplicator = CandidateDeduplicator()

    def run(self) -> tuple[list[dict], list[dict]]:
        queries = self._load_queries()
        raw: list[dict] = []

        if not self.kakao and not self.naver:
            raise RuntimeError("API 키가 없습니다. DataCollector/.env에 Kakao 또는 Naver 키를 설정하세요.")

        for region_code, query in queries:
            LOGGER.info("검색: %s [%s]", query, region_code)
            if self.kakao:
                try:
                    found = self.kakao.search(query, region_code)
                    raw.extend(found)
                    LOGGER.info("  Kakao: %d", len(found))
                except Exception as exc:
                    LOGGER.exception("  Kakao 실패: %s", exc)

            if self.naver:
                try:
                    found = self.naver.search(query, region_code)
                    if self.kakao:
                        self._enrich_naver_coordinates(found)
                    raw.extend(found)
                    LOGGER.info("  Naver: %d", len(found))
                except Exception as exc:
                    LOGGER.exception("  Naver 실패: %s", exc)

        deduped = self.deduplicator.deduplicate(raw)
        output_dir = BASE_DIR / "output"
        write_csv(output_dir / "candidates_raw.csv", raw, RAW_FIELDS)
        write_csv(output_dir / "candidates_deduped.csv", deduped, DEDUP_FIELDS)

        LOGGER.info("Raw=%d / Unique=%d / Removed=%d", len(raw), len(deduped), len(raw) - len(deduped))
        return raw, deduped

    def _enrich_naver_coordinates(self, rows: list[dict]) -> None:
        if not self.kakao:
            return
        for row in rows:
            address = row.get("road_address") or row.get("address")
            if not address:
                continue
            try:
                lat, lon = self.kakao.geocode(address)
                if lat is not None and lon is not None:
                    row["latitude"] = lat
                    row["longitude"] = lon
            except Exception:
                LOGGER.debug("Naver 주소 좌표 보강 실패: %s", address, exc_info=True)

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
