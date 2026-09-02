import pandas as pd
from .base_pattern import BasePattern, PatternResult
class MaSupportPattern(BasePattern):
    pattern_id='MA_SUPPORT'; pattern_name='이동평균선 지지'; pattern_tip='상승하던 가격이 20일선 근처에서 다시 반등하는지 봐요.'; min_bars=35
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(35).copy(); x['ma20']=x.close.rolling(20).mean(); cur=x.iloc[-1]; prev=x.iloc[-2]
        dist=(float(prev.low)/float(prev.ma20)-1) if prev.ma20 else 9; rebound=float(cur.close/prev.close-1); slope=float(x.ma20.iloc[-1]/x.ma20.iloc[-5]-1)
        matched=abs(dist)<=.035 and rebound>=.015 and slope>0 and cur.close>=cur.ma20
        score=min(100,65+rebound*200+slope*250) if matched else 0
        return PatternResult(matched,score,'상승 중 20일 이동평균선 근처에서 가격이 지지를 받고 다시 올라오는 흐름이에요.')
