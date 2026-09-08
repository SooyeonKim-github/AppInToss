from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from utils import clean_html


class NaverLocalCollector:
    SEARCH_URL = "https://openapi.naver.com/v1/search/local.json"

    def __init__(self, client_id: str, client_secret: str, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            }
        )

    def search(self, query: str, region_code: str) -> list[dict[str, Any]]:
        response = self.session.get(
            self.SEARCH_URL,
            params={"query": query, "display": 5, "start": 1, "sort": "random"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        return [self._normalize(item, query=query, region_code=region_code) for item in items]

    @staticmethod
    def _normalize(item: dict[str, Any], query: str, region_code: str) -> dict[str, Any]:
        return {
            "source": "NAVER",
            "source_place_id": "",
            "name": clean_html(item.get("title", "")),
            "category": clean_html(item.get("category", "")),
            "phone": item.get("telephone", ""),
            "address": item.get("address", ""),
            "road_address": item.get("roadAddress", ""),
            "latitude": "",
            "longitude": "",
            "region_code": region_code,
            "source_url": item.get("link", ""),
            "search_query": query,
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "naver_mapx": item.get("mapx", ""),
            "naver_mapy": item.get("mapy", ""),
        }
