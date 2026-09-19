"""p88 · header hold-out · holdout=20260920-20261020 · cells=4 · added=0

Đen-một-lần cho header holdout · verify string format khớp exact.

Format spec (A3-5 p88): `holdout=YYYYMMDD-YYYYMMDD · cells=N · added=M`
  cells = số ô đã đăng ký TRƯỚC (từ AO grid = 4 ngưỡng)
  added = số ô THÊM SAU KHI THẤY KẾT QUẢ (phải = 0)
"""
import sys, re
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

def render_holdout_header(start_date, end_date, cells_registered, cells_added):
    """Trả string header holdout đúng format."""
    s = start_date.replace("-", "")
    e = end_date.replace("-", "")
    return f"holdout={s}-{e} · cells={cells_registered} · added={cells_added}"

# p88-a · Basic render
header = render_holdout_header("2026-09-20", "2026-10-20", 4, 0)
expected = "holdout=20260920-20261020 · cells=4 · added=0"
p88_a = header == expected
print(f"p88-a · header khớp expected · got='{header}' · expect='{expected}' · {'PASS' if p88_a else 'FAIL'}")

# p88-b · Regex parse
pat = re.compile(r"holdout=(\d{8})-(\d{8}) · cells=(\d+) · added=(\d+)")
m = pat.match(header)
p88_b = m is not None
print(f"p88-b · regex parse · {'PASS' if p88_b else 'FAIL'}")
if m:
    print(f"  start={m.group(1)} · end={m.group(2)} · cells={m.group(3)} · added={m.group(4)}")

# p88-c · Invariant: added must be 0 in pre-reg phase
p88_c = int(m.group(4)) == 0 if m else False
print(f"p88-c · added=0 (pre-reg lock) · {'PASS' if p88_c else 'FAIL'}")

# p88-d · Cells matches AO grid (4 thresholds)
p88_d = int(m.group(3)) == 4 if m else False
print(f"p88-d · cells=4 khớp AO pre-registered grid · {'PASS' if p88_d else 'FAIL'}")

# p88-e · Duration = 30 days holdout window
from datetime import datetime
if m:
    s = datetime.strptime(m.group(1), "%Y%m%d").date()
    e = datetime.strptime(m.group(2), "%Y%m%d").date()
    days = (e - s).days
    p88_e = days == 30
    print(f"p88-e · duration = {days} ngày · expect 30 · {'PASS' if p88_e else 'FAIL'}")
else:
    p88_e = False

fails = sum(1 for p in [p88_a, p88_b, p88_c, p88_d, p88_e] if not p)
print(f"\n═══ p88 · TỔNG 5 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
