from __future__ import annotations

from datetime import date, datetime
import re


def compact_text(*parts: str | None) -> str:
    text = " ".join(part or "" for part in parts).lower()
    return re.sub(r"\s+", " ", text).strip()


def parse_post_date(value: str | None) -> date | None:
    if not value:
        return None
    raw = re.sub(r"[^0-9]", "", value)
    if len(raw) < 8:
        return None
    try:
        return datetime.strptime(raw[:8], "%Y%m%d").date()
    except ValueError:
        return None


def recency_multiplier(post_date: str | None, as_of: date | None = None) -> float:
    current = as_of or date.today()
    parsed = parse_post_date(post_date)
    if parsed is None:
        return 0.55
    days = max((current - parsed).days, 0)
    if days <= 183:
        return 1.0
    if days <= 365:
        return 0.8
    if days <= 730:
        return 0.5
    return 0.2


def relevance_multiplier(value: str | int | None) -> float:
    try:
        score = int(value or 0)
    except (TypeError, ValueError):
        score = 0
    if score < 60:
        return 0.0
    return max(0.6, min(score / 100.0, 1.0))


def count_distinct_sources(rows: list[dict]) -> int:
    return len({row.get("source_url", "") for row in rows if row.get("source_url")})
