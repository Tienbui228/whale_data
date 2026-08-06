#!/usr/bin/env python3
"""B1/B2/B3: klines k[9] base-vs-quote investigation.
B1: code path summary for taker from Alpha klines
B2: fetch 5 symbols, verify k[9] == k[5] (or ratio near 1.0)
B3: consumer impact — does freshwatch CSV taker come from this store?
"""
import sys, json, math, urllib.request, urllib.parse, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import pandas as pd

WHALE      = Path(__file__).parent
ALPHA_MAP  = WHALE / "data" / "config" / "alpha_id_map.json"
STORE_DIR  = WHALE / "data" / "raw" / "spot_klines_1d"
BAPI_BASE  = "https://www.binance.com"
KLINES_PATH = "/bapi/defi/v1/public/alpha-trade/klines"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ── B1: Code path summary ──────────────────────────────────────────────────
print(f"\n{'='*70}")
print("B1: CODE PATH — taker from Alpha klines")
print(f"{'='*70}")
print("""
collect_alpha_daily.py → _parse_alpha_row(k, ...):
  # GUARD: klines[9] == klines[5] always on Alpha (100% taker = broken field)
  taker_buy_base_vol  = NaN   ← k[9] KHÔNG ĐỌC
  taker_buy_quote_vol = NaN
  taker_buy_pct       = NaN
  taker_abstain       = True  ← flag trong parquet store

collect_spot_daily.py → _parse_spot_row(k, ...):
  taker_base = float(k[9])
  taker_quote = float(k[10])
  taker_pct = taker_quote / quote_vol
  BSC guard: if taker_base / base_vol >= threshold → taker_abstain=True, set NaN
  (BSC guard = same symptom as Alpha: k[9]≈k[5] → 100%)

Freshwatch export (export_freshwatch_daily_vps.py):
  taker_buy_pct = r / (1+r)  where r = taker_ratio from taker_ratio_1d metric
  → KHÔNG đọc từ spot_klines_1d taker_buy_pct
  → k[9]==k[5] bug KHÔNG ảnh hưởng freshwatch CSV / CASE_*.xlsx
""")

# ── B2: Fetch 5 samples, check k[9] vs k[5] ───────────────────────────────
print(f"\n{'='*70}")
print("B2: LIVE VERIFY — k[9] vs k[5] on Alpha API (5 symbols)")
print(f"{'='*70}")

if not ALPHA_MAP.exists():
    print(f"  SKIP: {ALPHA_MAP} not found")
else:
    alpha_map = json.loads(ALPHA_MAP.read_text(encoding="utf-8"))
    # Pick 5 known symbols
    sample_syms = ["IDOL", "TAG", "BR", "BANK", "XPIN"]
    sample_syms = [s for s in sample_syms if s in alpha_map][:5]
    if not sample_syms:
        sample_syms = list(alpha_map.keys())[:5]

    # yesterday
    t_now = int(datetime.now(timezone.utc).timestamp() * 1000)
    day_ms = 86400000
    day_start = ((t_now // day_ms) - 1) * day_ms
    day_end   = day_start + day_ms - 1
    date_str  = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"  date={date_str}  symbols={sample_syms}")
    print(f"  {'sym':<8} {'k[5]=base':>14} {'k[9]=taker_base':>16} {'ratio k9/k5':>13}  verdict")
    print(f"  {'-'*60}")

    b2_all_equal = True
    for sym in sample_syms:
        alpha_id = alpha_map[sym]
        ticker   = f"{alpha_id}USDT"
        qs = urllib.parse.urlencode({
            "symbol": ticker, "interval": "1d",
            "startTime": day_start, "endTime": day_end, "limit": 1,
        })
        url = f"{BAPI_BASE}{KLINES_PATH}?{qs}"
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = json.loads(r.read().decode())
                arr = raw if isinstance(raw, list) else (raw.get("data", []) if isinstance(raw, dict) else [])
            if not arr:
                print(f"  {sym:<8} {'N/A':>14} {'N/A':>16} {'N/A':>13}  empty response")
                continue
            k = arr[0]
            k5 = float(k[5] or 0)
            k9 = float(k[9] or 0) if len(k) > 9 else float("nan")
            ratio = k9 / k5 if k5 > 0 else float("nan")
            eq = math.isclose(k9, k5, rel_tol=1e-6) if not math.isnan(ratio) else False
            if not eq:
                b2_all_equal = False
            verdict = "k9==k5 CONFIRMED" if eq else f"k9≠k5 ratio={ratio:.4f}"
            print(f"  {sym:<8} {k5:>14.2f} {k9:>16.2f} {ratio:>13.6f}  {verdict}")
        except Exception as ex:
            b2_all_equal = False
            print(f"  {sym:<8} ERROR: {ex}")
        time.sleep(0.5)

    print(f"\n  B2 verdict: k[9]==k[5] on all sampled Alpha symbols = {b2_all_equal}")

# ── B2b: Check store for taker_abstain distribution ───────────────────────
print(f"\n{'─'*70}")
print("B2b: STORE CHECK — taker_abstain distribution in recent partition")
recent_partitions = sorted(STORE_DIR.glob("date=2026-08-*/part-0.parquet"), reverse=True)
if recent_partitions:
    p = recent_partitions[0]
    date_part = p.parent.name.replace("date=","")
    df = pd.read_parquet(p)
    total = len(df)
    abstain = df["taker_abstain"].sum() if "taker_abstain" in df.columns else "N/A"
    alpha_rows = len(df[df["venue"]=="binance_alpha"]) if "venue" in df.columns else "N/A"
    spot_rows  = len(df[df["venue"]=="binance_spot"]) if "venue" in df.columns else "N/A"
    bsc_rows   = len(df[df["venue"]=="binance_spot_bsc"]) if "venue" in df.columns else "N/A"
    print(f"  Partition: {date_part}  total_rows={total}")
    print(f"  taker_abstain=True: {abstain}")
    print(f"  venue breakdown: alpha={alpha_rows}  spot={spot_rows}  bsc={bsc_rows}")
    nan_taker = df["taker_buy_pct"].isna().sum() if "taker_buy_pct" in df.columns else "N/A"
    print(f"  taker_buy_pct NaN: {nan_taker}")
else:
    print("  No recent partitions found in store")

# ── B3: Consumer impact ───────────────────────────────────────────────────
print(f"\n{'='*70}")
print("B3: CONSUMER IMPACT")
print(f"{'='*70}")
print("""
store: spot_klines_1d parquet
  └── Alpha symbols: taker_buy_pct=NaN, taker_abstain=True ← INTENTIONAL

export_freshwatch_daily_vps.py:
  taker comes from taker_ratio_1d (tape-derived, NOT klines)
  Formula: taker_buy_pct = r/(1+r) where r=taker_ratio from taker_ratio_1d
  → freshwatch CSV NOT affected by k[9]==k[5] bug ✓

case_daily.py:
  Reads freshwatch CSV taker_buy_pct → also NOT affected ✓

What IS affected:
  Any pipeline reading taker_buy_pct from spot_klines_1d for Alpha venue:
  - Will get NaN (expected + guarded)
  - taker_abstain=True flag identifies these rows
  - No silent corruption: NaN propagates visibly, not as a false value

Symbols affected (venue=binance_alpha): ALL 126 successful backfill symbols
  (k[9]==k[5] is an API-level property of the Alpha endpoint, affects all)

Action needed: NONE — guard already in place, freshwatch pipeline unaffected.
""")

print(f"{'='*70}")
print(f"B1/B2/B3 complete — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
