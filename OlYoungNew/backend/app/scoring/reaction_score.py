from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Mapping

WEIGHTS = {"review_velocity": 0.35, "rating": 0.15, "discount": 0.10, "exposure": 0.15, "new_badge": 0.10, "freshness": 0.15}


def _value(mapping: Mapping, key: str, default=None):
    try:
        value = mapping[key]
    except (KeyError, TypeError, IndexError):
        return default
    return default if value is None and default is not None else value


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def review_velocity_score(latest: Mapping, previous: Mapping | None) -> tuple[float, float]:
    latest_count = _value(latest, "review_count")
    if latest_count is None:
        return 35.0, 0.0
    latest_time = _parse_dt(_value(latest, "collected_at"))
    previous_count = _value(previous, "review_count") if previous else None
    previous_time = _parse_dt(_value(previous, "collected_at")) if previous else None
    if latest_time is None:
        return 40.0, 0.0
    if previous_count is None or previous_time is None:
        first_seen = _parse_dt(_value(latest, "first_seen_at"))
        if first_seen is None:
            return 40.0, 0.0
        age_days = max((latest_time - first_seen).total_seconds() / 86400, 1.0)
        per_day = max(float(latest_count), 0.0) / age_days
    else:
        delta_reviews = max(float(latest_count) - float(previous_count), 0.0)
        elapsed_days = max((latest_time - previous_time).total_seconds() / 86400, 1 / 24)
        per_day = delta_reviews / elapsed_days
    score = 100.0 * (1.0 - math.exp(-per_day / 50.0))
    return round(_clamp(score), 1), round(per_day, 2)


def rating_score(value: float | None) -> float:
    if value is None:
        return 50.0
    rating = float(value)
    if rating > 5:
        return round(_clamp(rating / 10.0 * 100.0), 1)
    return round(_clamp((rating - 3.5) / 1.5 * 100.0), 1)


def discount_score(value: float | None) -> float:
    return 30.0 if value is None else round(_clamp(float(value) / 50.0 * 100.0), 1)


def exposure_score(latest: Mapping) -> float:
    score = 30.0
    if _value(latest, "has_promotion"):
        score += 25.0
    if _value(latest, "is_oliveyoung_pick"):
        score += 35.0
    rank = _value(latest, "rank")
    if rank:
        score += max(0.0, 10.0 - (float(rank) - 1.0) * 0.3)
    return round(_clamp(score), 1)


def freshness_score(first_seen_at: str | None, now: datetime | None = None) -> tuple[float, float]:
    first_seen = _parse_dt(first_seen_at)
    if first_seen is None:
        return 50.0, 999.0
    now = now or datetime.now(timezone.utc)
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    age_days = max((now - first_seen).total_seconds() / 86400, 0.0)
    return round(_clamp(100.0 * math.exp(-age_days / 28.0)), 1), round(age_days, 2)


def calculate_reaction_score(latest: Mapping, previous: Mapping | None = None) -> dict:
    review_velocity, reviews_per_day = review_velocity_score(latest, previous)
    components = {
        "review_velocity": review_velocity,
        "rating": rating_score(_value(latest, "rating")),
        "discount": discount_score(_value(latest, "discount_rate")),
        "exposure": exposure_score(latest),
        "new_badge": 100.0 if _value(latest, "is_new_badge") else 35.0,
        "freshness": freshness_score(_value(latest, "first_seen_at"))[0],
    }
    age_days = freshness_score(_value(latest, "first_seen_at"))[1]
    score = sum(components[key] * WEIGHTS[key] for key in WEIGHTS)
    return {"score": round(_clamp(score), 1), **components, "reviews_per_day": reviews_per_day, "age_days": age_days, "weights": WEIGHTS, "sns_buzz": None, "version": "v1-no-sns"}
