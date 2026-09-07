from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureSignal:
    category: str
    key: str
    label: str
    state: str
    direction: str
    strength: float
    text: str
    value: float | str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["strength"] = round(float(self.strength), 4)
        return data


def _clamp(v: float) -> float:
    return float(max(0.0, min(1.0, v)))


def _pct(current: float, past: float) -> float:
    if not np.isfinite(current) or not np.isfinite(past) or past == 0:
        return 0.0
    return (current / past - 1.0) * 100.0


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def _mean(s: pd.Series) -> float:
    x = pd.to_numeric(s, errors="coerce").dropna()
    return float(x.mean()) if len(x) else 0.0


def _ma(close: pd.Series, period: int) -> float:
    if len(close) < period:
        return float("nan")
    return float(close.rolling(period).mean().iloc[-1])


def _signal(category: str, key: str, label: str, state: str, direction: str, strength: float,
            text: str, value=None, metadata=None) -> FeatureSignal:
    return FeatureSignal(category, key, label, state, direction, _clamp(strength), text, value, metadata)


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    if len(gain.dropna()) == 0 or len(loss.dropna()) == 0:
        return 50.0
    g, l = float(gain.iloc[-1]), float(loss.iloc[-1])
    if l <= 0:
        return 100.0 if g > 0 else 50.0
    rs = g / l
    return 100.0 - 100.0 / (1.0 + rs)


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = _num(df, "high"), _num(df, "low"), _num(df, "close")
    prev = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def short_trend_feature(df: pd.DataFrame) -> FeatureSignal:
    c = _num(df, "close")
    r5, r20 = _pct(float(c.iloc[-1]), float(c.iloc[-6])), _pct(float(c.iloc[-1]), float(c.iloc[-21]))
    strength = _clamp(abs(r20)/12.0*0.8 + abs(r5)/6.0*0.2)
    if r20 >= 4 and r5 >= -1.5:
        return _signal("TREND", "short_trend", "단기 추세", "RISING", "BULLISH", strength,
                       "최근 가격이 꾸준히 올라오고 있어요.", round(r20,2), {"return_5d":round(r5,2),"return_20d":round(r20,2)})
    if r20 <= -4 and r5 <= 1.5:
        return _signal("TREND", "short_trend", "단기 추세", "FALLING", "BEARISH", strength,
                       "최근 가격이 계속 낮아지고 있어요.", round(r20,2), {"return_5d":round(r5,2),"return_20d":round(r20,2)})
    return _signal("TREND", "short_trend", "단기 추세", "SIDEWAYS", "NEUTRAL", max(0.3,1-abs(r20)/8),
                   "최근에는 뚜렷한 한 방향보다 옆으로 움직이는 모습이에요.", round(r20,2))


def medium_trend_feature(df: pd.DataFrame) -> FeatureSignal:
    c = _num(df, "close")
    r20, r60 = _pct(float(c.iloc[-1]), float(c.iloc[-21])), _pct(float(c.iloc[-1]), float(c.iloc[-61]))
    strength = _clamp(abs(r60)/25*0.7 + abs(r20)/12*0.3)
    if r60 >= 8 and r20 >= -3:
        return _signal("TREND", "medium_trend", "중기 추세", "RISING", "BULLISH", strength,
                       "중기적으로도 상승 흐름이 이어지고 있어요.", round(r60,2))
    if r60 <= -8 and r20 <= 3:
        return _signal("TREND", "medium_trend", "중기 추세", "FALLING", "BEARISH", strength,
                       "중기적으로 하락 흐름이 이어지고 있어요.", round(r60,2))
    return _signal("TREND", "medium_trend", "중기 추세", "MIXED", "NEUTRAL", max(0.35,strength),
                   "중기 흐름은 아직 한 방향으로 뚜렷하게 정리되지 않았어요.", round(r60,2))


