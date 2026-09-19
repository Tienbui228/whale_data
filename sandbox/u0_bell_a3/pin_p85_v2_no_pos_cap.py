"""p85 v2 · A5-0 · BTR 08-10 PHẢI kêu vì bỏ cap |Δpos|.

Old A3-1 strict: BTR 08-10 Δacc=-21.8% ĐẠT nhưng |Δpos|=12.8% > cap 10% → MISS.
New A5-0 (bỏ cap): BTR 08-10 Δacc=-21.8% ≤ -20% ∧ div=0.314 ≤ 0.5 → BELL.

Đen-một-lần: p85 cần chạy lại với bell function mới.
"""
import sys, csv, importlib, math
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
import u0_bell as u0mod; importlib.reload(u0mod)
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import u0_bell, format_bell_line, delta_bwd

by_sym = {}
for m in ["07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

TOK = "BTR"
rows = by_sym[TOK]

print(f"═══ p85 v2 · BTR sau A5-0 (bỏ cap |Δpos|) ═══\n")

# Case 1 · BTR 08-10 PHẢI kêu
D = "2026-08-10"
res = u0_bell(rows, D, _div_avg3)
p85v2_a = res["status"] == "BELL"
print(f"p85v2-a · BTR {D} · status={res['status']} · reason={res['reason']}")
print(f"  Δacc_bwd={res['dacc_bwd']*100:+.1f}% · Δpos_bwd={res['dpos_bwd']*100:+.1f}% · div={res['div_D']:.3f}")
print(f"  Expect BELL · {'PASS' if p85v2_a else 'FAIL'}")
if p85v2_a:
    print(f"  Line: {format_bell_line(TOK, D, res)}")

# Case 2 · BTR 08-12 (D_cross, div>0.5) vẫn MISS
D2 = "2026-08-12"
res2 = u0_bell(rows, D2, _div_avg3)
p85v2_b = res2["status"] == "MISS"
print(f"\np85v2-b · BTR {D2} (D_cross div=0.607>0.5) · status={res2['status']}")
print(f"  Expect MISS (không hedge) · {'PASS' if p85v2_b else 'FAIL'}")

# Case 3 · Mutate acc(D=08-10) UP → BTR 08-10 không còn BELL
rows_mut = [dict(r) if r["date"] == D else r for r in rows]
for r in rows_mut:
    if r["date"] == D and isinstance(r, dict):
        r["lsr_acc_r"] = "4.0"   # gần acc(D-3=08-07). Δacc gần 0.
res_mut = u0_bell(rows_mut, D, _div_avg3)
p85v2_c = res_mut["status"] in ("MISS", "NEAR")
print(f"\np85v2-c · Mutate acc({D})=4.0 · status={res_mut['status']} · Δacc={res_mut['dacc_bwd']*100:+.1f}%")
print(f"  Expect KHÔNG BELL · {'PASS' if p85v2_c else 'FAIL'}")

# Case 4 · Line format check: có [Δpos_bwd=... · desc] không?
if p85v2_a:
    line = format_bell_line(TOK, D, res)
    p85v2_d = "· desc]" in line and "Δpos_bwd" in line
    print(f"\np85v2-d · Line format có [Δpos_bwd=... · desc] · {'PASS' if p85v2_d else 'FAIL'}")
else:
    p85v2_d = False

fails = sum(1 for p in [p85v2_a, p85v2_b, p85v2_c, p85v2_d] if not p)
print(f"\n═══ p85 v2 · TỔNG 4 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
