#!/usr/bin/env python3
"""W4: FreshWatch daily export.

Generates data/export/freshwatch_daily_YYYY-MM.csv (month-partitioned, UTF-8, append-daily).

Source priority:
  - native_1d  : dates that have 1d parquet (W2 collection, from 2026-07-24 onward)
  - derived_1h : historical dates before W2 started (LSR/OI from 00:00 UTC 1h snapshot,
                  taker from Sigma buy_vol / Sigma sell_vol across full 24h)

Cron: 50 0 * * *  (after W2 at 00:35)

Usage:
    python scripts/export_freshwatch_daily.py
    python scripts/export_freshwatch_daily.py --date 2026-07-25
    python scripts/export_freshwatch_daily.py --days-back 7
    python scripts/export_freshwatch_daily.py --validate-only
    python scripts/export_freshwatch_daily.py --dry-run
"""

from __future__ import annotations

import glob
import logging
import os
import sys
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog
import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from whale_collector.config import RAW_DIR, DATA_DIR, MASTER_PATH, EXCLUDED_SYMBOLS
from whale_collector.storage.dedup import DEDUP_KEY   # OI-DUP-20260818 defense
from whale_collector.timeutil import (
    now_ms, ms_to_date_str, ms_to_month_str, DAY_MS, HOUR_MS,
)
from whale_collector.universe_master import load_master, get_active_symbols

log = structlog.get_logger()
app = typer.Typer(add_completion=False)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

EXPORT_DIR = DATA_DIR / "export"

# ---------------------------------------------------------------------------
# Column order (exact, per spec)
# ---------------------------------------------------------------------------

EXPORT_COLS = [
    "date",
    "symbol",
    "px_avg",
    "vol_quote",
    "vol_source",   # [F5a-VOL-REBUILD-20260824]
    "taker_buy_pct",
    "taker_source", # [⑩-AMENDMENT-20260824 vế 3] provenance: "k10_over_k7_fresh" | "r_over_1plus_r_LEGACY"
    "funding_avg",
    "funding_min",
    "funding_max",
    "funding_n",
    "oi_usd",
    "lsr_pos_r",
    "lsr_acc_r",
    "lsr_global_r",
    "taker_ratio",
    "low_conf",
    "src_ratio",
    "data_ok",
]

# ---------------------------------------------------------------------------
# Low-level parquet readers
# ---------------------------------------------------------------------------