def high_structure_feature(df: pd.DataFrame) -> FeatureSignal:
    h = _num(df, "high")
    recent, previous = float(h.iloc[-10:].max()), float(h.iloc[-30:-10].max())
    chg = _pct(recent, previous)
    if chg >= 1.5:
        return _signal("PRICE_STRUCTURE", "high_structure", "고점 구조", "HIGHER_HIGH", "BULLISH", abs(chg)/8,
                       "최근 고점이 이전보다 높아지고 있어요.", round(chg,2))
    if chg <= -1.5:
        return _signal("PRICE_STRUCTURE", "high_structure", "고점 구조", "LOWER_HIGH", "BEARISH", abs(chg)/8,
                       "반등하더라도 고점이 이전보다 낮아지고 있어요.", round(chg,2))
    return _signal("PRICE_STRUCTURE", "high_structure", "고점 구조", "FLAT_HIGH", "NEUTRAL", max(0.3,1-abs(chg)/3),
                   "최근 고점은 비슷한 가격대에서 형성되고 있어요.", round(chg,2))


def low_structure_feature(df: pd.DataFrame) -> FeatureSignal:
    l = _num(df, "low")
    recent, previous = float(l.iloc[-10:].min()), float(l.iloc[-30:-10].min())
    chg = _pct(recent, previous)
    if chg >= 1.5:
        return _signal("PRICE_STRUCTURE", "low_structure", "저점 구조", "HIGHER_LOW", "BULLISH", abs(chg)/8,
                       "최근 저점이 이전보다 높아지고 있어요.", round(chg,2))
    if chg <= -1.5:
        return _signal("PRICE_STRUCTURE", "low_structure", "저점 구조", "LOWER_LOW", "BEARISH", abs(chg)/8,
                       "최근 저점이 이전보다 더 낮아지고 있어요.", round(chg,2))
    return _signal("PRICE_STRUCTURE", "low_structure", "저점 구조", "FLAT_LOW", "NEUTRAL", max(0.3,1-abs(chg)/3),
                   "최근 저점은 비슷한 가격대에서 형성되고 있어요.", round(chg,2))


def ma_alignment_feature(df: pd.DataFrame) -> FeatureSignal:
    c = _num(df, "close")
    m5,m20,m60 = _ma(c,5),_ma(c,20),_ma(c,60)
    m120 = _ma(c,120) if len(c)>=120 else float("nan")
    last=float(c.iloc[-1]); spread=(max(m5,m20,m60)-min(m5,m20,m60))/last*100 if last else 0
    bullish = m5>m20>m60 and (not np.isfinite(m120) or m60>m120)
    bearish = m5<m20<m60 and (not np.isfinite(m120) or m60<m120)
    meta={"ma5":round(m5,2),"ma20":round(m20,2),"ma60":round(m60,2)}
    if np.isfinite(m120): meta["ma120"]=round(m120,2)
    if bullish:
        return _signal("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "BULLISH_ALIGNMENT", "BULLISH", spread/8+0.2,
                       "단기·중기 이동평균선이 상승 방향으로 정렬돼 있어요.", "5>20>60", meta)
    if bearish:
        return _signal("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "BEARISH_ALIGNMENT", "BEARISH", spread/8+0.2,
                       "단기·중기 이동평균선이 하락 방향으로 정렬돼 있어요.", "5<20<60", meta)
    return _signal("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "MIXED", "NEUTRAL", max(0.35,spread/12),
                   "이동평균선 배열이 서로 엇갈려 있어 방향이 아직 뚜렷하지 않아요.", "MIXED", meta)


