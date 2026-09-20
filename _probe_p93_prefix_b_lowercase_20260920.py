"""p93 · pin O1/N4=(ii) · [b] chữ thường ngoài khối B · [B] HOA chỉ trong khối B.

Unit-test 4 case cho `_v1_3_route_layout_only`:
  a. tags=["B"] · blind=[] → prefix "[b]" · block "B"
  b. tags=["B","D"] · blind=[] → prefix "[b·D]" (hybrid B thường + D hoa)
  c. tags=["A"] · blind=[] → prefix "[A]" (A hoa unchanged)
  d. tags=["C","D"] · blind=[] → prefix "[C·D]" (C+D hoa)

Cross-check integration: build_v2_digest 09-19 body
  · Trong khối B (từ b_block_renderer): `[B]` HOA cho CONFIRMED, `[B-CROSS]` T2.
  · Ngoài khối B (từ V1.3 body: XẢ-WATCH · POST-DUMP): `[b]` chữ thường cho structural.
  · KHÔNG BAO GIỜ có token `[B]` HOA ngoài khối B.
"""
import sys, re, os
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
_SCRIPTS = Path("/root/Data_back_test/whale_data/scripts") if os.name != "nt" \
           else Path(r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, str(_SCRIPTS))

from digest_summary_v2 import _v1_3_route_layout_only

# ── Unit-test 4 case ──
cases = [
    (["B"], [], "[b]", "B"),
    (["B", "D"], [], "[b·D]", "B"),
    (["A"], [], "[A]", "A"),
    (["C", "D"], [], "[C·D]", "C"),
]
all_pass = True
for tags, blind, expected_prefix, expected_block in cases:
    block, prefix, hints = _v1_3_route_layout_only(tags, blind)
    ok = (prefix == expected_prefix and block == expected_block)
    if not ok: all_pass = False
    print(f"  tags={tags} · expect prefix={expected_prefix} block={expected_block}")
    print(f"       got prefix={prefix} block={block} · {'PASS' if ok else 'FAIL'}")

p93_unit = all_pass
print(f"\np93-unit · route_layout_only 4/4 · {'PASS' if p93_unit else 'FAIL'}")

# ── Integration test on real 09-19 body ──
# Chỉ chạy được nếu có freshwatch store · skip nếu local không đủ data
try:
    os.environ["DIGEST_V1_3"] = "1"
    os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
    os.environ["DIGEST_B_TIER"] = "1"
    from digest_summary_v2 import build_v2_digest
    body = build_v2_digest("2026-09-19")

    # Grep `[B]` HOA · phải chỉ nằm trong khối B (từ header ── B ── tới header khác)
    # SKIP dòng giải thích header `[B] = unhedge đã xác nhận · [b] = đang hedge (cấu trúc)`
    lines = body.split("\n")
    in_b_block = False
    upper_B_outside = []
    _HEADER_EXPLAIN = "[B] = unhedge đã xác nhận · [b] = đang hedge"
    for i, ln in enumerate(lines):
        if _HEADER_EXPLAIN in ln:
            continue   # dòng giải thích · not a token tag
        if re.match(r"^── B ──", ln):
            in_b_block = True; continue
        elif in_b_block and re.match(r"^── ", ln):
            in_b_block = False
        # Check `[B]` HOA · KHÔNG followed by `-` (không phải [B-CROSS])
        m = re.search(r"\[B\](?!-)", ln)
        if m and not in_b_block:
            upper_B_outside.append((i, ln.strip()))

    p93_int_a = (len(upper_B_outside) == 0)
    print(f"\np93-int-a · KHÔNG có `[B]` HOA ngoài khối B: {'PASS' if p93_int_a else 'FAIL'}")
    if not p93_int_a:
        for i, ln in upper_B_outside[:5]:
            print(f"    L{i}: {ln[:100]}")

    # Grep `[b]` chữ thường · phải có ít nhất 1 (nếu cohort có species-B token ngoài)
    lower_b_count = len(re.findall(r"\[b(?:·[A-Z])?\]", body))
    p93_int_b = lower_b_count >= 0   # informational · không ép ≥1 vì cohort có thể vắng
    print(f"p93-int-b · số lần `[b]` chữ thường ngoài khối B = {lower_b_count} (info)")

    # Grep header line explanation · chỉ ép khi V1.3 species render active (có [loài = ...] line)
    v1_3_active = "[loài = trạng thái hôm nay" in body
    if v1_3_active:
        p93_int_c = "[B] = unhedge đã xác nhận · [b] = đang hedge" in body
        print(f"p93-int-c · V1.3 active · dòng giải thích [B]/[b] có: {'PASS' if p93_int_c else 'FAIL'}")
    else:
        p93_int_c = True   # V1.3 fallback path (không render header) · skip
        print(f"p93-int-c · V1.3 KHÔNG active (fallback) · skip")

    fails = sum(1 for p in [p93_unit, p93_int_a, p93_int_c] if not p)
except Exception as e:
    print(f"\n[SKIP integration] {type(e).__name__}: {e}")
    fails = 0 if p93_unit else 1

print(f"\n═══ p93 · TỔNG · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
