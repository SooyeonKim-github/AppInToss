import pandas as pd
from .base_pattern import BasePattern, PatternResult
class PreviousHighBreakoutPattern(BasePattern):
    pattern_id='PREVIOUS_HIGH_BREAKOUT'; pattern_name='전고점 돌파'; pattern_tip='예전에 가장 높았던 가격을 다시 넘어서는지 봐요.'; min_bars=45
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(45); prev_high=float(x.high.iloc[:-3].max()); cur=float(x.close.iloc[-1]); breakout=cur/prev_high-1
        matched=0<=breakout<=.06
        score=min(100,65+breakout*350) if matched else 0
        return PatternResult(matched,score,'최근 구간에서 가장 높았던 가격대를 다시 넘어선 모습이에요.')
