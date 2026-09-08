from __future__ import annotations

import csv
import html
import math
import re
from pathlib import Path
from typing import Iterable

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^0-9a-zA-Z가-힣]")


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = _TAG_RE.sub("", value)
    return _SPACE_RE.sub(" ", value).strip()


def normalize_name(value: str | None) -> str:
    value = clean_html(value).lower()
    for token in ("카페", "cafe", "coffee", "커피", "점"):
        value = value.replace(token, "")
    return _NON_ALNUM_RE.sub("", value)


def normalize_address(value: str | None) -> str:
    value = clean_html(value).lower()
    value = value.replace("서울특별시", "서울")
    return _NON_ALNUM_RE.sub("", value)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
