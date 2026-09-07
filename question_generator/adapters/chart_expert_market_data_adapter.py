from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


class ChartExpertMarketDataAdapter:
    """AppInToss에서 ChartExpertAnalyzer/MarketData만 얇게 재사용하는 어댑터."""

    def __init__(
        self,
        chart_expert_root: str | Path,
        *,
        info_excel: str | Path | None = None,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.chart_expert_root = Path(chart_expert_root).expanduser().resolve()
        market_data_dir = self.chart_expert_root / "MarketData"
        if not market_data_dir.exists():
            raise FileNotFoundError(
                f"ChartExpertAnalyzer/MarketData not found: {market_data_dir}"
            )

        root_text = str(self.chart_expert_root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)

        try:
            from MarketData import MarketDataService, build_liquidity_universe
        except Exception as exc:
            raise RuntimeError(
                "ChartExpertAnalyzer MarketData import failed. "
                "Install AppInToss question_generator requirements first."
            ) from exc

        self._build_liquidity_universe = build_liquidity_universe
        self.info_excel = Path(
            info_excel
            if info_excel is not None
            else self.chart_expert_root / "KJBChartAnalyzer" / "KOSPI_Info.xlsx"
        ).expanduser().resolve()
        if not self.info_excel.exists():
            raise FileNotFoundError(f"Universe Excel not found: {self.info_excel}")

        resolved_cache = (
            Path(cache_dir).expanduser().resolve()
            if cache_dir is not None
            else self.chart_expert_root / "cache" / "MarketData"
        )
        self.service = MarketDataService(cache_dir=resolved_cache, use_cache=True)

    @staticmethod
    def _normalize_markets(markets: Iterable[str]) -> tuple[str, ...]:
        result = tuple(
            dict.fromkeys(str(x).strip().upper() for x in markets if str(x).strip())
        )
        invalid = [x for x in result if x not in {"KOSPI", "KOSDAQ"}]
        if invalid:
            raise ValueError(f"Unsupported markets: {invalid}")
        if not result:
            raise ValueError("At least one market is required.")
        return result

    def build_liquidity_universe(
        self,
        as_of: str,
        *,
        top_n: int = 300,
        lookback: int = 20,
        markets: Iterable[str] = ("KOSPI", "KOSDAQ"),
    ) -> pd.DataFrame:
        market_tuple = self._normalize_markets(markets)
        universe = self._build_liquidity_universe(
            as_of,
            as_of,
            top_n=int(top_n),
            lookback=int(lookback),
            markets=market_tuple,
            info_excel=self.info_excel,
            service=self.service,
        )
        if universe is None or universe.empty:
            raise RuntimeError("Liquidity universe is empty.")

        out = universe.copy()
        out["ticker"] = out["ticker"].astype(str).str.zfill(6)
        out["market"] = out["market"].fillna("").astype(str).str.upper()
        if "name" not in out.columns:
            out["name"] = out["ticker"]
        out["name"] = out["name"].fillna(out["ticker"]).astype(str)

        if "source_rank" in out.columns:
            out["source_rank"] = pd.to_numeric(out["source_rank"], errors="coerce")
            out = out.sort_values(["source_rank", "ticker"], na_position="last")
        return out.drop_duplicates("ticker", keep="first").reset_index(drop=True)

    @staticmethod
    def _existing_covers(path: Path, start: pd.Timestamp, end: pd.Timestamp) -> bool:
        if not path.exists():
            return False
        try:
            dates = pd.read_csv(path, usecols=["date"])["date"]
            dates = pd.to_datetime(dates, errors="coerce").dropna()
            return (
                not dates.empty
                and dates.min().normalize() <= start
                and dates.max().normalize() >= end
            )
        except Exception:
            return False

    def sync_ohlcv(
        self,
        universe: pd.DataFrame,
        *,
        start: str,
        end: str,
        out_dir: str | Path,
        overwrite: bool = False,
        min_rows: int = 50,
    ) -> pd.DataFrame:
        start_ts = pd.Timestamp(start).normalize()
        end_ts = min(pd.Timestamp(end).normalize(), pd.Timestamp.today().normalize())
        if start_ts > end_ts:
            raise ValueError(f"start > end: {start_ts.date()} > {end_ts.date()}")

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        rows: list[dict] = []
        total = len(universe)

        for idx, row in universe.iterrows():
            ticker = str(row["ticker"]).zfill(6)
            raw_name = row.get("name")
            name = ticker if pd.isna(raw_name) or not str(raw_name).strip() else str(raw_name)
            raw_market = row.get("market")
            market = "" if pd.isna(raw_market) else str(raw_market).upper()
            target = out_path / f"{ticker}.csv"

            if not overwrite and self._existing_covers(target, start_ts, end_ts):
                existing = pd.read_csv(target)
                rows.append(
                    {
                        "ticker": ticker,
                        "name": name,
                        "market": market,
                        "status": "SKIPPED_CACHED",
                        "bars": int(len(existing)),
                        "path": str(target),
                        "error": "",
                    }
                )
                print(f"[SYNC] {idx + 1}/{total} {ticker} {name} -> cached")
                continue

            try:
                bars = self.service.get_ohlcv(
                    ticker,
                    start_ts,
                    end_ts,
                    market_hint=market or None,
                    allow_etf=False,
                    fallback_yfinance=True,
                )
                if bars is None or bars.empty:
                    raise RuntimeError("empty OHLCV")

                frame = bars.copy().reset_index()
                frame = frame.rename(columns={frame.columns[0]: "date"})
                frame["date"] = pd.to_datetime(
                    frame["date"], errors="coerce"
                ).dt.normalize()
                frame = frame.dropna(subset=["date"]).sort_values("date")
                frame = frame[
                    (frame["date"] >= start_ts) & (frame["date"] <= end_ts)
                ].copy()
                if len(frame) < int(min_rows):
                    raise RuntimeError(
                        f"insufficient bars: {len(frame)} < min_rows={int(min_rows)}"
                    )

                for col in ("open", "high", "low", "close", "volume"):
                    if col not in frame.columns:
                        raise RuntimeError(f"missing OHLCV column: {col}")
                if "trading_value" not in frame.columns:
                    frame["trading_value"] = (
                        pd.to_numeric(frame["close"], errors="coerce")
                        * pd.to_numeric(frame["volume"], errors="coerce").fillna(0.0)
                    )

                frame["ticker"] = ticker
                frame["name"] = name
                frame["market"] = market
                keep = [
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "trading_value",
                    "ticker",
                    "name",
                    "market",
                ]
                frame[keep].to_csv(target, index=False, encoding="utf-8-sig")
                rows.append(
                    {
                        "ticker": ticker,
                        "name": name,
                        "market": market,
                        "status": "OK",
                        "bars": int(len(frame)),
                        "path": str(target),
                        "error": "",
                    }
                )
                print(f"[SYNC] {idx + 1}/{total} {ticker} {name} -> {len(frame)} bars")
            except Exception as exc:
                rows.append(
                    {
                        "ticker": ticker,
                        "name": name,
                        "market": market,
                        "status": "FAILED",
                        "bars": 0,
                        "path": str(target),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                print(
                    f"[WARN] {idx + 1}/{total} {ticker} {name} -> "
                    f"{type(exc).__name__}: {exc}"
                )

        return pd.DataFrame(rows)
