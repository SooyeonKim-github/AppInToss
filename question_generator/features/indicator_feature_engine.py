from __future__ import annotations

"""15 chart-reading features backed by the user's Indicators repository ideas.

The public feature vocabulary stays beginner-friendly, while the numerical layer uses
moving-average structure/slope/disparity, Wilder RSI/DMI/ADX, Bollinger width/%B,
ATR, price-volume relation, and candle location. Only data available at the base date
is used; future returns are never referenced here.
"""

from typing import Callable

import numpy as np
import pandas as pd

from .chart_feature_engine import FeatureSignal


EPS = 1e-12


def _clamp(v: float) -> float:
    return float(max(0.0, min(1.0, v)))


def _safe_float(v, default: float = np.nan) -> float:
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _pct(a: float, b: float) -> float:
    if not np.isfinite(a) or not np.isfinite(b) or abs(b) < EPS:
        return 0.0
    return (a / b - 1.0) * 100.0


def _sig(category: str, key: str, label: str, state: str, direction: str,
         strength: float, text: str, value=None, metadata=None) -> FeatureSignal:
    return FeatureSignal(
        category=category,
        key=key,
        label=label,
        state=state,
        direction=direction,
        strength=_clamp(strength),
        text=text,
        value=value,
        metadata=metadata or {},
    )


def _rolling_percentile_last(values: np.ndarray) -> float:
    if len(values) == 0 or not np.isfinite(values[-1]):
        return np.nan
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        return np.nan
    return float((valid <= values[-1]).mean() * 100.0)


