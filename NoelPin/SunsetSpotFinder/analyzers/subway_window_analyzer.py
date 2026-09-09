from __future__ import annotations

from datetime import date
import pandas as pd
from analyzers.sun_analyzer import SunDirectionAnalyzer
from geo_utils import bearing_deg


def _window_side(train_bearing:float,sun_bearing:float)->str:
    relative=(sun_bearing-train_bearing+180)%360-180
    if abs(relative)<=35:return "진행방향 앞쪽"
    if abs(relative)>=145:return "진행방향 뒤쪽"
    return "오른쪽 창문" if relative>0 else "왼쪽 창문"


class SubwayWindowAnalyzer:
    def __init__(self,sun_analyzer:SunDirectionAnalyzer): self.sun_analyzer=sun_analyzer
    def build(self,segments:pd.DataFrame,target_date:date)->pd.DataFrame:
        rows=[]
        for s in segments.itertuples(index=False):
            surface=str(s.is_surface).lower() in {"1","true","y","yes"} if not isinstance(s.is_surface,bool) else s.is_surface; bridge=str(s.is_bridge).lower() in {"1","true","y","yes"} if not isinstance(s.is_bridge,bool) else s.is_bridge
            if not surface: continue
            lat=(float(s.from_lat)+float(s.to_lat))/2; lon=(float(s.from_lon)+float(s.to_lon))/2; sunset_at,sun=self.sun_analyzer.sunset_info(lat,lon,target_date); train=bearing_deg(float(s.from_lat),float(s.from_lon),float(s.to_lat),float(s.to_lon))
            rows.append({"line":str(s.line),"from_station":str(s.from_station),"to_station":str(s.to_station),"direction":str(s.direction),"latitude":lat,"longitude":lon,"train_bearing_deg":round(train,1),"sunset_azimuth_deg":round(sun,1),"window_side":_window_side(train,sun),"sunset_at":sunset_at,"is_bridge":bool(bridge),"transit_priority":1.0 if bridge else .75,"verification_status":"CANDIDATE"})
        return pd.DataFrame(rows)
