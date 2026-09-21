"""p87 · pin LUẬT AO2 · Δacc ≤ -15% ∧ |Δpos| ≤ 10% → L1.

Ca minh hoạ BULLA D_cross=2026-08-30 · Δacc -25.9% · |Δpos| 9.4% (REAL đo).
Kiểm LUẬT, không kiểm "BULLA phải CONFIRMED".
"""
import sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

from b_state_tracker import (
    _load_fw_rows, _find_latest_cross, _check_u0_class_L1,
    L1_DACC_MAX, L1_DPOS_MAX_ABS,
)
from u0_bell import delta_bwd

print(f"═══ p87 · pin LUẬT L1 dương-tính (AO1 ngưỡng ký) ═══")
print(f"  L1 config: Δacc ≤ {L1_DACC_MAX*100:+.0f}% ∧ |Δpos| ≤ {L1_DPOS_MAX_ABS*100:.0f}%")

# ── BULLA REAL số đo ──
print("\n─── BULLA REAL (số đo từ freshwatch) ───")
print(f"{'target':12s} | {'D_cross':10s} | {'Δacc':>7s} | {'|Δpos|':>7s} | class")
for tgt in ["2026-09-11", "2026-09-13", "2026-09-14", "2026-09-15", "2026-09-17", "2026-09-19"]:
    by_sym = _load_fw_rows(tgt)
    rows = by_sym.get("BULLA", [])
    if not rows: continue
    d_cross = _find_latest_cross(rows, tgt)
    if not d_cross: continue
    dacc, _, _ = delta_bwd(rows, d_cross, "lsr_acc_r")
    dpos, _, _ = delta_bwd(rows, d_cross, "lsr_pos_r")
    if dacc is None or dpos is None:
        print(f"  {tgt:12s} | {d_cross:10s} | (blind)")
        continue
    is_l1 = dacc <= L1_DACC_MAX and abs(dpos) <= L1_DPOS_MAX_ABS
    cls = "L1" if is_l1 else "L2_OR_L3"
    print(f"  {tgt:12s} | {d_cross:10s} | {dacc*100:+6.1f}% | {abs(dpos)*100:6.1f}% | {cls}")

# ── Rule check: BULLA number (dacc=-0.259, dpos=-0.094) ──
DACC_BULLA = -0.259
DPOS_BULLA = -0.094
is_l1 = DACC_BULLA <= L1_DACC_MAX and abs(DPOS_BULLA) <= L1_DPOS_MAX_ABS
p87 = is_l1
print(f"\n─── LUẬT: (Δacc={DACC_BULLA*100:.1f}%, |Δpos|={abs(DPOS_BULLA)*100:.1f}%) → is_L1={is_l1}")
print(f"═══ p87 · LUẬT · {'PASS' if p87 else 'FAIL'} ═══")
sys.exit(0 if p87 else 1)
