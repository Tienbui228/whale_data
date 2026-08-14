"""
PHASE 5 VERIFY: Chạy compute_h_daily cho 2026-08-13 với --dry-run.
1. Verify dedup (BANK/CYS 48→24, AKE 24→24)
2. Sample output: token có H đủ + token NaN mỗi guard
3. Header ledger
Run trên VPS: python3 _probe_5_h_sample_20260814.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/root/Data_back_test/whale_data")))
sys.path.insert(0, str(Path("/root/Data_back_test/whale_data") / "scripts"))

from scripts.compute_h_daily import (
    load_klines_day, load_oi_day, build_watchlist,
    range_medians_14d, compute_symbol, LEDGER_HEADER,
    BOOK_THIN_FRAC, H1_MIN_HOURS, load_funding_intervals,
)
import pandas as pd
import math

TARGET = "2026-08-13"
NaN = float("nan")

print("=" * 80)
print(f"PHASE 5 VERIFY — {TARGET}")
print("=" * 80)

# ── [A] DEDUP VERIFY ────────────────────────────────────────────────────────────
print("\n[A] DEDUP VERIFY")
print("-" * 50)
RAW = Path("/root/Data_back_test/whale_data/data/raw")
for sym in ["BANKUSDT", "CYSUSDT", "AKEUSDT"]:
    pq = RAW / "klines_1h" / f"date=2026-06-30" / "part-0.parquet"
    import pandas as pd2
    df_raw = pd2.read_parquet(pq)
    sym_raw = df_raw[df_raw["symbol"] == sym]
    rows_raw = len(sym_raw)
    sym_dedup = sym_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
    rows_dedup = len(sym_dedup)
    print(f"  klines_1h {sym} 2026-06-30: rows_raw={rows_raw} → after_dedup={rows_dedup} (dropped={rows_raw-rows_dedup})")

for sym in ["BANKUSDT", "CYSUSDT", "AKEUSDT"]:
    pq = RAW / "oi_hist_1h" / f"date=2026-06-30" / "part-0.parquet"
    try:
        df_raw = pd2.read_parquet(pq)
        sym_raw = df_raw[df_raw["symbol"] == sym]
        rows_raw = len(sym_raw)
        sym_dedup = sym_raw.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
        rows_dedup = len(sym_dedup)
        print(f"  oi_hist_1h {sym} 2026-06-30: rows_raw={rows_raw} → after_dedup={rows_dedup} (dropped={rows_raw-rows_dedup})")
    except Exception as e:
        print(f"  oi_hist_1h {sym}: {e}")

# ── [B] FULL COMPUTE Aug 13 ──────────────────────────────────────────────────────
print(f"\n[B] COMPUTE h1-h4 for {TARGET}")
print("-" * 50)

from scripts.compute_h_daily import compute_h_day, LEDGER_HEADER
rows = compute_h_day(TARGET, verbose=False)

print(f"\n  Total rows: {len(rows)}")
n_h1  = sum(1 for r in rows if r["h1_skew"] != "")
n_h2  = sum(1 for r in rows if r["h2_oiw"] != "")
n_h3  = sum(1 for r in rows if r["h3_conc"] != "")
n_h4  = sum(1 for r in rows if r["h4_cloc"] != "")
n_wl  = sum(1 for r in rows if r["in_watchlist"])
n_nan = sum(1 for r in rows if all(r[k] == "" for k in ["h1_skew","h2_oiw","h3_conc","h4_cloc"]))
n_settle1h = sum(1 for r in rows if r["guard_settle_1h_unfilt"])
n_bkthin   = sum(1 for r in rows if int(r.get("guard_book_thin_nan", 0)) > 0)

print(f"  h1_skew valid    : {n_h1}")
print(f"  h2_oiw valid     : {n_h2}")
print(f"  h3_conc valid    : {n_h3}")
print(f"  h4_cloc valid    : {n_h4}")
print(f"  in_watchlist     : {n_wl}")
print(f"  all_NaN rows     : {n_nan}")
print(f"  settle_1h_unfilt : {n_settle1h}")
print(f"  book_thin_fired  : {n_bkthin}")

# ── [C] HEADER LEDGER ────────────────────────────────────────────────────────────
print(f"\n[C] LEDGER HEADER")
print("  " + ",".join(LEDGER_HEADER))

# ── [D] SAMPLE ROWS ─────────────────────────────────────────────────────────────
print(f"\n[D] SAMPLE ROWS — token có H đủ + NaN từng loại guard")
print("-" * 110)
hdr = f"{'symbol':>16} {'h1_skew':>9} {'h2_oiw':>9} {'h3_conc':>8} {'h4_cloc':>8} {'wl':>3} {'s_ex':>5} {'s1u':>4} {'bt':>4} {'note'}"
print(hdr)
print("-" * 110)

shown = set()

def show(r, note=""):
    sym = r["symbol"]
    if sym in shown: return
    shown.add(sym)
    h1 = r["h1_skew"] if r["h1_skew"] else "NaN"
    h2 = r["h2_oiw"]  if r["h2_oiw"]  else "NaN"
    h3 = r["h3_conc"] if r["h3_conc"] else "NaN"
    h4 = r["h4_cloc"] if r["h4_cloc"] else "NaN"
    wl = "WL" if r["in_watchlist"] else "  "
    se = r["guard_settle_excl"]
    s1 = r["guard_settle_1h_unfilt"]
    bt = r["guard_book_thin_nan"]
    print(f"  {sym:>16} {h1:>9} {h2:>9} {h3:>8} {h4:>8} {wl:>3} {str(se):>5} {str(s1):>4} {str(bt):>4}  {note}")

# Find specific tokens of interest
by_sym = {r["symbol"]: r for r in rows}

# Priority tokens
for sym in ["BANKUSDT", "TUTUSDT", "CYSUSDT", "AKEUSDT"]:
    if sym in by_sym:
        note = "positive-case"
        if sym == "AKEUSDT": note += " (AKE store from Jun26)"
        show(by_sym[sym], note)

# Token with full H (all 4 valid)
for r in rows:
    if all(r[k] != "" for k in ["h1_skew","h2_oiw","h3_conc","h4_cloc"]):
        show(r, "full H (all 4 valid)")
        break

# Token with h1=NaN (insufficient hours per side)
for r in rows:
    if r["h1_skew"] == "" and r["h3_conc"] != "":
        show(r, "h1=NaN (< 5hrs/side or few hrs)")
        break

# Token with h2=NaN (not in watchlist)
for r in rows:
    if r["h2_oiw"] == "" and r["h1_skew"] != "" and not r["in_watchlist"]:
        show(r, "h2=NaN (not in watchlist)")
        break

# Token with h2=NaN but in watchlist (OI missing)
for r in rows:
    if r["h2_oiw"] == "" and r["in_watchlist"]:
        show(r, "h2=NaN (in WL but no OI data)")
        break

# Token with book_thin_nan > 0
for r in rows:
    if int(r["guard_book_thin_nan"]) > 0:
        show(r, f"Δ7 book_thin fired")
        break

# Token with settle_1h_unfilt
for r in rows:
    if r["guard_settle_1h_unfilt"]:
        show(r, "Δ8 settle_1h_unfiltered")
        break

# More tokens with WL
for r in rows:
    if r["in_watchlist"] and r["symbol"] not in shown:
        show(r, "watchlist")
    if len(shown) >= 15: break

print("-" * 110)
print(f"\n  guard_dup_klines (day total): {rows[0]['guard_dup_klines'] if rows else 'N/A'}")
print(f"  guard_dup_oi (day total)    : {rows[0]['guard_dup_oi'] if rows else 'N/A'}")

print("\n" + "=" * 80)
print("DONE")
