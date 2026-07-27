#!/usr/bin/env python3
"""Phase 1: 30-day backfill for Binance USD-M Futures whale data.

Usage:
    python scripts/backfill_30d.py
    python scripts/backfill_30d.py --max-symbols 5 --days-back 7
    python scripts/backfill_30d.py --dry-run
    python scripts/backfill_30d.py --resume
"""

from __future__ import annotations

import asyncio
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import structlog
import typer

# Ensure package root is on path when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import (
    META_DIR, LOGS_DIR, RATE_LIMIT_WEIGHT_PER_MIN, SEMAPHORE_SIZE,
    COINGECKO_API_KEY, KLINE_LIMIT, OI_LIMIT, RATIO_LIMIT, FUNDING_LIMIT,
    ASSUMED_RETENTION_DAYS,
)
from whale_collector.http_client import BinanceClient, RateLimiter, FetchLogger
from whale_collector.timeutil import (
    now_ms, ms_to_date_str, days_back_ms, today_str, HOUR_MS,
)
from whale_collector.binance.endpoints import PATHS
from whale_collector.binance.parsers import (
    parse_klines, parse_oi_hist, parse_top_pos, parse_top_acct,
    parse_retail, parse_taker_ratio, parse_funding,
)
from whale_collector.binance.retention import probe_all_retentions, PROBEABLE_ENDPOINTS
from whale_collector.storage.writer import write_parquet_partition, write_dataframe_direct
from whale_collector.storage.paths import universe_partition_path
from whale_collector.storage.reader import read_latest_universe
from whale_collector.universe import select_universe
from whale_collector.audit import compute_gap_report

log = structlog.get_logger()
app = typer.Typer(add_completion=False)


@dataclass
class MetricConfig:
    key: str
    path: str
    parser: Callable
    weight: int
    limit: int
    ts_extractor: Callable
    extra_params: dict
    # /futures/data/ endpoints reject startTime >= 30d (code -1130); cap at 29d
    max_lookback_days: Optional[int] = None
    # Pagination cursor step: +1ms works for klines (candle open_time is hour-aligned);
    # /futures/data/* returns [] when startTime is between period boundaries → must step
    # by exactly one period so the next call lands on a valid hour boundary.
    ts_step_ms: int = 1


HOURLY_METRICS: list[MetricConfig] = [
    MetricConfig("klines_1h", PATHS["klines"], parse_klines, 2, KLINE_LIMIT,
                 lambda x: int(x[0]), {"interval": "1h"}),
    MetricConfig("oi_hist_1h", PATHS["oi_hist"], parse_oi_hist, 1, OI_LIMIT,
                 lambda x: int(x["timestamp"]), {"period": "1h"},
                 max_lookback_days=29, ts_step_ms=HOUR_MS),
    MetricConfig("top_pos_1h", PATHS["top_pos"], parse_top_pos, 1, RATIO_LIMIT,
                 lambda x: int(x["timestamp"]), {"period": "1h"},
                 max_lookback_days=29, ts_step_ms=HOUR_MS),
    MetricConfig("top_acct_1h", PATHS["top_acct"], parse_top_acct, 1, RATIO_LIMIT,
                 lambda x: int(x["timestamp"]), {"period": "1h"},
                 max_lookback_days=29, ts_step_ms=HOUR_MS),
    MetricConfig("retail_global_1h", PATHS["retail"], parse_retail, 1, RATIO_LIMIT,
                 lambda x: int(x["timestamp"]), {"period": "1h"},
                 max_lookback_days=29, ts_step_ms=HOUR_MS),
    MetricConfig("taker_ratio_1h", PATHS["taker"], parse_taker_ratio, 1, RATIO_LIMIT,
                 lambda x: int(x["timestamp"]), {"period": "1h"},
                 max_lookback_days=29, ts_step_ms=HOUR_MS),
]

