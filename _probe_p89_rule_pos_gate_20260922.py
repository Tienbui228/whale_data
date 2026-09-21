"""p89 · pin LUẬT AO2 · event có |Δpos| > 10% → KHÔNG L1 (thành L2/L3).

Kiểm LUẬT, không kiểm "token X phải/không được CONFIRMED".
Ca minh hoạ: SOPH 08/09 (per thư dẫn 29.6% / bảng A2 dẫn 24% — in số REAL đo được).

Sau đổi ngưỡng: in mọi event SOPH (Δacc · |Δpos| · loại) trong window quét.
Nếu có event nào |Δpos| ≤ 10% thì nó LÀ L1 theo luật — ghi nhận, không dịch ngưỡng.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

from b_state_tracker import (
    _load_fw_rows, _find_latest_cross, _check_u0_class_L1,
    L1_DACC_MAX, L1_DPOS_MAX_ABS,
)
from u0_bell import delta_bwd

print(f"═══ p89 · pin LUẬT L1: |Δpos| ≤ 10% (AO1 ngưỡng ký) ═══")
print(f"  L1 config: Δacc ≤ {L1_DACC_MAX*100:+.0f}% ∧ |Δpos| ≤ {L1_DPOS_MAX_ABS*100:.0f}%")

# ── Part 1 · RULE test: fabricated (dacc, dpos) → class ──
cases = [
    # (dacc, dpos, expected_is_L1, note)
    (-0.10, 0.05, False, "Δacc -10% > -15% → L2/L3"),
    (-0.20, 0.05, True,  "Δacc -20% ≤ -15% ∧ |Δpos| 5% ≤ 10% → L1"),
    (-0.20, 0.15, False, "|Δpos| 15% > 10% → L2/L3"),
    (-0.60, 0.25, False, "|Δpos| 25% > 10% (SOPH-like) → L2/L3"),
    (-0.26, 0.09, True,  "Δacc -26% ∧ |Δpos| 9% (BULLA-like) → L1"),
]
rule_pass = True
print("\n─── Case đo LUẬT (fixed dacc/dpos) ───")
for dacc, dpos, exp, note in cases:
    is_l1 = dacc <= L1_DACC_MAX and abs(dpos) <= L1_DPOS_MAX_ABS
    ok = "PASS" if is_l1 == exp else "FAIL"
    if is_l1 != exp: rule_pass = False
    print(f"  Δacc={dacc*100:+.0f}% · |Δpos|={abs(dpos)*100:.0f}% → is_L1={is_l1} (expect {exp}) · {ok} · {note}")

# ── Part 2 · in số đo REAL cho SOPH: mọi (dacc, dpos) tại các D_cross trong 09-08..09-20 ──
print("\n─── SOPH REAL (số đo từ freshwatch) ───")
print(f"{'target':12s} | {'D_cross':10s} | {'Δacc':>7s} | {'|Δpos|':>7s} | class")
for tgt in ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11", "2026-09-13", "2026-09-14",
            "2026-09-15", "2026-09-17", "2026-09-19"]:
    by_sym = _load_fw_rows(tgt)
    rows = by_sym.get("SOPH", [])
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

print(f"\n═══ p89 · LUẬT · {'PASS' if rule_pass else 'FAIL'} ═══")
sys.exit(0 if rule_pass else 1)
