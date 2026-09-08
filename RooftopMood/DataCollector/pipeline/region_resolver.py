from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from utils import haversine_m


@dataclass(frozen=True)
class RegionConfig:
    code: str
    name: str
    latitude: float
    longitude: float
    search_radius_m: int
    accept_radius_m: int
    fallback_radius_m: int
    address_keywords: tuple[str, ...]


class RegionResolver:
    """카카오 검색어가 아니라 실제 주소/좌표로 앱의 지역 코드를 결정한다.

    1. 주소 키워드가 맞고 중심점 허용 반경 안에 있는 지역을 우선한다.
    2. 여러 지역이 겹치면 더 구체적인 주소 키워드가 있는 지역을 우선한다.
    3. 주소 키워드가 없더라도 중심점 아주 가까이에 있으면 fallback을 허용한다.

    검색 단계에서도 같은 중심점/반경을 Kakao Local의 x/y/radius에 전달해
    애초에 엉뚱한 서울 전역 결과가 섞이는 양을 줄인다.
    """

    def __init__(self, config_path: Path):
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        self.regions: dict[str, RegionConfig] = {}
        for code, raw in (payload.get("regions") or {}).items():
            center = raw.get("center") or {}
            self.regions[code] = RegionConfig(
                code=code,
                name=str(raw.get("name", code)),
                latitude=float(center["latitude"]),
                longitude=float(center["longitude"]),
                search_radius_m=int(raw.get("search_radius_m", 3000)),
                accept_radius_m=int(raw.get("accept_radius_m", raw.get("search_radius_m", 3000))),
                fallback_radius_m=int(raw.get("fallback_radius_m", 1000)),
                address_keywords=tuple(str(x).strip() for x in raw.get("address_keywords", []) if str(x).strip()),
            )

    def search_params(self, region_code: str) -> dict[str, float | int]:
        region = self.regions[region_code]
        return {
            "x": region.longitude,
            "y": region.latitude,
            "radius_m": region.search_radius_m,
        }

    def resolve(self, row: dict[str, Any]) -> dict[str, Any]:
        lat, lon = self._coords(row)
        if lat is None or lon is None:
            return self._empty("NO_COORDINATES")

        address = self._address_text(row)
        if "서울" not in address:
            return self._empty("OUTSIDE_SEOUL")

        keyword_matches: list[tuple[int, float, RegionConfig, str]] = []
        distances: list[tuple[float, RegionConfig]] = []

        for region in self.regions.values():
            distance = haversine_m(lat, lon, region.latitude, region.longitude)
            distances.append((distance, region))
            matched = [keyword for keyword in region.address_keywords if keyword in address]
            if matched and distance <= region.accept_radius_m:
                # "종로구"보다 "삼청동"처럼 더 긴/구체적인 키워드를 우선한다.
                best_keyword = max(matched, key=len)
                keyword_matches.append((len(best_keyword), distance, region, best_keyword))

        if keyword_matches:
            specificity, distance, region, keyword = sorted(
                keyword_matches,
                key=lambda item: (-item[0], item[1], item[2].code),
            )[0]
            return {
                "region_code": region.code,
                "region_resolution_source": f"ADDRESS:{keyword}",
                "region_distance_m": round(distance),
                "region_resolution_confidence": 0.95 if specificity >= 4 else 0.90,
            }

        distance, region = min(distances, key=lambda item: item[0])
        if distance <= region.fallback_radius_m:
            return {
                "region_code": region.code,
                "region_resolution_source": "COORDINATE_FALLBACK",
                "region_distance_m": round(distance),
                "region_resolution_confidence": 0.70,
            }

        return self._empty("NO_REGION_MATCH", distance=distance)

    @staticmethod
    def _coords(row: dict[str, Any]) -> tuple[float | None, float | None]:
        try:
            return float(row.get("latitude")), float(row.get("longitude"))
        except (TypeError, ValueError):
            return None, None

    @staticmethod
    def _address_text(row: dict[str, Any]) -> str:
        return " ".join(
            str(value or "").strip()
            for value in (row.get("road_address"), row.get("address"))
            if str(value or "").strip()
        )

    @staticmethod
    def _empty(reason: str, distance: float | None = None) -> dict[str, Any]:
        return {
            "region_code": "",
            "region_resolution_source": reason,
            "region_distance_m": "" if distance is None else round(distance),
            "region_resolution_confidence": 0.0,
        }
