from __future__ import annotations

from typing import Any
import pandas as pd
from geo_utils import angular_distance_deg, linear_score, nearest_point


def _geojson_vertices(payload: dict[str, Any] | None) -> list[tuple[float, float, str]]:
    if not payload:
        return []
    vertices = []

    def walk(value: Any, label: str) -> None:
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            lon, lat = float(value[0]), float(value[1])
            vertices.append((lat, lon, label))
            return
        if isinstance(value, list):
            for item in value:
                walk(item, label)

    for idx, feature in enumerate(payload.get("features") or []):
        props = feature.get("properties") or {}
        label = str(props.get("name") or props.get("NAME") or f"water-{idx}")
        walk((feature.get("geometry") or {}).get("coordinates") or [], label)
    return vertices


class ContextAnalyzer:
    def __init__(self, config: dict[str, Any]):
        analysis = config.get("analysis") or {}
        self.station_good_m = float(analysis.get("station_good_m", 500))
        self.station_max_m = float(analysis.get("station_max_m", 1200))
        self.office_good_m = float(analysis.get("office_good_m", 1000))
        self.water_good_m = float(analysis.get("water_good_m", 1200))

    def annotate(
        self,
        candidates: pd.DataFrame,
        stations: pd.DataFrame,
        office_hubs: pd.DataFrame,
        water_geojson: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        frame = candidates.copy()
        station_rows = [
            (float(row.latitude), float(row.longitude), f"{row.station}({row.line})")
            for row in stations.itertuples(index=False)
        ]
        office_rows = [
            (float(row.latitude), float(row.longitude), str(row.name))
            for row in office_hubs.itertuples(index=False)
        ]
        water_rows = _geojson_vertices(water_geojson)

        out = {
            key: []
            for key in [
                "nearest_station",
                "station_distance_m",
                "station_score",
                "nearest_office_hub",
                "office_distance_m",
                "commute_score",
                "water_distance_m",
                "water_bearing_deg",
                "water_sunset_alignment_deg",
                "view_score",
                "uniqueness_score",
                "category_hint",
            ]
        }

        # Values are internal discovery priors only; they are never exposed as a user sunset score.
        uniqueness_by_source = {
            "PEDESTRIAN_BRIDGE": .95,
            "BRIDGE": .90,
            "URBAN_STREET": .92,
            "RIVER": .75,
            "TRAIL": .72,
            "PARK": .55,
            "STAIR": .88,
            "HILL_ROAD": .86,
            "VIEW_DECK": .80,
            "LEVEE": .82,
            "RIVER_STAIRS": .84,
            "PLAZA": .65,
            "BIKE_PATH": .70,
        }
        base_view_by_source = {
            "BRIDGE": .85,
            "RIVER": .82,
            "PEDESTRIAN_BRIDGE": .72,
            "TRAIL": .68,
            "PARK": .58,
            "URBAN_STREET": .62,
            "STAIR": .68,
            "HILL_ROAD": .70,
            "VIEW_DECK": .86,
            "LEVEE": .78,
            "RIVER_STAIRS": .84,
            "PLAZA": .60,
            "BIKE_PATH": .68,
        }

        for row in frame.itertuples(index=False):
            station = nearest_point(float(row.latitude), float(row.longitude), station_rows)
            office = nearest_point(float(row.latitude), float(row.longitude), office_rows)
            water = nearest_point(float(row.latitude), float(row.longitude), water_rows) if water_rows else None

            station_name, station_distance = (station[0], station[1]) if station else ("", 99999.0)
            office_name, office_distance = (office[0], office[1]) if office else ("", 99999.0)
            water_distance, water_bearing = (water[1], water[2]) if water else (99999.0, float("nan"))

            station_score = linear_score(station_distance, self.station_good_m, self.station_max_m)
            office_score = linear_score(office_distance, self.office_good_m, 5000.0)
            commute_score = min(1.0, .72 * station_score + .28 * office_score)

            source = str(row.source_type)
            sunset = float(getattr(row, "sunset_azimuth_deg", 270.0))
            view_score = base_view_by_source.get(source, .5)
            alignment = float("nan")
            if water:
                alignment = angular_distance_deg(water_bearing, sunset)
                view_score = min(
                    1.0,
                    view_score * .65
                    + linear_score(water_distance, 0, self.water_good_m)
                    * max(0.0, 1 - alignment / 90)
                    * .35,
                )

            if source == "URBAN_STREET":
                hint = "BUILDING_GAP"
            elif source in {"BRIDGE", "RIVER", "LEVEE", "RIVER_STAIRS", "BIKE_PATH"} or (
                water and water_distance <= self.water_good_m
            ):
                hint = "WATER_VIEW"
            elif source in {"PEDESTRIAN_BRIDGE", "STAIR", "HILL_ROAD", "VIEW_DECK"}:
                hint = "ELEVATED_VIEW"
            elif source in {"TRAIL", "PARK"}:
                hint = "WALK_SUNSET"
            elif source == "PLAZA":
                hint = "OPEN_SPACE"
            else:
                hint = "COMMUTE_SUNSET"

            values = [
                station_name,
                round(station_distance, 1),
                round(station_score, 4),
                office_name,
                round(office_distance, 1),
                round(commute_score, 4),
                round(water_distance, 1) if water else float("nan"),
                round(water_bearing, 1) if water else float("nan"),
                round(alignment, 1) if water else float("nan"),
                round(view_score, 4),
                uniqueness_by_source.get(source, .5),
                hint,
            ]
            for key, value in zip(out, values):
                out[key].append(value)

        for key, values in out.items():
            frame[key] = values
        return frame
