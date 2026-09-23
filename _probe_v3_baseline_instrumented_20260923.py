"""V3 · S4 baseline recompute · instrumented COPY của _probe_ao_20260918.py.

MUC TIÊU (đo, không kết luận):
  · n_num (tử số) · n_denom (mẫu số) · rate (33.4%) → in số chính xác
  · Loại token-night có [D−2, D+10] ∩ {24, 25, 26/07} ≠ ∅
    → n_loại · n_num' · n_denom' · rate'
  · Rate theo dải div_avg3(D): {<0.3, 0.3-0.4, 0.4-0.5}
    → mỗi dải: n_num/n_denom/rate

Nguồn gốc: bản sao _probe_ao_20260918.py · original md5=d840135ca65420e6a8322dae57839666
  KHÔNG sửa bản gốc · file này là bản mới độc lập.

NGUỒN input: data/export/freshwatch_daily_2026-{05..09}.csv
Window: TODAY=2026-09-17 · WINDOW_START=2026-06-19 · WINDOW_END=2026-09-05 (79 ngày)
Baseline gate: div_avg3(D) ≤ 0.5 (hedge state · pre-registered)
"""
import sys, os, csv, math
from pathlib import Path
from datetime import datetime, timedelta

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

import importlib
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3

TARGET = "2026-09-17"
TODAY = datetime.strptime(TARGET, "%Y-%m-%d").date()

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = _REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None

fw_p = _REPO / "data/config/freshwatch_symbols.txt"
universe = [l.strip().replace("USDT","") for l in fw_p.read_text(encoding="utf-8").splitlines() if l.strip()]

WINDOW_START = TODAY - timedelta(days=90)
WINDOW_END = TODAY - timedelta(days=12)

# Exclusion set · [D-2, D+10] ∩ {24, 25, 26/07} ≠ ∅
EXCL_DATES = {(2026, 7, 24), (2026, 7, 25), (2026, 7, 26)}

def _touches_excl(d):
    """D thỏa: [D-2, D+10] intersects EXCL_DATES."""
    for i in range(-2, 11):
        dd = d + timedelta(days=i)
        if (dd.year, dd.month, dd.day) in EXCL_DATES:
            return True
    return False

def find_cross(rows, d_start, d_end):
    d = d_start
    while d <= d_end:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt)
        vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            return dt
        d += timedelta(days=1)
    return None


def scan_baseline():
    """Scan mọi token-night có div_avg3(D) ≤ 0.5 · check [D+1, D+10] cross.
    Trả list of (tok, D, div_D, cross_date_or_None, touches_excl).
    KHÔNG áp threshold dacc — chỉ base rate.
    """
    baseline = []
    for tok in universe:
        if tok not in by_sym: continue
        rows = by_sym[tok]
        d = WINDOW_START
        while d <= WINDOW_END:
            div_D = _div_avg3(rows, d.isoformat())
            if div_D is None or div_D > 0.5:
                d += timedelta(days=1); continue
            cr = find_cross(rows, d + timedelta(days=1), d + timedelta(days=10))
            excl = _touches_excl(d)
            baseline.append((tok, d.isoformat(), div_D, cr, excl))
            d += timedelta(days=1)
    return baseline


print("═══ V3 · S4 baseline recompute · instrumented (đo, không kết luận) ═══\n")
print(f"NGUỒN: data/export/freshwatch_daily_2026-{{05..09}}.csv (5 files)")
print(f"NGUỒN: universe = data/config/freshwatch_symbols.txt · n={len(universe)}")
print(f"NGUỒN: gate = div_avg3(D) ≤ 0.5 (hedge state · pre-registered)")
print(f"WINDOW: {WINDOW_START.isoformat()} → {WINDOW_END.isoformat()} ({(WINDOW_END-WINDOW_START).days + 1} ngày)")
print(f"FORWARD: [D+1, D+10] · cross-check\n")

baseline = scan_baseline()
n_denom = len(baseline)
n_num = sum(1 for r in baseline if r[3] is not None)
rate = n_num / n_denom * 100 if n_denom > 0 else 0

print(f"─── Bảng V3.a · baseline TOÀN cửa sổ ───")
print(f"n_denom (token-night hedge): {n_denom}")
print(f"n_num   (cross trong [D+1, D+10]): {n_num}")
print(f"rate = n_num / n_denom = {rate:.2f}% · so với spec 33.4%: {rate-33.4:+.2f} pp\n")

# Loại 24-26/07
excl_baseline = [r for r in baseline if r[4]]
kept_baseline = [r for r in baseline if not r[4]]
n_denom_excl = len(kept_baseline)
n_num_excl = sum(1 for r in kept_baseline if r[3] is not None)
rate_excl = n_num_excl / n_denom_excl * 100 if n_denom_excl > 0 else 0

print(f"─── Bảng V3.b · loại token-night [D-2, D+10] chạm 24-26/07 ───")
print(f"n_loại (D thỏa chạm 24-26/07): {len(excl_baseline)}")
print(f"n_denom' (giữ): {n_denom_excl}")
print(f"n_num' (giữ · cross trong [D+1, D+10]): {n_num_excl}")
print(f"rate' = n_num' / n_denom' = {rate_excl:.2f}% · so với rate ban đầu {rate:.2f}%: {rate_excl-rate:+.2f} pp\n")

# Rate theo dải div_avg3
print(f"─── Bảng V3.c · rate theo dải div_avg3(D) ───")
buckets = {
    "<0.3":       [r for r in baseline if r[2] < 0.3],
    "0.3-0.4":    [r for r in baseline if 0.3 <= r[2] < 0.4],
    "0.4-0.5":    [r for r in baseline if 0.4 <= r[2] <= 0.5],
}
print(f"{'bucket':>12s} | {'n_num':>7s} | {'n_denom':>8s} | {'rate':>7s}")
print(f"{'-'*12} | {'-'*7} | {'-'*8} | {'-'*7}")
for name, rows in buckets.items():
    d = len(rows)
    n = sum(1 for r in rows if r[3] is not None)
    r_ = n/d*100 if d > 0 else 0
    print(f"{name:>12s} | {n:>7d} | {d:>8d} | {r_:>6.2f}%")

print()
print(f"═══ V3 TỔNG · IN SỐ · KHÔNG kết luận ═══")
