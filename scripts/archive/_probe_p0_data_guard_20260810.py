"""P0 (b): Check NaN% in lsr/oi/taker cols for FF in freshwatch CSVs 08-01→08-09.

data-source: scratch/freshwatch_daily_2026-08.csv (local) + VPS path (SSH)
machine: local
date-range: 2026-08-01 → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, csv, json
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")

CHECK_COLS = ["px_avg", "vol_quote", "taker_buy_pct", "funding_avg",
              "oi_usd", "lsr_pos_r", "lsr_acc_r", "lsr_global_r", "taker_ratio"]
DATE_FROM = "2026-08-01"
DATE_TO   = "2026-08-09"

def check_csv(path: Path, label: str) -> None:
    print(f"\n=== {label}: {path.name} ===")
    if not path.exists():
        print(f"  NOT FOUND: {path}")
        return

    rows_ff = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol", "")
            dt  = row.get("date", "")
            if sym == "FFUSDT" and DATE_FROM <= dt <= DATE_TO:
                rows_ff.append(row)

    if not rows_ff:
        print(f"  NO FFUSDT rows in {DATE_FROM}→{DATE_TO}")
        return

    rows_ff.sort(key=lambda r: r.get("date",""))
    print(f"  Found {len(rows_ff)} FFUSDT rows: {rows_ff[0]['date']} → {rows_ff[-1]['date']}")

    # Check each column for null/blank
    def is_null(v): return v is None or str(v).strip() in ("", "nan", "None", "N/A")

    print(f"\n  {'date':<12} {'px_avg':>8} {'vol_quote':>10} {'oi_usd':>12} {'lsr_pos_r':>10} "
          f"{'lsr_acc_r':>10} {'lsr_global_r':>12} {'taker_ratio':>12} {'funding_avg':>12}")
    print("  " + "-"*105)
    null_counts = {c: 0 for c in CHECK_COLS}
    for r in rows_ff:
        def sf(c): return r.get(c,"") or ""
        def fv(c):
            v = sf(c)
            if is_null(v): null_counts[c] += 1; return "NULL"
            try: return f"{float(v):.4f}"
            except: return v[:8]
        print(f"  {r['date']:<12} {fv('px_avg'):>8} {fv('vol_quote'):>10} {fv('oi_usd'):>12} "
              f"{fv('lsr_pos_r'):>10} {fv('lsr_acc_r'):>10} {fv('lsr_global_r'):>12} "
              f"{fv('taker_ratio'):>12} {fv('funding_avg'):>12}")

    n = len(rows_ff)
    print(f"\n  NULL counts out of {n} rows:")
    for c in CHECK_COLS:
        pct = null_counts[c] / n * 100
        flag = " ⚠" if pct > 50 else (" !" if pct > 0 else "")
        print(f"    {c:<15}: {null_counts[c]}/{n} = {pct:.0f}%{flag}")

# Check local scratch
check_csv(ROOT / "scratch" / "freshwatch_daily_2026-08.csv", "LOCAL SCRATCH")

# Also check data/export if present locally
check_csv(ROOT / "data" / "export" / "freshwatch_daily_2026-08.csv", "LOCAL EXPORT")

print("\n[Done — VPS canonical check: run same script on VPS or SSH separately]")