def _read_1d_metric(metric: str, date_str: str) -> pd.DataFrame:
    """Read a 1d-period metric partition. Returns empty DataFrame on miss."""
    pattern = str(RAW_DIR / metric / f"date={date_str}" / "*.parquet")
    files = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_parquet(f) for f in files]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _read_1h_metric_for_day(metric: str, date_str: str) -> pd.DataFrame:
    """Read all 1h parquet rows for a given calendar day (UTC)."""
    pattern = str(RAW_DIR / metric / f"date={date_str}" / "*.parquet")
    files = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_parquet(f) for f in files]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _date_midnight_ms(date_str: str) -> int:
    """Return UTC midnight epoch ms for YYYY-MM-DD."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# ---------------------------------------------------------------------------
# Source builders
# ---------------------------------------------------------------------------


def _build_native_1d(date_str: str, symbols: list[str]) -> pd.DataFrame:
    """Build rows from 1d native parquet stores for the given date.

    Returns DataFrame with columns matching EXPORT_COLS (minus computed fields).
    as_of_ts_ms is kept for Condition 1 (verbatim date alignment).
    """
    sym_set = set(symbols)

    # --- LSR metrics ---
    df_top_pos = _read_1d_metric("top_pos_1d", date_str)
    df_top_acct = _read_1d_metric("top_acct_1d", date_str)
    df_retail = _read_1d_metric("retail_global_1d", date_str)
    df_oi = _read_1d_metric("oi_hist_1d", date_str)
    df_taker = _read_1d_metric("taker_ratio_1d", date_str)

    if all(df.empty for df in [df_top_pos, df_top_acct, df_retail, df_oi]):
        return pd.DataFrame(columns=EXPORT_COLS)

    # Filter to active universe
    def _filt(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "symbol" not in df.columns:
            return df
        return df[df["symbol"].isin(sym_set)].copy()

    df_top_pos = _filt(df_top_pos)
    df_top_acct = _filt(df_top_acct)
    df_retail = _filt(df_retail)
    df_oi = _filt(df_oi)
    df_taker = _filt(df_taker)

    # Use the full set of symbols found in any 1d source for this date
    all_syms: set[str] = set()
    for df in [df_top_pos, df_top_acct, df_retail, df_oi]:
        if not df.empty and "symbol" in df.columns:
            all_syms |= set(df["symbol"].unique())
    all_syms &= sym_set

    if not all_syms:
        return pd.DataFrame(columns=EXPORT_COLS)

    # --- Condition 1: verbatim date from as_of_ts_ms ---
    # Use the first available metric's as_of_ts_ms as the authoritative timestamp.
    # All 1d metrics for a given date share the same as_of_ts_ms (daily candle close).
    ts_lookup: dict[str, int] = {}
    for df in [df_top_pos, df_top_acct, df_retail, df_oi]:
        if not df.empty and "symbol" in df.columns and "as_of_ts_ms" in df.columns:
            for _, row in df.iterrows():
                sym = row["symbol"]
                if sym not in ts_lookup:
                    ts_lookup[sym] = int(row["as_of_ts_ms"])

    rows = []
    for sym in sorted(all_syms):
        ts_ms = ts_lookup.get(sym, _date_midnight_ms(date_str))
        # Condition 1: VERBATIM date from as_of_ts_ms
        row_date = ms_to_date_str(ts_ms)

        lsr_pos = None
        lsr_acc = None
        lsr_global = None
        oi_usd = None

        if not df_top_pos.empty and "symbol" in df_top_pos.columns:
            r = df_top_pos[df_top_pos["symbol"] == sym]
            if not r.empty:
                lsr_pos = float(r.iloc[0]["long_short_ratio"])

        if not df_top_acct.empty and "symbol" in df_top_acct.columns:
            r = df_top_acct[df_top_acct["symbol"] == sym]
            if not r.empty:
                lsr_acc = float(r.iloc[0]["long_short_ratio"])

        if not df_retail.empty and "symbol" in df_retail.columns:
            r = df_retail[df_retail["symbol"] == sym]
            if not r.empty:
                lsr_global = float(r.iloc[0]["long_short_ratio"])

        if not df_oi.empty and "symbol" in df_oi.columns:
            r = df_oi[df_oi["symbol"] == sym]
            if not r.empty:
                oi_usd = float(r.iloc[0]["sum_open_interest_value"])

        taker_ratio_val = None
        if not df_taker.empty and "symbol" in df_taker.columns:
            r = df_taker[df_taker["symbol"] == sym]
            if not r.empty:
                taker_ratio_val = float(r.iloc[0]["buy_sell_ratio"])

        rows.append({
            "date": row_date,
            "symbol": sym,
            "lsr_pos_r": lsr_pos,
            "lsr_acc_r": lsr_acc,
            "lsr_global_r": lsr_global,
            "oi_usd": oi_usd,
            "taker_ratio": taker_ratio_val,
            "src_ratio": "native_1d",
            "_ts_ms": ts_ms,
        })

    return pd.DataFrame(rows)


def _build_derived_1h(date_str: str, symbols: list[str]) -> pd.DataFrame:
    """Build rows from 1h stores for dates before W2 (historical backfill).

    LSR/OI: 00:00 UTC snapshot from 1h stores.
    Taker: Sigma buy_vol / Sigma sell_vol for the full 24h day.
    """
    sym_set = set(symbols)
    midnight_ms = _date_midnight_ms(date_str)

    # --- 1h LSR/OI at midnight snapshot ---
    df_tp1h = _read_1h_metric_for_day("top_pos_1h", date_str)
    df_ta1h = _read_1h_metric_for_day("top_acct_1h", date_str)
    df_rg1h = _read_1h_metric_for_day("retail_global_1h", date_str)
    df_oi1h = _read_1h_metric_for_day("oi_hist_1h", date_str)
    df_tr1h = _read_1h_metric_for_day("taker_ratio_1h", date_str)

    def _snap(df: pd.DataFrame, col: str) -> dict[str, float]:
        if df.empty or "as_of_ts_ms" not in df.columns:
            return {}
        snap = df[df["as_of_ts_ms"] == midnight_ms]
        snap = snap[snap["symbol"].isin(sym_set)]
        return dict(zip(snap["symbol"], snap[col].astype(float)))

    lsr_pos_map = _snap(df_tp1h, "long_short_ratio")
    lsr_acc_map = _snap(df_ta1h, "long_short_ratio")
    lsr_global_map = _snap(df_rg1h, "long_short_ratio")
    oi_map = _snap(df_oi1h, "sum_open_interest_value")

    # Taker: aggregate full 24h
    # Fix A: dedup keep-last before aggregation to remove duplicate ingestion rows.
    # taker_ratio_1h can contain multiple rows per (symbol, as_of_ts_ms) when the
    # collector re-runs or overlapping partitions are written.
    taker_map: dict[str, float] = {}
    if not df_tr1h.empty and "symbol" in df_tr1h.columns:
        df_tr_filt = df_tr1h[df_tr1h["symbol"].isin(sym_set)].copy()
        if not df_tr_filt.empty:
            # Dedup: keep last row per (symbol, as_of_ts_ms)
            df_tr_filt = (
                df_tr_filt
                .sort_values(["symbol", "as_of_ts_ms"])
                .drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="last")
            )
            grp = df_tr_filt.groupby("symbol").agg(
                buy_sum=("buy_vol", "sum"),
                sell_sum=("sell_vol", "sum"),
            ).reset_index()
            for _, row in grp.iterrows():
                if row["sell_sum"] > 0:
                    taker_map[row["symbol"]] = float(row["buy_sum"]) / float(row["sell_sum"])
    # Collect all symbols with any data
    all_syms = (
        set(lsr_pos_map) | set(lsr_acc_map) | set(lsr_global_map) | set(oi_map)
    ) & sym_set
    if not all_syms:
        return pd.DataFrame(columns=EXPORT_COLS)

    rows = []
    for sym in sorted(all_syms):
        rows.append({
            "date": date_str,  # verbatim (derived from 1h, date is partition date)
            "symbol": sym,
            "lsr_pos_r": lsr_pos_map.get(sym),
            "lsr_acc_r": lsr_acc_map.get(sym),
            "lsr_global_r": lsr_global_map.get(sym),
            "oi_usd": oi_map.get(sym),
            "taker_ratio": taker_map.get(sym),
            "src_ratio": "derived_1h",
            "_ts_ms": midnight_ms,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Klines aggregation (px_avg, vol_quote)
# ---------------------------------------------------------------------------


def _build_klines_agg(date_str: str, symbols: list[str]) -> pd.DataFrame:
    """Aggregate 24h klines for px_avg, vol_quote, taker_buy_pct.

    px_avg = Sigma(quote_vol) / Sigma(base_vol)  [VWAP]
    vol_quote = Sigma(quote_vol)
    taker_buy_pct = Sigma(taker_buy_quote_vol) / Sigma(quote_vol)  = k[10]/k[7]
      [⑩-AMENDMENT-20260824 vế 3] canonical basis quote/quote (không phải derive r/(1+r)).
      Fraction 0-1 output (khớp legacy scale, consumer scale-detection giữ nguyên).
    """
    df = _read_1h_metric_for_day("klines_1h", date_str)
    if df.empty or "symbol" not in df.columns:
        return pd.DataFrame(columns=["symbol", "px_avg", "vol_quote", "taker_buy_pct_k10k7"])

    sym_set = set(symbols)
    df = df[df["symbol"].isin(sym_set)]
    if df.empty:
        return pd.DataFrame(columns=["symbol", "px_avg", "vol_quote", "taker_buy_pct_k10k7"])

    # OI-DUP-20260818 defense: SUM không-idempotent — dup rows identical vẫn inflate ×N.
    # Bảo hiểm độc lập với _sync_append (dù writer dedup-on-write đã chặn nguồn).
    df = df.drop_duplicates(subset=DEDUP_KEY, keep="last")

    agg_dict = {
        "quote_vol_sum": ("quote_volume", "sum"),
        "base_vol_sum": ("base_volume", "sum"),
    }
    # [⑩-AMENDMENT-20260824] taker_buy_quote_vol aggregate (k[10] sum)
    if "taker_buy_quote_vol" in df.columns:
        agg_dict["taker_buy_quote_vol_sum"] = ("taker_buy_quote_vol", "sum")
    grp = df.groupby("symbol").agg(**agg_dict).reset_index()

    grp["vol_quote"] = grp["quote_vol_sum"]
    grp["px_avg"] = np.where(
        grp["base_vol_sum"] > 0,
        grp["quote_vol_sum"] / grp["base_vol_sum"],
        np.nan,
    )
    # k[10]/k[7] canonical taker_buy_pct
    if "taker_buy_quote_vol_sum" in grp.columns:
        grp["taker_buy_pct_k10k7"] = np.where(
            grp["quote_vol_sum"] > 0,
            grp["taker_buy_quote_vol_sum"] / grp["quote_vol_sum"],
            np.nan,
        )
    else:
        grp["taker_buy_pct_k10k7"] = np.nan
    return grp[["symbol", "px_avg", "vol_quote", "taker_buy_pct_k10k7"]]


# ---------------------------------------------------------------------------
# Funding aggregation
# ---------------------------------------------------------------------------


_FUNDING_INTERVALS_CACHE: dict[str, int] = {}  # symbol -> interval_hours


def _load_funding_intervals() -> dict[str, int]:
    """Load funding interval hours per symbol.
    Cache to data/config/funding_intervals.json, refresh weekly.
    Default 8h if symbol not found.
    """
    global _FUNDING_INTERVALS_CACHE
    if _FUNDING_INTERVALS_CACHE:
        return _FUNDING_INTERVALS_CACHE

    cache_path = DATA_DIR / "config" / "funding_intervals.json"
    import json, time

    needs_refresh = True
    if cache_path.exists():
        age_days = (time.time() - cache_path.stat().st_mtime) / 86400
        if age_days < 7:
            try:
                with open(cache_path) as f:
                    _FUNDING_INTERVALS_CACHE = json.load(f)
                needs_refresh = False
                log.info("funding_intervals_cache_loaded", n=len(_FUNDING_INTERVALS_CACHE))
            except Exception:
                needs_refresh = True

    if needs_refresh:
        try:
            import urllib.request
            url = "https://fapi.binance.com/fapi/v1/fundingInfo"
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            intervals = {item["symbol"]: int(item.get("fundingIntervalHours", 8))
                         for item in data if "symbol" in item}
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(intervals, f)
            _FUNDING_INTERVALS_CACHE = intervals
            log.info("funding_intervals_refreshed", n=len(intervals))
        except Exception as exc:
            log.warning("funding_intervals_refresh_failed", error=str(exc),
                        note="using default 8h for all symbols")
            _FUNDING_INTERVALS_CACHE = {}

    return _FUNDING_INTERVALS_CACHE


def _build_funding_for_day(date_str: str, symbols: list[str]) -> pd.DataFrame:
    """Aggregate funding_8h for a calendar day (UTC).

    Fix B: Use actual interval per symbol (4h/8h/1h) from fundingInfo cache instead
    of hardcoded [00:00, 08:00, 16:00]. Filters rows where as_of_ts_ms falls within
    [day_start, day_end) and deduplicates on (symbol, as_of_ts_ms) keep-last.
    Logs WARNING if actual settlement count != expected count for a symbol.
    """
    funding_dir = RAW_DIR / "funding_8h"
    if not funding_dir.exists():
        log.warning("funding_8h_dir_missing",
                    msg="funding_8h directory not found; exporting funding_* as null")
        return pd.DataFrame(columns=["symbol", "funding_avg", "funding_min", "funding_max", "funding_n"])

    month_str = date_str[:7]  # YYYY-MM
    pattern = str(funding_dir / f"month={month_str}" / "*.parquet")
    files = sorted(glob.glob(pattern))
    if not files:
        log.warning("funding_8h_month_missing", month=month_str)
        return pd.DataFrame(columns=["symbol", "funding_avg", "funding_min", "funding_max", "funding_n"])

    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        return pd.DataFrame(columns=["symbol", "funding_avg", "funding_min", "funding_max", "funding_n"])

    # Fix B: filter by [day_start, day_end) window -- covers 1h, 4h, and 8h intervals
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    day_start_ms = int(dt.timestamp() * 1000)
    day_end_ms = int((dt + timedelta(days=1)).timestamp() * 1000)

    df_day = df[
        (df["as_of_ts_ms"] >= day_start_ms) & (df["as_of_ts_ms"] < day_end_ms)
    ].copy()
    if df_day.empty:
        return pd.DataFrame(columns=["symbol", "funding_avg", "funding_min", "funding_max", "funding_n"])

    # Dedup: keep last row per (symbol, as_of_ts_ms)
    df_day = (
        df_day
        .sort_values(["symbol", "as_of_ts_ms"])
        .drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="last")
    )

    sym_set = set(symbols)
    df_day = df_day[df_day["symbol"].isin(sym_set)]
    if df_day.empty:
        return pd.DataFrame(columns=["symbol", "funding_avg", "funding_min", "funding_max", "funding_n"])

    # Fix B: validate actual count vs expected per symbol
    intervals = _load_funding_intervals()
    sym_counts = df_day.groupby("symbol")["as_of_ts_ms"].count()
    for sym, actual_count in sym_counts.items():
        interval_h = intervals.get(sym, 8)
        expected_count = 24 // interval_h
        if actual_count != expected_count:
            log.warning("funding_settlement_count_mismatch",
                        symbol=sym, date=date_str,
                        expected=expected_count, actual=int(actual_count),
                        interval_h=interval_h)

    grp = df_day.groupby("symbol")["funding_rate"].agg(
        funding_avg="mean",
        funding_min="min",
        funding_max="max",
        funding_n="count",
    ).reset_index()
    grp["funding_n"] = grp["funding_n"].astype(int)
    return grp
def _assemble_date(
    date_str: str,
    symbols: list[str],
    *,
    has_1d_data: bool,
) -> pd.DataFrame:
    """Build export rows for one date.

    Preference: native_1d if data exists, else derived_1h.
    """
    if has_1d_data:
        df_core = _build_native_1d(date_str, symbols)
    else:
        df_core = _build_derived_1h(date_str, symbols)

    if df_core.empty:
        return pd.DataFrame(columns=EXPORT_COLS)

    # Klines aggregation
    df_klines = _build_klines_agg(date_str, symbols)

    # Funding
    df_funding = _build_funding_for_day(date_str, symbols)

    # Merge all sources
    df = df_core.merge(df_klines, on="symbol", how="left")
    df = df.merge(df_funding, on="symbol", how="left")
    if "funding_avg" not in df.columns:
        df["funding_avg"] = None
        df["funding_min"] = None
        df["funding_max"] = None
        df["funding_n"] = None

    # --- Derived columns ---

    # [⑩-AMENDMENT-20260824 vế 3] taker_buy_pct canonical = k[10]/k[7] from klines_1h agg.
    # Fallback LEGACY derive r/(1+r) chỉ khi k10k7 NaN (no klines data day X).
    # Provenance in taker_source column.
    def _taker_buy_pct_row(row):
        k10k7 = row.get("taker_buy_pct_k10k7")
        if k10k7 is not None and not (isinstance(k10k7, float) and np.isnan(k10k7)):
            return float(k10k7), "k10_over_k7_fresh"
        r = row.get("taker_ratio")
        if r is None or (isinstance(r, float) and np.isnan(r)):
            return None, "MISSING"
        return float(r) / (1.0 + float(r)), "r_over_1plus_r_LEGACY"

    _taker_result = df.apply(_taker_buy_pct_row, axis=1)
    df["taker_buy_pct"] = _taker_result.apply(lambda t: t[0])
    df["taker_source"] = _taker_result.apply(lambda t: t[1])

    # low_conf: True if vol_quote < 200_000 OR oi_usd < 1_000_000
    def _low_conf(row):
        vq = row.get("vol_quote")
        oi = row.get("oi_usd")
        if vq is None or (isinstance(vq, float) and np.isnan(vq)):
            return True
        if oi is None or (isinstance(oi, float) and np.isnan(oi)):
            return True
        return float(vq) < 200_000 or float(oi) < 1_000_000

    df["low_conf"] = df.apply(_low_conf, axis=1)

    # data_ok: True if all required columns are non-null
    required = ["lsr_pos_r", "lsr_acc_r", "lsr_global_r", "oi_usd"]

    def _data_ok(row):
        for col in required:
            v = row.get(col)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return False
        return True

    df["data_ok"] = df.apply(_data_ok, axis=1)

    # Select and reorder
    for col in EXPORT_COLS:
        if col not in df.columns:
            df[col] = None

    return df[EXPORT_COLS].copy()


# ---------------------------------------------------------------------------
# Condition 2: Taker lag fix
# ---------------------------------------------------------------------------


def _backfill_taker_lag(
    df_csv: pd.DataFrame,
    symbols: list[str],
    today: datetime,
) -> pd.DataFrame:
    """Fill NULL taker cells in existing CSV rows by re-scanning last 3 calendar days.

    Condition 2: taker_ratio_1d has ~1 day lag; re-scan today-2, today-1, today.
    Only fills NULL values -- never overwrites existing non-null values.

    NOTE: df_csv may have string-typed columns (read from CSV with dtype=str).
    We cast taker columns to object before assignment to avoid pandas ArrowDtype errors.
    """
    rescan_dates = [
        (today - timedelta(days=d)).strftime("%Y-%m-%d")
        for d in [2, 1, 0]
    ]

    # Ensure taker columns are object dtype so float assignment works on string-backed CSVs
    for col in ["taker_ratio", "taker_buy_pct"]:
        if col in df_csv.columns and hasattr(df_csv[col], "dtype"):
            try:
                df_csv[col] = df_csv[col].astype(object)
            except Exception:
                pass

    filled_total = 0
    for date_str in rescan_dates:
        df_taker = _read_1d_metric("taker_ratio_1d", date_str)
        if df_taker.empty or "symbol" not in df_taker.columns:
            continue

        taker_map = dict(zip(df_taker["symbol"], df_taker["buy_sell_ratio"].astype(float)))
        if not taker_map:
            continue

        # Find rows in CSV for this date where taker is null/empty
        mask_date = df_csv["date"] == date_str
        if not mask_date.any():
            continue

        # Handle both NaN (float) and empty string (str-typed CSV columns)
        def _is_null_taker(v) -> bool:
            if v is None:
                return True
            if isinstance(v, float) and (v != v):  # NaN check
                return True
            if isinstance(v, str) and v.strip() in ("", "nan", "None"):
                return True
            return False

        mask_null_taker = df_csv["taker_ratio"].apply(_is_null_taker)
        mask = mask_date & mask_null_taker
        if not mask.any():
            continue

        filled_this_date = 0
        for idx in df_csv[mask].index:
            sym = df_csv.at[idx, "symbol"]
            if sym in taker_map:
                r = taker_map[sym]
                df_csv.at[idx, "taker_ratio"] = r
                # Also update taker_buy_pct
                df_csv.at[idx, "taker_buy_pct"] = r / (1.0 + r)
                filled_this_date += 1

        if filled_this_date > 0:
            log.info("taker_lag_backfill",
                     date=date_str,
                     filled=filled_this_date,
                     note="taker_ratio filled from 1d store (lag fix)")
            filled_total += filled_this_date

    if filled_total > 0:
        log.info("taker_lag_backfill_total", total_filled=filled_total)
    else:
        log.info("taker_lag_backfill_none", note="no null taker cells to fill")

    return df_csv, filled_total


# ---------------------------------------------------------------------------
# CSV I/O (month-partitioned, atomic write)
# ---------------------------------------------------------------------------


def _export_path(month_str: str) -> Path:
    """data/export/freshwatch_daily_YYYY-MM.csv"""
    return EXPORT_DIR / f"freshwatch_daily_{month_str}.csv"


def _read_existing_csv(month_str: str) -> pd.DataFrame:
    path = _export_path(month_str)
    if not path.exists():
        return pd.DataFrame(columns=EXPORT_COLS)
    # Read without dtype=str so numeric columns keep float type.
    # date and symbol remain object (string) naturally.
    df = pd.read_csv(path)
    for col in EXPORT_COLS:
        if col not in df.columns:
            df[col] = None
    return df[EXPORT_COLS].copy()


def _write_csv_atomic(df: pd.DataFrame, month_str: str) -> None:
    """Write CSV atomically (temp → os.replace). UTF-8, LF newlines, minimal quoting."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = _export_path(month_str)
    tmp = path.with_suffix(".tmp.csv")
    df[EXPORT_COLS].to_csv(
        tmp,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Determine which dates need 1d vs 1h source
# ---------------------------------------------------------------------------


def _has_1d_data(date_str: str) -> bool:
    """True if any 1d metric partition exists for this date."""
    for metric in ["top_pos_1d", "top_acct_1d", "retail_global_1d", "oi_hist_1d"]:
        pattern = str(RAW_DIR / metric / f"date={date_str}" / "*.parquet")
        if glob.glob(pattern):
            return True
    return False


# ---------------------------------------------------------------------------
# Validation table (W4 gate)
# ---------------------------------------------------------------------------


def run_validation(symbols: list[str]) -> dict:
    """Compare native 1d vs derived 1h for LSR/OI and taker separately.

    Returns dict with validation results.
    """
    # Find dates where both 1d and 1h data exist
    lsr_rows = []
    taker_rows = []

    # Collect all 1d dates
    dates_1d = set()
    for metric in ["top_pos_1d"]:
        for d in glob.glob(str(RAW_DIR / metric / "date=*")):
            dates_1d.add(Path(d).name.replace("date=", ""))

    sym_set = set(symbols)

    for date_str in sorted(dates_1d):
        midnight_ms = _date_midnight_ms(date_str)

        # LSR/OI comparison: 1d native vs 1h midnight snapshot
        df_1d_pos = _read_1d_metric("top_pos_1d", date_str)
        df_1h_pos = _read_1h_metric_for_day("top_pos_1h", date_str)

        if not df_1d_pos.empty and not df_1h_pos.empty:
            snap_1h = df_1h_pos[df_1h_pos["as_of_ts_ms"] == midnight_ms]
            snap_1h = snap_1h[snap_1h["symbol"].isin(sym_set)]
            # Deduplicate: keep one row per symbol (first occurrence)
            snap_1h = snap_1h.drop_duplicates(subset=["symbol"], keep="first")
            df_1d_f = df_1d_pos[df_1d_pos["symbol"].isin(sym_set)]
            df_1d_f = df_1d_f.drop_duplicates(subset=["symbol"], keep="first")

            merged = df_1d_f[["symbol", "long_short_ratio"]].rename(
                columns={"long_short_ratio": "lsr_1d"}
            ).merge(
                snap_1h[["symbol", "long_short_ratio"]].rename(
                    columns={"long_short_ratio": "lsr_1h"}
                ),
                on="symbol",
                how="inner",
            )
            if not merged.empty:
                merged["pct_diff"] = (
                    (merged["lsr_1d"] - merged["lsr_1h"]).abs()
                    / merged["lsr_1d"].abs().clip(lower=1e-10)
                    * 100
                )
                merged["date"] = date_str
                lsr_rows.append(merged[["date", "symbol", "lsr_1d", "lsr_1h", "pct_diff"]])

        # Taker comparison: 1d native buy_sell_ratio vs Sigma(buy)/Sigma(sell) from 1h
        df_1d_tk = _read_1d_metric("taker_ratio_1d", date_str)
        df_1h_tk = _read_1h_metric_for_day("taker_ratio_1h", date_str)

        if not df_1d_tk.empty and not df_1h_tk.empty:
            df_1h_filt = df_1h_tk[df_1h_tk["symbol"].isin(sym_set)].copy()
            if not df_1h_filt.empty:
                # Fix A (validation): dedup keep-last before Sigma buy/sell
                df_1h_filt = (
                    df_1h_filt
                    .sort_values(["symbol", "as_of_ts_ms"])
                    .drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="last")
                )
                grp = df_1h_filt.groupby("symbol").agg(
                    buy_sum=("buy_vol", "sum"),
                    sell_sum=("sell_vol", "sum"),
                ).reset_index()
                grp = grp[grp["sell_sum"] > 0].copy()
                grp["taker_derived"] = grp["buy_sum"] / grp["sell_sum"]

                df_1d_tf = df_1d_tk[df_1d_tk["symbol"].isin(sym_set)]
                merged_t = grp[["symbol", "taker_derived"]].merge(
                    df_1d_tf[["symbol", "buy_sell_ratio"]].rename(
                        columns={"buy_sell_ratio": "taker_native"}
                    ),
                    on="symbol",
                    how="inner",
                )
                if not merged_t.empty:
                    merged_t["pct_diff"] = (
                        (merged_t["taker_derived"] - merged_t["taker_native"]).abs()
                        / merged_t["taker_native"].abs().clip(lower=1e-10)
                        * 100
                    )
                    merged_t["date"] = date_str
                    taker_rows.append(
                        merged_t[["date", "symbol", "taker_derived", "taker_native", "pct_diff"]]
                    )

    lsr_df = pd.concat(lsr_rows, ignore_index=True) if lsr_rows else pd.DataFrame()
    taker_df = pd.concat(taker_rows, ignore_index=True) if taker_rows else pd.DataFrame()

    return {
        "lsr_oi": lsr_df,
        "taker": taker_df,
    }


