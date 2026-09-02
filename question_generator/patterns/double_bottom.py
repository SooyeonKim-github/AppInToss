import pandas as pd
from .base_pattern import BasePattern, PatternResult
class DoubleBottomPattern(BasePattern):
    pattern_id='DOUBLE_BOTTOM'; pattern_name='쌍바닥'; pattern_tip='비슷한 가격에서 두 번 버티는 W 모양이 보이는지 찾아봐요.'; min_bars=45
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(45); lows=x.low.reset_index(drop=True); first_i=int(lows.iloc[:22].idxmin()); second_rel=int(lows.iloc[23:40].idxmin()); second_i=second_rel
        first=float(lows.iloc[first_i]); second=float(lows.iloc[second_i]); similarity=abs(second/first-1)
        middle=float(x.high.reset_index(drop=True).iloc[first_i:second_i+1].max()); cur=float(x.close.iloc[-1]); rebound=cur/min(first,second)-1
        matched=similarity<=.06 and middle/max(first,second)-1>=.05 and rebound>=.06
        score=min(100,65+(0.06-similarity)*250+rebound*80) if matched else 0
        return PatternResult(matched,score,'비슷한 가격에서 두 차례 하락이 멈추고 다시 반등하는 W형 구조가 나타났어요.')
