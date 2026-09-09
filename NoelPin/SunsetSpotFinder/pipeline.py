from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
import pandas as pd
from analyzers.context_analyzer import ContextAnalyzer
from analyzers.elevation_analyzer import ElevationAnalyzer
from analyzers.openness_analyzer import OpennessAnalyzer
from analyzers.seasonality_analyzer import SeasonalityAnalyzer
from analyzers.subway_window_analyzer import SubwayWindowAnalyzer
from analyzers.sun_analyzer import SunDirectionAnalyzer
from collectors.local_collector import LocalCollector
from config_loader import resolve_path
from generators.candidate_generator import CandidateGenerator
from generators.urban_sunset_generator import UrbanSunsetGenerator
from layer_utils import line_segments_from_geojson
from ranking.candidate_ranker import CandidateRanker
from review.exporter import ReviewExporter

STAGES={"v1":1,"v2":2,"v3":3,"v4":4,"v5":5}

@dataclass
class PipelineResult:
    candidates:pd.DataFrame
    subway_candidates:pd.DataFrame
    manifest:dict[str,Path]

class SunsetSpotFinderPipeline:
    def __init__(self,config:dict[str,Any],allow_demo:bool=True):
        self.config=config; self.allow_demo=allow_demo; self.collector=LocalCollector(config); self.output_dir=resolve_path(config,config["paths"]["output_dir"]); self.processed_dir=resolve_path(config,config["paths"]["processed_dir"]); self.output_dir.mkdir(parents=True,exist_ok=True); self.processed_dir.mkdir(parents=True,exist_ok=True); self.reference_date=date.fromisoformat(str(config["project"]["reference_date"])); self.sun=SunDirectionAnalyzer(config["project"].get("timezone","Asia/Seoul"))
    def run(self,through:str="v5")->PipelineResult:
        if through not in STAGES: raise ValueError(f"unknown stage: {through}")
        target=STAGES[through]; candidates=self._v1(); self._save(candidates,"v1_candidates.csv")
        if target==1:return PipelineResult(candidates,pd.DataFrame(),{})
        candidates=self._v2(candidates); self._save(candidates,"v2_geo_analysis.csv")
        if target==2:return PipelineResult(candidates,pd.DataFrame(),{})
        candidates=self._v3(candidates); self._save(candidates,"v3_commute_urban.csv")
        if target==3:return PipelineResult(candidates,pd.DataFrame(),{})
        subway=self._v4(); self._save(subway,"v4_subway_window.csv")
        if target==4:return PipelineResult(candidates,subway,{})
        candidates,manifest=self._v5(candidates,subway); self._save(candidates,"v5_ranked.csv"); return PipelineResult(candidates,subway,manifest)
    def _v1(self)->pd.DataFrame:
        generator=CandidateGenerator(float(self.config["project"].get("sample_interval_m",50))); candidates=generator.build(self.collector.candidate_source_payloads(),self.collector.demo_candidates() if self.allow_demo else None)
        if candidates.empty: raise RuntimeError("No candidate sources found. Put normalized files in data/raw or run without --no-demo.")
        return self.sun.annotate(candidates,self.reference_date)
    def _v2(self,candidates:pd.DataFrame)->pd.DataFrame:
        water=self.collector.load_geojson(self.config["context_layers"]["water_geojson"]); buildings=self.collector.load_geojson(self.config["context_layers"]["buildings_geojson"]); frame=ContextAnalyzer(self.config).annotate(candidates,self.collector.stations(),self.collector.office_hubs(),water); frame=ElevationAnalyzer(self.config).annotate(frame); return OpennessAnalyzer(self.config).annotate(frame,buildings,self.collector.trees())
    def _v3(self,candidates:pd.DataFrame)->pd.DataFrame:
        roads=self.collector.load_geojson(self.config["context_layers"]["roads_geojson"]); segments=line_segments_from_geojson(roads); urban=UrbanSunsetGenerator(); generated=urban.generate_from_roads(segments)
        if not generated.empty:
            generated=self.sun.annotate(generated,self.reference_date); candidates=pd.concat([candidates,generated],ignore_index=True,sort=False).drop_duplicates(subset=["source_type","latitude","longitude"]).reset_index(drop=True); candidates=self._v2(candidates)
        candidates=urban.annotate(candidates,segments); max_station=float(self.config["analysis"].get("station_max_m",1200)); candidates["is_commute_candidate"]=pd.to_numeric(candidates["station_distance_m"],errors="coerce").le(max_station); return candidates
    def _v4(self)->pd.DataFrame: return SubwayWindowAnalyzer(self.sun).build(self.collector.subway_segments(),self.reference_date)
    def _v5(self,candidates:pd.DataFrame,subway:pd.DataFrame)->tuple[pd.DataFrame,dict[str,Path]]:
        frame=CandidateRanker(self.config).rank(candidates); frame=SeasonalityAnalyzer(self.sun,self.reference_date.year).annotate(frame); return frame,ReviewExporter(self.output_dir,int(self.config["project"].get("top_n",100))).export(frame,subway)
    def _save(self,frame:pd.DataFrame,filename:str)->None: frame.to_csv(self.processed_dir/filename,index=False,encoding="utf-8-sig")
