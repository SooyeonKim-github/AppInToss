import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "seoul_rooftop_cafes.json"


class CafeRepository:
    def __init__(self) -> None:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            self._cafes: list[dict[str, Any]] = json.load(f)

    def all(self) -> list[dict[str, Any]]:
        return list(self._cafes)

    def get(self, cafe_id: int) -> dict[str, Any] | None:
        return next((c for c in self._cafes if c["id"] == cafe_id), None)

    def find_regions_for_view(self, view: str) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = {}
        for cafe in self._cafes:
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
            for cafe in self._cafes
            if cafe.get("active", True)
            and cafe["region"]["code"] == region
            and cafe["views"].get(view, 0) > 0
        ]
