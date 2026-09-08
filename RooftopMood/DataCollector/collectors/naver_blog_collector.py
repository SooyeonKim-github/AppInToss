from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from utils import clean_html


class NaverBlogCollector:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout: float = 10.0,
        base_url: str = "https://naverapihub.apigw.ntruss.com",
    ):
        self.timeout = timeout
        self.search_url = f"{base_url.rstrip('/')}/search/v1/blog"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-NCP-APIGW-API-KEY-ID": client_id,
                "X-NCP-APIGW-API-KEY": client_secret,
            }
        )

    def search(self, query: str, display: int = 10, sort: str = "sim") -> list[dict[str, Any]]:
        response = self.session.get(
            self.search_url,
            params={
                "query": query,
                "display": min(max(display, 1), 100),
                "start": 1,
                "sort": sort,
                "format": "json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [self._normalize(item) for item in response.json().get("items", [])]

    @staticmethod
    def _normalize(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": clean_html(item.get("title", "")),
            "description": clean_html(item.get("description", "")),
            "link": item.get("link", ""),
            "blogger_name": clean_html(item.get("bloggername", "")),
            "blogger_link": item.get("bloggerlink", ""),
            "post_date": item.get("postdate", ""),
            "collected_at": datetime.now().isoformat(timespec="seconds"),
        }
