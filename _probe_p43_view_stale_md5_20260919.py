"""p43 · pin L3 · view_stale_check dùng MD5, KHÔNG dùng AGE.

3 sub-cases:
  a. md5 khớp (dù age = 100 ngày) → IM (return "")
  b. md5 lệch → kêu "[VIEW-STALE · nguồn đã đổi, map chưa regen]"
  c. sidecar thiếu → kêu "[VIEW-STALE · không kiểm được nguồn]" (fail-closed)

Import prod trực tiếp — không tự cài compose.
"""
import sys, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

from lib.view_stale_check import check_view_stale

FAKE_MD5_A = "0123456789abcdef0123456789abcdef"   # md5 xưa của nguồn
FAKE_MD5_B = "fedcba9876543210fedcba9876543210"   # md5 mới của nguồn (khác A)

tmp = Path(tempfile.mkdtemp(prefix="p43_"))
view_p = tmp / "case_state_map.md"
sidecar_p = tmp / "case_index_source.md5"

def make_view(source_md5, generated_at):
    view_p.write_text(f"""# case_state_map — VIEW
<!-- source_md5: {source_md5} -->
<!-- generated_at: {generated_at} -->

| token | state | ... |
| TST | COLD_START | ... |
""", encoding="utf-8")


# ── p43-a · md5 khớp · age = 100 ngày · IM ──
make_view(FAKE_MD5_A, "2026-06-11T01:00:00+00:00")
sidecar_p.write_text(FAKE_MD5_A + "\n", encoding="utf-8")

result_a = check_view_stale(view_path=view_p, source_md5_path=sidecar_p)
p43_a = (result_a == "")
print(f"p43-a · md5 khớp (view={FAKE_MD5_A[:8]} sidecar={FAKE_MD5_A[:8]}) · age=100d")
print(f"        result='{result_a}'")
print(f"        → {'PASS' if p43_a else 'FAIL'} · doctrine: view đúng thì 100d tuổi vẫn đúng\n")


# ── p43-b · md5 lệch · KÊU ──
sidecar_p.write_text(FAKE_MD5_B + "\n", encoding="utf-8")   # nguồn đã đổi

result_b = check_view_stale(view_path=view_p, source_md5_path=sidecar_p)
p43_b = ("VIEW-STALE" in result_b and "nguồn đã đổi" in result_b
         and FAKE_MD5_A[:8] in result_b and FAKE_MD5_B[:8] in result_b)
print(f"p43-b · md5 lệch (view={FAKE_MD5_A[:8]} sidecar={FAKE_MD5_B[:8]})")
print(f"        result='{result_b}'")
print(f"        → {'PASS' if p43_b else 'FAIL'} · phải kêu 'nguồn đã đổi, map chưa regen'\n")


# ── p43-c · sidecar THIẾU · KÊU (fail-closed) ──
sidecar_p.unlink()

result_c = check_view_stale(view_path=view_p, source_md5_path=sidecar_p)
p43_c = ("VIEW-STALE" in result_c and "không kiểm được nguồn" in result_c
         and "sidecar thiếu" in result_c)
print(f"p43-c · sidecar THIẾU · fail-closed")
print(f"        result='{result_c}'")
print(f"        → {'PASS' if p43_c else 'FAIL'} · phải kêu 'không kiểm được nguồn' KHÁC HẲN case b\n")


# Cross-check: 3 message KHÁC NHAU
distinct = len({result_a, result_b, result_c}) == 3
print(f"═══ cross-check: 3 message distinct = {distinct} (a='', b='nguồn đổi', c='không kiểm được') ═══")

fails = sum(1 for p in [p43_a, p43_b, p43_c] if not p)
print(f"═══ p43 · TỔNG 3 sub-cases · {fails} FAIL ═══")
sys.exit(0 if (fails == 0 and distinct) else 1)
