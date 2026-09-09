from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from typing import Any, Iterable

from shapely.geometry import LineString, Point, shape
from shapely.ops import nearest_points

from geo_utils import angular_distance_deg, bearing_deg, haversine_m


def stable_auto_id(source_type: str, lat: float, lon: float, seed: str) -> str:
    raw = f"{source_type}|{lat:.6f}|{lon:.6f}|{seed}"
    return "A" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


def iter_lines(payload: dict[str, Any] | None) -> list[tuple[LineString, dict[str, Any]]]:
    rows: list[tuple[LineString, dict[str, Any]]] = []
    if not payload:
        return rows
    for feature in payload.get("features") or []:
        props = dict(feature.get("properties") or {})
        try:
            geom = shape(feature.get("geometry") or {})
        except Exception:
            continue
        if geom.is_empty:
            continue
        if geom.geom_type == "LineString":
            rows.append((geom, props))
        elif geom.geom_type == "MultiLineString":
            rows.extend((line, props) for line in geom.geoms if not line.is_empty)
    return rows


def iter_polygons(payload: dict[str, Any] | None) -> list[tuple[Any, dict[str, Any]]]:
    rows: list[tuple[Any, dict[str, Any]]] = []
    if not payload:
        return rows
    for feature in payload.get("features") or []:
        props = dict(feature.get("properties") or {})
        try:
            geom = shape(feature.get("geometry") or {})
        except Exception:
            continue
        if geom.is_empty:
            continue
        if geom.geom_type == "Polygon":
            rows.append((geom, props))
        elif geom.geom_type == "MultiPolygon":
            rows.extend((poly, props) for poly in geom.geoms if not poly.is_empty)
    return rows


def line_length_m(line: LineString) -> float:
    coords = list(line.coords)
    return sum(haversine_m(c1[1], c1[0], c2[1], c2[0]) for c1, c2 in zip(coords, coords[1:]))


def line_axis_bearing(line: LineString) -> float:
    start = line.coords[0]
    end = line.coords[-1]
    return bearing_deg(start[1], start[0], end[1], end[0])


def westward_viewpoint(line: LineString, sunset_azimuth: float, fraction: float = 0.20) -> tuple[Point, float, float]:
    axis = line_axis_bearing(line)
    reverse = (axis + 180.0) % 360.0
    if angular_distance_deg(axis, sunset_azimuth) <= angular_distance_deg(reverse, sunset_azimuth):
        viewpoint = line.interpolate(max(0.02, min(0.48, fraction)), normalized=True)
        view_bearing = axis
    else:
        viewpoint = line.interpolate(1.0 - max(0.02, min(0.48, fraction)), normalized=True)
        view_bearing = reverse
    alignment = angular_distance_deg(view_bearing, sunset_azimuth)
    return viewpoint, view_bearing, alignment


def property_number(props: dict[str, Any], names: Iterable[str]) -> float | None:
    for name in names:
        value = props.get(name)
        if value in (None, ""):
            continue
        try:
            text = str(value).replace("m", "").replace(",", "").strip()
            return float(text)
        except (TypeError, ValueError):
            continue
    return None


def property_name(props: dict[str, Any], fallback: str) -> str:
    for key in ("name", "NAME", "road_name", "ROAD_NAME", "도로명", "시설명"):
        value = props.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def nearest_line_point(point: Point, lines: list[tuple[LineString, dict[str, Any]]]) -> tuple[Point, float] | None:
    best: tuple[Point, float] | None = None
    for line, _ in lines:
        try:
            candidate = nearest_points(point, line)[1]
        except Exception:
            continue
        distance = haversine_m(point.y, point.x, candidate.y, candidate.x)
        if best is None or distance < best[1]:
            best = (candidate, distance)
    return best


def snap_to_public_path(
    point: Point,
    pedestrian_lines: list[tuple[LineString, dict[str, Any]]],
    max_distance_m: float,
) -> tuple[Point, str, float]:
    if not pedestrian_lines:
        return point, "ACCESS_UNCHECKED", float("nan")
    nearest = nearest_line_point(point, pedestrian_lines)
    if nearest is None or nearest[1] > max_distance_m:
        return point, "NO_PUBLIC_PATH_NEARBY", nearest[1] if nearest else float("inf")
    return nearest[0], "PEDESTRIAN_NETWORK", nearest[1]


def relative_angle(reference: float, target: float) -> float:
    return (target - reference + 180.0) % 360.0 - 180.0


def building_centroids(buildings: list[tuple[Any, dict[str, Any]]]) -> list[tuple[Point, dict[str, Any]]]:
    return [(geom.centroid, props) for geom, props in buildings if not geom.is_empty]


def corridor_counts(
    point: Point,
    view_bearing: float,
    centroids: list[tuple[Point, dict[str, Any]]],
    flank_radius_m: float = 70.0,
    front_radius_m: float = 180.0,
    front_half_angle_deg: float = 16.0,
) -> tuple[int, int, int]:
    left = right = front = 0
    for centroid, _ in centroids:
        distance = haversine_m(point.y, point.x, centroid.y, centroid.x)
        if distance > max(flank_radius_m, front_radius_m):
            continue
        direction = bearing_deg(point.y, point.x, centroid.y, centroid.x)
        rel = relative_angle(view_bearing, direction)
        if distance <= front_radius_m and abs(rel) <= front_half_angle_deg:
            front += 1
        if distance <= flank_radius_m:
            if -135.0 <= rel <= -45.0:
                left += 1
            elif 45.0 <= rel <= 135.0:
                right += 1
    return left, right, front


def candidate_row(
    source_type: str,
    sunset_type: str,
    source_name: str,
    point: Point,
    view_bearing: float,
    sunset_alignment_deg: float,
    frame_score: float,
    access_status: str,
    seed: str,
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate_id": stable_auto_id(source_type, point.y, point.x, seed),
        "source_type": source_type,
        "sunset_type": sunset_type,
        "source_name": source_name,
        "latitude": float(point.y),
        "longitude": float(point.x),
        "geometry_role": "AUTO_DISCOVERY",
        "segment_index": None,
        "verification_status": "CANDIDATE",
        "view_bearing_deg": round(float(view_bearing), 2),
        "auto_sunset_alignment_deg": round(float(sunset_alignment_deg), 2),
        "frame_score": round(max(0.0, min(1.0, float(frame_score))), 4),
        "access_status": access_status,
        "auto_generated": True,
        "requires_access_verification": access_status != "PEDESTRIAN_NETWORK",
    }
    row.update(extra)
    return row


def grid_pairs(points: list[tuple[Point, Any]], cell_deg: float = 0.0012):
    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, (point, _) in enumerate(points):
        buckets[(math.floor(point.y / cell_deg), math.floor(point.x / cell_deg))].append(index)
    seen: set[tuple[int, int]] = set()
    for index, (point, _) in enumerate(points):
        key = (math.floor(point.y / cell_deg), math.floor(point.x / cell_deg))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for other in buckets.get((key[0] + dy, key[1] + dx), []):
                    pair = (min(index, other), max(index, other))
                    if index == other or pair in seen:
                        continue
                    seen.add(pair)
                    yield pair
