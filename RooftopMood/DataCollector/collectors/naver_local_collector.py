from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from utils import clean_html


class NaverLocalCollector:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout: float = 10.0,
        base_url: str = "https://naverapihub.apigw.ntruss.com",
    ):
        self.timeout = timeout
        self.search_url = f"{base_url.rstrip('/')}/search/v1/local"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-NCP-APIGW-API-KEY-ID": client_id,
                "X-NCP-APIGW-API-KEY": client_secret,
            }
        )

    def search(self, query: str, region_code: str) -> list[dict[str, Any]]:
        response = self.session.get(
            self.search_url,
            params={
                "query": query,
                "display": 5,
                "start": 1,
                "sort": "random",
                "format": "json",
            },
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
