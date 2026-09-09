from __future__ import annotations

from typing import Any

import pandas as pd
from shapely.geometry import shape

from geo_utils import angular_distance_deg, bearing_deg, clamp01, haversine_m


class OpennessAnalyzer:
    def __init__(self, config: dict[str, Any]):
        analysis = config.get("analysis") or {}
        self.radius_m = float(analysis.get("obstruction_radius_m", 800))
        self.half_angle = float(analysis.get("obstruction_half_angle_deg", 8))
        self.tree_radius_m = float(analysis.get("tree_radius_m", 120))

    def _building_centroids(self, payload: dict[str, Any] | None) -> list[tuple[float, float, float]]:
        rows = []
        if not payload:
            return rows
        for feature in payload.get("features") or []:
            try:
                geom = shape(feature.get("geometry") or {})
                props = feature.get("properties") or {}
                if geom.is_empty:
                    continue
                centroid = geom.centroid
                rows.append((float(centroid.y), float(centroid.x), float(props.get("height_m") or props.get("HEIGHT") or 18)))
            except Exception:
                continue
        return rows

    def annotate(self, candidates: pd.DataFrame, buildings_geojson: dict[str, Any] | None, trees: pd.DataFrame) -> pd.DataFrame:
        frame = candidates.copy()
        buildings = self._building_centroids(buildings_geojson)
        tree_points = [(float(row.latitude), float(row.longitude)) for row in trees.itertuples(index=False)] if not trees.empty else []
        openness, building_counts, tree_counts = [], [], []
        baseline = {
            "BRIDGE": .95, "RIVER": .94, "PEDESTRIAN_BRIDGE": .82,
            "TRAIL": .78, "PARK": .74, "URBAN_STREET": .60,
            "STAIR": .76, "HILL_ROAD": .75, "VIEW_DECK": .91,
            "LEVEE": .88, "RIVER_STAIRS": .86, "PLAZA": .80, "BIKE_PATH": .83,
            "PARK_EDGE": .82, "RIVER_ACCESS": .80, "PEDESTRIAN_PATH": .73,
            "FORTRESS_TRAIL": .81, "RIDGE_TRAIL": .88, "SPORTS_GROUND": .86,
            "ROAD_AXIS": .78, "ALLEY_AXIS": .54, "RAIL_EDGE": .82, "APARTMENT_GAP": .56,
        }
        for row in frame.itertuples(index=False):
            lat, lon = float(row.latitude), float(row.longitude)
            target = float(getattr(row, "sunset_azimuth_deg", 270))
            building_count = 0
            weighted = 0.0
            for building_lat, building_lon, height in buildings:
                distance = haversine_m(lat, lon, building_lat, building_lon)
                if distance <= self.radius_m and angular_distance_deg(bearing_deg(lat, lon, building_lat, building_lon), target) <= self.half_angle:
                    building_count += 1
                    weighted += height / max(50.0, distance)
            tree_count = sum(
                1 for tree_lat, tree_lon in tree_points
                if haversine_m(lat, lon, tree_lat, tree_lon) <= self.tree_radius_m
                and angular_distance_deg(bearing_deg(lat, lon, tree_lat, tree_lon), target) <= self.half_angle * 1.5
            )
            building_penalty = min(.60, building_count * .055 + weighted * .05) if buildings else 0.0
            tree_penalty = min(.25, tree_count * .04)
            openness.append(round(clamp01(baseline.get(str(row.source_type), .65) - building_penalty - tree_penalty), 4))
            building_counts.append(building_count)
            tree_counts.append(tree_count)
        frame["openness_score"] = openness
        frame["sunset_sector_building_count"] = building_counts
        frame["sunset_sector_tree_count"] = tree_counts
        frame["obstruction_data_available"] = bool(buildings) or bool(tree_points)
        return frame
