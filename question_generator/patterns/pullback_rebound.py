import pandas as pd
from .base_pattern import BasePattern, PatternResult
class PullbackReboundPattern(BasePattern):
    pattern_id='PULLBACK_REBOUND'; pattern_name='눌림목 후 재상승'; pattern_tip='오르던 차트가 잠시 쉬었다가 다시 힘을 내는지 살펴봐요.'; min_bars=35
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(35); c=x.close; ma20=c.rolling(20).mean(); recent_high=float(c.iloc[-15:-5].max()); pull_low=float(c.iloc[-6:-1].min()); cur=float(c.iloc[-1])
        prior_run=recent_high/float(c.iloc[-25])-1; pull=(pull_low/recent_high)-1; rebound=cur/pull_low-1; above=cur>=float(ma20.iloc[-1])
        matched=prior_run>=.08 and -.15<=pull<=-.025 and rebound>=.025 and above
        score=min(100,55+prior_run*90+rebound*130-max(0,abs(pull)-.08)*100) if matched else 0
        return PatternResult(matched,score,'앞선 상승 뒤 조정을 거쳤지만 추세 기준선 부근에서 다시 반등하는 흐름이에요.')
