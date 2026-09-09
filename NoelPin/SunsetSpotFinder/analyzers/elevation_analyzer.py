from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
from config_loader import resolve_path
from geo_utils import clamp01


class ElevationAnalyzer:
    def __init__(self,config:dict[str,Any]):
        self.config=config; self.structure_bonus=(config.get("analysis") or {}).get("source_structure_bonus_m") or {}; self.dem_path=resolve_path(config,config.get("paths",{}).get("dem_path","data/raw/seoul_dem.tif"))

    def _sample_dem(self,frame:pd.DataFrame)->list[float]|None:
        if not self.dem_path.exists(): return None
        try: import rasterio
        except ImportError: return None
        with rasterio.open(self.dem_path) as ds:
            return [float(sample[0]) for sample in ds.sample([(float(r.longitude),float(r.latitude)) for r in frame.itertuples(index=False)])]

    def annotate(self,candidates:pd.DataFrame)->pd.DataFrame:
        frame=candidates.copy(); dem=self._sample_dem(frame); elevations=[]; relatives=[]; scores=[]
        for i,row in enumerate(frame.itertuples(index=False)):
            bonus=float(self.structure_bonus.get(str(row.source_type),0.0)); base=dem[i] if dem is not None and np.isfinite(dem[i]) else float("nan")
            elevations.append(round(base+bonus,2) if np.isfinite(base) else float("nan")); relatives.append(bonus); scores.append(round(clamp01(.45+bonus/20.0),4))
        frame["elevation_m"]=elevations; frame["relative_elevation_m"]=relatives; frame["elevation_score"]=scores; frame["dem_available"]=dem is not None
        return frame
