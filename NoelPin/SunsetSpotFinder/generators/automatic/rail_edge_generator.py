from __future__ import annotations

from typing import Any
import pandas as pd
from shapely.geometry import Point
from shapely.ops import nearest_points

from geo_utils import angular_distance_deg, bearing_deg, haversine_m, sample_coordinates
from .common import candidate_row, iter_lines, property_name


class RailEdgeGenerator:
    def __init__(self, config: dict[str, Any]):
        cfg = (config.get("automatic_discovery") or {}).get("rail_edge") or {}
        self.sample_interval_m = float(cfg.get("sample_interval_m", 90))
        self.min_rail_distance_m = float(cfg.get("min_rail_distance_m", 15))
        self.max_rail_distance_m = float(cfg.get("max_rail_distance_m", 160))
        self.max_alignment_deg = float(cfg.get("max_alignment_deg", 28))
        self.max_candidates = int(cfg.get("max_candidates", 2000))
        self.min_candidate_spacing_m = float(cfg.get("min_candidate_spacing_m", 120))

    def generate(self, railways, pedestrian_network, sunset_azimuth: float) -> pd.DataFrame:
        rails = iter_lines(railways)
        public_lines = iter_lines(pedestrian_network)
        if not rails or not public_lines:
            return pd.DataFrame()
        rows: list[dict[str, Any]] = []
        accepted_points: list[Point] = []
        for path_index, (path, path_props) in enumerate(public_lines):
            coords = list(path.coords)
            for sample_index, (lat, lon) in enumerate(sample_coordinates(coords, self.sample_interval_m)):
                point = Point(lon, lat)
                best = None
                for rail_index, (rail, rail_props) in enumerate(rails):
                    rail_point = nearest_points(point, rail)[1]
                    distance = haversine_m(lat, lon, rail_point.y, rail_point.x)
                    if best is None or distance < best[0]:
                        best = (distance, rail_point, rail_index, rail_props)
                if best is None:
                    continue
                distance, rail_point, rail_index, rail_props = best
                if distance < self.min_rail_distance_m or distance > self.max_rail_distance_m:
                    continue
                direction = bearing_deg(lat, lon, rail_point.y, rail_point.x)
                alignment = angular_distance_deg(direction, sunset_azimuth)
                if alignment > self.max_alignment_deg:
                    continue
                if any(haversine_m(point.y, point.x, prior.y, prior.x) < self.min_candidate_spacing_m for prior in accepted_points):
                    continue
                frame = .68 + .18 * max(0.0, 1.0 - alignment / self.max_alignment_deg)
                rows.append(candidate_row(
                    "RAIL_EDGE", "철길너머노을",
                    property_name(rail_props, f"철길너머 후보 {rail_index + 1}"),
                    point, direction, alignment, frame, "PEDESTRIAN_NETWORK", f"rail-{path_index}-{sample_index}-{rail_index}",
                    rail_distance_m=round(distance, 1),
                    pedestrian_path_name=property_name(path_props, f"보행로 {path_index + 1}"),
                    discovery_reason="PUBLIC_PATH_LOOKING_WEST_ACROSS_RAIL",
                ))
                accepted_points.append(point)
                if len(rows) >= self.max_candidates:
                    return pd.DataFrame(rows)
        return pd.DataFrame(rows)
