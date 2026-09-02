import pandas as pd
from .base_pattern import BasePattern, PatternResult
class BottomBasePattern(BasePattern):
    pattern_id='BOTTOM_BASE'; pattern_name='바닥 다지기'; pattern_tip='하락이 멈춘 뒤 일정 기간 옆으로 움직이다 방향을 바꾸는지 봐요.'; min_bars=50
    def detect(self,df:pd.DataFrame)->PatternResult:
        x=df.tail(50); early=float(x.close.iloc[0]); low=float(x.low.iloc[15:35].min()); base=x.iloc[25:45]; width=(float(base.high.max())-float(base.low.min()))/max(float(base.close.mean()),1); cur=float(x.close.iloc[-1]); decline=low/early-1; recovery=cur/float(base.close.mean())-1
        matched=decline<=-.12 and width<=.12 and recovery>=.04
        score=min(100,60+abs(decline)*70+(0.12-width)*100+recovery*80) if matched else 0
        return PatternResult(matched,score,'하락 뒤 가격 변동이 줄어들며 바닥을 다진 후 다시 위쪽으로 움직이기 시작한 형태예요.')
