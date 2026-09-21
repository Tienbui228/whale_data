"""AP2 · đo tg_len 2 format 'ngoài L1' · 6 đêm · CHƯA WIRE.

Format A (đủ tên có loại):
  ngoài L1: N (TOK1 L2 · TOK2 L2 · TOK3 L3 · ...)

Format B (chỉ đếm theo loại):
  ngoài L1: N (n_L2 L2 · n_L3 L3 · n_BLIND blind)

Không wire · chỉ đo · in tg_len utf16-u mỗi đêm.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

from b_state_tracker import build_b_state, L2L3_AUDIT, L1_DACC_MAX, L1_DPOS_MAX_ABS
from lib.tg_len import tg_len

print(f"L1 config: Δacc ≤ {L1_DACC_MAX*100:+.0f}% ∧ |Δpos| ≤ {L1_DPOS_MAX_ABS*100:.0f}%")
print()
print(f"{'target':12s} | {'n_out':>5s} | {'formA_len':>9s} | {'formB_len':>9s} | Δ (A-B)")
print(f"{'-'*12} | {'-'*5} | {'-'*9} | {'-'*9} | {'-'*7}")

if L2L3_AUDIT.exists(): L2L3_AUDIT.unlink()

for tgt in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20"]:
    build_b_state(tgt)   # populate audit file
    entries = []
    if L2L3_AUDIT.exists():
        for line in L2L3_AUDIT.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("target") == tgt: entries.append(e)
            except Exception: pass  # L-66-OK (audit parse benign)

    n = len(entries)
    # Classify by dacc/dpos (approx L2 vs L3 based on how far from L1 thresholds)
    n_l2 = n_l3 = n_blind = 0
    tok_labels = []
    for e in entries:
        tok = e.get("token", "?")
        dacc = e.get("dacc_bwd")
        dpos = e.get("dpos_bwd")
        if dacc is None or dpos is None:
            n_blind += 1
            tok_labels.append(f"{tok} BLIND")
        elif dacc <= -0.10 and abs(dpos) <= 0.15:
            n_l2 += 1
            tok_labels.append(f"{tok} L2")
        else:
            n_l3 += 1
            tok_labels.append(f"{tok} L3")

    formA = f"ngoài L1: {n} (" + " · ".join(tok_labels) + ")"
    formB = f"ngoài L1: {n} ({n_l2} L2 · {n_l3} L3 · {n_blind} blind)"
    lenA = tg_len(formA); lenB = tg_len(formB)
    print(f"{tgt:12s} | {n:>5d} | {lenA:>9d} | {lenB:>9d} | {lenA-lenB:>+7d}")

    if L2L3_AUDIT.exists(): L2L3_AUDIT.unlink()
