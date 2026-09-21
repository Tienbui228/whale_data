"""p109 · pin AS1 · CHƯA XẾP LOÀI không bao giờ thành đuôi (+n nữa) · cờ giữ đủ.

Rules:
  · Mọi token trong CHƯA XẾP LOÀI phải có DÒNG RIÊNG với format `TOK cờ direction`
  · KHÔNG có dòng (+N nữa: A·B·C) trong khối CHƯA XẾP
  · Cờ ⏸ / [?] / [ĐỘNG-CƠ:KHÓA] / ✦ được giữ · không mất

Đo trên 6 đêm mẫu · body real từ build_v2_digest.
"""
import sys, os, re
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import digest_summary_v2 as dsv

def _extract_chua_xep(body: str) -> tuple:
    """Trả (header, list token lines) của khối CHƯA XẾP LOÀI."""
    lines = body.split("\n")
    start = None; end = None
    for i, l in enumerate(lines):
        if l.startswith("── CHƯA XẾP LOÀI ──"):
            start = i; continue
        if start is not None and (l.startswith("── ") or l.startswith("🔻") or l == ""):
            if i > start: end = i; break
    if start is None: return (None, [])
    if end is None: end = len(lines)
    return (lines[start], lines[start+1:end])


fails = 0
print(f"═══ p109 · CHƯA XẾP no-tail + cờ giữ · 6 đêm ═══")
print(f"{'target':12s} | {'n_header':>8s} | {'n_lines':>7s} | {'match':>5s} | {'tail?':>5s} | flags kept")
print(f"{'-'*12} | {'-'*8} | {'-'*7} | {'-'*5} | {'-'*5} | {'-'*40}")

for tgt in ["2026-09-15","2026-09-16","2026-09-17","2026-09-18","2026-09-19","2026-09-20"]:
    try:
        # No-cap render to see full CHUA_XEP
        _orig_cap = dsv._v1_3_apply_3tier_cap
        try:
            dsv._v1_3_apply_3tier_cap = lambda b, budget=3680: b
            body = dsv.build_v2_digest(tgt)
        finally:
            dsv._v1_3_apply_3tier_cap = _orig_cap
    except Exception as e:
        print(f"{tgt}: ERR {e}"); fails += 1; continue

    header, tok_lines = _extract_chua_xep(body)
    if header is None:
        print(f"{tgt:12s} | no CHUA_XEP block"); continue

    m_n = re.search(r"\((\d+)\)", header)
    n_header = int(m_n.group(1)) if m_n else 0

    # Count real token lines (skip empty)
    real_lines = [l for l in tok_lines if l.strip()]
    n_lines = len(real_lines)

    # p109-a: match count
    match = (n_lines == n_header)

    # p109-b: no tail (+N nữa)
    has_tail = any("(+" in l and "nữa" in l for l in real_lines)

    # p109-c: flags preserved · count lines with flag
    flag_lines = [l for l in real_lines if re.search(r"^\s*(⏸|✦|\[\?\]|\[ĐỘNG-CƠ:KHÓA\])", l)]
    flag_str = ", ".join(re.match(r"^\s*(\S+)", l).group(1) for l in flag_lines[:4]) if flag_lines else "(none)"

    pass_line = match and not has_tail
    if not pass_line: fails += 1

    print(f"{tgt:12s} | {n_header:>8d} | {n_lines:>7d} | {str(match):>5s} | {str(has_tail):>5s} | {flag_str}")

print()
print(f"═══ p109 · TỔNG · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
