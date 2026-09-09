from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

from geo_utils import sample_coordinates
from models import Candidate


def _stable_id(source_type: str, name: str, lat: float, lon: float, index: int) -> str:
    raw = f"{source_type}|{name}|{lat:.6f}|{lon:.6f}|{index}"
    return "S" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


def _candidate(source_type: str, name: str, lat: float, lon: float, index: int, role: str, metadata: dict[str, Any] | None = None) -> Candidate:
    return Candidate(candidate_id=_stable_id(source_type, name, lat, lon, index), source_type=source_type, source_name=name, latitude=float(lat), longitude=float(lon), geometry_role=role, segment_index=index, metadata=metadata or {})


class CandidateGenerator:
    def __init__(self, sample_interval_m: float = 50.0):
        self.sample_interval_m = sample_interval_m

    def from_point_frame(self, frame: pd.DataFrame, source: dict[str, Any]) -> list[Candidate]:
        name_col = source.get("name_column", "name")
        lat_col = source.get("lat_column", "latitude")
        lon_col = source.get("lon_column", "longitude")
        source_type = source["source_type"]
        results: list[Candidate] = []
        for index, row in frame.iterrows():
            if pd.isna(row.get(lat_col)) or pd.isna(row.get(lon_col)):
                continue
            name = str(row.get(name_col) or f"{source_type}-{index}")
            metadata = {str(k): v for k, v in row.to_dict().items() if k not in {name_col, lat_col, lon_col}}
            results.append(_candidate(source_type, name, float(row[lat_col]), float(row[lon_col]), int(index), "POINT", metadata))
        return results

    def from_geojson(self, geojson: dict[str, Any], source: dict[str, Any]) -> list[Candidate]:
        source_type = source["source_type"]
        name_property = source.get("name_property", "name")
        results: list[Candidate] = []
        global_index = 0
        for feature_index, feature in enumerate(geojson.get("features") or []):
            geometry = feature.get("geometry") or {}
            properties = feature.get("properties") or {}
            name = str(properties.get(name_property) or f"{source_type}-{feature_index}")
            for role, coord_set in self._extract_point_sets(geometry.get("type"), geometry.get("coordinates") or []):
                sampled = sample_coordinates(coord_set, self.sample_interval_m) if role != "POINT" else [(float(coord_set[0][1]), float(coord_set[0][0]))]
                for lat, lon in sampled:
                    results.append(_candidate(source_type, name, lat, lon, global_index, role, dict(properties)))
                    global_index += 1
        return results

    def _extract_point_sets(self, geometry_type: str, coordinates: Any) -> list[tuple[str, list[list[float]]]]:
        if geometry_type == "Point": return [("POINT", [coordinates])]
        if geometry_type == "MultiPoint": return [("POINT", [point]) for point in coordinates]
        if geometry_type == "LineString": return [("LINE", coordinates)]
        if geometry_type == "MultiLineString": return [("LINE", line) for line in coordinates]
        if geometry_type == "Polygon": return [("POLYGON_BOUNDARY", ring) for ring in coordinates[:1]]
        if geometry_type == "MultiPolygon":
            return [("POLYGON_BOUNDARY", ring) for polygon in coordinates for ring in polygon[:1]]
        return []

    def build(self, payloads: list[dict[str, Any]], demo_frame: pd.DataFrame | None = None) -> pd.DataFrame:
        candidates: list[Candidate] = []
        for payload in payloads:
            source = payload["config"]
            if source.get("kind") == "point_csv": candidates.extend(self.from_point_frame(payload["data"], source))
            elif source.get("kind") == "geojson": candidates.extend(self.from_geojson(payload["data"], source))
        if not candidates and demo_frame is not None:
            for index, row in demo_frame.iterrows():
                candidates.append(_candidate(str(row.source_type), str(row.source_name), float(row.latitude), float(row.longitude), int(index), "POINT", {"demo": True}))
        frame = pd.DataFrame([candidate.to_dict() for candidate in candidates])
        if frame.empty:
            return pd.DataFrame(columns=["candidate_id", "source_type", "source_name", "latitude", "longitude", "verification_status"])
        return frame.drop_duplicates(subset=["source_type", "latitude", "longitude"]).reset_index(drop=True)
