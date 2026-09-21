"""Quick debug: BULLA state + D_cross detection over 09-11..09-17."""
import sys
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")
from b_state_tracker import _load_fw_rows, _find_latest_cross, build_b_state, _check_u0_class_L1

for tgt in ["2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17"]:
    by_sym = _load_fw_rows(tgt)
    bulla = by_sym.get("BULLA", [])
    if not bulla:
        print(f"{tgt}: BULLA rows=0 (no data)")
        continue
    d = _find_latest_cross(bulla, tgt)
    state = build_b_state(tgt, universe=["BULLA"], by_sym={"BULLA": bulla})
    if d:
        l1, dacc, dpos = _check_u0_class_L1(bulla, d)
        s = state.get("BULLA", {"tier": "None"})
        print(f"{tgt}: BULLA D_cross={d} · L1={l1} (dacc={dacc}, dpos={dpos}) · tier={s.get('tier')}")
    else:
        print(f"{tgt}: BULLA D_cross=None · state={state.get('BULLA', 'None')}")
