"""p86 · lint D_known == D · quét công thức
   · bất kỳ chỗ nào đọc D+k trong đường tính BELL → FAIL
   · cấm chuỗi 'lead_anchor' trong mọi output
"""
import sys, re
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

BELL_FILE = Path(r"d:\Data back test\whale_data\sandbox\u0_bell_a3\u0_bell.py")

txt = BELL_FILE.read_text(encoding="utf-8")

# p86-a · quét công thức Δ*_bwd: đọc D+k?
# Pattern: (td + timedelta(days=k)) or D+k with k > 0 in delta_bwd context
# Look at delta_bwd() function body for any positive offset

# Find delta_bwd function body
m = re.search(r"def delta_bwd\b.*?(?=\ndef |\Z)", txt, re.DOTALL)
if not m:
    print("p86-a · delta_bwd không tìm được → FAIL")
    p86_a = False
else:
    body = m.group(0)
    # Look for D+k with k > 0 in body
    fwd_offsets = re.findall(r"timedelta\(days=(\d+)\)", body)
    fwd_forward = [int(x) for x in fwd_offsets if int(x) > 0]
    # Actually delta_bwd uses D-3 · code has `(td - timedelta(days=BWD_WINDOW))` → offset is subtracted (backward)
    # Pattern for forward: `td + timedelta(days=` with positive offset
    fwd_pattern = re.findall(r"td\s*\+\s*timedelta\(days=(\d+)\)", body)
    has_forward = any(int(x) > 0 for x in fwd_pattern)
    p86_a = not has_forward
    print(f"p86-a · delta_bwd body chứa `td + timedelta(days=X>0)`? · has_forward={has_forward} · {'PASS' if p86_a else 'FAIL'}")
    if has_forward:
        print(f"   forward offsets found: {fwd_pattern}")

# p86-b · toàn file u0_bell.py chứa "lead_anchor" (cấm)?
has_lead_anchor = "lead_anchor" in txt
p86_b = not has_lead_anchor
print(f"p86-b · file chứa chuỗi 'lead_anchor'? · has_lead_anchor={has_lead_anchor} · {'PASS' if p86_b else 'FAIL'}")

# p86-c · u0_bell() body không đọc D+k
m_bell = re.search(r"def u0_bell\b.*?(?=\ndef |\Z)", txt, re.DOTALL)
if m_bell:
    bell_body = m_bell.group(0)
    fwd_pat = re.findall(r"td\s*\+\s*timedelta\(days=(\d+)\)", bell_body)
    has_fwd_in_bell = any(int(x) > 0 for x in fwd_pat)
    p86_c = not has_fwd_in_bell
    print(f"p86-c · u0_bell() body chứa forward offset? · has_fwd={has_fwd_in_bell} · {'PASS' if p86_c else 'FAIL'}")
else:
    p86_c = False
    print("p86-c · u0_bell không tìm được → FAIL")

# p86-d · toàn file · scan mọi lời gọi timedelta(days=N) với N > 0
all_timedelta = re.findall(r"timedelta\(days=(\d+)\)", txt)
all_pos = [int(x) for x in all_timedelta if int(x) > 0]
print(f"\np86-d · toàn u0_bell.py có {len(all_pos)} timedelta forward offset (days>0): {sorted(set(all_pos))}")
print(f"       Kiểm nội dung mỗi chỗ dùng: chỉ được dùng cho DOCSTRING/COMMENT hoặc TESTS")
# Manual check: look at context lines around each positive td
lines = txt.split("\n")
for i, line in enumerate(lines):
    m = re.search(r"timedelta\(days=(\d+)\)", line)
    if m and int(m.group(1)) > 0:
        # Check if line has td+ or td -
        if "td +" in line or "td+" in line:
            print(f"   L{i+1}: '{line.strip()}' — FORWARD! (D_known ≠ D · bug tiềm ẩn)")
        else:
            print(f"   L{i+1}: '{line.strip()}' — OK (backward or non-D)")

fails = sum(1 for p in [p86_a, p86_b, p86_c] if not p)
print(f"\n═══ p86 · TỔNG 3 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