BTC_METRIC = MetricConfig("btc_market_1h", PATHS["klines"], parse_klines, 2, KLINE_LIMIT,
                           lambda x: int(x[0]), {"interval": "1h"})

FUNDING_METRIC = MetricConfig("funding_8h", PATHS["funding"], parse_funding, 1, FUNDING_LIMIT,
                               lambda x: int(x["fundingTime"]), {})

# Maps metric storage key → retention probe key (from PROBEABLE_ENDPOINTS)
# "retail_global_1h" → "retail" and "taker_ratio_1h" → "taker" differ from storage key
METRIC_TO_RETENTION_KEY: dict[str, str] = {
    "oi_hist_1h":       "oi_hist",
    "top_pos_1h":       "top_pos",
    "top_acct_1h":      "top_acct",
    "retail_global_1h": "retail",
    "taker_ratio_1h":   "taker",
}


async def _paginate(
    client: BinanceClient,
    mc: MetricConfig,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> list:
    """Paginate through an endpoint. Returns all items in chronological order.

    /futures/data/* (ts_step_ms=HOUR_MS): API returns the NEWEST `limit` items when
    range > limit. Walk endTime backward so each page covers an earlier window, then
    reassemble in chronological order.

    klines (ts_step_ms=1): API returns items ascending from startTime; walk startTime
    forward (confirmed correct).
    """
    if mc.ts_step_ms > 1:
        # Align start_ms down to the nearest period boundary so startTime is always
        # on a valid hour mark (period-based endpoints reject mid-period startTimes).
        aligned_start = (start_ms // mc.ts_step_ms) * mc.ts_step_ms

        max_pages = math.ceil((end_ms - aligned_start) / mc.ts_step_ms / mc.limit) + 2
        segments: list[list] = []
        cur_end = end_ms
        prev_cur_end = cur_end + 1  # sentinel; must strictly decrease each iteration

        for _page in range(max_pages):
            if cur_end <= aligned_start:
                break
            if cur_end >= prev_cur_end:
                log.error("paginate_endtime_not_decreasing",
                          metric=mc.key, symbol=symbol,
                          cur_end=cur_end, prev_end=prev_cur_end)
                break

            params = {
                "symbol": symbol,
                "startTime": aligned_start,
                "endTime": cur_end,
                "limit": mc.limit,
                **mc.extra_params,
            }
            log.info("paginate_request", metric=mc.key, symbol=symbol,
                     page=_page + 1, params=params)

            try:
                data = await client.get(mc.path, params, weight=mc.weight)
            except Exception as exc:
                log.error("paginate_fetch_error", metric=mc.key, symbol=symbol,
                          page=_page + 1, error=str(exc))
                break

            if not data:
                # Verify: retry once with a short delay before accepting as data edge.
                await asyncio.sleep(2)
                try:
                    data = await client.get(mc.path, params, weight=mc.weight)
                except Exception as exc:
                    log.error("paginate_fetch_error_retry", metric=mc.key, symbol=symbol,
                              page=_page + 1, error=str(exc))
                    break
                if not data:
                    break

            segments.append(data)

            if len(data) < mc.limit:
                break

            prev_cur_end = cur_end
            oldest_ts = min(mc.ts_extractor(x) for x in data)
            cur_end = oldest_ts - mc.ts_step_ms

        else:
            log.error("paginate_max_pages_reached",
                      metric=mc.key, symbol=symbol, max_pages=max_pages)

        # Post-condition: warn when collected window is still short of aligned_start
        # on a full final page — sign of a paging regression or unexpected API cap.
        # Runs even when the loop exits via break (fetch error, empty, guard) so the
        # tripwire fires on partial collections as well as normal completions.
        if segments:
            flat = [x for seg in segments for x in seg]
            collected_min_ts = min(mc.ts_extractor(x) for x in flat)
            if collected_min_ts > aligned_start + mc.ts_step_ms and len(segments[-1]) == mc.limit:
                log.warning("paginate_truncation_gap",
                            metric=mc.key, symbol=symbol,
                            collected_min_ts=collected_min_ts,
                            aligned_start=aligned_start)

        # Segments collected newest→oldest; reverse to restore chronological order
        all_items: list = []
        for seg in reversed(segments):
            all_items.extend(seg)
        return all_items

    # startTime cursor for ascending endpoints (klines — paging confirmed correct)
    all_items = []
    cur_start = start_ms
    while cur_start < end_ms:
        params = {
            "symbol": symbol,
            "startTime": cur_start,
            "endTime": end_ms,
            "limit": mc.limit,
            **mc.extra_params,
        }
        data = await client.get(mc.path, params, weight=mc.weight)
        if not data:
            break
        all_items.extend(data)
        if len(data) < mc.limit:
            break
        cur_start = mc.ts_extractor(data[-1]) + mc.ts_step_ms
    return all_items


async def _collect_symbol(
    client: BinanceClient,
    mc: MetricConfig,
    symbol: str,
    start_ms: int,
    end_ms: int,
    sem: asyncio.Semaphore,
    fetched_at_ms: int,
) -> tuple[str, int, Optional[str]]:
    """Fetch one metric for one symbol and write to storage.
    Returns (symbol, rows_written, error_message|None).
    """
    async with sem:
        try:
            data = await _paginate(client, mc, symbol, start_ms, end_ms)
        except ValueError as exc:
            return symbol, 0, f"bad_symbol: {exc}"
        except Exception as exc:
            return symbol, 0, f"{type(exc).__name__}: {exc}"

        if not data:
            return symbol, 0, None

        try:
            df = mc.parser(data, symbol, fetched_at_ms)
        except Exception as exc:
            return symbol, 0, f"parse_error: {type(exc).__name__}: {exc}"

        if df.empty:
            return symbol, 0, None

        df["_date"] = df["as_of_ts_ms"].apply(ms_to_date_str)
        try:
            for date_str, group in df.groupby("_date"):
                g = group.drop(columns=["_date"])
                await write_parquet_partition(g, mc.key, date_str)
        except Exception as exc:
            return symbol, 0, f"write_error: {type(exc).__name__}: {exc}"

        return symbol, len(df), None


async def run_backfill(
    *,
    days_back: int = 30,
    max_symbols: Optional[int] = None,
    symbols_override: Optional[list[str]] = None,
    metrics_override: Optional[list[str]] = None,
    resume: bool = False,
    workers: int = SEMAPHORE_SIZE,
    dry_run: bool = False,
) -> int:
    """Main backfill coroutine. Returns exit code (0=success, 1=failed criteria)."""
    # Setup directories
    META_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    fetch_logger = FetchLogger()
    limiter = RateLimiter(max_weight_per_min=RATE_LIMIT_WEIGHT_PER_MIN)
    # /futures/data/* pool is separate from the general fapi pool; empirically
    # saturates below the 2000 weight/min ceiling. Start conservative at 500/min.
    futures_data_limiter = RateLimiter(max_weight_per_min=500)

    now = now_ms()
    end_ms = now
    default_start_ms = days_back_ms(days_back, from_ms=now)

    # Step 1: Build universe
    log.info("building_universe")
    universe_df, _exchange_info = await select_universe(coingecko_api_key=COINGECKO_API_KEY)
    if universe_df.empty:
        log.error("universe_empty")
        return 1

    if symbols_override is not None:
        symbols = list(symbols_override)
    else:
        symbols = universe_df["symbol"].tolist()
        if max_symbols:
            symbols = symbols[:max_symbols]

    log.info("universe_ready", total=len(symbols))

    # Write universe snapshot
    snap_path = universe_partition_path(today_str())
    await write_dataframe_direct(universe_df, snap_path, overwrite=True)
    log.info("universe_snapshot_written", path=str(snap_path))

    if dry_run:
        log.info("dry_run_complete", symbols=len(symbols))
        return 0

    async with BinanceClient(limiter, fetch_logger,
                              futures_data_limiter=futures_data_limiter) as client:
        # Step 2: Probe retentions
        log.info("probing_retentions")
        retentions = await probe_all_retentions(client)

        # Save retention probe
        probe_rows = [
            {"endpoint": k, "oldest_ts_ms": v, "probed_at_ms": now}
            for k, v in retentions.items()
        ]
        probe_df = pd.DataFrame(probe_rows)
        await write_dataframe_direct(probe_df, META_DIR / "retention_probe.parquet",
                                      overwrite=True)

        sem = asyncio.Semaphore(workers)

        # Step 3: Pull BTC market data (skip if metrics_override excludes klines)
        if metrics_override is None or "klines_1h" in metrics_override:
            log.info("pulling_btc_data")
            btc_symbol, btc_rows, btc_err = await _collect_symbol(
                client, BTC_METRIC, "BTCUSDT", default_start_ms, end_ms, sem, now
            )
            if btc_err:
                log.error("btc_failed", error=btc_err)

        # Step 4: Pull hourly metrics (filtered by metrics_override when set)
        metrics_to_run = [
            mc for mc in HOURLY_METRICS
            if metrics_override is None or mc.key in metrics_override
        ]
        all_errors: dict[str, list[str]] = {}

        for mc in metrics_to_run:
            # Clamp start_ms: /futures/data/ endpoints reject startTime >= 30d (-1130)
            if mc.max_lookback_days is not None:
                cap_ms = now - mc.max_lookback_days * 86_400_000
                start_ms = max(default_start_ms, cap_ms)
            else:
                start_ms = default_start_ms
            # Also honour retention probe result (whichever is more recent wins)
            retention_key = METRIC_TO_RETENTION_KEY.get(mc.key)
            if retention_key and retention_key in retentions:
                start_ms = max(start_ms, retentions[retention_key])

            log.info("metric_start", metric=mc.key, symbols=len(symbols),
                     start=ms_to_date_str(start_ms))

            tasks = [
                _collect_symbol(client, mc, sym, start_ms, end_ms, sem, now)
                for sym in symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            errors_this_metric: list[str] = []
            total_rows = 0
            for res in results:
                if isinstance(res, Exception):
                    errors_this_metric.append(str(res))
                    continue
                sym_r, rows_r, err_r = res
                total_rows += rows_r
                if err_r:
                    errors_this_metric.append(f"{sym_r}: {err_r}")
                    log.warning("symbol_error", metric=mc.key, symbol=sym_r, error=err_r)

            all_errors[mc.key] = errors_this_metric
            log.info("metric_done", metric=mc.key, total_rows=total_rows,
                     errors=len(errors_this_metric))

        # Step 5: Pull funding rates
        log.info("pulling_funding")
        funding_tasks = [
            _collect_symbol(client, FUNDING_METRIC, sym, default_start_ms, end_ms, sem, now)
            for sym in symbols
        ]
        funding_results = await asyncio.gather(*funding_tasks, return_exceptions=True)
        funding_errors = []
        for res in funding_results:
            if isinstance(res, Exception):
                funding_errors.append(str(res))
            elif isinstance(res, tuple) and res[2]:
                funding_errors.append(f"{res[0]}: {res[2]}")
        log.info("funding_done", errors=len(funding_errors))

    # Step 6: Flush fetch log
    fetch_logger.flush(META_DIR / "fetch_log.parquet")

    # Step 7: Run audit
    log.info("running_audit")
    window_start = days_back_ms(days_back)
    all_gap_dfs: list[pd.DataFrame] = []

    hourly_metrics_keys = [mc.key for mc in HOURLY_METRICS]
    for mk in hourly_metrics_keys:
        gap_df = compute_gap_report(mk, expected_period_ms=HOUR_MS,
                                     window_start_ms=window_start, window_end_ms=now_ms())
        all_gap_dfs.append(gap_df)

    # BTC market gap check (100% completion required)
    btc_gap = compute_gap_report("btc_market_1h", expected_period_ms=HOUR_MS,
                                  window_start_ms=window_start, window_end_ms=now_ms())
    all_gap_dfs.append(btc_gap)

    # Funding gap check (8h = 28800000 ms)
    funding_gap = compute_gap_report("funding_8h", expected_period_ms=8 * 3600 * 1000,
                                      window_start_ms=window_start, window_end_ms=now_ms())
    all_gap_dfs.append(funding_gap)

    gap_report = pd.DataFrame(columns=[
        "metric", "symbol", "n_expected", "n_actual",
        "completion_pct", "largest_gap_ms", "first_gap_ts_ms", "last_gap_ts_ms",
    ])
    if all_gap_dfs:
        non_empty = [d for d in all_gap_dfs if not d.empty]
        if non_empty:
            gap_report = pd.concat(non_empty, ignore_index=True)
            await write_dataframe_direct(gap_report, META_DIR / "gap_report_latest.parquet",
                                          overwrite=True)

    # Step 8: Evaluate success criteria
    passed = True
    for mk in hourly_metrics_keys:
        sub = gap_report[gap_report["metric"] == mk] if not gap_report.empty else pd.DataFrame()
        if sub.empty:
            log.warning("criteria_no_data", metric=mk)
            passed = False
            continue
        avg_completion = sub["completion_pct"].mean()
        if avg_completion < 85.0:
            log.warning("criteria_failed", metric=mk, avg_completion=avg_completion)
            passed = False
        else:
            log.info("criteria_passed", metric=mk, avg_completion=round(avg_completion, 1))

    # BTC must have 100% completion
    btc_sub = gap_report[gap_report["metric"] == "btc_market_1h"] if not gap_report.empty else pd.DataFrame()
    if btc_sub.empty:
        log.warning("criteria_no_data", metric="btc_market_1h")
        passed = False
    else:
        btc_completion = btc_sub["completion_pct"].mean()
        if btc_completion < 100.0:
            log.warning("criteria_failed", metric="btc_market_1h", avg_completion=btc_completion)
            passed = False
        else:
            log.info("criteria_passed", metric="btc_market_1h", avg_completion=btc_completion)

    return 0 if passed else 1


RATIO_METRICS = ["oi_hist_1h", "top_pos_1h", "top_acct_1h", "retail_global_1h", "taker_ratio_1h"]


@app.command()
def main(
    days_back: int = typer.Option(30, help="Days to look back"),
    max_symbols: Optional[int] = typer.Option(None, help="Limit symbols for testing"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override list"),
    metrics: Optional[str] = typer.Option(None, help="Comma-separated metric keys; 'ratio' expands to 5 /futures/data/ metrics"),
    resume: bool = typer.Option(False, help="Skip metrics already complete"),
    workers: int = typer.Option(SEMAPHORE_SIZE, help="Concurrent symbol workers"),
    dry_run: bool = typer.Option(False, help="Probe + universe only, no pulls"),
) -> None:
    """Phase 1: 30-day backfill of Binance USD-M Futures data."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    symbols_override = [s.strip() for s in symbols.split(",")] if symbols else None
    if metrics:
        raw = [m.strip() for m in metrics.split(",")]
        metrics_override: Optional[list[str]] = []
        for m in raw:
            if m == "ratio":
                metrics_override.extend(RATIO_METRICS)
            else:
                metrics_override.append(m)
    else:
        metrics_override = None
    exit_code = asyncio.run(run_backfill(
        days_back=days_back,
        max_symbols=max_symbols,
        symbols_override=symbols_override,
        metrics_override=metrics_override,
        resume=resume,
        workers=workers,
        dry_run=dry_run,
    ))
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
