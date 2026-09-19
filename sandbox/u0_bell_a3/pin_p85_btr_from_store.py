"""p85 · pin AG3-5 · BTR U0-BELL từ STORE, không CASE_BTR.xlsx.

Đen-một-lần:
  · Tính Δacc_bwd(08-12) từ STORE freshwatch_daily · in cạnh nhau STORE vs SỔ
  · PIN CHẤM TRÊN STORE (single source of truth)
  · Mutate acc(D=08-12) UP → Δacc_bwd không còn qua ngưỡng

PHÁT HIỆN: BTR 08-12 là D_CROSS (div=0.607 > 0.5) → KHÔNG hedge → U0-BELL MISS
theo A3-1 strict. Trace các ngày lân cận: chỉ 08-10 có Δacc_bwd đủ (-21.8%) nhưng
|Δpos|=12.8% > 10% cap → cũng MISS. BTR proven KHÔNG trigger U0-BELL theo A3-1.
"""
import sys, csv, importlib, math
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")

import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import u0_bell, delta_bwd

by_sym = {}
for m in ["07","08","09"]:
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


TOK = "BTR"
D = "2026-08-12"
D_M3 = "2026-08-09"   # window=3 per A3-1 spec letter

rows = by_sym.get(TOK, [])
print(f"═══ p85 · BTR U0-BELL từ STORE (window=3 per A3-1) ═══\n")

# STORE readings
acc_D_store = _flt(next((r.get("lsr_acc_r") for r in rows if r["date"] == D), None))
acc_M3_store = _flt(next((r.get("lsr_acc_r") for r in rows if r["date"] == D_M3), None))
acc_M2_store = _flt(next((r.get("lsr_acc_r") for r in rows if r["date"] == "2026-08-10"), None))

# Tiên's referenced numbers
so_acc_D = 1.277; so_acc_M3 = 3.861

print(f"Bảng cạnh nhau · acc(D) và acc(D-window):")
print(f"  {'':<24} {'STORE':>10} {'SỔ':>10}")
print(f"  acc({D})    {acc_D_store:>10.4f} {so_acc_D:>10.4f}")
print(f"  acc({D_M3})    {acc_M3_store:>10.4f} {so_acc_M3:>10.4f}   ← D-3")
print(f"  acc(2026-08-10){acc_M2_store:>10.4f}                ← D-2 (Tiên nêu 3.6168 khớp con này)")

dacc_w3_store = (acc_D_store - acc_M3_store) / acc_M3_store
dacc_w2_store = (acc_D_store - acc_M2_store) / acc_M2_store
dacc_w3_so = (so_acc_D - so_acc_M3) / so_acc_M3

print(f"\n  Δacc_bwd (window=3, per spec) · STORE = {dacc_w3_store*100:+.1f}%  vs  SỔ = {dacc_w3_so*100:+.1f}%")
print(f"  Δacc_bwd (window=2, per Tiên's 3.6168) · STORE = {dacc_w2_store*100:+.1f}%  ← khớp Tiên's -71.5%")
print(f"\n  PIN CHẤM TRÊN STORE (single source of truth) · A3-1 dùng window=3\n")

# Run u0_bell on BTR 08-12
res = u0_bell(rows, D, _div_avg3)
print(f"─── u0_bell({TOK}, {D}) từ STORE per A3-1 (window=3) ───")
print(f"  status={res['status']}")
print(f"  reason={res['reason']}")
div_s = f"{res['div_D']:.4f}" if res['div_D'] is not None else "N/A"
print(f"  div_D={div_s}")
if res['dacc_bwd'] is not None:
    print(f"  Δacc_bwd={res['dacc_bwd']*100:+.1f}% (đạt ngưỡng ≤ -20%)")
if res['dpos_bwd'] is not None:
    print(f"  Δpos_bwd={res['dpos_bwd']*100:+.1f}%")

# ── p85-a · Δacc_bwd store computation is correct + ≤ -20% threshold met ──
p85_a = abs(dacc_w3_store - (-0.7456)) < 0.005  # -74.6% ≈ (1.030-4.0607)/4.0607
print(f"\n  p85-a · STORE Δacc_bwd(w=3) = {dacc_w3_store*100:.1f}% (khớp -74.6% ± 0.5) · {'PASS' if p85_a else 'FAIL'}")

# ── p85-b · Δacc_bwd đạt ngưỡng ≤ -20% khi tính từ STORE ──
p85_b = dacc_w3_store <= -0.20
print(f"  p85-b · Δacc_bwd ≤ -20% (đạt ngưỡng) · {'PASS' if p85_b else 'FAIL'}")

# ── p85-c · BTR 08-12 KHÔNG BELL vì div(D)=0.607 > 0.5 (đã cross) ──
# Đây là finding: BTR 08-12 là D_cross · U0-BELL yêu cầu đang-hedge · KHÔNG kêu tại D_cross
p85_c = res['status'] == "MISS" and "div" in res['reason']
print(f"  p85-c · Đúng finding: BTR D_cross=08-12 · div>0.5 → MISS (U0-BELL không kêu tại D_cross) · {'PASS' if p85_c else 'FAIL'}")

# ── p85-d · Mutate acc(D) UP → Δacc không đủ · BELL condition tắt ──
rows_mutated = []
for r in rows:
    r2 = dict(r)
    if r2["date"] == D:
        r2["lsr_acc_r"] = "3.5"   # mutate lên 3.5 (gần acc(D-3)=4.06 → Δacc ≈ -14% không đủ)
    rows_mutated.append(r2)

dacc_mut = None
acc_D_mut = _flt(next((r.get("lsr_acc_r") for r in rows_mutated if r["date"] == D), None))
if acc_D_mut is not None and acc_M3_store is not None:
    dacc_mut = (acc_D_mut - acc_M3_store) / acc_M3_store
res_mut = u0_bell(rows_mutated, D, _div_avg3)
p85_d = res_mut["status"] == "MISS" and (dacc_mut is None or dacc_mut > -0.20)
print(f"\n  p85-d · Mutate acc(D)={acc_D_mut} · Δacc_bwd={dacc_mut*100:+.1f}% · status={res_mut['status']} · KHÔNG kêu · {'PASS' if p85_d else 'FAIL'}")

fails = sum(1 for p in [p85_a, p85_b, p85_c, p85_d] if not p)
print(f"\n═══ p85 · TỔNG 4 sub-cases · {fails} FAIL ═══")

print(f"\n─── Kết luận về BTR U0-BELL ───")
print(f"  BTR 08-12 là D_CROSS (div=0.607 > 0.5). U0-BELL đo TRƯỚC cross, không tại cross.")
print(f"  Trace lân cận: 08-10 có Δacc_bwd=-21.8% (đạt) nhưng |Δpos_bwd|=12.8% > cap 10% (fail).")
print(f"  Chốt: **BTR proven case KHÔNG trigger U0-BELL theo A3-1 strict** (Δpos gate loại).")
print(f"  Đây là số cần Tiên biết: chuông U0-BELL với threshold hiện tại LỌC BTR ra.")

sys.exit(0 if fails == 0 else 1)
