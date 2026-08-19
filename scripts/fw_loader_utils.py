#!/usr/bin/env python3
"""fw_loader_utils.py — FreshWatch CSV → DayData loader for gom_scan --daily.

S-rules applied in build_token_days():
  S1: funding_n < expected(interval_h) → _partial_day=True → skip Q1 in update_chain
  S2: data_ok=False                    → _skip_eval=True  → no eval_gom, break_streak++
  S-missing: date absent from CSV      → _suspect=True    → synthetic NaN day
  S4 (tripwire): already in signals.py suppressors/perday_dq — no extra handling here
"""
from __future__ import annotations

import json
import math
import sys
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Taker scale check (token-level, used by original callers)
# ---------------------------------------------------------------------------

def taker_scale_check(
    tok: str,
    raw_values: Iterable[float],
    *,
    log=None,
) -> float:
    """Inspect raw taker_buy_pct values; return scale factor (1.0 or 100.0).

    Rules:
    - max(raw) ≤ 1.0 → fraction format → return 100.0
    - max(raw) > 1.0 and min(raw) > 1.0 → already pct → return 1.0
    - mixed (max > 1.0 and min ≤ 1.0) → raise ValueError (cannot auto-correct)
    - empty → return 100.0 (freshwatch convention default)
    """
    vals = [v for v in raw_values if not (v != v)]  # drop NaN
    if not vals:
        return 100.0

    mx, mn = max(vals), min(vals)

    if mx > 1.0 and mn < 1.0:
        raise ValueError(
            f"TRIPWIRE [{tok}]: mixed taker_buy_pct scale "
            f"(min={mn:.4f}, max={mx:.4f}) — cannot auto-convert"
        )

    if mx > 1.0:
        msg = f"TRIPWIRE [{tok}]: taker max={mx:.2f} > 1 → already pct, no ×100"
        if log is not None:
            log.warning("taker_scale_pct_unexpected", token=tok,
                        max=round(mx, 2), hint="already pct — ×100 not applied")
        else:
            print(f"WARNING {msg}", file=sys.stderr)
        return 1.0

    msg = f"TRIPWIRE [{tok}]: taker max={mx:.4f} ≤ 1 → fraction, ×100 applied"
    if log is not None:
        log.warning("taker_scale_fraction_converted", token=tok,
                    max=round(mx, 4), hint="decimal→pct ×100 applied")
    else:
        print(f"WARNING {msg}", file=sys.stderr)
    return 100.0


def taker_scale_check_dict_rows(
    tok: str,
    rows: Iterable[dict],
    field: str = "taker_buy_pct",
    *,
    log=None,
) -> float:
    """Convenience wrapper: extract `field` from each row dict, then call taker_scale_check."""
    raw = []
    for row in rows:
        v = row.get(field, "")
        try:
            fv = float(v)
            if not math.isnan(fv):
                raw.append(fv)
        except (TypeError, ValueError):
            pass
    return taker_scale_check(tok, raw, log=log)


