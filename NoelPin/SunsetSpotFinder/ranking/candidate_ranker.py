from __future__ import annotations

from typing import Any
import pandas as pd


class CandidateRanker:
    def __init__(self,config:dict[str,Any]): self.weights=(config.get("ranking") or {}).get("weights") or {}
    def rank(self,candidates:pd.DataFrame)->pd.DataFrame:
        frame=candidates.copy(); metric_map={"openness":"openness_score","commute":"commute_score","view":"view_score","elevation":"elevation_score","station":"station_score","uniqueness":"uniqueness_score"}; total=sum(float(self.weights.get(k,0)) for k in metric_map) or 1.0; score=pd.Series(0.0,index=frame.index)
        for key,column in metric_map.items(): score += pd.to_numeric(frame.get(column,0.0),errors="coerce").fillna(0.0).clip(0,1)*(float(self.weights.get(key,0))/total)
        frame["candidate_priority"]=(score*100).round(2); frame["rank"]=frame["candidate_priority"].rank(method="first",ascending=False).astype(int)
        if "urban_gap_hint" in frame.columns: frame.loc[frame["urban_gap_hint"].fillna("").eq("BUILDING_GAP"),"category_hint"]="BUILDING_GAP"
        return frame.sort_values(["candidate_priority","station_distance_m"],ascending=[False,True]).reset_index(drop=True)
