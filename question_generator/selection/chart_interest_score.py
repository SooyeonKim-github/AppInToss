from __future__ import annotations

from ..features.chart_feature_engine import FeatureSignal


def chart_interest_score(signals: list[FeatureSignal]) -> float:
    if not signals:
        return 0.0
    active = [s for s in signals if s.strength >= 0.42]
    top = sorted(signals, key=lambda x: x.strength, reverse=True)[:5]
    strength_score = (sum(s.strength for s in top) / max(len(top), 1)) * 45.0
    diversity_score = min(len({s.category for s in active}) / 5.0, 1.0) * 20.0

    bull = sum(s.strength for s in active if s.direction == "BULLISH")
    bear = sum(s.strength for s in active if s.direction == "BEARISH")
    total = bull + bear
    minority_ratio = min(bull, bear) / total if total > 0 else 0.0
    conflict_score = min(minority_ratio / 0.30, 1.0) * 15.0

    readability_score = min(len(active) / 5.0, 1.0) * 20.0
    return round(min(100.0, strength_score + diversity_score + conflict_score + readability_score), 2)


def feature_difficulty_score(signals: list[FeatureSignal]) -> float:
    directional = [s for s in signals if s.direction in {"BULLISH", "BEARISH"} and s.strength >= 0.35]
    if not directional:
        return 100.0

    bull = sum(s.strength for s in directional if s.direction == "BULLISH")
    bear = sum(s.strength for s in directional if s.direction == "BEARISH")
    total = bull + bear
    conflict = 2.0 * min(bull, bear) / total if total > 0 else 1.0
    top = sorted(directional, key=lambda x: x.strength, reverse=True)[:3]
    clarity = sum(s.strength for s in top) / max(len(top), 1)
    neutral_ratio = sum(1 for s in signals if s.direction == "NEUTRAL") / max(len(signals), 1)

    score = conflict * 65.0 + (1.0 - clarity) * 25.0 + neutral_ratio * 10.0
    return round(max(0.0, min(100.0, score)), 2)


def difficulty_level(score: float) -> str:
    if score <= 45.0:
        return "BEGINNER"
    if score <= 70.0:
        return "INTERMEDIATE"
    return "ADVANCED"
