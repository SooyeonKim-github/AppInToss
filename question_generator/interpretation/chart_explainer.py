from __future__ import annotations

from collections import Counter

from ..features.chart_feature_engine import FeatureSignal


EDUCATION_BUCKETS = {
    "TREND_STRUCTURE": {"TREND", "PRICE_STRUCTURE"},
    "MOVING_AVERAGE": {"MOVING_AVERAGE"},
    "PARTICIPATION": {"VOLUME", "MOMENTUM"},
    "CONTEXT_RISK": {"PRICE_POSITION", "VOLATILITY", "SUPPORT_RESISTANCE", "PULLBACK_REBOUND"},
}


def _bucket(signal: FeatureSignal) -> str:
    for name, categories in EDUCATION_BUCKETS.items():
        if signal.category in categories:
            return name
    return signal.category


def select_primary_features(
    signals: list[FeatureSignal],
    *,
    max_count: int = 4,
    min_strength: float = 0.42,
) -> list[FeatureSignal]:
    """Pick a readable cross-section of the base-date chart.

    The answer/future return is intentionally not an input. We prefer different
    educational viewpoints so users see trend, moving averages, participation and
    risk/context rather than four variants of the same indicator family.
    """
    if not signals:
        return []

    active = [s for s in signals if s.strength >= min_strength]
    if len(active) < max_count:
        active = sorted(signals, key=lambda x: x.strength, reverse=True)

    directional = [s for s in active if s.direction in {"BULLISH", "BEARISH"}]
    bull_strength = sum(s.strength for s in directional if s.direction == "BULLISH")
    bear_strength = sum(s.strength for s in directional if s.direction == "BEARISH")
    dominant = "BULLISH" if bull_strength >= bear_strength else "BEARISH"
    opposite = "BEARISH" if dominant == "BULLISH" else "BULLISH"

    chosen: list[FeatureSignal] = []
    used_buckets: set[str] = set()

    # 1) First cover different chart-reading viewpoints using dominant/neutral evidence.
    preferred = [s for s in active if s.direction in {dominant, "NEUTRAL"}]
    for signal in sorted(preferred, key=lambda x: x.strength, reverse=True):
        bucket = _bucket(signal)
        if bucket in used_buckets:
            continue
        chosen.append(signal)
        used_buckets.add(bucket)
        if len(chosen) >= max_count - 1:
            break

    # 2) If a meaningful counter-signal exists, keep exactly one so the quiz is not a giveaway.
    counter = sorted(
        [s for s in active if s.direction == opposite and s not in chosen],
        key=lambda x: x.strength,
        reverse=True,
    )
    if counter and len(chosen) < max_count:
        chosen.append(counter[0])

    # 3) Fill remaining slots by strength while avoiding exact duplicate keys.
    for signal in sorted(active, key=lambda x: x.strength, reverse=True):
        if signal in chosen or any(x.key == signal.key for x in chosen):
            continue
        chosen.append(signal)
        if len(chosen) >= max_count:
            break

    return chosen[:max_count]


def feature_counts(signals: list[FeatureSignal]) -> dict[str, int]:
    counts = Counter(s.direction for s in signals)
    return {
        "bullish": int(counts.get("BULLISH", 0)),
        "bearish": int(counts.get("BEARISH", 0)),
        "neutral": int(counts.get("NEUTRAL", 0)),
    }


def build_intro_tip(primary: list[FeatureSignal]) -> str:
    if not primary:
        return "차트의 추세, 이동평균선, 거래량과 변동성을 함께 살펴보세요."
    return " / ".join(signal.text for signal in primary)


def build_result_explanation(primary: list[FeatureSignal], answer: str, return_d20: float) -> str:
    result_word = "상승" if answer == "UP" else "하락"
    signed = f"{return_d20:+.1f}%"
    if not primary:
        return f"20거래일 뒤 실제 결과는 {signed} {result_word}이었어요."

    bull = [s for s in primary if s.direction == "BULLISH"]
    bear = [s for s in primary if s.direction == "BEARISH"]
    if bull and bear:
        context = "상승과 하락 쪽 특징이 함께 보였던 차트예요."
    elif bull:
        context = "상승 쪽 특징이 상대적으로 더 많이 보였던 차트예요."
    elif bear:
        context = "하락 쪽 특징이 상대적으로 더 많이 보였던 차트예요."
    else:
        context = "방향보다 차트 상태 자체를 읽는 요소가 중심이었던 차트예요."

    highlights = " ".join(signal.text for signal in primary[:3])
    return (
        f"20거래일 뒤 실제 결과는 {signed} {result_word}이었어요. "
        f"{context} 기준일에는 {highlights} "
        "각 특징은 정답을 보장하는 신호가 아니라 당시 차트 상태를 설명하는 단서로 봐주세요."
    )
