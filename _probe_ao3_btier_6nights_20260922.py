"""AO3 · bảng btier 6 đêm sau AO1 · CONFIRMED · CROSS · FAILED · ngoài L1.
Không bình luận theo giá."""
import sys, json
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

from b_state_tracker import build_b_state, L1_DACC_MAX, L1_DPOS_MAX_ABS, L2L3_AUDIT

# Clear audit file each run · fresh count
if L2L3_AUDIT.exists(): L2L3_AUDIT.unlink()

print(f"L1 config: Δacc ≤ {L1_DACC_MAX*100:+.0f}% ∧ |Δpos| ≤ {L1_DPOS_MAX_ABS*100:.0f}%")
print()
print(f"{'target':12s} | {'CONF':>4s} | {'CROSS':>5s} | {'cand':>4s} | {'FAIL':>4s} | {'STALE':>5s} | {'ngoài L1':>8s}")
print(f"{'-'*12} | {'-'*4} | {'-'*5} | {'-'*4} | {'-'*4} | {'-'*5} | {'-'*8}")

for tgt in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20"]:
    state = build_b_state(tgt)
    counts = {"CONFIRMED": 0, "CROSS": 0, "cand": 0, "FAILED": 0, "STALE": 0}
    for s in state.values():
        t = s.get("tier")
        if t in counts: counts[t] += 1

    # Count "ngoài L1" từ audit reject file cho target này
    n_out = 0
    if L2L3_AUDIT.exists():
        for line in L2L3_AUDIT.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("target") == tgt: n_out += 1
            except Exception: pass  # L-66-OK (audit parse benign)

    print(f"{tgt:12s} | {counts['CONFIRMED']:>4d} | {counts['CROSS']:>5d} | "
          f"{counts['cand']:>4d} | {counts['FAILED']:>4d} | {counts['STALE']:>5d} | {n_out:>8d}")

    # Reset audit sau mỗi đêm để count đúng cho đêm sau
    if L2L3_AUDIT.exists(): L2L3_AUDIT.unlink()