def taker_scale_check_df(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame-level scale check and correction.

    Freshwatch CSV stores taker_buy_pct = r/(1+r) ∈ [0,1] (decimal).
    DayData.taker_buy_pct expects 0–100 scale.
    Mixed scale → ValueError. Returns modified copy; NaN rows left as-is.
    """
    df = df.copy()
    if "taker_buy_pct" not in df.columns:
        return df

    vals = pd.to_numeric(df["taker_buy_pct"], errors="coerce").dropna()
    if vals.empty:
        return df

    all_decimal = (vals <= 1.0).all()
    all_pct     = (vals > 1.0).all()

    if all_decimal:
        df["taker_buy_pct"] = pd.to_numeric(df["taker_buy_pct"], errors="coerce") * 100.0
    elif all_pct:
        pass  # already in pct form
    else:
        raise ValueError(
            f"taker_buy_pct mixed scale: min={float(vals.min()):.4f} "
            f"max={float(vals.max()):.4f} — cannot auto-correct; check source CSV"
        )
    return df


# ---------------------------------------------------------------------------
# CSV loader (month-partitioned)
# ---------------------------------------------------------------------------

def load_fw_csvs(store: Path, up_to_date: str, lookback_days: int = 60) -> pd.DataFrame:
    """Load freshwatch_daily_YYYY-MM.csv covering [up_to_date-lookback_days, up_to_date].

    store: directory with freshwatch_daily_YYYY-MM.csv files,
           OR path to a single CSV file (single-month test mode).
    Returns concatenated DataFrame sorted by (date, symbol). Empty DF if no files found.
    """
    end_dt    = datetime.strptime(up_to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_dt  = end_dt - timedelta(days=lookback_days)
    start_str = start_dt.strftime("%Y-%m-%d")

    frames = []

    if store.is_file():
        frames.append(pd.read_csv(store))
    else:
        # Enumerate months in window
        months: list[str] = []
        cur = start_dt.replace(day=1)
        while cur <= end_dt:
            months.append(cur.strftime("%Y-%m"))
            # advance to next month
            cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)

        for month_str in months:
            csv_path = store / f"freshwatch_daily_{month_str}.csv"
            if csv_path.exists():
                frames.append(pd.read_csv(csv_path))

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df[(df["date"] >= start_str) & (df["date"] <= up_to_date)].copy()
    df = df.sort_values(["date", "symbol"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Funding intervals helper
# ---------------------------------------------------------------------------

def load_funding_intervals(config_dir: Path) -> dict[str, int]:
    """Load data/config/funding_intervals.json. Returns {} if not found (callers default 8h).

    [F3.1 19/08] File EXISTS but corrupt → RAISE (nhất quán L-44 fail-loud
    cutover đã deploy: export_freshwatch_daily_vps.py:377-381 RAISE nếu
    fundingInfo fetch fail). Silent-fallback ở đây MÂU THUẪN cutover.
    Missing file (không tồn tại) giữ default {} — legit no-config case.
    """
    path = config_dir / "funding_intervals.json"
    if not path.exists():
        return {}
    # File tồn tại nhưng corrupt → JSONDecodeError propagate → callers see it
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def expected_funding_n(interval_h: int) -> int:
    """Expected daily settlements per day: 4h→6, 8h→3, 1h→24."""
    return 24 // max(1, interval_h)


# ---------------------------------------------------------------------------
# DayData builder per token
# ---------------------------------------------------------------------------

def _nan_day(date_str: str) -> dict:
    nan = float("nan")
    return {
        "date": date_str,
        "lsr_pos": nan, "lsr_acc": nan, "lsr_global": nan,
        "taker_ratio": nan, "taker_buy_pct": nan,
        "vol_quote": nan, "avg_px": nan, "oi_usd": nan,
        "funding_avg": nan, "funding_min": nan, "funding_max": nan,
    }


def _f(v) -> float:
    """Parse to float; return NaN on failure/None."""
    if v is None:
        return float("nan")
    try:
        f = float(v)
        return f if not math.isnan(f) else float("nan")
    except (ValueError, TypeError):
        return float("nan")


def _bool_val(v, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, float):
        return bool(v) if not math.isnan(v) else default
    if isinstance(v, int):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return default


def build_token_days(
    df: pd.DataFrame,
    symbol: str,
    date_from: str,
    date_to: str,
    intervals: dict[str, int],
) -> tuple[list[dict], list[str]]:
    """Build DayData-compatible list for one token over [date_from, date_to] with S-rules.

    CSV columns mapped to DayData fields:
      lsr_pos_r    → lsr_pos   (ratio space, no conversion needed)
      lsr_acc_r    → lsr_acc
      lsr_global_r → lsr_global
      taker_ratio  → taker_ratio
      taker_buy_pct→ taker_buy_pct  (must already be ×100 — call taker_scale_check_df first)
      vol_quote    → vol_quote
      px_avg       → avg_px
      oi_usd       → oi_usd
      funding_avg/min/max → funding_avg/min/max

    Returns:
      days          — DayData-compatible dicts including synthetic NaN rows for missing dates
      suspect_dates — YYYY-MM-DD strings where data was absent (S-missing) or bad (S2)
    """
    df_sym = df[df["symbol"] == symbol].copy()

    # Index by date
    csv_by_date: dict[str, object] = {}
    for _, row in df_sym.iterrows():
        csv_by_date[str(row["date"])] = row

    # Full date range — insert synthetic rows for missing dates (break_streak handles gap logic)
    start_dt = datetime.strptime(date_from, "%Y-%m-%d")
    end_dt   = datetime.strptime(date_to,   "%Y-%m-%d")
    all_dates: list[str] = []
    cur = start_dt
    while cur <= end_dt:
        all_dates.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    interval_h = intervals.get(symbol, 8)
    exp_fn     = expected_funding_n(interval_h)

    days: list[dict]         = []
    suspect_dates: list[str] = []

    for date_str in all_dates:
        if date_str not in csv_by_date:
            # S-missing: absent row → synthetic NaN day (break_streak++ in update_chain)
            day = _nan_day(date_str)
            day["_suspect"] = True
            day["_interval_h"] = interval_h  # propagate so callers can normalize funding
            suspect_dates.append(date_str)
            days.append(day)
            continue

        row = csv_by_date[date_str]

        # S2: data_ok=False → skip eval entirely, pass false result to update_chain
        if not _bool_val(row.get("data_ok"), default=True):
            day = _nan_day(date_str)
            day["_skip_eval"] = True
            suspect_dates.append(date_str)
            days.append(day)
            continue

        # Normal valid row
        day = {
            "date":          date_str,
            "lsr_pos":       _f(row.get("lsr_pos_r")),
            "lsr_acc":       _f(row.get("lsr_acc_r")),
            "lsr_global":    _f(row.get("lsr_global_r")),
            "taker_ratio":   _f(row.get("taker_ratio")),
            "taker_buy_pct": _f(row.get("taker_buy_pct")),
            "vol_quote":     _f(row.get("vol_quote")),
            "avg_px":        _f(row.get("px_avg")),
            "oi_usd":        _f(row.get("oi_usd")),
            "funding_avg":   _f(row.get("funding_avg")),
            "funding_min":   _f(row.get("funding_min")),
            "funding_max":   _f(row.get("funding_max")),
        }

        # S1: PARTIAL_DAY — insufficient funding settlements → Q1 skip flag
        fn_val = row.get("funding_n")
        if fn_val is not None and fn_val == fn_val:  # not NaN
            day["funding_n"] = int(float(fn_val))
            try:
                if int(float(fn_val)) < exp_fn:
                    day["_partial_day"] = True
            except (ValueError, TypeError):
                pass

        # Propagate low_conf flag (used in eval_gom display)
        day["low_conf"] = _bool_val(row.get("low_conf"), default=False)
        # Propagate funding interval so callers can normalize funding_avg to 8h-equivalent
        day["_interval_h"] = interval_h

        days.append(day)

    return days, suspect_dates


def enrich_token_days(days: list[dict]) -> None:
    """Add derived fields d_pos_3d and oi_cycle_pos to day dicts in-place.

    d_pos_3d:     lsr_pos[i] - lsr_pos[i-3]; NaN if i<3 or any source NaN
    oi_cycle_pos: (oi_usd - min30d) / (max30d - min30d) rolling 30d;
                  NaN if <10 valid points or min==max
    """
    n = len(days)

    # d_pos_3d = lsr_pos[i] - lsr_pos[i-3]  (spec A4)
    for i in range(n):
        if i < 3:
            days[i]["d_pos_3d"] = float("nan")
            continue
        p_now  = days[i].get("lsr_pos", float("nan"))
        p_prev = days[i - 3].get("lsr_pos", float("nan"))
        if math.isnan(p_now) or math.isnan(p_prev):
            days[i]["d_pos_3d"] = float("nan")
        else:
            days[i]["d_pos_3d"] = round(p_now - p_prev, 6)

    # oi_cycle_pos = (oi_usd - min30d) / (max30d - min30d)  (spec A5, rolling 30d)
    for i in range(n):
        start  = max(0, i - 29)
        window = [days[j].get("oi_usd", float("nan")) for j in range(start, i + 1)]
        valid  = [v for v in window if not math.isnan(v)]
        cur    = days[i].get("oi_usd", float("nan"))
        if len(valid) < 10 or math.isnan(cur):
            days[i]["oi_cycle_pos"] = float("nan")
            continue
        mn, mx = min(valid), max(valid)
        if mx <= mn:
            days[i]["oi_cycle_pos"] = float("nan")
        else:
            days[i]["oi_cycle_pos"] = round((cur - mn) / (mx - mn), 4)


# ---------------------------------------------------------------------------
# M1 canonical div_avg3 — Amendment v1.5, Phụ lục A
# ---------------------------------------------------------------------------

def div_avg3(days: list[dict], i: int) -> float:
    """Canonical div_avg3 = avg3(lsr_pos) / avg3(lsr_acc) — ratio-of-means.

    M1 (Amendment v1.5, Phụ lục A): KHÔNG dùng avg3(pos/acc) = mean-of-ratios.
    Paired-NaN: nếu lsr_pos[j] hoặc lsr_acc[j] là NaN → bỏ cả cặp j đó.
    Equivalent formula: signals._div_ratio (same computation, kept in-repo for signals.py).
    NaN nếu không có pair hợp lệ nào hoặc avg(acc) ≈ 0.
    """
    start = max(0, i - 2)
    valid_pairs: list[tuple[float, float]] = []
    for j in range(start, i + 1):
        p = days[j].get("lsr_pos", float("nan"))
        a = days[j].get("lsr_acc", float("nan"))
        if not math.isnan(p) and not math.isnan(a):
            valid_pairs.append((p, a))
    if not valid_pairs:
        return float("nan")
    avg_pos = sum(p for p, _ in valid_pairs) / len(valid_pairs)
    avg_acc = sum(a for _, a in valid_pairs) / len(valid_pairs)
    if avg_acc < 1e-9:
        return float("nan")
    return avg_pos / avg_acc
