"""AR1+AR2 · đo CHƯA XẾP format ĐÃ KÝ (E4(iii)-1) · cờ giữ nguyên · 6 đêm.

Định dạng mới: mỗi token 1 dòng `TOK cờ direction`.
Cờ ⏸/[?]/[ĐỘNG-CƠ:KHÓA]/✦ giữ (p109 luật nén-không-nuốt-cờ).

Đo:
  · tg_len khối CHƯA XẾP hiện tại (2-3 dòng full + tail)
  · tg_len khối CHƯA XẾP mới (mỗi token 1 dòng gọn)
  · Δ per night
  · AR2: cộng Δ + Δ_B (AQ1) vào pre_now → p108 6 đêm
"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import digest_summary_v2 as dsv
from lib.tg_len import tg_len

def _extract_chua_xep_block(body: str) -> tuple:
    """Trả (block_text, list of token lines) khối CHƯA XẾP LOÀI."""
    lines = body.split("\n")
    start = None; end = None
    for i, l in enumerate(lines):
        if l.startswith("── CHƯA XẾP LOÀI ──"):
            start = i
        elif start is not None and (l.startswith("── ") and i > start) or (start is not None and l.startswith("🔻") and i > start):
            end = i; break
    if start is None: return ("", [])
    if end is None: end = len(lines)
    block_lines = lines[start:end]
    return ("\n".join(block_lines), block_lines)


def _new_format_chua_xep(block_lines: list) -> str:
    """Chuyển thành format E4(iii)-1: mỗi token `TOK cờ direction`.

    Đọc từ 2-3 dòng full + tail `(+n nữa: A·B·C)`.
    Giả sử direction lấy được từ dòng full (VD `→ PRE`).
    Cờ ⏸/[?] parse từ prefix line.
    Tail names KHÔNG có direction · nên gán `?` (dữ liệu source mất).
    """
    header = block_lines[0]   # `── CHƯA XẾP LOÀI ── (N)`
    m_n = re.search(r"\((\d+)\)", header)
    n_tot = int(m_n.group(1)) if m_n else 0
    new_lines = [f"── CHƯA XẾP LOÀI ── ({n_tot})"]

    # Parse full lines: `   TOK N-trục (...) ... → PRE [NEW]`
    for l in block_lines[1:]:
        s = l.strip()
        if not s: continue
        # Tail overflow
        m_ov = re.match(r"\(\+(\d+)\s+nữa:\s+([^)]+)\)", s)
        if m_ov:
            names = [n.strip() for n in m_ov.group(2).split("·")]
            for n in names:
                # Không có direction từ tail · dùng `?`
                new_lines.append(f"   {n} ?")
            continue
        # Full token line: extract TOK + flags + direction
        # Match ⏸ or [?] or [ĐỘNG-CƠ:KHÓA] or ✦ optional prefix
        m_full = re.match(r"^([⏸✦]?)(\[\?\]|\[ĐỘNG-CƠ:KHÓA\])?\s*(\S+)\s.*→\s*(\S+)", s)
        if m_full:
            flag1 = m_full.group(1)
            flag2 = m_full.group(2) or ""
            tok = m_full.group(3)
            direction = m_full.group(4)
            flag = f"{flag1}{flag2}"
            new_lines.append(f"   {flag}{tok} {direction}")
        else:
            # fallback: keep truncated
            m_tok = re.match(r"^\s*(\S+)", l)
            if m_tok:
                new_lines.append(f"   {m_tok.group(1)} ?")

    return "\n".join(new_lines)


# ── Get AQ1 est (B rút) per night ──
from b_state_tracker import build_b_state
from b_block_renderer import render_b_block

_orig_cap = dsv._v1_3_apply_3tier_cap

print(f"AR1+AR2 · đo CHƯA XẾP format mới + tổng với AQ1 Δ_B · 6 đêm")
print()
print(f"{'target':12s} | {'pre_now':>7s} | {'CX_now':>6s} | {'CX_new':>6s} | {'ΔCX':>4s} | "
      f"{'Δ_B':>4s} | {'est_new':>7s} | p108")
print(f"{'-'*12} | {'-'*7} | {'-'*6} | {'-'*6} | {'-'*4} | {'-'*4} | {'-'*7} | {'-'*4}")

for tgt in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20"]:
    try:
        dsv._v1_3_apply_3tier_cap = lambda b, budget=3680: b
        body = dsv.build_v2_digest(tgt)
    finally:
        dsv._v1_3_apply_3tier_cap = _orig_cap

    pre_now = tg_len(body)
    cx_text, cx_lines = _extract_chua_xep_block(body)
    cx_now = tg_len(cx_text)
    cx_new_text = _new_format_chua_xep(cx_lines) if cx_lines else ""
    cx_new = tg_len(cx_new_text)
    d_cx = cx_new - cx_now

    # AQ1 Δ_B (B_reduced - B_current)
    state = build_b_state(tgt)
    b_now = tg_len(render_b_block(tgt))
    conf = [(t, s) for t, s in state.items() if s.get("tier") == "CONFIRMED"]
    cross = [(t, s) for t, s in state.items() if s.get("tier") == "CROSS"]
    n_cand = sum(1 for s in state.values() if s.get("tier") == "cand")
    n_fail = sum(1 for s in state.values() if s.get("tier") == "FAILED")
    n_stale = sum(1 for s in state.values() if s.get("tier") == "STALE")
    b_new_lines = [f"── B ── ({len(conf)+len(cross)} · {len(conf)} CONFIRMED · {len(cross)} CROSS L1) [CAL-ONLY]"]
    for tok, s in conf: b_new_lines.append(f"[B] {tok} +{s['d_plus_k']}d")
    for tok, s in cross: b_new_lines.append(f"[B-CROSS] {tok} · L1 · D+{s['d_plus_k']}")
    b_new_lines.append(f"── (khối HEDGE v2 giữ: {n_cand} cand · {n_fail} FAILED · {n_stale} STALE · +ngoài L1)")
    b_new = tg_len("\n".join(b_new_lines))
    d_b = b_new - b_now

    est_new = pre_now + d_cx + d_b
    p108 = "PASS" if est_new <= 4096 else "FAIL"

    print(f"{tgt:12s} | {pre_now:>7d} | {cx_now:>6d} | {cx_new:>6d} | {d_cx:>+4d} | "
          f"{d_b:>+4d} | {est_new:>7d} | {p108}")
