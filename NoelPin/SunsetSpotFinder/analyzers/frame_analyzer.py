from __future__ import annotations

import pandas as pd


AUTO_TYPES = {"ROAD_AXIS", "ALLEY_AXIS", "RAIL_EDGE", "APARTMENT_GAP"}


class FrameAnalyzer:
    """Normalizes photographic framing potential without exposing it as a public score."""

    def annotate(self, candidates: pd.DataFrame) -> pd.DataFrame:
        frame = candidates.copy()
        if "frame_score" not in frame.columns:
            frame["frame_score"] = .50
        frame["frame_score"] = (
            pd.to_numeric(frame["frame_score"], errors="coerce").fillna(.50).clip(0, 1)
        )
        source = (
            frame["source_type"].astype(str)
            if "source_type" in frame.columns
            else pd.Series("", index=frame.index)
        )
        auto_flag = (
            frame["auto_generated"].fillna(False).astype(bool)
            if "auto_generated" in frame.columns
            else pd.Series(False, index=frame.index)
        )
        frame["is_auto_discovered"] = source.isin(AUTO_TYPES) | auto_flag
        return frame
