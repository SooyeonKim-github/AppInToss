from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_generator.features.chart_feature_engine import extract_feature_signals


def make_df(direction: str, rows: int = 160) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=rows)
    if direction == "UP":
        close = np.linspace(100, 160, rows) + np.sin(np.arange(rows) / 4) * 1.5
        volume = np.linspace(100000, 180000, rows)
    else:
        close = np.linspace(160, 95, rows) + np.sin(np.arange(rows) / 4) * 1.5
        volume = np.linspace(100000, 190000, rows)
    return pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.995,
            "high": close * 1.015,
            "low": close * 0.985,
            "close": close,
            "volume": volume,
            "ticker": "000000",
            "name": "TEST",
            "market": "KOSPI",
        }
    )


def summarize(direction: str) -> None:
    signals = extract_feature_signals(make_df(direction))
    assert len(signals) == 15, f"expected 15 features, got {len(signals)}"
    counts = {
        "BULLISH": sum(s.direction == "BULLISH" for s in signals),
        "BEARISH": sum(s.direction == "BEARISH" for s in signals),
        "NEUTRAL": sum(s.direction == "NEUTRAL" for s in signals),
    }
    print(f"[{direction}] counts={counts}")
    for signal in signals:
        print(
            f"  {signal.label:16s} | {signal.direction:7s} | "
            f"{signal.strength:.2f} | {signal.text}"
        )
    if direction == "UP":
        assert counts["BULLISH"] > counts["BEARISH"], counts
    else:
        assert counts["BEARISH"] > counts["BULLISH"], counts


if __name__ == "__main__":
    summarize("UP")
    summarize("DOWN")
    print("[OK] 15-feature bullish/bearish smoke test passed")
