import pandas as pd
from .base_pattern import BasePattern, PatternResult
class VolumeBreakoutPattern(BasePattern):
    pattern_id='VOLUME_BREAKOUT'; pattern_name='거래량 동반 돌파'; pattern_tip='가격이 움직일 때 거래량도 함께 커지는지 확인해봐요.'; min_bars=25
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(25); cur=x.iloc[-1]; prev=x.iloc[:-1]; high=float(prev.high.tail(15).max()); vr=float(cur.volume/max(prev.volume.tail(20).mean(),1)); price=float(cur.close/high-1)
        matched=cur.close>=high and vr>=1.35 and cur.close>cur.open
        score=min(100,50+min(vr,3)*15+max(price,0)*300) if matched else 0
        return PatternResult(matched,score,'이전 고점을 넘어설 때 평소보다 거래량이 크게 늘어 움직임의 힘이 강해진 모습이에요.')
