from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..classifiers.outcome_classifier import classify_outcome
from ..config.question_config import (
    CHART_LOOKBACK_BARS,
    FUTURE_DISPLAY_BARS,
    MAX_DIFFICULTY_SCORE,
    MAX_QUESTIONS_PER_TICKER,
    MIN_ACTIVE_FEATURES,
    MIN_CHART_INTEREST_SCORE,
    MIN_FEATURE_STRENGTH,
    MIN_HISTORY_BARS,
    PRIMARY_FEATURE_COUNT,
)
from ..features.chart_feature_engine import extract_feature_signals
from ..interpretation.chart_explainer import (
    build_intro_tip,
    build_result_explanation,
    feature_counts,
    select_primary_features,
)
from ..selection.chart_interest_score import (
    chart_interest_score,
    difficulty_level,
    feature_difficulty_score,
)
from ..services.chart_window_service import future_window, history_window
from ..services.future_return_service import future_returns


def _ticker_meta(df: pd.DataFrame) -> tuple[str, str, str]:
    ticker = str(df.get("ticker", pd.Series(["UNKNOWN"])).iloc[0])
    name = str(df.get("name", pd.Series([ticker])).iloc[0])
    market = str(df.get("market", pd.Series(["KR"])).iloc[0])
    return ticker, name, market


def _balanced_top_candidates(candidates: list[dict], limit: int) -> list[dict]:
    if len(candidates) <= limit:
        return sorted(candidates, key=lambda x: x["chart_interest_score"], reverse=True)

    ups = sorted(
        [x for x in candidates if x["answer"] == "UP"],
        key=lambda x: x["chart_interest_score"],
        reverse=True,
    )
    downs = sorted(
        [x for x in candidates if x["answer"] == "DOWN"],
        key=lambda x: x["chart_interest_score"],
        reverse=True,
    )

    target_each = limit // 2
    selected = ups[:target_each] + downs[:target_each]
    used = {x["question_id"] for x in selected}
    remainder = sorted(
        [x for x in candidates if x["question_id"] not in used],
        key=lambda x: x["chart_interest_score"],
        reverse=True,
    )
    selected.extend(remainder[: max(0, limit - len(selected))])
    return sorted(selected[:limit], key=lambda x: x["base_date"])


def generate_for_dataframe(df: pd.DataFrame) -> list[dict]:
    ticker, name, market = _ticker_meta(df)
    candidates: list[dict] = []

    for i in range(MIN_HISTORY_BARS, len(df) - 20):
        hist = df.iloc[: i + 1]
        returns = future_returns(df, i)
        if returns is None:
            continue

        answer = classify_outcome(returns[20])
        if answer is None:
            continue

        try:
            signals = extract_feature_signals(hist)
        except ValueError:
            continue

        active_count = sum(
            1 for signal in signals if signal.strength >= MIN_FEATURE_STRENGTH
        )
        if active_count < MIN_ACTIVE_FEATURES:
            continue

        interest = chart_interest_score(signals)
        if interest < MIN_CHART_INTEREST_SCORE:
            continue

        difficulty_score = feature_difficulty_score(signals)
        if difficulty_score > MAX_DIFFICULTY_SCORE:
            continue

        primary = select_primary_features(
            signals,
            max_count=PRIMARY_FEATURE_COUNT,
            min_strength=MIN_FEATURE_STRENGTH,
        )
        counts = feature_counts(signals)
        base_date = df.date.iloc[i].strftime("%Y-%m-%d")
        qid = f"{ticker}-{df.date.iloc[i].strftime('%Y%m%d')}-FEATURE"

        candidates.append(
            {
                "question_id": qid,
                "ticker": ticker,
                "name": name,
                "market": market,
                "base_date": base_date,
                "base_price": round(float(df.close.iloc[i]), 4),
                # Legacy columns are retained so the current API/UI remains compatible.
                "pattern_type": "FEATURE_READING",
                "pattern_name": "차트의 흐름 읽기",
                "pattern_tip": build_intro_tip(primary),
                "pattern_score": "",
                "difficulty": difficulty_level(difficulty_score),
                "difficulty_score": difficulty_score,
                "answer": answer,
                "return_d1": returns[1],
                "return_d5": returns[5],
                "return_d10": returns[10],
                "return_d20": returns[20],
                "explanation": build_result_explanation(primary, answer, returns[20]),
                "feature_signals_json": json.dumps(
                    [signal.to_dict() for signal in signals], ensure_ascii=False
                ),
                "primary_features_json": json.dumps(
                    [signal.to_dict() for signal in primary], ensure_ascii=False
                ),
                "bullish_feature_count": counts["bullish"],
                "bearish_feature_count": counts["bearish"],
                "neutral_feature_count": counts["neutral"],
                "chart_interest_score": interest,
                "candles_json": json.dumps(
                    history_window(df, i, CHART_LOOKBACK_BARS), ensure_ascii=False
                ),
                "future_candles_json": json.dumps(
                    future_window(df, i, FUTURE_DISPLAY_BARS), ensure_ascii=False
                ),
                "analyzer": "",
                "analyzer_score": "",
                "timing_score": "",
                "is_active": "true",
            }
        )

    return _balanced_top_candidates(candidates, MAX_QUESTIONS_PER_TICKER)


def export_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