def ma_slope_feature(df: pd.DataFrame) -> FeatureSignal:
    c=_num(df,"close"); ma20=c.rolling(20).mean(); ma60=c.rolling(60).mean()
    s20,s60=_pct(float(ma20.iloc[-1]),float(ma20.iloc[-6])),_pct(float(ma60.iloc[-1]),float(ma60.iloc[-11]))
    strength=_clamp(abs(s20)/3*0.6+abs(s60)/4*0.4)
    meta={"ma20_slope_5d_pct":round(s20,2),"ma60_slope_10d_pct":round(s60,2)}
    if s20>0.5 and s60>0.2:
        return _signal("MOVING_AVERAGE","ma_slope","이동평균선 기울기","RISING","BULLISH",strength,
                       "20일선과 60일선이 함께 위를 향하고 있어요.",round(s20,2),meta)
    if s20<-0.5 and s60<-0.2:
        return _signal("MOVING_AVERAGE","ma_slope","이동평균선 기울기","FALLING","BEARISH",strength,
                       "20일선과 60일선이 함께 아래를 향하고 있어요.",round(s20,2),meta)
    return _signal("MOVING_AVERAGE","ma_slope","이동평균선 기울기","FLAT_OR_MIXED","NEUTRAL",max(0.3,strength),
                   "이동평균선 기울기가 완만하거나 서로 다른 방향을 보고 있어요.",round(s20,2),meta)


def price_vs_ma_feature(df: pd.DataFrame) -> FeatureSignal:
    c=_num(df,"close"); last=float(c.iloc[-1]); m20,m60=_ma(c,20),_ma(c,60)
    d20,d60=_pct(last,m20),_pct(last,m60); strength=_clamp((abs(d20)+abs(d60))/14)
    meta={"vs_ma20_pct":round(d20,2),"vs_ma60_pct":round(d60,2)}
    if last>m20 and last>m60:
        return _signal("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","ABOVE","BULLISH",max(0.4,strength),
                       "가격이 20일선과 60일선 위에서 움직이고 있어요.",round(d20,2),meta)
    if last<m20 and last<m60:
        return _signal("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","BELOW","BEARISH",max(0.4,strength),
                       "가격이 20일선과 60일선 아래에서 움직이고 있어요.",round(d20,2),meta)
    return _signal("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","BETWEEN","NEUTRAL",max(0.35,strength),
                   "가격이 주요 이동평균선 사이에서 움직이고 있어요.",round(d20,2),meta)


def ma_distance_feature(df: pd.DataFrame) -> FeatureSignal:
    c=_num(df,"close"); dist=_pct(float(c.iloc[-1]),_ma(c,20)); strength=_clamp(abs(dist)/10)
    if 1<=dist<=6:
        return _signal("MOVING_AVERAGE","ma_distance","이동평균선 이격도","HEALTHY_ABOVE","BULLISH",max(0.4,strength),
                       "가격이 20일선 위에서 무리하지 않은 거리를 유지하고 있어요.",round(dist,2))
    if dist>=8:
        return _signal("MOVING_AVERAGE","ma_distance","이동평균선 이격도","OVEREXTENDED_ABOVE","BEARISH",max(0.55,strength),
                       "가격이 20일선에서 많이 멀어져 단기 부담이 커진 상태예요.",round(dist,2))
    if dist<=-8:
        return _signal("MOVING_AVERAGE","ma_distance","이동평균선 이격도","OVEREXTENDED_BELOW","BEARISH",max(0.6,strength),
                       "가격이 20일선 아래로 크게 벌어져 약세가 강한 상태예요.",round(dist,2))
    if dist<=-1:
        return _signal("MOVING_AVERAGE","ma_distance","이동평균선 이격도","BELOW","BEARISH",max(0.4,strength),
                       "가격이 20일선 아래에서 약하게 움직이고 있어요.",round(dist,2))
    return _signal("MOVING_AVERAGE","ma_distance","이동평균선 이격도","NEAR_MA20","NEUTRAL",0.4,
                   "가격이 20일 이동평균선 가까이에서 움직이고 있어요.",round(dist,2))


