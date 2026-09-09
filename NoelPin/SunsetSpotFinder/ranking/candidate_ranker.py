from __future__ import annotations

from typing import Any

import pandas as pd


SUNSET_TYPE_BY_SOURCE = {
    "PEDESTRIAN_BRIDGE": "육교위노을",
    "BRIDGE": "다리위노을",
    "RIVER": "한강노을",
    "TRAIL": "산책노을",
    "PARK": "산책노을",
    "URBAN_STREET": "건물사이노을",
    "STAIR": "계단위노을",
    "HILL_ROAD": "언덕길노을",
    "VIEW_DECK": "전망데크노을",
    "LEVEE": "제방위노을",
    "RIVER_STAIRS": "수변계단노을",
    "PLAZA": "광장노을",
    "BIKE_PATH": "자전거길노을",
    "PARK_EDGE": "공원끝노을",
    "RIVER_ACCESS": "나들목노을",
    "PEDESTRIAN_PATH": "보행로노을",
    "FORTRESS_TRAIL": "성곽길노을",
    "RIDGE_TRAIL": "능선노을",
    "SPORTS_GROUND": "운동장노을",
    "ROAD_AXIS": "대로끝노을",
    "ALLEY_AXIS": "골목끝노을",
    "RAIL_EDGE": "철길너머노을",
    "APARTMENT_GAP": "아파트사이노을",
}


class CandidateRanker:
    def __init__(self, config: dict[str, Any]):
        self.weights = (config.get("ranking") or {}).get("weights") or {}

    def rank(self, candidates: pd.DataFrame) -> pd.DataFrame:
        frame = candidates.copy()
        metric_map = {
            "openness": "openness_score",
            "commute": "commute_score",
            "view": "view_score",
            "elevation": "elevation_score",
            "station": "station_score",
            "uniqueness": "uniqueness_score",
            "frame": "frame_score",
        }
        total = sum(float(self.weights.get(key, 0)) for key in metric_map) or 1.0
        score = pd.Series(0.0, index=frame.index)
        for key, column in metric_map.items():
            values = frame[column] if column in frame.columns else pd.Series(0.0, index=frame.index)
            score += (
                pd.to_numeric(values, errors="coerce").fillna(0.0).clip(0, 1)
                * (float(self.weights.get(key, 0)) / total)
            )

        frame["candidate_priority"] = (score * 100).round(2)
        frame["rank"] = frame["candidate_priority"].rank(method="first", ascending=False).astype(int)
        source_types = frame["source_type"].astype(str) if "source_type" in frame.columns else pd.Series("", index=frame.index)
        fallback_types = source_types.map(SUNSET_TYPE_BY_SOURCE).fillna("숨은노을")
        if "sunset_type" in frame.columns:
            existing = frame["sunset_type"].fillna("").astype(str).str.strip()
            frame["sunset_type"] = existing.where(existing.ne(""), fallback_types)
        else:
            frame["sunset_type"] = fallback_types
        frame["category_hint"] = frame["sunset_type"]
        frame["sunset_tags"] = frame.apply(self._build_tags, axis=1)
        return frame.sort_values(["candidate_priority", "station_distance_m"], ascending=[False, True]).reset_index(drop=True)

    @staticmethod
    def _build_tags(row: pd.Series) -> str:
        tags: list[str] = [str(row.get("sunset_type") or "숨은노을")]
        if bool(row.get("is_commute_candidate", False)):
            tags.append("퇴근길노을")
        if str(row.get("urban_gap_hint", "")) == "BUILDING_GAP" and "건물사이노을" not in tags:
            tags.append("건물사이노을")
        if bool(row.get("water_in_sunset_direction", False)) and "한강노을" not in tags:
            tags.append("한강노을")
        return "|".join(dict.fromkeys(tags))
