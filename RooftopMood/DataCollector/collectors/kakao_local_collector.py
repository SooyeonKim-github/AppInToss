from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import requests


class KakaoLocalCollector:
    SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
    ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"

    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"KakaoAK {api_key}"})

    def search(self, query: str, region_code: str, max_pages: int = 45) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            response = self.session.get(
                self.SEARCH_URL,
                params={
                    "query": query,
                    "category_group_code": "CE7",
                    "page": page,
                    "size": 15,
                    "sort": "accuracy",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("documents", []):
                results.append(self._normalize(item, query=query, region_code=region_code))

            if payload.get("meta", {}).get("is_end", True):
                break
            time.sleep(0.05)
        return results

    def geocode(self, address: str) -> tuple[float | None, float | None]:
        if not address:
            return None, None
        response = self.session.get(
            self.ADDRESS_URL,
            params={"query": address},
            timeout=self.timeout,
        )
        response.raise_for_status()
        docs = response.json().get("documents", [])
        if not docs:
            return None, None
        return float(docs[0]["y"]), float(docs[0]["x"])

    @staticmethod
    def _normalize(item: dict[str, Any], query: str, region_code: str) -> dict[str, Any]:
        return {
            "source": "KAKAO",
            "source_place_id": item.get("id", ""),
            "name": item.get("place_name", ""),
            "category": item.get("category_name", ""),
            "phone": item.get("phone", ""),
            "address": item.get("address_name", ""),
            "road_address": item.get("road_address_name", ""),
            "latitude": item.get("y", ""),
            "longitude": item.get("x", ""),
            "region_code": region_code,
            "source_url": item.get("place_url", ""),
            "search_query": query,
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "naver_mapx": "",
            "naver_mapy": "",
        }
