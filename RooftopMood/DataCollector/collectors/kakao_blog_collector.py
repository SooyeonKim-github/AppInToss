from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse
from typing import Any

import requests

from utils import clean_html


class KakaoBlogCollector:
    """Daum 블로그 검색 API를 사용해 카페 후기 Evidence를 수집한다."""

    SEARCH_URL = "https://dapi.kakao.com/v2/search/blog"

    def __init__(self, api_key: str, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"KakaoAK {api_key}"})

    def search(
        self,
        query: str,
        *,
        size: int = 10,
        max_pages: int = 1,
        sort: str = "accuracy",
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        size = max(1, min(int(size), 50))
        max_pages = max(1, min(int(max_pages), 50))

        for page in range(1, max_pages + 1):
            response = self.session.get(
                self.SEARCH_URL,
                params={
                    "query": query,
                    "sort": sort,
                    "page": page,
                    "size": size,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("documents", []):
                results.append(self._normalize(item))
            if payload.get("meta", {}).get("is_end", True):
                break
        return results

    @staticmethod
    def _normalize(item: dict[str, Any]) -> dict[str, Any]:
        url = str(item.get("url") or "").strip()
        host = (urlparse(url).hostname or "").lower()
        is_tistory = host == "tistory.com" or host.endswith(".tistory.com")
        dt = str(item.get("datetime") or "").strip()
        post_date = dt[:10].replace("-", "") if dt else ""
        return {
            "title": clean_html(str(item.get("title") or "")),
            "description": clean_html(str(item.get("contents") or "")),
            "link": url,
            "blogger_name": clean_html(str(item.get("blogname") or "")),
            "blogger_link": "",
            "post_date": post_date,
            "source_host": host,
            "source_kind": "TISTORY" if is_tistory else "DAUM_BLOG",
            "is_tistory": int(is_tistory),
            "collected_at": datetime.now().isoformat(timespec="seconds"),
        }