def add_indicator_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Add only the indicator primitives needed by the 15 beginner features.

    Formula choices intentionally mirror the user's Indicators repo:
    - MA5/20/60/120 + slope + disparity
    - Wilder smoothed ATR / +DI / -DI / ADX
    - Bollinger(20, 2) width percentile and %B
    - Wilder RSI(14)
    - price/volume and candle-location context
    """
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"feature columns missing: {sorted(missing)}")

    x = df.copy()
    for col in required:
        x[col] = pd.to_numeric(x[col], errors="coerce")
    x = x.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    if len(x) < 130:
        raise ValueError("at least 130 valid historical bars are required")

    o, h, l, c, v = (x[k] for k in ("open", "high", "low", "close", "volume"))

    # Moving averages: compatible with MovingAverageAnalysis.
    for p in (5, 20, 60, 120):
        ma = c.rolling(p, min_periods=p).mean()
        x[f"ma{p}"] = ma
        slope_lb = 5 if p <= 20 else 10
        x[f"ma{p}_slope_pct"] = (ma / ma.shift(slope_lb) - 1.0) * 100.0
        x[f"disparity{p}"] = c / ma * 100.0
        x[f"close_to_ma{p}_pct"] = (c / ma - 1.0) * 100.0

    x["return_5d"] = c.pct_change(5) * 100.0
    x["return_20d"] = c.pct_change(20) * 100.0
    x["return_60d"] = c.pct_change(60) * 100.0

    # Volume context.
    x["volume_ma20"] = v.rolling(20, min_periods=10).mean()
    x["volume_ratio20"] = v / x["volume_ma20"].replace(0, np.nan)

    # Wilder DMI/ADX: compatible with DMIAnalyzer.
    prev_close = c.shift(1)
    up_move = h.diff()
    down_move = -l.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=x.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=x.index)
    tr = pd.concat([(h - l).abs(), (h - prev_close).abs(), (l - prev_close).abs()], axis=1).max(axis=1)
    period = 14
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_sm = plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    minus_sm = minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_di = 100.0 * plus_sm / atr.replace(0, np.nan)
    minus_di = 100.0 * minus_sm / atr.replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    x["atr14"] = atr
    x["atr_pct"] = atr / c.replace(0, np.nan) * 100.0
    x["plus_di"] = plus_di
    x["minus_di"] = minus_di
    x["di_gap"] = plus_di - minus_di
    x["adx"] = adx
    x["adx_change_3d"] = adx - adx.shift(3)

    # Bollinger width / %B: compatible with BollingerBandAnalyzer.
    middle = c.rolling(20, min_periods=20).mean()
    std = c.rolling(20, min_periods=20).std(ddof=0)
    upper = middle + 2.0 * std
    lower = middle - 2.0 * std
    band_range = upper - lower
    width = band_range / middle.replace(0, np.nan) * 100.0
    x["bb_middle"] = middle
    x["bb_upper"] = upper
    x["bb_lower"] = lower
    x["bb_width_pct"] = width
    x["bb_width_change_3d_pct"] = width.pct_change(3) * 100.0
    x["bb_width_percentile"] = width.rolling(60, min_periods=30).apply(_rolling_percentile_last, raw=True)
    x["bb_percent_b"] = (c - lower) / band_range.replace(0, np.nan) * 100.0

    # Wilder RSI: compatible with OscillatorAnalysis RSIAnalyzer.
    delta = c.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.where(avg_loss.ne(0.0), 100.0)
    rsi = rsi.where(avg_gain.ne(0.0), 0.0)
    x["rsi14"] = rsi.clip(0, 100)
    x["rsi_slope_3d"] = x["rsi14"] - x["rsi14"].shift(3)

    # Candle pressure / close location.
    candle_range = (h - l).replace(0, np.nan)
    x["close_location"] = (c - l) / candle_range
    x["upper_wick_ratio"] = (h - np.maximum(o, c)) / candle_range
    x["lower_wick_ratio"] = (np.minimum(o, c) - l) / candle_range
    x["body_pct"] = (c - o) / o.replace(0, np.nan) * 100.0
    return x


def _latest(x: pd.DataFrame, col: str, default=np.nan) -> float:
    return _safe_float(x[col].iloc[-1], default)


def short_trend(x: pd.DataFrame) -> FeatureSignal:
    r5, r20 = _latest(x, "return_5d", 0), _latest(x, "return_20d", 0)
    pdi, mdi, adx = _latest(x, "plus_di", 0), _latest(x, "minus_di", 0), _latest(x, "adx", 0)
    directional = (pdi - mdi) / max(abs(pdi) + abs(mdi), 1.0)
    score = _clamp(abs(r20) / 12 * 0.55 + abs(r5) / 6 * 0.15 + abs(directional) * 0.30)
    meta = {"return_5d": round(r5, 2), "return_20d": round(r20, 2), "plus_di": round(pdi, 2), "minus_di": round(mdi, 2), "adx": round(adx, 2)}
    if r20 >= 3.5 and pdi > mdi:
        return _sig("TREND", "short_trend", "단기 추세", "RISING", "BULLISH", max(.45, score), "최근 가격이 올라오고 있고 단기 매수 방향의 힘이 더 강해요.", round(r20, 2), meta)
    if r20 <= -3.5 and mdi > pdi:
        return _sig("TREND", "short_trend", "단기 추세", "FALLING", "BEARISH", max(.45, score), "최근 가격이 낮아지고 있고 단기 매도 방향의 힘이 더 강해요.", round(r20, 2), meta)
    return _sig("TREND", "short_trend", "단기 추세", "MIXED", "NEUTRAL", .35, "최근 단기 흐름은 한 방향으로 뚜렷하게 기울지 않았어요.", round(r20, 2), meta)


def medium_trend(x: pd.DataFrame) -> FeatureSignal:
    r60 = _latest(x, "return_60d", 0)
    slope60 = _latest(x, "ma60_slope_pct", 0)
    adx, adx_chg = _latest(x, "adx", 0), _latest(x, "adx_change_3d", 0)
    pdi, mdi = _latest(x, "plus_di", 0), _latest(x, "minus_di", 0)
    strength = _clamp(abs(r60) / 25 * .45 + abs(slope60) / 4 * .25 + max(adx - 15, 0) / 35 * .30)
    meta = {"return_60d": round(r60, 2), "ma60_slope_pct": round(slope60, 2), "adx": round(adx, 2), "adx_change_3d": round(adx_chg, 2)}
    if r60 >= 7 and slope60 > 0 and pdi > mdi:
        text = "중기 가격 흐름과 60일선이 함께 올라가고 있어요."
        if adx >= 25: text = "중기 상승 방향이 뚜렷하고 추세의 힘도 강한 편이에요."
        return _sig("TREND", "medium_trend", "중기 추세", "UP_TREND", "BULLISH", max(.48, strength), text, round(r60, 2), meta)
    if r60 <= -7 and slope60 < 0 and mdi > pdi:
        text = "중기 가격 흐름과 60일선이 함께 내려가고 있어요."
        if adx >= 25: text = "중기 하락 방향이 뚜렷하고 하락 추세의 힘도 강한 편이에요."
        return _sig("TREND", "medium_trend", "중기 추세", "DOWN_TREND", "BEARISH", max(.48, strength), text, round(r60, 2), meta)
    return _sig("TREND", "medium_trend", "중기 추세", "SIDEWAYS_OR_TRANSITION", "NEUTRAL", .38, "중기 흐름은 횡보하거나 방향이 바뀌는 구간에 가까워요.", round(r60, 2), meta)


def _structure(x: pd.DataFrame, kind: str) -> FeatureSignal:
    col = "high" if kind == "high" else "low"
    s = pd.to_numeric(x[col], errors="coerce")
    prev = s.iloc[-40:-20]
    recent = s.iloc[-20:]
    if kind == "high":
        a, b = float(prev.max()), float(recent.max())
        label, key = "고점 구조", "high_structure"
        if _pct(b, a) >= 1.5:
            return _sig("PRICE_STRUCTURE", key, label, "HIGHER_HIGH", "BULLISH", _clamp(abs(_pct(b,a))/7+.25), "최근 고점이 이전 고점보다 높아지고 있어요.", round(_pct(b,a),2))
        if _pct(b, a) <= -1.5:
            return _sig("PRICE_STRUCTURE", key, label, "LOWER_HIGH", "BEARISH", _clamp(abs(_pct(b,a))/7+.25), "반등해도 고점이 이전보다 낮아지는 모습이에요.", round(_pct(b,a),2))
    else:
        a, b = float(prev.min()), float(recent.min())
        label, key = "저점 구조", "low_structure"
        if _pct(b, a) >= 1.5:
            return _sig("PRICE_STRUCTURE", key, label, "HIGHER_LOW", "BULLISH", _clamp(abs(_pct(b,a))/7+.25), "최근 저점이 이전보다 높아지며 가격을 지키고 있어요.", round(_pct(b,a),2))
        if _pct(b, a) <= -1.5:
            return _sig("PRICE_STRUCTURE", key, label, "LOWER_LOW", "BEARISH", _clamp(abs(_pct(b,a))/7+.25), "최근 저점이 다시 낮아지며 하락 구조가 이어지고 있어요.", round(_pct(b,a),2))
    return _sig("PRICE_STRUCTURE", key, label, "FLAT", "NEUTRAL", .34, f"최근 {label[:2]}은 비슷한 가격대에서 형성되고 있어요.", round(_pct(b,a),2))


def high_structure(x): return _structure(x, "high")
def low_structure(x): return _structure(x, "low")


def ma_alignment(x: pd.DataFrame) -> FeatureSignal:
    m5, m20, m60, m120 = (_latest(x, f"ma{p}") for p in (5,20,60,120))
    vals = [m5,m20,m60,m120]
    spread = (max(vals)-min(vals)) / max(abs(np.mean(vals)), EPS) * 100
    meta = {f"ma{p}": round(_latest(x,f"ma{p}"),2) for p in (5,20,60,120)}
    if m5 > m20 > m60 > m120:
        return _sig("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "BULLISH_ALIGNMENT", "BULLISH", _clamp(.45+spread/10), "5·20·60·120일선이 위에서부터 차례로 정렬된 상승 배열이에요.", "5>20>60>120", meta)
    if m5 < m20 < m60 < m120:
        return _sig("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "BEARISH_ALIGNMENT", "BEARISH", _clamp(.45+spread/10), "5·20·60·120일선이 아래에서부터 차례로 정렬된 하락 배열이에요.", "5<20<60<120", meta)
    return _sig("MOVING_AVERAGE", "ma_alignment", "이동평균선 배열", "MIXED", "NEUTRAL", .38, "이동평균선이 서로 엇갈려 있어 추세 전환이나 횡보 가능성을 함께 봐야 해요.", "MIXED", meta)


def ma_slope(x: pd.DataFrame) -> FeatureSignal:
    s20, s60 = _latest(x,"ma20_slope_pct",0), _latest(x,"ma60_slope_pct",0)
    strength = _clamp(abs(s20)/3*.55 + abs(s60)/4*.45)
    meta={"ma20_slope_pct":round(s20,2),"ma60_slope_pct":round(s60,2)}
    if s20 > .5 and s60 > .15:
        return _sig("MOVING_AVERAGE","ma_slope","이동평균선 기울기","RISING","BULLISH",max(.45,strength),"20일선과 60일선이 모두 위를 향하고 있어요.",round(s20,2),meta)
    if s20 < -.5 and s60 < -.15:
        return _sig("MOVING_AVERAGE","ma_slope","이동평균선 기울기","FALLING","BEARISH",max(.45,strength),"20일선과 60일선이 모두 아래를 향하고 있어요.",round(s20,2),meta)
    return _sig("MOVING_AVERAGE","ma_slope","이동평균선 기울기","MIXED_OR_FLAT","NEUTRAL",.35,"이동평균선의 기울기가 완만하거나 서로 다른 방향이에요.",round(s20,2),meta)


def price_vs_ma(x: pd.DataFrame) -> FeatureSignal:
    close=_latest(x,"close"); m20,m60=_latest(x,"ma20"),_latest(x,"ma60")
    d20,d60=_pct(close,m20),_pct(close,m60)
    meta={"vs_ma20_pct":round(d20,2),"vs_ma60_pct":round(d60,2)}
    if close>m20 and close>m60:
        return _sig("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","ABOVE","BULLISH",_clamp(.4+(abs(d20)+abs(d60))/20),"가격이 20일선과 60일선 위에서 움직이고 있어요.",round(d20,2),meta)
    if close<m20 and close<m60:
        return _sig("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","BELOW","BEARISH",_clamp(.4+(abs(d20)+abs(d60))/20),"가격이 20일선과 60일선 아래에서 움직이고 있어요.",round(d20,2),meta)
    return _sig("MOVING_AVERAGE","price_vs_ma","가격과 이동평균선 관계","BETWEEN","NEUTRAL",.38,"가격이 20일선과 60일선 사이에 있어 방향 확인이 더 필요해요.",round(d20,2),meta)


def ma_distance(x: pd.DataFrame) -> FeatureSignal:
    d20=_latest(x,"close_to_ma20_pct",0); slope20=_latest(x,"ma20_slope_pct",0)
    if 1 <= d20 <= 6 and slope20>0:
        return _sig("MOVING_AVERAGE","ma_distance","이동평균선 이격도","HEALTHY_ABOVE","BULLISH",_clamp(.42+d20/15),"가격이 상승 중인 20일선 위에서 과도하지 않은 거리를 유지해요.",round(d20,2))
    if d20 >= 9:
        return _sig("MOVING_AVERAGE","ma_distance","이동평균선 이격도","OVEREXTENDED_UP","BEARISH",_clamp(.55+d20/30),"가격이 20일선에서 많이 벌어져 단기 과열 부담이 있어요.",round(d20,2))
    if -6 <= d20 <= -1 and slope20<0:
        return _sig("MOVING_AVERAGE","ma_distance","이동평균선 이격도","HEALTHY_BELOW","BEARISH",_clamp(.42+abs(d20)/15),"가격이 하락 중인 20일선 아래에서 약세 흐름을 이어가고 있어요.",round(d20,2))
    if d20 <= -9:
        return _sig("MOVING_AVERAGE","ma_distance","이동평균선 이격도","OVEREXTENDED_DOWN","NEUTRAL",_clamp(.5+abs(d20)/35),"가격이 20일선 아래로 크게 벌어져 약세가 강하지만 단기 과매도 반등도 주의해야 해요.",round(d20,2))
    return _sig("MOVING_AVERAGE","ma_distance","이동평균선 이격도","NEAR_MA20","NEUTRAL",.36,"가격이 20일선 가까이에서 움직이고 있어요.",round(d20,2))


def price_position(x: pd.DataFrame) -> FeatureSignal:
    close=_latest(x,"close"); hi=float(pd.to_numeric(x.high.iloc[-60:],errors="coerce").max()); lo=float(pd.to_numeric(x.low.iloc[-60:],errors="coerce").min())
    pos=(close-lo)/max(hi-lo,EPS); pb=_latest(x,"bb_percent_b",50)
    meta={"range_position":round(pos,3),"bb_percent_b":round(pb,1)}
    if pos>=.82 and pb>=60:
        return _sig("PRICE_POSITION","price_position","최근 고점·저점 위치","NEAR_HIGH","BULLISH",_clamp(.45+(pos-.8)*2),"최근 60일 고점 가까이에서 가격을 유지하고 있어요.",round(pos,3),meta)
    if pos<=.18 and pb<=40:
        return _sig("PRICE_POSITION","price_position","최근 고점·저점 위치","NEAR_LOW","BEARISH",_clamp(.45+(.2-pos)*2),"최근 60일 저점 가까이에서 약하게 움직이고 있어요.",round(pos,3),meta)
    return _sig("PRICE_POSITION","price_position","최근 고점·저점 위치","MIDDLE","NEUTRAL",.34,"최근 60일 가격 범위의 중간권에서 움직이고 있어요.",round(pos,3),meta)


def volume_level(x: pd.DataFrame) -> FeatureSignal:
    ratio=_latest(x,"volume_ratio20",1); r5=_latest(x,"return_5d",0); clv=float(pd.to_numeric(x.close_location.iloc[-5:],errors="coerce").mean())
    meta={"volume_ratio20":round(ratio,2),"return_5d":round(r5,2),"close_location_5d":round(clv,2)}
    if ratio>=1.25 and r5>1 and clv>=.5:
        return _sig("VOLUME","volume_level","거래량 수준","EXPANDING_UP","BULLISH",_clamp(.45+(ratio-1)/1.5),"가격이 오르는 구간에서 거래량도 평소보다 늘고 있어요.",round(ratio,2),meta)
    if ratio>=1.25 and r5<-1 and clv<=.5:
        return _sig("VOLUME","volume_level","거래량 수준","EXPANDING_DOWN","BEARISH",_clamp(.45+(ratio-1)/1.5),"가격이 내려가는 구간에서 거래량도 크게 늘고 있어요.",round(ratio,2),meta)
    if ratio<=.7:
        return _sig("VOLUME","volume_level","거래량 수준","QUIET","NEUTRAL",_clamp(.4+(1-ratio)),"최근 거래량이 평소보다 줄어 방향을 확정하기엔 힘이 약해요.",round(ratio,2),meta)
    return _sig("VOLUME","volume_level","거래량 수준","NORMAL","NEUTRAL",.34,"최근 거래량은 평소와 크게 다르지 않아요.",round(ratio,2),meta)


def up_down_volume(x: pd.DataFrame) -> FeatureSignal:
    work=x.iloc[-20:].copy(); chg=pd.to_numeric(work.close,errors="coerce").diff(); vol=pd.to_numeric(work.volume,errors="coerce")
    up=float(vol[chg>0].mean()) if (chg>0).any() else np.nan
    down=float(vol[chg<0].mean()) if (chg<0).any() else np.nan
    if not np.isfinite(up) or not np.isfinite(down) or min(up,down)<=0:
        return _sig("VOLUME","up_down_volume","상승·하락일 거래량","INSUFFICIENT","NEUTRAL",.28,"오르는 날과 내리는 날의 거래량 차이는 아직 뚜렷하지 않아요.")
    ratio=up/down
    if ratio>=1.25:
        return _sig("VOLUME","up_down_volume","상승·하락일 거래량","UP_STRONGER","BULLISH",_clamp(.45+abs(np.log(ratio))/1.2),"오르는 날의 거래량이 내리는 날보다 더 강해요.",round(ratio,2))
    if ratio<=.8:
        return _sig("VOLUME","up_down_volume","상승·하락일 거래량","DOWN_STRONGER","BEARISH",_clamp(.45+abs(np.log(ratio))/1.2),"내리는 날의 거래량이 오르는 날보다 더 강해요.",round(ratio,2))
    return _sig("VOLUME","up_down_volume","상승·하락일 거래량","BALANCED","NEUTRAL",.34,"상승일과 하락일의 거래량 차이가 크지 않아요.",round(ratio,2))


def volatility(x: pd.DataFrame) -> FeatureSignal:
    atr=_latest(x,"atr_pct",0); pctile=_latest(x,"bb_width_percentile",50); width_chg=_latest(x,"bb_width_change_3d_pct",0); r5=_latest(x,"return_5d",0)
    meta={"atr_pct":round(atr,2),"bb_width_percentile":round(pctile,1),"bb_width_change_3d_pct":round(width_chg,2)}
    if pctile<=25 and abs(width_chg)<8:
        return _sig("VOLATILITY","volatility","변동성","SQUEEZE","NEUTRAL",_clamp(.48+(25-pctile)/50),"최근 가격 움직임이 평소보다 좁아져 힘을 모으는 구간이에요.",round(pctile,1),meta)
    if width_chg>=8 and r5>=1:
        return _sig("VOLATILITY","volatility","변동성","EXPANDING_UP","BULLISH",_clamp(.5+min(width_chg,30)/60),"상승하면서 가격 변동폭도 함께 넓어지고 있어요.",round(width_chg,2),meta)
    if width_chg>=8 and r5<=-1:
        return _sig("VOLATILITY","volatility","변동성","EXPANDING_DOWN","BEARISH",_clamp(.5+min(width_chg,30)/60),"하락하면서 가격 변동폭도 함께 커지고 있어요.",round(width_chg,2),meta)
    if atr>=7:
        return _sig("VOLATILITY","volatility","변동성","HIGH_VOLATILITY","NEUTRAL",_clamp(.5+(atr-7)/10),"최근 가격 흔들림이 큰 편이라 방향 예측 난도가 높아요.",round(atr,2),meta)
    return _sig("VOLATILITY","volatility","변동성","NORMAL","NEUTRAL",.33,"최근 가격 변동폭은 평소 범위에 가까워요.",round(atr,2),meta)


def momentum(x: pd.DataFrame) -> FeatureSignal:
    rsi=_latest(x,"rsi14",50); slope=_latest(x,"rsi_slope_3d",0); pdi,mdi,adx=_latest(x,"plus_di",0),_latest(x,"minus_di",0),_latest(x,"adx",0)
    meta={"rsi14":round(rsi,1),"rsi_slope_3d":round(slope,2),"plus_di":round(pdi,1),"minus_di":round(mdi,1),"adx":round(adx,1)}
    if 52<=rsi<=72 and slope>=0 and pdi>mdi:
        return _sig("MOMENTUM","momentum","모멘텀","POSITIVE","BULLISH",_clamp(.45+(rsi-50)/45+max(adx-20,0)/80),"RSI와 방향성 지표가 모두 상승 쪽 힘이 우세하다고 보여줘요.",round(rsi,1),meta)
    if 28<=rsi<=48 and slope<=0 and mdi>pdi:
        return _sig("MOMENTUM","momentum","모멘텀","NEGATIVE","BEARISH",_clamp(.45+(50-rsi)/45+max(adx-20,0)/80),"RSI와 방향성 지표가 모두 하락 쪽 힘이 우세하다고 보여줘요.",round(rsi,1),meta)
    if rsi>=72:
        return _sig("MOMENTUM","momentum","모멘텀","OVERBOUGHT","NEUTRAL",_clamp(.45+(rsi-70)/25),"상승 힘은 강하지만 RSI가 높은 구간이라 단기 과열도 함께 봐야 해요.",round(rsi,1),meta)
    if rsi<=28:
        return _sig("MOMENTUM","momentum","모멘텀","OVERSOLD","NEUTRAL",_clamp(.45+(30-rsi)/25),"하락 힘이 강하지만 RSI가 낮아 단기 반등 가능성도 함께 봐야 해요.",round(rsi,1),meta)
    return _sig("MOMENTUM","momentum","모멘텀","MIXED","NEUTRAL",.36,"상승과 하락의 힘이 한쪽으로 뚜렷하게 기울지 않았어요.",round(rsi,1),meta)


def support_resistance(x: pd.DataFrame) -> FeatureSignal:
    close=_latest(x,"close"); ma20=_latest(x,"ma20"); slope20=_latest(x,"ma20_slope_pct",0); low5=float(pd.to_numeric(x.low.iloc[-5:],errors="coerce").min()); high5=float(pd.to_numeric(x.high.iloc[-5:],errors="coerce").max())
    prior_high=float(pd.to_numeric(x.high.iloc[-25:-5],errors="coerce").max()); prior_low=float(pd.to_numeric(x.low.iloc[-25:-5],errors="coerce").min())
    tol=.015
    if low5<=ma20*(1+tol) and high5>=ma20*(1-tol) and close>ma20 and slope20>0:
        return _sig("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","MA20_SUPPORT","BULLISH",_clamp(.5+_pct(close,low5)/15),"상승 중인 20일선 부근에서 지지를 받고 다시 올라온 모습이에요.",round(_pct(close,low5),2))
    if low5<=ma20*(1+tol) and high5>=ma20*(1-tol) and close<ma20 and slope20<0:
        return _sig("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","MA20_RESISTANCE","BEARISH",_clamp(.5+abs(_pct(close,high5))/15),"반등했지만 하락 중인 20일선 부근에서 다시 밀린 모습이에요.",round(_pct(close,high5),2))
    if close>prior_high*1.01:
        return _sig("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","RESISTANCE_BREAK","BULLISH",_clamp(.5+_pct(close,prior_high)/10),"최근 여러 번 막히던 가격대를 위로 넘어섰어요.",round(_pct(close,prior_high),2))
    if close<prior_low*.99:
        return _sig("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","SUPPORT_BREAK","BEARISH",_clamp(.5+abs(_pct(close,prior_low))/10),"최근 버티던 가격대를 아래로 이탈했어요.",round(_pct(close,prior_low),2))
    return _sig("SUPPORT_RESISTANCE","support_resistance","지지·저항 반응","NO_CLEAR_REACTION","NEUTRAL",.34,"최근에는 뚜렷한 지지나 저항 반응이 확인되지 않아요.")


def pullback_rebound(x: pd.DataFrame) -> FeatureSignal:
    close=_latest(x,"close"); ma20=_latest(x,"ma20"); prior_return=_pct(_safe_float(x.close.iloc[-6]),_safe_float(x.close.iloc[-21])); recent5=_latest(x,"return_5d",0); prior_high=float(pd.to_numeric(x.high.iloc[-25:-5],errors="coerce").max()); prior_low=float(pd.to_numeric(x.low.iloc[-25:-5],errors="coerce").min())
    drawdown=_pct(close,prior_high); rebound=_pct(close,prior_low); vr=_latest(x,"volume_ratio20",1)
    meta={"prior_15d_return":round(prior_return,2),"recent_5d_return":round(recent5,2),"drawdown_from_prior_high":round(drawdown,2),"rebound_from_prior_low":round(rebound,2),"volume_ratio20":round(vr,2)}
    if prior_return>=5 and -8<=drawdown<=-1 and close>=ma20*.98 and recent5>=0:
        return _sig("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","HEALTHY_PULLBACK","BULLISH",_clamp(.48+(8-abs(drawdown))/16),"앞선 상승 뒤 조정이 깊지 않고 20일선 부근에서 다시 버티는 모습이에요.",round(drawdown,2),meta)
    if prior_return<=-5 and recent5>0 and close<ma20:
        recovery=recent5/max(abs(prior_return),EPS)
        return _sig("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","WEAK_REBOUND","BEARISH",_clamp(.5+(1-min(recovery,1))*.35),"반등은 나왔지만 이전 하락폭을 충분히 회복하지 못하고 20일선 아래에 있어요.",round(recovery,2),meta)
    if recent5<=-3 and close<ma20:
        return _sig("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","DECLINE_CONTINUING","BEARISH",_clamp(.45+abs(recent5)/15),"최근 조정이 더 깊어지고 아직 뚜렷한 회복 힘이 보이지 않아요.",round(recent5,2),meta)
    if recent5>=3 and close>ma20:
        return _sig("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","RECOVERY","BULLISH",_clamp(.45+recent5/15),"최근 눌림 뒤 가격이 20일선 위에서 다시 회복하고 있어요.",round(recent5,2),meta)
    return _sig("PULLBACK_REBOUND","pullback_rebound","조정·반등의 힘","MIXED","NEUTRAL",.34,"최근 조정이나 반등의 힘은 아직 한쪽으로 뚜렷하지 않아요.",round(recent5,2),meta)


EXTRACTORS: tuple[Callable[[pd.DataFrame], FeatureSignal], ...] = (
    short_trend,
    medium_trend,
    high_structure,
    low_structure,
    ma_alignment,
    ma_slope,
    price_vs_ma,
    ma_distance,
    price_position,
    volume_level,
    up_down_volume,
    volatility,
    momentum,
    support_resistance,
    pullback_rebound,
)


def extract_feature_signals(df: pd.DataFrame) -> list[FeatureSignal]:
    enriched = add_indicator_snapshot(df)
    signals = [fn(enriched) for fn in EXTRACTORS]
    if len(signals) != 15:
        raise RuntimeError(f"expected 15 feature signals, got {len(signals)}")
    return signals
