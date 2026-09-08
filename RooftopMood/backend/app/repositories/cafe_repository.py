import json
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "seoul_rooftop_cafes.json"


class CafeRepository:
    def __init__(self) -> None:
        self._use_supabase = settings.data_backend.lower() == "supabase"
        self._cafes: list[dict[str, Any]] = []

        if self._use_supabase:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise RuntimeError(
                    "DATA_BACKEND=supabase 인 경우 SUPABASE_URL과 "
                    "SUPABASE_SERVICE_ROLE_KEY가 필요합니다."
                )
        else:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                self._cafes = json.load(f)

    @property
    def _headers(self) -> dict[str, str]:
        key = settings.supabase_service_role_key or ""
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }

    @staticmethod
    def _to_cafe(row: dict[str, Any]) -> dict[str, Any]:
        photos = row.get("cafe_photos") or []
        approved_photo = next(
            (photo for photo in photos if photo.get("status") == "APPROVED"),
            None,
        )
        existing_photo = photos[0] if photos else None

        return {
            "id": row["id"],
            "name": row["name"],
            "region": {
                "code": row["region_code"],
                "name": row["region_name"],
            },
            "address": row["address"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "views": row.get("views") or {},
            "sunsetViewScore": row.get("sunset_view_score", 0),
            "openViewScore": row.get("open_view_score", 0),
            "cafeQualityScore": row.get("cafe_quality_score", 0),
            "viewDescription": row.get("view_description") or "",
            "bestSeatTip": row.get("best_seat_tip") or "",
            "imageUrl": approved_photo.get("image_url") if approved_photo else None,
            "photoStatus": existing_photo.get("status") if existing_photo else None,
            "canUploadPhoto": existing_photo is None,
            "kakaoMapUrl": row.get("kakao_map_url"),
            "active": row.get("active", True),
            "viewDirectionDeg": row.get("view_direction_deg"),
            "viewDirectionConfidence": row.get("view_direction_confidence") or 0.0,
            "viewDirectionSource": row.get("view_direction_source"),
        }

    @staticmethod
    def _decorate_json_cafe(cafe: dict[str, Any]) -> dict[str, Any]:
        result = dict(cafe)
        result.setdefault("photoStatus", None)
        result.setdefault("canUploadPhoto", result.get("imageUrl") is None)
        result.setdefault("kakaoMapUrl", None)
        return result

    def _fetch_supabase_cafes(self) -> list[dict[str, Any]]:
        assert settings.supabase_url is not None
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafes",
            headers=self._headers,
            params={
                "select": "*,cafe_photos(image_url,status)",
                "active": "eq.true",
                "order": "id.asc",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return [self._to_cafe(row) for row in response.json()]

    def all(self) -> list[dict[str, Any]]:
        if self._use_supabase:
            return self._fetch_supabase_cafes()
        return [self._decorate_json_cafe(cafe) for cafe in self._cafes]

    def get(self, cafe_id: int) -> dict[str, Any] | None:
        return next((cafe for cafe in self.all() if cafe["id"] == cafe_id), None)

    def find_regions_for_view(self, view: str) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = {}
        for cafe in self.all():
            if cafe.get("active", True) and cafe["views"].get(view, 0) > 0:
                region = cafe["region"]
                if region["code"] not in buckets:
                    buckets[region["code"]] = {
                        "code": region["code"],
                        "name": region["name"],
                        "cafeCount": 0,
                    }
                buckets[region["code"]]["cafeCount"] += 1
        return sorted(
            buckets.values(),
            key=lambda x: (-x["cafeCount"], x["name"]),
        )

    def find_by_view_region(self, view: str, region: str) -> list[dict[str, Any]]:
        return [
            cafe
            for cafe in self.all()
            if cafe.get("active", True)
            and cafe["region"]["code"] == region
            and cafe["views"].get(view, 0) > 0
        ]
