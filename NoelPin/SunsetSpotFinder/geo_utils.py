from __future__ import annotations

import math
from collections.abc import Iterable

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def angular_distance_deg(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def interpolate_segment(lat1: float, lon1: float, lat2: float, lon2: float, interval_m: float) -> list[tuple[float, float]]:
    distance = haversine_m(lat1, lon1, lat2, lon2)
    if distance <= interval_m:
        return [(lat1, lon1), (lat2, lon2)]
    steps = max(1, math.ceil(distance / interval_m))
    return [(lat1 + (lat2 - lat1) * i / steps, lon1 + (lon2 - lon1) * i / steps) for i in range(steps + 1)]


def sample_coordinates(coords: Iterable[Iterable[float]], interval_m: float) -> list[tuple[float, float]]:
    points = list(coords)
    if not points:
        return []
    if len(points) == 1:
        lon, lat = points[0][:2]
        return [(float(lat), float(lon))]
    sampled: list[tuple[float, float]] = []
    for index in range(len(points) - 1):
        lon1, lat1 = points[index][:2]
        lon2, lat2 = points[index + 1][:2]
        segment = interpolate_segment(float(lat1), float(lon1), float(lat2), float(lon2), interval_m)
        if sampled and segment:
            segment = segment[1:]
        sampled.extend(segment)
    return sampled


def nearest_point(lat: float, lon: float, rows: Iterable[tuple[float, float, str]]) -> tuple[str, float, float] | None:
    best: tuple[str, float, float] | None = None
    for item_lat, item_lon, label in rows:
        distance = haversine_m(lat, lon, item_lat, item_lon)
        item_bearing = bearing_deg(lat, lon, item_lat, item_lon)
        if best is None or distance < best[1]:
            best = (label, distance, item_bearing)
    return best


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def linear_score(value: float, best: float, worst: float, reverse: bool = False) -> float:
    if best == worst:
        return 1.0
    if reverse:
        score = (value - worst) / (best - worst)
    else:
        score = (worst - value) / (worst - best)
    return clamp01(score)
