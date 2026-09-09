from __future__ import annotations

from typing import Any
import pandas as pd
from geo_utils import angular_distance_deg, linear_score, nearest_point


def _geojson_vertices(payload: dict[str, Any] | None) -> list[tuple[float, float, str]]:
    if not payload: return []
    vertices=[]
    def walk(value: Any, label: str) -> None:
        if isinstance(value,list) and len(value)>=2 and all(isinstance(item,(int,float)) for item in value[:2]):
            lon,lat=float(value[0]),float(value[1]); vertices.append((lat,lon,label)); return
        if isinstance(value,list):
            for item in value: walk(item,label)
    for idx,feature in enumerate(payload.get("features") or []):
        props=feature.get("properties") or {}; label=str(props.get("name") or props.get("NAME") or f"water-{idx}")
        walk((feature.get("geometry") or {}).get("coordinates") or [],label)
    return vertices


class ContextAnalyzer:
    def __init__(self, config: dict[str, Any]):
        a=config.get("analysis") or {}; self.station_good_m=float(a.get("station_good_m",500)); self.station_max_m=float(a.get("station_max_m",1200)); self.office_good_m=float(a.get("office_good_m",1000)); self.water_good_m=float(a.get("water_good_m",1200))

    def annotate(self,candidates:pd.DataFrame,stations:pd.DataFrame,office_hubs:pd.DataFrame,water_geojson:dict[str,Any]|None=None)->pd.DataFrame:
        frame=candidates.copy(); station_rows=[(float(r.latitude),float(r.longitude),f"{r.station}({r.line})") for r in stations.itertuples(index=False)]; office_rows=[(float(r.latitude),float(r.longitude),str(r.name)) for r in office_hubs.itertuples(index=False)]; water_rows=_geojson_vertices(water_geojson)
        out={k:[] for k in ["nearest_station","station_distance_m","station_score","nearest_office_hub","office_distance_m","commute_score","water_distance_m","water_bearing_deg","water_sunset_alignment_deg","view_score","uniqueness_score","category_hint"]}
        uniq={"PEDESTRIAN_BRIDGE":.95,"BRIDGE":.90,"URBAN_STREET":.92,"RIVER":.75,"TRAIL":.72,"PARK":.55}
        base={"BRIDGE":.85,"RIVER":.82,"PEDESTRIAN_BRIDGE":.72,"TRAIL":.68,"PARK":.58,"URBAN_STREET":.62}
        for row in frame.itertuples(index=False):
            station=nearest_point(float(row.latitude),float(row.longitude),station_rows); office=nearest_point(float(row.latitude),float(row.longitude),office_rows); water=nearest_point(float(row.latitude),float(row.longitude),water_rows) if water_rows else None
            s_name,s_dist=(station[0],station[1]) if station else ("",99999.0); o_name,o_dist=(office[0],office[1]) if office else ("",99999.0); w_dist,w_bearing=(water[1],water[2]) if water else (99999.0,float("nan"))
            s_score=linear_score(s_dist,self.station_good_m,self.station_max_m); o_score=linear_score(o_dist,self.office_good_m,5000.0); c_score=min(1.0,.72*s_score+.28*o_score)
            source=str(row.source_type); sunset=float(getattr(row,"sunset_azimuth_deg",270.0)); v=base.get(source,.5); align=float("nan")
            if water:
                align=angular_distance_deg(w_bearing,sunset); v=min(1.0,v*.65+linear_score(w_dist,0,self.water_good_m)*max(0.0,1-align/90)*.35)
            hint="BUILDING_GAP" if source=="URBAN_STREET" else "HAN_RIVER" if source in {"BRIDGE","RIVER"} or (water and w_dist<=self.water_good_m) else "COMMUTE_BRIDGE" if source=="PEDESTRIAN_BRIDGE" else "WALK_SUNSET" if source=="TRAIL" else "COMMUTE_SUNSET"
            vals=[s_name,round(s_dist,1),round(s_score,4),o_name,round(o_dist,1),round(c_score,4),round(w_dist,1) if water else float("nan"),round(w_bearing,1) if water else float("nan"),round(align,1) if water else float("nan"),round(v,4),uniq.get(source,.5),hint]
            for key,val in zip(out,vals): out[key].append(val)
        for key,val in out.items(): frame[key]=val
        return frame