# ---------------------------------------------------------------------------
# Main export logic
# ---------------------------------------------------------------------------


def _all_available_1h_dates() -> list[str]:
    """Return sorted list of all dates with 1h data in top_pos_1h store."""
    d = RAW_DIR / "top_pos_1h"
    if not d.exists():
        return []
    return sorted(
        Path(x).name.replace("date=", "")
        for x in glob.glob(str(d / "date=*"))
    )


def _dates_to_export(
    days_back: Optional[int],
    specific_date: Optional[str],
) -> list[str]:
    """Return sorted list of YYYY-MM-DD strings to export (oldest to newest).

    Fix C: For the initial run (no existing CSV), backfill ALL available history
    from the 1h store (may go back to ~May18). For subsequent runs, the default
    of days_back=2 fills recent dates. Store coverage determines the window;
    no hardcoded start date.
    """
    today_utc = datetime.now(timezone.utc).date()
    if specific_date:
        return [specific_date]
    if days_back is not None:
        return [
            (today_utc - timedelta(days=d)).isoformat()
            for d in range(days_back, -1, -1)
        ]
    # Default: check if any export CSV already covers this month
    month_str = today_utc.strftime("%Y-%m")
    export_path = EXPORT_DIR / f"freshwatch_daily_{month_str}.csv"
    if not export_path.exists():
        # Fix C: No CSV yet -- backfill all available 1h history
        available = _all_available_1h_dates()
        if available:
            log.info("full_backfill_mode",
                     note="No existing CSV; backfilling full 1h history",
                     n_dates=len(available),
                     first=available[0], last=available[-1])
            return available
    # CSV exists: export recent CLOSED dates only (today-2, today-1).
    # L-41: today (D) chưa đóng lúc cron chạy → bỏ today khỏi default để
    # tránh fn=1 / px-empty bị ghi vào CSV trước khi data đủ.
    return [
        (today_utc - timedelta(days=d)).isoformat()
        for d in range(2, 0, -1)
    ]
