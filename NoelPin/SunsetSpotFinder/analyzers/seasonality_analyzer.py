from __future__ import annotations

import pandas as pd
from analyzers.sun_analyzer import SunDirectionAnalyzer


class SeasonalityAnalyzer:
    def __init__(self,sun_analyzer:SunDirectionAnalyzer,year:int):
        self.sun=sun_analyzer; self.year=year; self.profile=self.sun.monthly_profile(37.5665,126.9780,year)

    def annotate(self,candidates:pd.DataFrame)->pd.DataFrame:
        frame=candidates.copy(); directions=[]; months=[]
        for row in frame.itertuples(index=False):
            water=getattr(row,"water_bearing_deg",float("nan")); alignment=getattr(row,"water_sunset_alignment_deg",float("nan")); direction=float(water) if pd.notna(water) and pd.notna(alignment) and float(alignment)<=55 else 270.0
            directions.append(round(direction,1)); months.append(",".join(str(v) for v in self.sun.recommended_months(self.profile,direction)))
        frame["inferred_view_direction_deg"]=directions; frame["recommended_months"]=months
        return frame
