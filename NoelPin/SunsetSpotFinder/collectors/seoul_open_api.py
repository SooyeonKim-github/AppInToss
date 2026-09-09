from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass
class SeoulApiSpec:
    service: str
    result_key: str | None = None
    page_size: int = 1000


class SeoulOpenApiClient:
    """Generic Seoul Open Data Plaza JSON pager."""

    def __init__(self, api_key: str | None = None, timeout_sec: int = 20):
        self.api_key = api_key or os.getenv("SEOUL_OPEN_DATA_API_KEY", "")
        self.timeout_sec = timeout_sec

    def fetch(self, spec: SeoulApiSpec, max_rows: int | None = None) -> pd.DataFrame:
        if not self.api_key:
            raise RuntimeError("SEOUL_OPEN_DATA_API_KEY is not set")
        start = 1
        rows: list[dict[str, Any]] = []
        while True:
            end = start + spec.page_size - 1
            url = f"http://openapi.seoul.go.kr:8088/{self.api_key}/json/{spec.service}/{start}/{end}/"
            response = requests.get(url, timeout=self.timeout_sec)
            response.raise_for_status()
            payload = response.json()
            root = payload.get(spec.result_key or spec.service) or {}
            page = root.get("row") or []
            if not page:
                break
            rows.extend(page)
            total = int(root.get("list_total_count") or len(rows))
            if max_rows and len(rows) >= max_rows:
                rows = rows[:max_rows]
                break
            if len(rows) >= total:
                break
            start = end + 1
        return pd.DataFrame(rows)