def price_position_feature(df: pd.DataFrame) -> FeatureSignal:
    c,h,l=_num(df,"close"),_num(df,"high"),_num(df,"low")
    hi,lo,last=float(h.iloc[-60:].max()),float(l.iloc[-60:].min()),float(c.iloc[-1])
    pos=(last-lo)/(hi-lo) if hi>lo else 0.5
    if pos>=0.8:
        return _signal("PRICE_POSITION","price_position","최근 고점·저점 위치","NEAR_HIGH","BULLISH",(pos-0.5)/0.5,
                       "최근 60일 고점 가까이에서 움직이고 있어요.",round(pos,3))
    if pos<=0.2:
        return _signal("PRICE_POSITION","price_position","최근 고점·저점 위치","NEAR_LOW","BEARISH",(0.5-pos)/0.5,
                       "최근 60일 저점 가까이 내려와 있어요.",round(pos,3))
    return _signal("PRICE_POSITION","price_position","최근 고점·저점 위치","MIDDLE","NEUTRAL",0.35,
                   "최근 60일 가격 범위의 중간 부근에서 움직이고 있어요.",round(pos,3))


def volume_level_feature(df: pd.DataFrame) -> FeatureSignal:
    v,c=_num(df,"volume"),_num(df,"close")
    recent,base=_mean(v.iloc[-5:]),_mean(v.iloc[-25:-5]); ratio=recent/base if base>0 else 1.0
    r5=_pct(float(c.iloc[-1]),float(c.iloc[-6])); strength=_clamp(abs(ratio-1)/1.2+abs(r5)/15)
    if ratio>=1.3 and r5>1:
        return _signal("VOLUME","volume_level","거래량 수준","EXPANDING_UP","BULLISH",strength,
                       "가격이 오르는 동안 평소보다 거래량도 늘고 있어요.",round(ratio,2))
    if ratio>=1.3 and r5<-1:
        return _signal("VOLUME","volume_level","거래량 수준","EXPANDING_DOWN","BEARISH",strength,
                       "가격이 내려가는 동안 거래량이 크게 늘고 있어요.",round(ratio,2))
    if ratio<=0.7:
        return _signal("VOLUME","volume_level","거래량 수준","QUIET","NEUTRAL",(1-ratio)/0.7,
                       "최근 거래량이 평소보다 줄어 조용한 흐름이에요.",round(ratio,2))
    return _signal("VOLUME","volume_level","거래량 수준","NORMAL","NEUTRAL",0.35,
                   "최근 거래량은 평소와 비슷한 수준이에요.",round(ratio,2))


def up_down_volume_feature(df: pd.DataFrame) -> FeatureSignal:
    c,v=_num(df,"close"),_num(df,"volume"); chg=c.diff(); recent=pd.DataFrame({"chg":chg.iloc[-20:],"volume":v.iloc[-20:]})
    up=_mean(recent.loc[recent.chg>0,"volume"]); down=_mean(recent.loc[recent.chg<0,"volume"])
    if up<=0 or down<=0:
        return _signal("VOLUME","up_down_volume","상승·하락일 거래량","INSUFFICIENT","NEUTRAL",0.25,
                       "상승일과 하락일 거래량 차이는 아직 뚜렷하지 않아요.",1.0)
    ratio=up/down; strength=_clamp(abs(np.log(max(ratio,1e-6)))/np.log(2.5))
    if ratio>=1.25:
        return _signal("VOLUME","up_down_volume","상승·하락일 거래량","UP_VOLUME_STRONGER","BULLISH",max(0.45,strength),
                       "오르는 날의 거래량이 내리는 날보다 더 강해요.",round(ratio,2))
    if ratio<=0.8:
        return _signal("VOLUME","up_down_volume","상승·하락일 거래량","DOWN_VOLUME_STRONGER","BEARISH",max(0.45,strength),
                       "내리는 날의 거래량이 오르는 날보다 더 강해요.",round(ratio,2))
    return _signal("VOLUME","up_down_volume","상승·하락일 거래량","BALANCED","NEUTRAL",0.35,
                   "상승일과 하락일의 거래량 차이가 크지 않아요.",round(ratio,2))


