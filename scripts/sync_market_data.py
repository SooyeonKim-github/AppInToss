from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_generator.adapters.chart_expert_market_data_adapter import (
    ChartExpertMarketDataAdapter,
)


def _default_chart_expert_root() -> Path:
    env = os.getenv("CHART_EXPERT_ROOT")
    if env:
        return Path(env)
    return ROOT.parent / "ChartExpertAnalyzer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync KOSPI/KOSDAQ OHLCV from ChartExpertAnalyzer MarketData."
    )
    parser.add_argument(
        "--chart-expert-root",
        type=Path,
        default=_default_chart_expert_root(),
        help="Path to ChartExpertAnalyzer repository.",
    )
    parser.add_argument("--info-excel", type=Path, default=None)
    parser.add_argument("--markets", nargs="+", default=["KOSPI", "KOSDAQ"])
    parser.add_argument("--top-n", type=int, default=300)
    parser.add_argument("--lookback", type=int, default=20)
    parser.add_argument("--start", default="20230101")
    parser.add_argument(
        "--end",
        default=pd.Timestamp.today().strftime("%Y%m%d"),
    )
    parser.add_argument(
        "--universe-date",
        default=None,
        help="Liquidity ranking date. Defaults to --end.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--min-rows", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    universe_date = args.universe_date or args.end

    adapter = ChartExpertMarketDataAdapter(
        args.chart_expert_root,
        info_excel=args.info_excel,
    )

    print(
        "[CONFIG] "
        f"markets={','.join(args.markets)} top_n={args.top_n} "
        f"lookback={args.lookback} universe_date={universe_date} "
        f"range={args.start}~{args.end}"
    )
    print(f"[CONFIG] ChartExpertAnalyzer={adapter.chart_expert_root}")
    print(f"[CONFIG] Universe Excel={adapter.info_excel}")

    universe = adapter.build_liquidity_universe(
        universe_date,
        top_n=args.top_n,
        lookback=args.lookback,
        markets=args.markets,
    )

    universe_dir = ROOT / "data" / "universe"
    universe_dir.mkdir(parents=True, exist_ok=True)
    universe_path = universe_dir / "korea_liquidity_universe.csv"
    universe.to_csv(universe_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] universe rows={len(universe)} -> {universe_path}")

    report = adapter.sync_ohlcv(
        universe,
        start=args.start,
        end=args.end,
        out_dir=ROOT / "data" / "ohlcv",
        overwrite=args.overwrite,
        min_rows=args.min_rows,
    )
    report_path = universe_dir / "market_data_sync_report.csv"
    report.to_csv(report_path, index=False, encoding="utf-8-sig")

    ok = (
        int(report["status"].isin(["OK", "SKIPPED_CACHED"]).sum())
        if not report.empty
        else 0
    )
    failed = int((report["status"] == "FAILED").sum()) if not report.empty else 0
    print(f"[DONE] OHLCV success={ok} failed={failed} -> {report_path}")
    print(r"[NEXT] python scripts\generate_questions.py")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
