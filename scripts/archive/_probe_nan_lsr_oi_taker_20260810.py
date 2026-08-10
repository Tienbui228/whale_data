"""Item (2): NaN% in lsr/oi/taker cols — ALL symbols, freshwatch CSV 08-01→08-09.

Root-cause chẩn đoán nói "freshwatch thiếu OI/LSR" → cần đo đúng, không chỉ FF.
Nếu data thủng → gộp vào án 4-symbols-FAPI.

data-source: /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv (VPS)
machine: VPS via SSH → pull về local temp
date-range: 2026-08-01 → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, csv, subprocess, tempfile
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
VPS_CSV = "/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv"
DATE_FROM = "2026-08-01"
DATE_TO   = "2026-08-09"

CHECK_COLS = ["px_avg", "vol_quote", "taker_buy_pct", "funding_avg",
              "oi_usd", "lsr_pos_r", "lsr_acc_r", "lsr_global_r", "taker_ratio"]

def is_null(v):
    return v is None or str(v).strip() in ("", "nan", "None", "N/A")

# Fetch VPS CSV
print(f"Fetching {VPS_CSV} from VPS...")
result = subprocess.run(
    ["ssh", VPS, f"cat {VPS_CSV}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if result.returncode != 0:
    print(f"SSH ERROR: {result.stderr}")
    sys.exit(1)

lines = result.stdout.splitlines()
print(f"Fetched {len(lines)} lines from VPS CSV")

# Parse
reader = csv.DictReader(lines)
rows_in_range: list[dict] = []
for row in reader:
    dt = row.get("date", "")
    if DATE_FROM <= dt <= DATE_TO:
        rows_in_range.append(row)

print(f"Rows in {DATE_FROM}→{DATE_TO}: {len(rows_in_range)}")

if not rows_in_range:
    print("NO ROWS — check date range or CSV")
    sys.exit(1)

# Symbol stats
dates_all = sorted(set(r["date"] for r in rows_in_range))
syms_all  = sorted(set(r["symbol"] for r in rows_in_range))
print(f"Dates: {dates_all[0]} → {dates_all[-1]} ({len(dates_all)} days)")
print(f"Symbols: {len(syms_all)}")

# Per-col null stats across ALL symbols
print(f"\n=== NULL% PER COLUMN (all {len(syms_all)} symbols, {len(rows_in_range)} rows) ===")
col_nulls = {c: 0 for c in CHECK_COLS}
for row in rows_in_range:
    for c in CHECK_COLS:
        if is_null(row.get(c)):
            col_nulls[c] += 1

n = len(rows_in_range)
print(f"{'column':<18} {'null_count':>10} {'null%':>8} {'flag'}")
print("-" * 50)
any_issue = False
for c in CHECK_COLS:
    pct = col_nulls[c] / n * 100
    flag = " ⚠ HIGH" if pct > 50 else (" ! partial" if pct > 0 else " ✓")
    if pct > 0:
        any_issue = True
    print(f"  {c:<16} {col_nulls[c]:>10,} {pct:>8.1f}%{flag}")

# Per-symbol breakdown for problem cols (null > 0)
problem_cols = [c for c in CHECK_COLS if col_nulls[c] > 0]

if problem_cols:
    print(f"\n=== PER-SYMBOL BREAKDOWN for problem cols: {problem_cols} ===")
    sym_col_nulls: dict[str, dict[str, int]] = defaultdict(lambda: {c: 0 for c in CHECK_COLS})
    sym_row_count: dict[str, int] = defaultdict(int)
    for row in rows_in_range:
        sym = row.get("symbol","")
        sym_row_count[sym] += 1
        for c in problem_cols:
            if is_null(row.get(c)):
                sym_col_nulls[sym][c] += 1

    # Show only symbols with any null in problem cols
    affected_syms = [s for s in syms_all
                     if any(sym_col_nulls[s][c] > 0 for c in problem_cols)]
    print(f"Affected symbols (any null in problem cols): {len(affected_syms)} / {len(syms_all)}")

    if affected_syms:
        # Show per-symbol details, sorted by worst first
        affected_syms.sort(key=lambda s: -max(sym_col_nulls[s][c] for c in problem_cols))
        header = f"{'symbol':<20} " + " ".join(f"{c[:10]:>10}" for c in problem_cols)
        print(f"\n  {header}")
        print("  " + "-" * (20 + 11 * len(problem_cols)))
        for sym in affected_syms[:50]:  # cap at 50
            nr = sym_row_count[sym]
            vals = " ".join(
                f"{sym_col_nulls[sym][c]/nr*100:>9.0f}%"
                for c in problem_cols
            )
            print(f"  {sym:<20} {vals}")
        if len(affected_syms) > 50:
            print(f"  ... ({len(affected_syms)-50} more symbols)")
else:
    print(f"\n=== No problem cols found — data CLEAN ===")

# Specific check: known FAPI delistedSymbols
KNOWN_FAPI = {"ACXUSDT", "HFTUSDT", "VANRYUSDT", "VICUSDT"}
print(f"\n=== KNOWN FAPI DELIST SYMBOLS: {KNOWN_FAPI} ===")
for sym in sorted(KNOWN_FAPI):
    sym_rows = [r for r in rows_in_range if r.get("symbol") == sym]
    if not sym_rows:
        print(f"  {sym}: NOT IN CSV (gap — expected for delist)")
    else:
        nulls = {c: sum(1 for r in sym_rows if is_null(r.get(c))) for c in CHECK_COLS}
        worst = max(nulls.values())
        print(f"  {sym}: {len(sym_rows)} rows, worst null={worst}/{len(sym_rows)}")

print(f"\n=== VERDICT ===")
high_pct_cols = [c for c in CHECK_COLS if col_nulls[c]/n*100 > 50]
partial_cols  = [c for c in CHECK_COLS if 0 < col_nulls[c]/n*100 <= 50]
if not high_pct_cols and not partial_cols:
    print("DATA CLEAN — 0 nulls across all cols. Root cause WAS NOT missing data.")
    print("Gộp vào án FAPI: KHÔNG CẦN (data đầy).")
elif high_pct_cols:
    print(f"THỦNG NẶNG: {high_pct_cols} → gộp vào án 4-symbols-FAPI")
else:
    print(f"PARTIAL NULL: {partial_cols} — xem per-symbol breakdown trên")
    print("Kiểm tra có phải 4 symbols FAPI bị delist gây ra không.")
