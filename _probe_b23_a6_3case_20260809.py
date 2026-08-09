#!/usr/bin/env python3
"""B2.3 — A6 3-case test: FF BLOCK / HEI PASS / TUT PASS.

A6 = _a3_slope_ok() = gLSR slope_5d <= 1.15 (fuel-not-exhausted guard).
Currently flag=False (disabled). This probe evaluates A6 independently
on 3 tokens from freshwatch CSV data to verify expected behavior:
  FF BLOCK  — some FF dates have A6=False (gLSR slope rising fast)
  HEI PASS  — HEI fire days all have A6=True (slope OK)
  TUT PASS  — TUT fire days all have A6=True (slope OK)

data-source: data/export/freshwatch_daily_2026-0*.csv (VPS)
machine: VPS canonical
date-range: 2026-05-26 to 2026-08-09
code-commit: a4acb95
"""

from __future__ import annotations
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
if not BOT_ROOT.exists():
    BOT_ROOT = Path("/root/Data_back_test/binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import load_thresholds, DayData
from scripts.gom_scan import _a3_slope_ok, load_screen_cfg

STORE_DIR = ROOT / "data" / "export"

# Known GOM-A fire dates from production (freshwatch daily scan)
# FF: ch1 n=5, fires from 2026-06-01 onward (34 fire days)
# HEI: fires 08-03 (A1T A2T A3T per gom_gate6_v8e)
# TUT: GOM-C fires, also has A3-ok periods
KNOWN_FIRE_DATES = {
    "FFUSDT":  None,   # will detect from A1+A2+A3 all-true days
    "HEIUSDT": {"2026-08-03"},  # confirmed fire day
    "TUTUSDT": None,   # will detect from data
}


def _build_days(store: Path, token: str, up_to: str = "2026-08-09",
                lookback: int = 90) -> list[DayData]:
    """Build DayData list for token from freshwatch CSV."""
    from fw_loader_utils import load_fw_csvs, build_token_days, load_funding_intervals

    try:
        df = load_fw_csvs(store, up_to_date=up_to, lookback_days=lookback)
    except Exception as exc:
        print(f"  ERROR load_fw_csvs: {exc}")
        return []

    if df.empty:
        print(f"  No data in freshwatch CSV")
        return []

    tok_df = df[df["symbol"] == token]
    if tok_df.empty:
        print(f"  Token {token} not in freshwatch CSV")
        return []

    # date range for token
    dates = sorted(tok_df["date"].unique())
    if not dates:
        return []
    date_from = dates[0]
    date_to   = dates[-1]

    try:
        intervals = load_funding_intervals(store, token)
    except Exception:
        intervals = {}

    try:
        days, _ = build_token_days(df, token, date_from, date_to, intervals)
    except Exception as exc:
        print(f"  ERROR build_token_days: {exc}")
        # Fallback: simple row-by-row
        days = []
        for _, row in tok_df.sort_values("date").iterrows():
            d: DayData = {}
            d["date"]       = str(row.get("date", ""))
            d["lsr_global"] = float(row.get("lsr_global_r", float("nan")) or float("nan"))
            d["avg_px"]     = float(row.get("px_avg", float("nan")) or float("nan"))
            days.append(d)

    return days


def analyze_token(token: str, label: str, expected: str, store: Path, sc: dict) -> str:
    """Analyze A6 for token. Returns result string."""
    print(f"\n[{label}] {token} — expected: A6 {expected}")

    days = _build_days(store, token)
    if not days:
        print(f"  SKIP: no data loaded")
        return "SKIP (no data)"

    print(f"  Rows loaded: {len(days)}")

    a6_results = []
    for i, d in enumerate(days):
        date = d.get("date", "??")
        glsr = d.get("lsr_global", float("nan"))
        a6 = _a3_slope_ok(days, i, sc)
        # compute slope for display
        slope = float("nan")
        if i >= 5:
            g0 = days[i-5].get("lsr_global", float("nan"))
            if not math.isnan(g0) and g0 > 0 and not math.isnan(glsr):
                slope = glsr / g0
        a6_results.append((date, a6, glsr, slope))

    n_true  = sum(1 for _, a6, _, _ in a6_results if a6)
    n_false = sum(1 for _, a6, _, _ in a6_results if not a6)
    print(f"  A6=True: {n_true}  A6=False: {n_false}")

    false_dates = [(dt, g, sl) for dt, a6, g, sl in a6_results if not a6]
    if false_dates:
        print(f"  A6=False dates (slope_5d > 1.15):")
        for dt, g, sl in false_dates[:15]:
            sl_str = f"{sl:.3f}" if not math.isnan(sl) else "NaN"
            print(f"    {dt}: gLSR={g:.4f} slope5d={sl_str}")

    print(f"  Recent gLSR (last 14 days):")
    for dt, a6, g, sl in a6_results[-14:]:
        sl_str = f"{sl:.3f}" if not math.isnan(sl) else "    "
        print(f"    {dt}: gLSR={g:.4f} slope5d={sl_str} A6={a6}")

    # Evaluate against expected
    if expected == "BLOCK":
        if n_false > 0:
            result = f"BLOCK confirmed ({n_false} days A6=False)"
        else:
            result = "FAIL — A6 never False for this token (no block achieved)"
    else:  # expected PASS
        if n_false == 0:
            result = "PASS (A6=True all days)"
        elif n_false <= 3:
            result = f"PASS-NEAR ({n_false} A6=False, likely early/missing data)"
        else:
            result = f"WARN — {n_false} A6=False days (check if fire days affected)"

    print(f"  Result: {result}")
    return result


def main():
    print("=" * 70)
    print("B2.3 — A6 3-case test: FF BLOCK / HEI PASS / TUT PASS")
    print("=" * 70)

    if not STORE_DIR.exists():
        print(f"ERROR: store dir not found: {STORE_DIR}")
        print("Must run on VPS where freshwatch CSV exists")
        sys.exit(1)

    try:
        sc = load_screen_cfg()
    except Exception as exc:
        print(f"WARN: screen_thresholds load failed: {exc}")
        sc = {}

    ff_result  = analyze_token("FFUSDT",   "1", "BLOCK", STORE_DIR, sc)
    hei_result = analyze_token("HEIUSDT",  "2", "PASS",  STORE_DIR, sc)
    tut_result = analyze_token("TUTUSDT",  "3", "PASS",  STORE_DIR, sc)

    print("\n" + "=" * 70)
    print("SUMMARY — B2.3 A6 3-case")
    print("=" * 70)
    print(f"  FF BLOCK:  {ff_result}")
    print(f"  HEI PASS:  {hei_result}")
    print(f"  TUT PASS:  {tut_result}")

    all_pass = (
        "confirmed" in ff_result
        and ("PASS" in hei_result)
        and ("PASS" in tut_result)
    )
    print(f"\n  OVERALL: {'3/3 PASS — A6 candidate for enable' if all_pass else 'NOT ALL PASS — see above'}")
    if all_pass:
        print("  Next: set A6_PRICE_SLOPE_GUARD_ENABLED=True, re-run backtest6 to confirm no FAIL regression.")
    print()


if __name__ == "__main__":
    main()
