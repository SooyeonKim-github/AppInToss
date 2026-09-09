from __future__ import annotations

from typing import Any
import pandas as pd
from shapely.geometry import shape
from geo_utils import angular_distance_deg,bearing_deg,haversine_m,clamp01


class OpennessAnalyzer:
    def __init__(self,config:dict[str,Any]):
        a=config.get("analysis") or {}; self.radius_m=float(a.get("obstruction_radius_m",800)); self.half_angle=float(a.get("obstruction_half_angle_deg",8)); self.tree_radius_m=float(a.get("tree_radius_m",120))

    def _building_centroids(self,payload:dict[str,Any]|None)->list[tuple[float,float,float]]:
        rows=[]
        if not payload:return rows
        for feature in payload.get("features") or []:
            try:
                geom=shape(feature.get("geometry") or {}); props=feature.get("properties") or {}
                if geom.is_empty: continue
                c=geom.centroid; rows.append((float(c.y),float(c.x),float(props.get("height_m") or props.get("HEIGHT") or 18)))
            except Exception: continue
        return rows

    def annotate(self,candidates:pd.DataFrame,buildings_geojson:dict[str,Any]|None,trees:pd.DataFrame)->pd.DataFrame:
        frame=candidates.copy(); buildings=self._building_centroids(buildings_geojson); tree_points=[(float(r.latitude),float(r.longitude)) for r in trees.itertuples(index=False)] if not trees.empty else []; openness=[]; bc=[]; tc=[]
        baseline={"BRIDGE":.95,"RIVER":.94,"PEDESTRIAN_BRIDGE":.82,"TRAIL":.78,"PARK":.74,"URBAN_STREET":.60}
        for row in frame.itertuples(index=False):
            lat,lon=float(row.latitude),float(row.longitude); target=float(getattr(row,"sunset_azimuth_deg",270)); b_count=0; weighted=0.0
            for b_lat,b_lon,height in buildings:
                d=haversine_m(lat,lon,b_lat,b_lon)
                if d<=self.radius_m and angular_distance_deg(bearing_deg(lat,lon,b_lat,b_lon),target)<=self.half_angle: b_count+=1; weighted+=height/max(50.0,d)
            t_count=sum(1 for t_lat,t_lon in tree_points if haversine_m(lat,lon,t_lat,t_lon)<=self.tree_radius_m and angular_distance_deg(bearing_deg(lat,lon,t_lat,t_lon),target)<=self.half_angle*1.5)
            b_pen=min(.60,b_count*.055+weighted*.05) if buildings else 0.0; t_pen=min(.25,t_count*.04); openness.append(round(clamp01(baseline.get(str(row.source_type),.65)-b_pen-t_pen),4)); bc.append(b_count); tc.append(t_count)
        frame["openness_score"]=openness; frame["sunset_sector_building_count"]=bc; frame["sunset_sector_tree_count"]=tc; frame["obstruction_data_available"]=bool(buildings) or bool(tree_points)
        return frame
