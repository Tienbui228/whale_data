"""p91 · pin M4 · lint tham chiếu `(→ xem X)` phải có dòng đích trong khối X.

3 sub-cases:
  a. body có ref `(→ xem GOM-H)` + dòng đích `[GOM-H]` → PASS (no orphan)
  b. xoá dòng đích → FAIL (orphan detected)
  c. body không có ref nào → PASS trivially

Import prod: b_block_renderer.lint_b_references
"""
import sys
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

from b_block_renderer import lint_b_references

# ── p91-a · ref có đích [GOM-H] → PASS ──
body_a = """━━ HEADER
Line one
[B] TOK1 +2d
Some text (→ xem GOM-H) và (→ xem HEDGE) references.
── GOM-H ──
GOM-H detail line
── HEDGE ──
HEDGE detail line
"""
# Wait: lint checks for `[GOM-H]` or `GOM-H:` or `── GOM-H ──`
# Body has `── GOM-H ──` and `── HEDGE ──` → both targets present
orphans_a = lint_b_references(body_a)
p91_a = (orphans_a == [])
print(f"p91-a · 2 refs (GOM-H, HEDGE) · targets có · orphans={orphans_a}")
print(f"        → {'PASS' if p91_a else 'FAIL'}\n")

# ── p91-b · xoá đích HEDGE → orphan ──
body_b = """━━ HEADER
Line one
Some text (→ xem GOM-H) và (→ xem HEDGE) references.
── GOM-H ──
GOM-H detail line
"""
# HEDGE ref có, đích không → orphan
orphans_b = lint_b_references(body_b)
p91_b = (orphans_b == ["HEDGE"])
print(f"p91-b · 2 refs · HEDGE đích xoá · orphans={orphans_b}")
print(f"        → {'PASS' if p91_b else 'FAIL'}\n")

# ── p91-c · body không ref nào → PASS trivially ──
body_c = """━━ HEADER
[B] TOK +3d
── FAILED: 5 (X 15/09 · Y 14/09 · Z 12/09)
"""
orphans_c = lint_b_references(body_c)
p91_c = (orphans_c == [])
print(f"p91-c · 0 refs · orphans={orphans_c}")
print(f"        → {'PASS' if p91_c else 'FAIL'}\n")

fails = sum(1 for p in [p91_a, p91_b, p91_c] if not p)
print(f"═══ p91 · TỔNG 3 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
