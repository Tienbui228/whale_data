"""A3-7 · UNHEDGE line samples cho BTR · BULLA · LIGHT · LSK từ data thật.

In dòng UNHEDGE (format A3-1) cho MỌI ngày trong window mà U0-BELL / U0-NEAR trigger.
Nếu KHÔNG có ngày nào → in "no BELL day in window".
"""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import u0_bell, format_bell_line

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

TOKENS = ["BTR", "BULLA", "LIGHT", "LSK"]
WINDOW_START = datetime(2026, 6, 1).date()
WINDOW_END = datetime(2026, 9, 17).date()

print(f"═══ A3-7 · UNHEDGE line samples · window {WINDOW_START} → {WINDOW_END} ═══\n")

for tok in TOKENS:
    rows = by_sym.get(tok, [])
    if not rows:
        print(f"── {tok} ──")
        print(f"  [NO-DATA in fw store]\n")
        continue

    print(f"── {tok} ──")
    bell_days = []
    near_days = []
    d = WINDOW_START
    while d <= WINDOW_END:
        res = u0_bell(rows, d.isoformat(), _div_avg3)
        if res["status"] == "BELL":
            bell_days.append((d.isoformat(), res))
            line = format_bell_line(tok, d.isoformat(), res)
            print(f"  {line}")
        elif res["status"] == "NEAR":
            near_days.append((d.isoformat(), res))
        d += timedelta(days=1)

    if not bell_days:
        print(f"  no U0-BELL day (A3-1 strict: div ≤ 0.5 ∧ Δacc_bwd ≤ -20% ∧ |Δpos_bwd| ≤ 10%)")
    if near_days:
        print(f"  --- NEAR days (audit-only, không render dòng) ---")
        for dstr, r in near_days[:5]:  # limit 5
            print(f"    [U0-NEAR] {dstr} · Δacc_bwd={r['dacc_bwd']*100:+.1f}%")
        if len(near_days) > 5:
            print(f"    ... + {len(near_days)-5} NEAR days khác")
    print()

print("═══ Tổng kết A3-7 · UNHEDGE render samples ═══")
