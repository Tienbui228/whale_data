"""A3-4 · U1 v2∧v1 recalibration (bỏ v3) · sandbox · CALIBRATION-ONLY.

U1 mới: v2 (OI(D+5)/OI(D-1) ≥ 1.5) ∧ v1 (acc(D+5)/acc(D-1) ≤ 0.6). v3 pos in mô tả, không chấm.

Nhãn: [H-fit-n6][CALIBRATION-ONLY] — hindsight-fit trên n=6 proven, không hứa forward-generalize.
Mở lại khi ≥10 CONFIRMED.

Kỳ vọng: BULLA 08-30 thành CONFIRMED · tổng n=5.
"""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3

TARGET = "2026-09-17"
TODAY = datetime.strptime(TARGET, "%Y-%m-%d").date()

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
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

TOKENS = ["BTR","BULLA","UAI","LIGHT","SOPH","BROCCOLI","BROCCOLIF3B",
          "KOMA","BSB","AIA","BEAT","RIVER","SIGN"]

def find_all_crosses(rows):
    s = datetime(2026, 5, 1).date()
    crosses = []
    d = s
    while d <= TODAY:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt)
        vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            if not crosses or (d - datetime.strptime(crosses[-1], "%Y-%m-%d").date()).days > 7:
                crosses.append(dt)
        d += timedelta(days=1)
    return crosses

def check_u1(rows, d_cross):
    dc = datetime.strptime(d_cross, "%Y-%m-%d").date()
    d_p5 = (dc + timedelta(days=5)).isoformat()
    d_m1 = (dc - timedelta(days=1)).isoformat()
    if dc + timedelta(days=5) > TODAY: return None
    def _r(dt, f): return _flt(next((r.get(f) for r in rows if r["date"] == dt), None))
    acc_p5 = _r(d_p5, "lsr_acc_r"); acc_m1 = _r(d_m1, "lsr_acc_r")
    oi_p5 = _r(d_p5, "oi_usd"); oi_m1 = _r(d_m1, "oi_usd")
    pos_p5 = _r(d_p5, "lsr_pos_r"); pos_m1 = _r(d_m1, "lsr_pos_r")
    v1r = acc_p5/acc_m1 if (acc_p5 is not None and acc_m1 not in (None, 0)) else None
    v2r = oi_p5/oi_m1 if (oi_p5 is not None and oi_m1 not in (None, 0)) else None
    v3r = pos_p5/pos_m1 if (pos_p5 is not None and pos_m1 not in (None, 0)) else None
    v1p = v1r is not None and v1r <= 0.6
    v2p = v2r is not None and v2r >= 1.5
    v3p = v3r is not None and v3r >= 1.0
    return (v1r, v2r, v3r, v1p, v2p, v3p)

print(f"═══ A3-4 · U1 v2∧v1 recalibration · [H-fit-n6][CALIBRATION-ONLY] ═══\n")

# Table
print(f"{'token':<15} {'D_cross':<12} {'v1_ratio':>10} {'v2_ratio':>10} {'v3_ratio':>10} {'v2∧v1':>7} {'note':<30}")
print("─" * 92)

confirmed_v2v1 = []
for tok in TOKENS:
    rows = by_sym.get(tok, [])
    if not rows: continue
    for dc in find_all_crosses(rows):
        u1 = check_u1(rows, dc)
        if u1 is None: continue
        v1r, v2r, v3r, v1p, v2p, v3p = u1
        confirmed = v2p and v1p
        note = ""
        if confirmed:
            confirmed_v2v1.append((tok, dc, v1r, v2r, v3r))
            note = "★ CONFIRMED v2∧v1"
        v1s = f"{v1r:.3f}" if v1r else "—"
        v2s = f"{v2r:.3f}" if v2r else "—"
        v3s = f"{v3r:.3f} (desc)" if v3r else "—"
        print(f"  {tok:<13} {dc:<12} {v1s:>10} {v2s:>10} {v3s:>16} {'✓' if confirmed else '✗':>7} {note:<30}")

print(f"\n─── CONFIRMED n = {len(confirmed_v2v1)} ───")
for tok, dc, v1r, v2r, v3r in confirmed_v2v1:
    v3s = f"{v3r:.3f}" if v3r else "N/A"
    print(f"  {tok:<15} {dc:<12} · v1={v1r:.3f} · v2={v2r:.3f} · v3(desc)={v3s}")

# Check BULLA 08-30 in confirmed list
bulla_0830 = [x for x in confirmed_v2v1 if x[0] == "BULLA" and x[1] == "2026-08-30"]
if bulla_0830:
    print(f"\n★ BULLA 08-30 CONFIRMED · v3=0.970 (mô tả, không chấm) · KỲ VỌNG A3-4 ✓")
else:
    print(f"\n✗ BULLA 08-30 KHÔNG confirmed · lỗi kỳ vọng A3-4")

# Nhãn
print(f"\nNhãn tag: [H-fit-n6][CALIBRATION-ONLY]")
print(f"n_CONFIRMED = {len(confirmed_v2v1)} · Cần ≥10 để mở lại tune ngưỡng.")
