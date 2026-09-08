from __future__ import annotations

import logging
from typing import Any

import requests
import yaml

from settings import BASE_DIR, settings
from utils import read_csv

LOGGER = logging.getLogger(__name__)

PUBLISHABLE_ROOFTOP_STATUSES = {"CONFIRMED", "PROBABLE"}
VIEW_COLUMNS = {
    "HAN_RIVER": "han_river_score",
    "CITY": "city_score",
    "PALACE": "palace_score",
    "FOREST": "forest_score",
}


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _score(value: Any) -> int:
    parsed = _to_float(value, 0.0) or 0.0
    return max(0, min(5, round(parsed)))


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


class SupabasePublishPipeline:
    def __init__(self) -> None:
        self.region_names = self._load_region_names()

    @staticmethod
    def _load_region_names() -> dict[str, str]:
        path = BASE_DIR / "config" / "regions.yaml"
        with path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}
        return {
            code: str(config.get("name", code))
            for code, config in (payload.get("regions") or {}).items()
        }

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        }

    def _transform(self, row: dict[str, Any], include_review: bool) -> dict[str, Any] | None:
        rooftop_status = str(row.get("rooftop_status", "")).strip().upper()
        if rooftop_status not in PUBLISHABLE_ROOFTOP_STATUSES:
            return None
        if _truthy(row.get("description_review_required")) and not include_review:
            return None

        name = str(row.get("name", "")).strip()
        region_code = str(row.get("region_code", "")).strip()
        address = str(row.get("road_address") or row.get("address") or "").strip()
        latitude = _to_float(row.get("latitude"))
        longitude = _to_float(row.get("longitude"))
        view_description = str(row.get("view_description", "")).strip()

        if not all((name, region_code, address, view_description)):
            return None
        if latitude is None or longitude is None:
            return None

        kakao_place_id = str(row.get("kakao_place_id", "")).strip()
        cafe_id = str(row.get("cafe_id", "")).strip()
        external_place_id = kakao_place_id or cafe_id
        if not external_place_id:
            return None

        views = {
            view_code: _score(row.get(column))
            for view_code, column in VIEW_COLUMNS.items()
        }
        main_view_score = _score(row.get("main_view_score"))

        return {
            "external_source": "KAKAO" if kakao_place_id else "COLLECTOR",
            "external_place_id": external_place_id,
            "name": name,
            "region_code": region_code,
            "region_name": self.region_names.get(region_code, region_code),
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "views": views,
            # 아직 전용 카페 품질 점수가 없으므로 중립값을 사용하고,
            # 실제 수집 지표가 추가되면 이 값을 교체한다.
            "sunset_view_score": main_view_score,
            "open_view_score": 3,
            "cafe_quality_score": 3,
            "view_description": view_description,
            "best_seat_tip": "",
            "kakao_map_url": str(row.get("kakao_url", "")).strip() or None,
            "active": True,
            "view_direction_deg": _to_float(row.get("view_direction_deg")),
            "view_direction_confidence": _to_float(row.get("view_direction_confidence"), 0.0) or 0.0,
            "view_direction_source": str(row.get("view_direction_source", "")).strip() or None,
        }

    def run(
        self,
        *,
        dry_run: bool = False,
        include_review: bool = False,
        limit: int | None = None,
    ) -> dict[str, int]:
        source = BASE_DIR / "output" / "cafe_db_ready.csv"
        if not source.exists():
            raise FileNotFoundError(
                "cafe_db_ready.csv가 없습니다. 먼저 `python main.py describe`를 실행하세요."
            )

        rows = read_csv(source)
        transformed = [
            item
            for row in rows
            if (item := self._transform(row, include_review)) is not None
        ]
        if limit is not None:
            transformed = transformed[: max(0, limit)]

        result = {
            "source": len(rows),
            "publishable": len(transformed),
            "published": 0,
        }
        LOGGER.info(
            "Supabase publish preview | source=%d publishable=%d dry_run=%s",
            result["source"],
            result["publishable"],
            dry_run,
        )

        if dry_run or not transformed:
            return result
        if not settings.has_supabase:
            raise RuntimeError(
                "SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY를 DataCollector/.env에 설정하세요."
            )

        endpoint = f"{settings.supabase_url.rstrip('/')}/rest/v1/cafes"
        batch_size = 100
        for start in range(0, len(transformed), batch_size):
            batch = transformed[start : start + batch_size]
            response = requests.post(
                endpoint,
                headers=self._headers,
                params={"on_conflict": "external_place_id"},
                json=batch,
                timeout=settings.request_timeout_sec,
            )
            response.raise_for_status()
            result["published"] += len(response.json())

        LOGGER.info("Supabase publish complete | published=%d", result["published"])
        return result
