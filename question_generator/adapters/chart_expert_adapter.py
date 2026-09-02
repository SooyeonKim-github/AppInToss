from pathlib import Path
import pandas as pd

def load_confirmed_candidates(path: str|Path, min_score:float=70, min_timing:float=65)->pd.DataFrame:
    """ChartExpertAnalyzer 결과를 문제 후보 universe로 제한할 때 사용한다."""
    df=pd.read_csv(path,dtype={'ticker':str})
    if 'status' in df: df=df[df.status.astype(str).str.upper().isin(['CONFIRMED','STRONG_CONFIRMED'])]
    if 'score' in df: df=df[pd.to_numeric(df.score,errors='coerce').fillna(0)>=min_score]
    if 'timing_score' in df: df=df[pd.to_numeric(df.timing_score,errors='coerce').fillna(0)>=min_timing]
    keep=[c for c in ['scan_date','analyzer','ticker','name','score','timing_score','signal','pattern_type'] if c in df.columns]
    return df[keep].copy()
