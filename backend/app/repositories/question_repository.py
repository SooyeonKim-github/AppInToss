from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BANK = ROOT / "data" / "question_bank.csv"


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_questions() -> list[dict]:
    if not BANK.exists():
        return []
    out = []
    with BANK.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if str(row.get("is_active", "true")).lower() not in {"1", "true", "yes"}:
                continue
            for key in (
                "candles_json",
                "future_candles_json",
                "feature_signals_json",
                "primary_features_json",
            ):
                try:
                    row[key] = json.loads(row.get(key) or "[]")
                except json.JSONDecodeError:
                    row[key] = []
            for key in ("return_d1", "return_d5", "return_d10", "return_d20"):
                row[key] = _num(row.get(key))
            out.append(row)
    return out


def get_question(question_id: str) -> dict | None:
    return next((q for q in load_questions() if q.get("question_id") == question_id), None)