def volatility_feature(df: pd.DataFrame) -> FeatureSignal:
    c=_num(df,"close"); atr=_atr(df,14)
    recent=_mean(atr.iloc[-10:]/c.iloc[-10:]*100); previous=_mean(atr.iloc[-30:-10]/c.iloc[-30:-10]*100)
    ratio=recent/previous if previous>0 else 1.0; r10=_pct(float(c.iloc[-1]),float(c.iloc[-11])); strength=_clamp(abs(ratio-1)/0.8)
    if ratio>=1.25 and r10<=-2:
        return _signal("VOLATILITY","volatility","변동성","EXPANDING_DOWN","BEARISH",max(0.5,strength),
                       "하락하면서 가격 변동폭도 함께 커지고 있어요.",round(ratio,2))
    if ratio>=1.25 and r10>=2:
        return _signal("VOLATILITY","volatility","변동성","EXPANDING_UP","BULLISH",max(0.5,strength),
                       "상승하면서 가격 움직임도 활발해지고 있어요.",round(ratio,2))
    if ratio<=0.8:
        return _signal("VOLATILITY","volatility","변동성","CONTRACTING","NEUTRAL",max(0.45,strength),
                       "최근 가격 움직임의 폭이 점점 좁아지고 있어요.",round(ratio,2))
    return _signal("VOLATILITY","volatility","변동성","NORMAL","NEUTRAL",0.3,
                   "최근 가격 변동폭은 평소와 비슷한 수준이에요.",round(ratio,2))


def momentum_feature(df: pd.DataFrame) -> FeatureSignal:
    c=_num(df,"close"); rsi=_rsi(c,14); roc10=_pct(float(c.iloc[-1]),float(c.iloc[-11]))
    if 55<=rsi<=75 and roc10>=2:
        return _signal("MOMENTUM","momentum","모멘텀","POSITIVE","BULLISH",(rsi-50)/25*0.5+roc10/12*0.5,
                       "최근 상승 속도가 비교적 탄탄하게 유지되고 있어요.",round(rsi,2),{"roc10_pct":round(roc10,2)})
    if rsi<=45 and roc10<=-2:
        return _signal("MOMENTUM","momentum","모멘텀","NEGATIVE","BEARISH",(50-rsi)/25*0.5+abs(roc10)/12*0.5,
                       "최근 하락 속도가 강하고 매수 힘도 약한 편이에요.",round(rsi,2),{"roc10_pct":round(roc10,2)})
    if rsi>=75:
        return _signal("MOMENTUM","momentum","모멘텀","OVERHEATED","NEUTRAL",(rsi-70)/20,
                       "상승 힘은 강하지만 단기적으로 과열된 모습도 보여요.",round(rsi,2))
    if rsi<=30:
        return _signal("MOMENTUM","momentum","모멘텀","OVERSOLD","NEUTRAL",(35-rsi)/20,
                       "하락 힘이 강해 단기 과매도 구간에 가까워졌어요.",round(rsi,2))
    return _signal("MOMENTUM","momentum","모멘텀","MIXED","NEUTRAL",0.35,
                   "최근 상승·하락 속도는 한쪽으로 강하게 기울지 않았어요.",round(rsi,2))


