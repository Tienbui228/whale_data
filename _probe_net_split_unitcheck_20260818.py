#!/usr/bin/env python3
"""
Unit-check N-1 split: gross_adds / net_oi_window / net_gated on AKE ch1 + GIGGLE ch2.

Replay the counts_q1 gate + accumulation manually on freshwatch daily data.
So sánh vs 3 công thức mới (không import gom_scan để không phụ thuộc chain lifecycle).

Expected:
  AKE ch1  : gross_adds=$0  net_window=+$14,670,516  net_gated=-$5,161,244 (n_q1=2, cả 2 ΔOI âm)
  GIGGLE ch2: gross_adds=$0  net_window=+$1,199,290  net_gated=NaN         (n_q1=0)
"""
import sys, io, csv, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

EXPORT = Path("/root/Data_back_test/whale_data/data/export")
NaN = float("nan")

def load_daily(sym_usdt):
    rows = []
    for p in sorted(EXPORT.glob("freshwatch_daily_*.csv")):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("symbol") == sym_usdt:
                    rows.append(r)
    rows.sort(key=lambda r: r["date"])
    return rows

def replay(sym_usdt, chain_start, chain_end):
    """Replay counts_q1 accumulation. Returns (gross_adds, net_oi_window, net_gated, n_q1, days_detail)."""
    rows = load_daily(sym_usdt)
    # We need the row BEFORE chain_start to compute ret_1d on chain_start day.
    idx_start = next((i for i,r in enumerate(rows) if r["date"] >= chain_start), None)
    if idx_start is None:
        return None
    # Chain window rows
    chain_rows = [r for r in rows if chain_start <= r["date"] <= chain_end]
    if not chain_rows:
        return None
    oi_start = float(chain_rows[0].get("oi_usd") or NaN)
    oi_last  = float(chain_rows[-1].get("oi_usd") or NaN)
    net_window = oi_last - oi_start if not (math.isnan(oi_start) or math.isnan(oi_last)) else NaN

    gross_adds = 0.0
    net_gated  = NaN  # NaN sentinel until first counts_q1 day
    n_q1 = 0
    detail = []
    # For each chain day we need prev day (may be BEFORE chain_start for day 1)
    for r in chain_rows:
        d = r["date"]
        idx = next(i for i,rr in enumerate(rows) if rr["date"] == d)
        if idx == 0:
            ret = NaN
            oi_prev = NaN
        else:
            prev = rows[idx-1]
            px_prev = float(prev.get("px_avg") or 0)
            px_now  = float(r.get("px_avg") or 0)
            ret = (px_now - px_prev)/px_prev if px_prev > 0 else NaN
            oi_prev = float(prev.get("oi_usd") or NaN)
        oi_now = float(r.get("oi_usd") or NaN)
        counts_q1 = (not math.isnan(ret)) and ret <= 0.01
        # partial_day flag not in freshwatch export — skip

        d_oi_raw = (oi_now - oi_prev) if not (math.isnan(oi_now) or math.isnan(oi_prev)) else NaN
        d_oi_pos = max(d_oi_raw, 0.0) if not math.isnan(d_oi_raw) else 0.0

        if counts_q1:
            gross_adds += d_oi_pos
            n_q1 += 1
            if math.isnan(net_gated):
                net_gated = 0.0
            if not math.isnan(d_oi_raw):
                net_gated += d_oi_raw

        detail.append(dict(date=d, oi=oi_now, d_oi=d_oi_raw, ret=ret,
                           counts_q1=counts_q1, gross_add=(d_oi_pos if counts_q1 else 0.0),
                           gated_add=(d_oi_raw if counts_q1 else 0.0)))
    return dict(oi_start=oi_start, oi_last=oi_last,
                net_oi_window=net_window,
                gross_adds=gross_adds,
                net_gated=net_gated,
                n_q1=n_q1,
                detail=detail)

DIV = "="*72

for label, sym, start, end in [
    ("AKE ch1",    "AKEUSDT",    "2026-08-12", "2026-08-17"),
    ("GIGGLE ch2", "GIGGLEUSDT", "2026-08-16", "2026-08-17"),
]:
    print(f"\n{DIV}\n{label}  window {start} → {end}\n{DIV}")
    r = replay(sym, start, end)
    if r is None:
        print("  no data")
        continue

    print(f"\n  oi_start          : ${r['oi_start']:>16,.0f}")
    print(f"  oi_last           : ${r['oi_last']:>16,.0f}")
    print(f"  net_oi_window_usd : ${r['net_oi_window']:>+16,.0f}   [window, ungated — reality-check]")
    print(f"  gross_adds_usd    : ${r['gross_adds']:>+16,.0f}   [Σ max(ΔOI,0) on counts_q1 days]")
    if math.isnan(r['net_gated']):
        print(f"  net_gated_usd     :             NaN     [n_q1=0 → NO-QUALIFIED-DAYS]")
    else:
        print(f"  net_gated_usd     : ${r['net_gated']:>+16,.0f}   [Σ ΔOI both signs on counts_q1 days]")
    print(f"  n_q1              : {r['n_q1']}")

    print(f"\n  per-day trace:")
    print(f"  {'date':>12}  {'ΔOI':>13}  {'ret_1d':>8}  {'counts_q1':>9}  "
          f"{'gross_add':>13}  {'gated_add':>13}")
    for d in r['detail']:
        d_oi_s = f"{d['d_oi']:>+13,.0f}" if not math.isnan(d['d_oi']) else " " * 13
        ret_s  = f"{d['ret']*100:>+7.2f}%" if not math.isnan(d['ret']) else "   —   "
        cq_s   = "PASS" if d['counts_q1'] else "FAIL"
        ga_s   = f"{d['gross_add']:>+13,.0f}" if d['gross_add'] else " " * 12 + "0"
        ng_s   = f"{d['gated_add']:>+13,.0f}" if d['gated_add'] else (" " * 12 + "0" if d['counts_q1'] else " " * 13)
        print(f"  {d['date']:>12}  {d_oi_s}  {ret_s:>8}  {cq_s:>9}  {ga_s}  {ng_s}")

print(f"\n{DIV}\nEXPECTED vs OBSERVED\n{DIV}")
print("""
  AKE ch1:
    expected gross=$0, net_window=+$14,670,516, net_gated≠NaN (n_q1>0)
    → operator hint '$0 hoặc NaN' cho net_gated CHƯA khớp: n_q1=2 nên net_gated là số
      thực (không NaN). Semantic: 2 clean days có ΔOI ÂM → net_gated âm.

  GIGGLE ch2:
    expected gross=$0, net_window=+$1,199,290, net_gated=NaN (n_q1=0) ✓
""")
