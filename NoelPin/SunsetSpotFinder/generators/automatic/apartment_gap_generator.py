from __future__ import annotations

from typing import Any
import pandas as pd
from shapely.geometry import Point

from geo_utils import angular_distance_deg, bearing_deg, haversine_m, linear_score
from .common import candidate_row, grid_pairs, iter_lines, iter_polygons, snap_to_public_path


def _is_apartment(props: dict[str, Any]) -> bool:
    if str(props.get("is_apartment", "")).lower() in {"1", "true", "y", "yes"}:
        return True
    text = " ".join(str(value) for value in props.values()).lower()
    return any(token in text for token in ("아파트", "공동주택", "apartment", "residential tower"))


class ApartmentGapGenerator:
    def __init__(self, config: dict[str, Any]):
        cfg = (config.get("automatic_discovery") or {}).get("apartment_gap") or {}
        self.min_gap_m = float(cfg.get("min_gap_m", 20))
        self.max_gap_m = float(cfg.get("max_gap_m", 110))
        self.max_alignment_deg = float(cfg.get("max_alignment_deg", 20))
        self.public_snap_m = float(cfg.get("public_snap_m", 55))
        self.max_candidates = int(cfg.get("max_candidates", 1800))

    def generate(self, buildings, pedestrian_network, sunset_azimuth: float) -> pd.DataFrame:
        apartment_polys = [(geom, props) for geom, props in iter_polygons(buildings) if _is_apartment(props)]
        ped_lines = iter_lines(pedestrian_network)
        points = [(geom.centroid, (geom, props)) for geom, props in apartment_polys]
        rows: list[dict[str, Any]] = []
        for left_index, right_index in grid_pairs(points):
            c1, item1 = points[left_index]
            c2, item2 = points[right_index]
            distance = haversine_m(c1.y, c1.x, c2.y, c2.x)
            if distance < self.min_gap_m or distance > self.max_gap_m:
                continue
            cross = bearing_deg(c1.y, c1.x, c2.y, c2.x)
            options = ((cross + 90.0) % 360.0, (cross - 90.0) % 360.0)
            view_bearing = min(options, key=lambda angle: angular_distance_deg(angle, sunset_azimuth))
            alignment = angular_distance_deg(view_bearing, sunset_azimuth)
            if alignment > self.max_alignment_deg:
                continue
            midpoint = Point((c1.x + c2.x) / 2.0, (c1.y + c2.y) / 2.0)
            snapped, access_status, snap_distance = snap_to_public_path(midpoint, ped_lines, self.public_snap_m)
            if access_status == "NO_PUBLIC_PATH_NEARBY":
                continue
            gap_quality = linear_score(abs(distance - 55), 0, max(1.0, self.max_gap_m - 55))
            frame = .66 + .17 * gap_quality + .12 * max(0.0, 1.0 - alignment / self.max_alignment_deg)
            props1 = item1[1]
            props2 = item2[1]
            name1 = str(props1.get("name") or props1.get("NAME") or f"동 {left_index + 1}")
            name2 = str(props2.get("name") or props2.get("NAME") or f"동 {right_index + 1}")
            rows.append(candidate_row(
                "APARTMENT_GAP", "아파트사이노을", f"{name1} · {name2} 사이",
                snapped, view_bearing, alignment, frame, access_status, f"apt-{left_index}-{right_index}",
                building_gap_m=round(distance, 1),
                public_snap_distance_m=round(snap_distance, 1) if snap_distance == snap_distance else None,
                discovery_reason="WEST_ALIGNED_APARTMENT_CORRIDOR",
            ))
            if len(rows) >= self.max_candidates:
                break
        return pd.DataFrame(rows)
