from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import folium
import pandas as pd
from review.verification import build_verification_queue,validate_verification


class ReviewExporter:
    def __init__(self,output_dir:Path,top_n:int=100): self.output_dir=output_dir; self.output_dir.mkdir(parents=True,exist_ok=True); self.top_n=top_n
    def export(self,candidates:pd.DataFrame,subway:pd.DataFrame)->dict[str,Path]:
        top=candidates.head(self.top_n).copy(); paths={"candidates":self.output_dir/"candidates.csv","top_candidates":self.output_dir/"top_candidates.csv","subway_candidates":self.output_dir/"subway_window_candidates.csv","verification_queue":self.output_dir/"verification_queue.csv","excel_report":self.output_dir/"finder_report.xlsx","map":self.output_dir/"candidate_map.html","app_candidates":self.output_dir/"noelpin_candidates.json","verified_spots":self.output_dir/"verified_spots.json"}
        candidates.to_csv(paths["candidates"],index=False,encoding="utf-8-sig"); top.to_csv(paths["top_candidates"],index=False,encoding="utf-8-sig"); subway.to_csv(paths["subway_candidates"],index=False,encoding="utf-8-sig")
        queue=build_verification_queue(top,paths["verification_queue"]); queue.to_csv(paths["verification_queue"],index=False,encoding="utf-8-sig")
        with pd.ExcelWriter(paths["excel_report"],engine="openpyxl") as writer: top.to_excel(writer,sheet_name="TOP_CANDIDATES",index=False); subway.to_excel(writer,sheet_name="SUBWAY_WINDOW",index=False); queue.to_excel(writer,sheet_name="VERIFICATION",index=False)
        self._write_map(top,subway,paths["map"]); self._write_json(top,subway,paths["app_candidates"]); self._write_verified(top,queue,paths["verified_spots"])
        with (self.output_dir/"manifest.json").open("w",encoding="utf-8") as fp: json.dump({k:str(v) for k,v in paths.items()},fp,ensure_ascii=False,indent=2)
        return paths

    def _write_map(self,top:pd.DataFrame,subway:pd.DataFrame,path:Path)->None:
        fmap=folium.Map(location=[37.545,126.98],zoom_start=11,control_scale=True)
        for row in top.itertuples(index=False):
            popup=folium.Popup(f"<b>{row.source_name}</b><br>{row.source_type} / {getattr(row,'category_hint','')}<br>우선순위 {getattr(row,'candidate_priority','')}<br>가까운 역 {getattr(row,'nearest_station','')} {getattr(row,'station_distance_m','')}m<br>일몰방향 {getattr(row,'sunset_azimuth_deg','')}°<br>검증 {getattr(row,'verification_status','CANDIDATE')}",max_width=320)
            folium.Marker([float(row.latitude),float(row.longitude)],popup=popup,tooltip=f"#{getattr(row,'rank','')} {row.source_name}",icon=folium.DivIcon(html='<div style="font-size:22px">🌅</div>')).add_to(fmap)
        for row in subway.itertuples(index=False): folium.Marker([float(row.latitude),float(row.longitude)],popup=f"<b>{row.line} {row.from_station}→{row.to_station}</b><br>{row.window_side}<br>{row.direction}",tooltip=f"🚇 {row.line} 창밖노을",icon=folium.DivIcon(html='<div style="font-size:22px">🚇</div>')).add_to(fmap)
        fmap.save(path)

    def _write_json(self,top:pd.DataFrame,subway:pd.DataFrame,path:Path)->None:
        payload:dict[str,Any]={"spots":top.where(pd.notna(top),None).to_dict(orient="records"),"subway":subway.where(pd.notna(subway),None).to_dict(orient="records")}
        with path.open("w",encoding="utf-8") as fp: json.dump(payload,fp,ensure_ascii=False,indent=2,default=str)

    def _write_verified(self,top:pd.DataFrame,queue:pd.DataFrame,path:Path)->None:
        errors=validate_verification(queue); verified=queue[queue["status"].astype(str).eq("FIELD_VERIFIED")].copy(); merged=top.merge(verified,on="candidate_id",how="inner",suffixes=("","_review")); payload={"validation_errors":errors,"spots":merged.where(pd.notna(merged),None).to_dict(orient="records")}
        with path.open("w",encoding="utf-8") as fp: json.dump(payload,fp,ensure_ascii=False,indent=2,default=str)
