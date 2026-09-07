from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "question_bank.csv"
if not path.exists():
    raise SystemExit("question_bank.csv not found")


def _int_value(value) -> int:
    x = pd.to_numeric(value, errors="coerce")
    return 0 if pd.isna(x) else int(x)


df = pd.read_csv(path, dtype={"ticker": str})
required = {
    "question_id",
    "pattern_type",
    "difficulty",
    "answer",
    "return_d20",
    "candles_json",
    "future_candles_json",
}
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"missing columns: {sorted(missing)}")

assert df.question_id.is_unique, "question_id must be unique"
assert set(df.answer.dropna().unique()) <= {"UP", "DOWN"}

if "feature_signals_json" in df.columns:
    feature_required = {
        "primary_features_json",
        "bullish_feature_count",
        "bearish_feature_count",
        "neutral_feature_count",
        "chart_interest_score",
        "difficulty_score",
    }
    feature_missing = feature_required - set(df.columns)
    if feature_missing:
        raise SystemExit(f"missing feature columns: {sorted(feature_missing)}")

    bad_feature_rows: list[str] = []
    bad_primary_rows: list[str] = []
    for _, row in df.iterrows():
        qid = str(row.get("question_id", ""))
        try:
            features = json.loads(row.get("feature_signals_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            features = []
        try:
            primary = json.loads(row.get("primary_features_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            primary = []

        if len(features) != 15 or len({str(x.get("key", "")) for x in features}) != 15:
            bad_feature_rows.append(qid)
        if not 1 <= len(primary) <= 4:
            bad_primary_rows.append(qid)

        counts = {
            "BULLISH": _int_value(row.get("bullish_feature_count")),
            "BEARISH": _int_value(row.get("bearish_feature_count")),
            "NEUTRAL": _int_value(row.get("neutral_feature_count")),
        }
        if sum(counts.values()) != 15:
            bad_feature_rows.append(qid)

    if bad_feature_rows:
        raise SystemExit(f"invalid 15-feature rows: {sorted(set(bad_feature_rows))[:10]}")
    if bad_primary_rows:
        raise SystemExit(f"invalid primary feature rows: {bad_primary_rows[:10]}")

    if "analyzer" in df.columns:
        engines = sorted(set(df["analyzer"].fillna("").astype(str)))
        print("[FEATURE] engines=", engines)

    print("[FEATURE] enabled: 15 chart-reading features")
    print(
        df[
            [
                "bullish_feature_count",
                "bearish_feature_count",
                "neutral_feature_count",
                "chart_interest_score",
                "difficulty_score",
            ]
        ].describe()
    )

print("[OK] rows=", len(df))
print("[ANSWER]")
print(df["answer"].value_counts(dropna=False))
print("[TYPE x ANSWER]")
print(df.groupby(["pattern_type", "answer"]).size())
