"""AM · đo REAL Δacc/Δpos tại D_cross cho SOPH/BULLA/BTR."""
import sys
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from b_state_tracker import _load_fw_rows, _find_latest_cross
from u0_bell import delta_bwd

TARGETS = ["2026-09-13", "2026-09-14", "2026-09-19", "2026-09-20"]

for tgt in TARGETS:
    print(f"\n═══ target={tgt} ═══")
    by_sym = _load_fw_rows(tgt)
    for tok in ["SOPH", "BULLA", "BTR", "BMT"]:
        rows = by_sym.get(tok, [])
        if not rows:
            print(f"  {tok}: no data")
            continue
        d_cross = _find_latest_cross(rows, tgt)
        if not d_cross:
            print(f"  {tok}: D_cross=None")
            continue
        dacc, _, _ = delta_bwd(rows, d_cross, "lsr_acc_r")
        dpos, _, _ = delta_bwd(rows, d_cross, "lsr_pos_r")
        pass_15_10 = dacc is not None and dpos is not None and dacc <= -0.15 and abs(dpos) <= 0.10
        pass_30_5 = dacc is not None and dpos is not None and dacc <= -0.30 and abs(dpos) <= 0.05
        print(f"  {tok:6s}: D_cross={d_cross} · Δacc={dacc*100:+.1f}% · |Δpos|={abs(dpos)*100:.1f}% · "
              f"L1(-15/10)={pass_15_10} · L1(-30/5)={pass_30_5}")