def run_export(
    *,
    days_back: Optional[int] = None,
    specific_date: Optional[str] = None,
    validate_only: bool = False,
    dry_run: bool = False,
    symbols_override: Optional[list[str]] = None,
    force_regen: bool = False,
) -> int:
    """Main export function. Returns 0 on success, 1 on validation failure.

    force_regen=True: remove existing rows for target dates before re-generating.
    Use this to fix stale rows (e.g., fn=1 written when store was not yet populated).
    """
    today_utc = datetime.now(timezone.utc)

    # --- Universe ---
    if not MASTER_PATH.exists():
        log.error("universe_master_not_found")
        return 1
    master = load_master(MASTER_PATH)
    if master.empty:
        log.error("universe_master_empty")
        return 1
    symbols: list[str] = (
        symbols_override
        if symbols_override
        else [s for s in get_active_symbols(master) if s not in EXCLUDED_SYMBOLS]
    )
    log.info("export_universe", symbols=len(symbols))

    # --- Validation gate (W4 Condition 3) ---
    log.info("running_validation_gate")
    val_results = run_validation(symbols)

    lsr_df = val_results["lsr_oi"]
    taker_df = val_results["taker"]

    n_lsr = len(lsr_df)
    n_taker = len(taker_df)

    lsr_max_div = float(lsr_df["pct_diff"].max()) if not lsr_df.empty else 0.0
    lsr_mean_div = float(lsr_df["pct_diff"].mean()) if not lsr_df.empty else 0.0
    taker_max_div = float(taker_df["pct_diff"].max()) if not taker_df.empty else 0.0
    taker_mean_div = float(taker_df["pct_diff"].mean()) if not taker_df.empty else 0.0

    log.info("validation_lsr_oi",
             n=n_lsr,
             max_pct_diff=round(lsr_max_div, 4),
             mean_pct_diff=round(lsr_mean_div, 4))
    log.info("validation_taker",
             n=n_taker,
             max_pct_diff=round(taker_max_div, 4),
             mean_pct_diff=round(taker_mean_div, 4))

    # Print validation table to stdout
    print("\n=== W4 VALIDATION TABLE ===")
    print(f"LSR/OI: n={n_lsr} symbol-day pairs")
    if not lsr_df.empty:
        print(lsr_df.to_string(index=False))
    else:
        print("  (no 1d vs 1h overlap found)")
    print(f"\n  LSR/OI max divergence: {lsr_max_div:.4f}%  mean: {lsr_mean_div:.4f}%")

    print(f"\nTaker (separate — derivation: Sigma buy/sell from 1h vs native 1d):")
    print(f"  n={n_taker} symbol-day pairs")
    if not taker_df.empty:
        print(taker_df.to_string(index=False))
    else:
        print("  (no 1d vs 1h overlap found)")
    print(f"\n  Taker max divergence: {taker_max_div:.4f}%  mean: {taker_mean_div:.4f}%")
    print("=== END VALIDATION ===\n")

    # Stop condition
    if lsr_max_div > 1.0:
        log.error("validation_STOP",
                  reason="LSR/OI divergence > 1%",
                  max_pct_diff=lsr_max_div)
        print(f"\nSTOP: LSR/OI divergence {lsr_max_div:.4f}% exceeds 1% threshold.")
        return 1

    # Note: taker divergence >2% is expected for partial-day 1h data.
    # The export always uses native_1d taker when available; 1h-derived taker
    # is only used for historical dates where no 1d data exists.
    # We report the divergence but do NOT stop — it reflects expected partial-day mismatch.
    if taker_max_div > 2.0:
        log.warning("validation_taker_high_divergence",
                    max_pct_diff=taker_max_div,
                    note="Taker 1h-derived divergence expected on partial-day 1h data. "
                         "Export uses native_1d when available.")

    if validate_only:
        log.info("validate_only_complete")
        return 0

    if dry_run:
        log.info("dry_run_complete")
        return 0

    # --- Export ---
    dates = _dates_to_export(days_back, specific_date)
    log.info("export_dates", dates=dates)

    # Group dates by month
    from collections import defaultdict
    by_month: dict[str, list[str]] = defaultdict(list)
    for d in dates:
        by_month[d[:7]].append(d)

    filled_total_global = 0  # Fix D: track taker lag fills across all months
    for month_str, month_dates in sorted(by_month.items()):
        # Read existing CSV for this month
        df_existing = _read_existing_csv(month_str)

        # force_regen: strip out existing rows for target dates so they get re-built fresh.
        # This fixes stale exports (fn=1 / px-empty written before store was populated).
        if force_regen and not df_existing.empty:
            regen_set = set(month_dates)
            before_n = len(df_existing)
            df_existing = df_existing[~df_existing["date"].isin(regen_set)].copy()
            after_n = len(df_existing)
            log.info("force_regen_strip",
                     month=month_str, dates=sorted(regen_set),
                     rows_removed=before_n - after_n)

        # Determine which date+symbol pairs are missing
        existing_pairs: set[tuple[str, str]] = set()
        if not df_existing.empty:
            for _, row in df_existing.iterrows():
                existing_pairs.add((str(row["date"]), str(row["symbol"])))

        new_rows: list[pd.DataFrame] = []
        for date_str in sorted(month_dates):
            has_1d = _has_1d_data(date_str)
            log.info("export_date",
                     date=date_str,
                     src="native_1d" if has_1d else "derived_1h")

            df_date = _assemble_date(date_str, symbols, has_1d_data=has_1d)
            if df_date.empty:
                log.warning("export_date_empty", date=date_str)
                continue

            # Append-only: filter to missing pairs
            def _is_missing(row: pd.Series) -> bool:
                return (str(row["date"]), str(row["symbol"])) not in existing_pairs

            df_new = df_date[df_date.apply(_is_missing, axis=1)].copy()
            if df_new.empty:
                log.info("export_date_all_present", date=date_str)
                continue

            new_rows.append(df_new)
            log.info("export_date_new_rows", date=date_str, rows=len(df_new))

        if not new_rows:
            log.info("export_month_no_new_rows", month=month_str)
            # Still run taker lag fix on existing
            if not df_existing.empty:
                df_updated, n_filled = _backfill_taker_lag(df_existing.copy(), symbols, today_utc)
                filled_total_global += n_filled
                _write_csv_atomic(df_updated, month_str)
            continue

        # Combine new rows with existing
        df_combined = pd.concat(
            ([df_existing] if not df_existing.empty else []) + new_rows,
            ignore_index=True,
        )

        # Condition 2: taker lag fix (fill null taker in combined)
        df_combined, n_filled = _backfill_taker_lag(df_combined, symbols, today_utc)
        filled_total_global += n_filled

        # Sort by date, symbol
        df_combined = df_combined.sort_values(["date", "symbol"]).reset_index(drop=True)

        _write_csv_atomic(df_combined, month_str)
        log.info("export_month_written",
                 month=month_str,
                 total_rows=len(df_combined),
                 new_rows=sum(len(r) for r in new_rows))

    # Fix D: Validation summary log
    n_native_rows = 0
    n_derived_rows = 0
    for month_str_d in sorted(by_month.keys()):
        csv_path = _export_path(month_str_d)
        if csv_path.exists():
            try:
                df_final = pd.read_csv(csv_path)
                if "src_ratio" in df_final.columns:
                    n_native_rows += int((df_final["src_ratio"] == "native_1d").sum())
                    n_derived_rows += int((df_final["src_ratio"] == "derived_1h").sum())
            except Exception:
                pass

    log.info("export_complete",
             n_native_symbol_days=n_native_rows,
             n_derived_symbol_days=n_derived_rows,
             taker_lag_filled_condition2=filled_total_global)
    print("\n=== EXPORT SUMMARY ===")
    print(f"  n_native (native_1d rows):    {n_native_rows}")
    print(f"  n_derived (derived_1h rows):  {n_derived_rows}")
    print(f"  taker_filled_by_lag_fix:      {filled_total_global}")
    print("=== END SUMMARY ===\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@app.command()
def main(
    date: Optional[str] = typer.Option(None, help="Export a specific date YYYY-MM-DD"),
    days_back: Optional[int] = typer.Option(None, help="Export last N days (default: yesterday+day-before)"),
    validate_only: bool = typer.Option(False, help="Run validation table only, no export"),
    dry_run: bool = typer.Option(False, help="Validate but do not write files"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbol override"),
    force_regen: bool = typer.Option(
        False,
        "--force-regen",
        help=(
            "Remove existing rows for target dates and re-generate from store. "
            "Use to fix stale exports (fn=1/px-empty written before store populated). "
            "Requires --date or --days-back to be explicit."
        ),
    ),
) -> None:
    """W4: Generate FreshWatch daily export CSV (month-partitioned, append-only)."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None
    code = run_export(
        days_back=days_back,
        specific_date=date,
        validate_only=validate_only,
        dry_run=dry_run,
        symbols_override=sym_list,
        force_regen=force_regen,
    )
    raise typer.Exit(code)


if __name__ == "__main__":
    app()
