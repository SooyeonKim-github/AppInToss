import pandas as pd
from .base_pattern import BasePattern, PatternResult
class BoxBreakoutPattern(BasePattern):
    pattern_id='BOX_BREAKOUT'; pattern_name='박스권 돌파'; pattern_tip='오랫동안 막히던 가격대를 넘어서는지 살펴봐요. 거래량도 같이 보면 좋아요.'; min_bars=30
    def detect(self, df:pd.DataFrame)->PatternResult:
        x=df.tail(30); prior=x.iloc[:-1]; cur=x.iloc[-1]
        resistance=float(prior['high'].tail(20).max()); support=float(prior['low'].tail(20).min())
        box_width=(resistance-support)/max(resistance,1); vol=float(cur.volume/max(prior.volume.tail(20).mean(),1))
        breakout=float(cur.close/resistance-1)
        matched=0 < box_width <= .18 and breakout >= 0 and vol >= 1.05
        score=min(100,55+max(0,vol-1)*25+max(0,breakout)*400+max(0,.18-box_width)*80) if matched else 0
        return PatternResult(matched,score,'일정 가격대에서 움직이던 주가가 상단 가격대를 넘어섰고 거래량도 확인되는 형태예요.')
