"""AR3 · bảng ngân sách THEO KHỐI · 09-17 + 09-18 (nặng nhất).

Mỗi khối: n_lines · tg_len · %pre_cap. Không đề xuất cắt · chỉ số.
"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import digest_summary_v2 as dsv
from lib.tg_len import tg_len

# Block markers: pattern → label
BLOCKS = [
    (r"^━━ FRESHWATCH TỔNG", "khung tin"),
    (r"^⛔", "⛔ tripwire"),
    (r"^── UNHEDGE", "UNHEDGE"),
    (r"^🎯 hôm nay:", "🎯 focus"),
    (r"^\[loài =", "loài header"),
    (r"^\[B\] = U1", "prefix explain"),
    (r"^── A · GHẾ BẬT", "A · GHẾ BẬT"),
    (r"^── B ──", "B (khối)"),
    (r"^── C ·", "C"),
    (r"^── D ", "D · loài"),
    (r"^── E ", "E · loài"),
    (r"^── \? ", "? loài"),
    (r"^── CHƯA XẾP LOÀI", "CHƯA XẾP LOÀI"),
    (r"^🔻 XẢ-WATCH", "🔻 XẢ-WATCH"),
    (r"^POST-DUMP", "POST-DUMP"),
    (r"^\[DẢI-NỢ", "DẢI-NỢ"),
    (r"^\[DAO-DEFERRED", "DAO-DEFERRED"),
    (r"^📒 SỔ THƯỜNG", "📒 SỔ THƯỜNG"),
    (r"^🚪 RỜI-SỔ", "🚪 RỜI-SỔ"),
    (r"^GOM-H \d+ reo", "NHỊP-KÊNH pointer"),
    (r"^━━ footer", "footer"),
]

_orig_cap = dsv._v1_3_apply_3tier_cap

for tgt in ["2026-09-17", "2026-09-18"]:
    try:
        dsv._v1_3_apply_3tier_cap = lambda b, budget=3680: b
        body = dsv.build_v2_digest(tgt)
    finally:
        dsv._v1_3_apply_3tier_cap = _orig_cap

    total_len = tg_len(body)
    lines = body.split("\n")
    n_lines = len(lines)

    # Find block starts
    block_starts = []
    for i, l in enumerate(lines):
        for pat, label in BLOCKS:
            if re.match(pat, l):
                block_starts.append((i, label))
                break

    # Compute block sizes
    print(f"═══ target={tgt} · pre-cap total={total_len} · n_lines={n_lines} ═══")
    print(f"{'block':30s} | {'n_lines':>7s} | {'tg_len':>6s} | %")
    print(f"{'-'*30} | {'-'*7} | {'-'*6} | {'-'*4}")

    accounted = 0
    for i, (start, label) in enumerate(block_starts):
        end = block_starts[i+1][0] if i+1 < len(block_starts) else n_lines
        block_text = "\n".join(lines[start:end])
        block_len = tg_len(block_text)
        block_nl = end - start
        pct = 100.0 * block_len / total_len
        print(f"{label:30s} | {block_nl:>7d} | {block_len:>6d} | {pct:.1f}%")
        accounted += block_len

    unaccounted = total_len - accounted
    print(f"{'(unaccounted · gap/blank)':30s} |         | {unaccounted:>6d} | {100*unaccounted/total_len:.1f}%")
    print()
