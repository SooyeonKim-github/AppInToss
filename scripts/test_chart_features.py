from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_generator.features import add_indicator_snapshot, extract_feature_signals


def make_df(direction: str, rows: int = 180) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=rows)
    wave = np.sin(np.arange(rows) / 4) * 1.5
    if direction == "UP":
        close = np.linspace(100, 165, rows) + wave
        # Stronger volume on the latter half to make price-volume features meaningful.
        volume = np.linspace(100000, 190000, rows)
        open_ = close * 0.994
    else:
        close = np.linspace(165, 92, rows) + wave
        volume = np.linspace(100000, 200000, rows)
        open_ = close * 1.006
    return pd.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": np.maximum(open_, close) * 1.012,
            "low": np.minimum(open_, close) * 0.988,
            "close": close,
            "volume": volume,
            "ticker": "000000",
            "name": "TEST",
            "market": "KOSPI",
        }
    )


def summarize(direction: str) -> None:
    raw = make_df(direction)
    enriched = add_indicator_snapshot(raw)
    assert {"ma120", "rsi14", "plus_di", "minus_di", "adx", "bb_width_percentile", "atr_pct"}.issubset(enriched.columns)

    signals = extract_feature_signals(raw)
    assert len(signals) == 15, f"expected 15 features, got {len(signals)}"
    assert len({s.key for s in signals}) == 15, "feature keys must be unique"

    counts = {
        "BULLISH": sum(s.direction == "BULLISH" for s in signals),
        "BEARISH": sum(s.direction == "BEARISH" for s in signals),
        "NEUTRAL": sum(s.direction == "NEUTRAL" for s in signals),
    }
    print(f"[{direction}] counts={counts}")
    for signal in signals:
        print(
            f"  {signal.label:18s} | {signal.direction:7s} | "
            f"{signal.strength:.2f} | {signal.text}"
        )

    if direction == "UP":
        assert counts["BULLISH"] > counts["BEARISH"], counts
        assert enriched.iloc[-1]["plus_di"] > enriched.iloc[-1]["minus_di"]
    else:
        assert counts["BEARISH"] > counts["BULLISH"], counts
        assert enriched.iloc[-1]["minus_di"] > enriched.iloc[-1]["plus_di"]


if __name__ == "__main__":
    summarize("UP")
    summarize("DOWN")
    print("[OK] Indicators-based 15-feature smoke test passed")
