"""AQ1 · đo master sau E4(iii) chia lại · 6 đêm · CHƯA WIRE.

Master mới = khung + khối loài + CHƯA XẾP đủ (mỗi token `TOK cờ direction`)
             + khối B rút (CONFIRMED · CROSS L1 · 1 dòng đếm).

FAILED/cand/ngoài-L1 chuyển sang HEDGE v2 (không còn trong master).

Đo:
  · n_tokens CHƯA XẾP thật
  · tg_len pre-cap master mới (giả lập bằng trừ B đầy đủ + thêm B rút)
  · pin p108 (pre-cap ≤ 4096) từng đêm.

Không wire · chỉ đo.
"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import digest_summary_v2 as dsv
from lib.tg_len import tg_len
from b_state_tracker import build_b_state

def _b_reduced(state) -> str:
    """B rút = CONFIRMED tokens + CROSS L1 tokens + 1 dòng đếm."""
    conf = [(t, s) for t, s in state.items() if s.get("tier") == "CONFIRMED"]
    cross = [(t, s) for t, s in state.items() if s.get("tier") == "CROSS"]
    n_cand = sum(1 for s in state.values() if s.get("tier") == "cand")
    n_fail = sum(1 for s in state.values() if s.get("tier") == "FAILED")
    n_stale = sum(1 for s in state.values() if s.get("tier") == "STALE")

    lines = [f"── B ── ({len(conf)+len(cross)} · {len(conf)} CONFIRMED · {len(cross)} CROSS L1) [CAL-ONLY]"]
    for tok, s in conf:
        lines.append(f"[B] {tok} +{s['d_plus_k']}d")
    for tok, s in cross:
        lines.append(f"[B-CROSS] {tok} · L1 · D+{s['d_plus_k']}")
    lines.append(f"── (khối HEDGE v2 giữ: {n_cand} cand · {n_fail} FAILED · {n_stale} STALE · +ngoài L1)")
    return "\n".join(lines)


def _b_current(target, universe=None, by_sym=None) -> str:
    """B block hiện tại (M1-M8 + AO)."""
    from b_block_renderer import render_b_block
    return render_b_block(target, universe=universe, by_sym=by_sym)


print(f"AQ1 · ĐO master sau chia lại E4(iii) · 6 đêm · CHƯA WIRE")
print(f"Master mới = current - B_current + B_reduced (est)")
print()
print(f"{'target':12s} | {'pre_now':>7s} | {'B_now':>5s} | {'B_new':>5s} | {'Δ_B':>5s} | "
      f"{'est_new':>7s} | {'p108':>4s} | n_CHƯA_XẾP")
print(f"{'-'*12} | {'-'*7} | {'-'*5} | {'-'*5} | {'-'*5} | {'-'*7} | {'-'*4} | {'-'*10}")

# Get pre-cap current master (via monkey-patch as in dryrun)
_orig_cap = dsv._v1_3_apply_3tier_cap

for tgt in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20"]:
    try:
        dsv._v1_3_apply_3tier_cap = lambda b, budget=3680: b
        body_nocap = dsv.build_v2_digest(tgt)
    finally:
        dsv._v1_3_apply_3tier_cap = _orig_cap

    pre_now = tg_len(body_nocap)

    state = build_b_state(tgt)
    b_now = tg_len(_b_current(tgt))
    b_new = tg_len(_b_reduced(state))
    delta_b = b_new - b_now
    est_new = pre_now + delta_b
    p108 = "PASS" if est_new <= 4096 else "FAIL"

    # count CHƯA XẾP tokens · scan body_nocap
    m = re.search(r"── CHƯA XẾP LOÀI ── \((\d+)\)", body_nocap)
    n_chua = int(m.group(1)) if m else 0

    print(f"{tgt:12s} | {pre_now:>7d} | {b_now:>5d} | {b_new:>5d} | {delta_b:>+5d} | "
          f"{est_new:>7d} | {p108:>4s} | {n_chua}")

print()
print(f"Ước ANALYSIS: 1000-1400 chars saved. Δ_B trong bảng chỉ tính đổi khối B đầy → rút;")
print(f"chưa trừ FAILED/cand/ngoài-L1 (nếu chưa nằm trong B_current thì Δ nhỏ hơn kỳ vọng).")
