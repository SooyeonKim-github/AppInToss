from __future__ import annotations

from typing import Any


def line_segments_from_geojson(payload: dict[str, Any] | None) -> list[dict[str, float]]:
    if not payload:
        return []
    segments: list[dict[str, float]] = []

    def add_line(coords: list[list[float]]) -> None:
        for index in range(len(coords) - 1):
            lon1, lat1 = coords[index][:2]
            lon2, lat2 = coords[index + 1][:2]
            segments.append({"lat1": float(lat1), "lon1": float(lon1), "lat2": float(lat2), "lon2": float(lon2)})

    for feature in payload.get("features") or []:
        geometry = feature.get("geometry") or {}
        kind = geometry.get("type")
        coords = geometry.get("coordinates") or []
        if kind == "LineString":
            add_line(coords)
        elif kind == "MultiLineString":
            for line in coords:
                add_line(line)
    return segments
