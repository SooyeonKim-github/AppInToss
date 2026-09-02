import pandas as pd
from .base_pattern import BasePattern, PatternResult
class TrendContinuationPattern(BasePattern):
    pattern_id='TREND_CONTINUATION'; pattern_name='상승 추세 유지'; pattern_tip='고점과 저점이 이전보다 조금씩 높아지는지 살펴봐요.'; min_bars=40
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(40); c=x.close; ma20=c.rolling(20).mean(); r10=float(c.iloc[-1]/c.iloc[-11]-1); r30=float(c.iloc[-1]/c.iloc[-31]-1); slope=float(ma20.iloc[-1]/ma20.iloc[-6]-1)
        h1=float(x.high.iloc[-20:-10].max()); h2=float(x.high.iloc[-10:].max()); l1=float(x.low.iloc[-20:-10].min()); l2=float(x.low.iloc[-10:].min())
        matched=r30>=.08 and r10>-.04 and slope>0 and h2>=h1 and l2>=l1*.98
        score=min(100,60+r30*70+slope*200+max(r10,0)*80) if matched else 0
        return PatternResult(matched,score,'최근 고점과 저점이 높아지고 이동평균의 방향도 위쪽을 향해 상승 추세가 이어지는 모습이에요.')
