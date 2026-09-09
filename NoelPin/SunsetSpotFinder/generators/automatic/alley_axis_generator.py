from __future__ import annotations

from typing import Any
import pandas as pd

from geo_utils import linear_score
from .common import (
    building_centroids,
    candidate_row,
    corridor_counts,
    iter_lines,
    iter_polygons,
    line_length_m,
    property_name,
    property_number,
    snap_to_public_path,
    westward_viewpoint,
)


class AlleyAxisGenerator:
    def __init__(self, config: dict[str, Any]):
        cfg = (config.get("automatic_discovery") or {}).get("alley_axis") or {}
        self.min_length_m = float(cfg.get("min_length_m", 40))
        self.max_length_m = float(cfg.get("max_length_m", 220))
        self.max_alignment_deg = float(cfg.get("max_alignment_deg", 18))
        self.max_width_m = float(cfg.get("max_width_m", 9))
        self.min_flank_buildings = int(cfg.get("min_flank_buildings", 2))
        self.max_front_buildings = int(cfg.get("max_front_buildings", 1))
        self.public_snap_m = float(cfg.get("public_snap_m", 25))
        self.max_candidates = int(cfg.get("max_candidates", 2500))

    def generate(self, roads, buildings, pedestrian_network, sunset_azimuth: float) -> pd.DataFrame:
        road_lines = iter_lines(roads)
        ped_lines = iter_lines(pedestrian_network)
        centroids = building_centroids(iter_polygons(buildings))
        if not centroids:
            return pd.DataFrame()
        rows: list[dict[str, Any]] = []
        for index, (line, props) in enumerate(road_lines):
            length = line_length_m(line)
            if length < self.min_length_m or length > self.max_length_m:
                continue
            width = property_number(props, ("width_m", "WIDTH_M", "width", "road_width", "도로폭"))
            if width is not None and width > self.max_width_m:
                continue
            viewpoint, view_bearing, alignment = westward_viewpoint(line, sunset_azimuth, fraction=.18)
            if alignment > self.max_alignment_deg:
                continue
            left, right, front = corridor_counts(viewpoint, view_bearing, centroids, flank_radius_m=65, front_radius_m=150)
            if left < 1 or right < 1 or left + right < self.min_flank_buildings or front > self.max_front_buildings:
                continue
            snapped, access_status, snap_distance = snap_to_public_path(viewpoint, ped_lines, self.public_snap_m)
            if access_status == "NO_PUBLIC_PATH_NEARBY":
                continue
            symmetry = 1.0 - abs(left - right) / max(1, left + right)
            frame = .50 + .08 * min(4, left + right) + .15 * symmetry - .16 * front
            frame += .10 * linear_score(alignment, 0, self.max_alignment_deg)
            rows.append(candidate_row(
                "ALLEY_AXIS", "골목끝노을", property_name(props, f"골목축 후보 {index + 1}"),
                snapped, view_bearing, alignment, frame, access_status, f"alley-{index}",
                road_length_m=round(length, 1), road_width_m=width,
                flank_left_buildings=left, flank_right_buildings=right, front_buildings=front,
                frame_symmetry=round(symmetry, 4),
                public_snap_distance_m=round(snap_distance, 1) if snap_distance == snap_distance else None,
                discovery_reason="BUILDING_FRAMED_WEST_ALLEY",
            ))
            if len(rows) >= self.max_candidates:
                break
        return pd.DataFrame(rows)
