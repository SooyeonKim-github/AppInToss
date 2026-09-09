from __future__ import annotations

import hashlib
import pandas as pd

from geo_utils import angular_distance_deg, bearing_deg, haversine_m
from models import Candidate


def _urban_id(lat: float, lon: float, index: int) -> str:
    raw = f"URBAN_STREET|{lat:.6f}|{lon:.6f}|{index}"
    return "U" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


class UrbanSunsetGenerator:
    def __init__(self, max_road_distance_m: float = 120):
        self.max_road_distance_m = max_road_distance_m

    def generate_from_roads(self, road_segments: list[dict[str, float]]) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for index, road in enumerate(road_segments):
            road_bearing = bearing_deg(road["lat1"], road["lon1"], road["lat2"], road["lon2"])
            alignment = min(angular_distance_deg(road_bearing, 270), angular_distance_deg((road_bearing + 180) % 360, 270))
            if alignment > 25: continue
            lat = (road["lat1"] + road["lat2"]) / 2
            lon = (road["lon1"] + road["lon2"]) / 2
            candidate = Candidate(candidate_id=_urban_id(lat, lon, index), source_type="URBAN_STREET", source_name=f"건물사이노을 도로 후보 {index + 1}", latitude=lat, longitude=lon, geometry_role="ROAD_MIDPOINT", segment_index=index, metadata={"road_west_alignment_deg": round(alignment, 2)})
            rows.append(candidate.to_dict())
        return pd.DataFrame(rows)

    def annotate(self, candidates: pd.DataFrame, road_segments: list[dict[str, float]]) -> pd.DataFrame:
        frame = candidates.copy(); hints=[]; alignments=[]
        for row in frame.itertuples(index=False):
            best_alignment = 180.0; best_distance = float("inf")
            for road in road_segments:
                mid_lat=(road["lat1"]+road["lat2"])/2; mid_lon=(road["lon1"]+road["lon2"])/2
                distance=haversine_m(row.latitude,row.longitude,mid_lat,mid_lon)
                if distance > self.max_road_distance_m: continue
                road_bearing=bearing_deg(road["lat1"],road["lon1"],road["lat2"],road["lon2"])
                alignment=min(angular_distance_deg(road_bearing,270), angular_distance_deg((road_bearing+180)%360,270))
                if alignment < best_alignment or (alignment == best_alignment and distance < best_distance): best_alignment=alignment; best_distance=distance
            hints.append("BUILDING_GAP" if best_alignment <= 25 else "")
            alignments.append(best_alignment if best_alignment < 180 else float("nan"))
        frame["urban_gap_hint"]=hints; frame["road_west_alignment_deg"]=alignments
        return frame