def support_resistance_feature(df: pd.DataFrame) -> FeatureSignal:
    c,h,l=_num(df,"close"),_num(df,"high"),_num(df,"low"); last=float(c.iloc[-1]); m20=_ma(c,20)
    recent_low=float(l.iloc[-20:-1].min()); recent_high=float(h.iloc[-20:-1].max())
    touched=float(l.iloc[-5:].min())<=m20*1.015 and float(h.iloc[-5:].max())>=m20*0.985
    if touched and last>m20*1.01:
        bounce=_pct(last,float(l.iloc[-5:].min()))
        return _signal("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","MA20_SUPPORT","BULLISH",bounce/8,
                       "20일선 부근에서 밀리지 않고 다시 올라오는 모습이 보여요.",round(bounce,2))
    if touched and last<m20*0.99:
        reject=abs(_pct(last,float(h.iloc[-5:].max())))
        return _signal("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","MA20_REJECTION","BEARISH",reject/8,
                       "반등했지만 20일선 부근에서 다시 밀리는 모습이 보여요.",round(reject,2))
    if last>recent_high*1.01:
        return _signal("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","RESISTANCE_BREAK","BULLISH",_pct(last,recent_high)/6,
                       "최근 여러 번 막히던 가격대를 위로 넘어섰어요.",round(_pct(last,recent_high),2))
    if last<recent_low*0.99:
        return _signal("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","SUPPORT_BREAK","BEARISH",abs(_pct(last,recent_low))/6,
                       "최근 버티던 가격대를 아래로 이탈했어요.",round(_pct(last,recent_low),2))
    return _signal("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","NO_CLEAR_REACTION","NEUTRAL",0.3,
                   "최근에는 뚜렷한 지지나 저항 반응이 크게 나타나지 않았어요.")


def pullback_rebound_feature(df: pd.DataFrame) -> FeatureSignal:
    c,h=_num(df,"close"),_num(df,"high"); last=float(c.iloc[-1]); m20=_ma(c,20)
    prior_return=_pct(float(c.iloc[-6]),float(c.iloc[-21])); recent5=_pct(last,float(c.iloc[-6])); prior_high=float(h.iloc[-25:-5].max())
    drawdown=_pct(last,prior_high)
    if prior_return>=5 and -8<=drawdown<=-1 and recent5>=0.5:
        return _signal("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","HEALTHY_PULLBACK","BULLISH",
                       (8-abs(drawdown))/8*0.5+min(recent5,8)/8*0.5,
                       "상승 후 조정이 깊지 않고 다시 회복하려는 모습이에요.",round(drawdown,2))
    if prior_return<=-5 and recent5>0 and last<m20:
        recovery=recent5/max(abs(prior_return),1e-6)
        return _signal("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","WEAK_REBOUND","BEARISH",
                       (1-min(recovery,1))*0.6+abs(prior_return)/20*0.4,
                       "최근 반등이 나왔지만 이전 하락폭을 충분히 회복하지 못하고 있어요.",round(recovery,2))
    if recent5<=-3 and last<m20:
        return _signal("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","PULLBACK_DEEPENING","BEARISH",abs(recent5)/10,
                       "최근 조정이 깊어지며 아직 뚜렷한 반등 힘이 보이지 않아요.",round(recent5,2))
    if recent5>=3 and last>m20:
        return _signal("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","REBOUNDING","BULLISH",recent5/10,
                       "최근 조정 뒤 다시 회복하는 힘이 나타나고 있어요.",round(recent5,2))
    return _signal("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","MIXED","NEUTRAL",0.35,
                   "최근 조정과 반등의 힘은 어느 한쪽이 뚜렷하게 우세하지 않아요.",round(recent5,2))


FEATURE_EXTRACTORS=(short_trend_feature,medium_trend_feature,high_structure_feature,low_structure_feature,
                    ma_alignment_feature,ma_slope_feature,price_vs_ma_feature,ma_distance_feature,
                    price_position_feature,volume_level_feature,up_down_volume_feature,volatility_feature,
                    momentum_feature,support_resistance_feature,pullback_rebound_feature)


def extract_feature_signals(df: pd.DataFrame) -> list[FeatureSignal]:
    required={"open","high","low","close","volume"}
    missing=required-set(df.columns)
    if missing:
        raise ValueError(f"feature columns missing: {sorted(missing)}")
    if len(df)<61:
        raise ValueError("at least 61 historical bars are required for chart features")
    clean=df.copy()
    for col in required:
        clean[col]=pd.to_numeric(clean[col],errors="coerce")
    clean=clean.dropna(subset=["open","high","low","close"])
    if len(clean)<61:
        raise ValueError("insufficient valid historical bars after cleaning")
    return [extractor(clean) for extractor in FEATURE_EXTRACTORS]
