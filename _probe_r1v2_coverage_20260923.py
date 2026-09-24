"""R1.v2 · Bảng coverage: mục → dòng trong registration (số dòng). Không sửa file."""
import pathlib, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REG = pathlib.Path("docs/holdout_u0bell_registration_20260923.md")
text = REG.read_text(encoding="utf-8")
lines = text.split("\n")

def _grep(pattern, first_only=False, regex=False):
    """Return list of line numbers (1-based) matching pattern (substring or regex)."""
    out = []
    for i, l in enumerate(lines, 1):
        if regex:
            if re.search(pattern, l):
                out.append(i)
        else:
            if pattern in l:
                out.append(i)
        if first_only and out:
            break
    return out

# Each entry: (label, list of substring patterns or regex, description of match)
CHECKS = [
    ("cửa sổ 21/09→20/10", ["2026-09-21 → 2026-10-20"], "hard-string window"),
    ("09-20 mô tả", ["09-20: **chỉ mô tả**"], "day 09-20 mô tả marker"),
    ("09-21 vào (md5 2f41f23f)", ["2f41f23f8bd306d500695c7bdb449cff"], "V5a canonical md5"),
    ("09-22 vào", ["09-22: **vào cửa sổ**", "ee71db39016cd3424e5b2070ad8547c1", "e668138a7ad8"], "09-22 vào markers"),
    ("ô chính w=3 T=−20%", ["w=3, T=−20%", "w=3 T=−20%"], "Q4 primary cell"),
    ("kết cục cross 0.5 trong 10d", ["div_avg3 vượt 0.5 trong [10] ngày", "div_avg3 vượt 0.5 trong 10 ngày"], "Q1 outcome"),
    ("pass 3 vế", ["Precision ≥ 55%", "Lift ≥ 1.5×", "Nhất quán trên nền lift phân tầng"], "3 điều kiện PASS"),
    ("lift C9 (i) + 3 quy tắc biên", ["P_obs / Σ w_b·base_b", "[0, 0.3) · [0.3, 0.4) · [0.4, 0.5]", "chuông ĐẦU episode", "w=0"], "C9 formula + 3 boundary rules"),
    ("nền loại outage", ["loại outage", "[GAP-0724]"], "C8b outage removed"),
    ("đơn vị episode (R1a)", ["token-episode (gộp 14d)", "R1a"], "episode unit + R1a addendum ref"),
    ("roster theo ngày", ["roster theo ngày, roster_<date>.txt"], "Q3 roster per day"),
    ("file events chuẩn data/artifacts + md5 legacy", ["data/artifacts/events_<T>.jsonl", "29915ce7f6e7f3b10bb9afd7039cfef9"], "events chuẩn + legacy md5"),
    ("chuẩn hoá so sánh (3 type, bỏ computed_at)", ["type ∈ {bell, bell_blind, bell_near}", "drop `computed_at`"], "Section 2 normalization"),
    ("md5 bộ R0 (Section 3)", ["baa8f525a8c03c2d183351f7fe64ba8c", "2a6ab5a578e91e8d2b3483347faf7b59", "b422d88e8898bb02fbaae782ba5b5e51"], "R0 snap md5s"),
    ("roster_daily md5 (bộ R0)", ["7d5ce81904259b295e90dd6f37e305ac"], "roster_daily.py in R0 set"),
    ("2 probe md5 (Section 4)", ["d840135ca65420e6a8322dae57839666", "0ac206841dc711241676bf380f25ef84", "62392a4121c643535ac8f492bea7849a", "2a1a1b010e466b3038574e15bd2fedfc"], "probe md5s (4 listed · ≥2)"),
    ("2 đợt chấm (graded_at · data_through · bell_range)", ["| Đợt 1 |", "| Đợt 2 |", "graded_at", "data_through", "bell_range"], "grading table"),
    ("nguồn rulings c74098082bdf", ["c74098082bdf4d9ad5efb9b8d0bab7a9"], "rulings md5 citation"),
]

print("| # | mục | dòng | trạng |")
print("|--:|-----|------|:---:|")
missing = []
for idx, (label, pats, desc) in enumerate(CHECKS, 1):
    line_nums_per_pat = []
    all_found = True
    for pat in pats:
        nums = _grep(pat)
        line_nums_per_pat.append((pat, nums))
        if not nums:
            all_found = False
    if all_found:
        flat = sorted({n for _p, nums in line_nums_per_pat for n in nums})
        # Show shortest representation
        line_str = ", ".join(f"L{n}" for n in flat[:6])
        if len(flat) > 6:
            line_str += f" (+{len(flat)-6} nữa)"
        print(f"| {idx} | {label} | {line_str} | ✓ |")
    else:
        missing.append((label, pats, line_nums_per_pat))
        # Show what was found + what missing
        found = ", ".join(f"L{n}" for _p, nums in line_nums_per_pat for n in nums)
        missing_pats = [p for p, nums in line_nums_per_pat if not nums]
        print(f"| {idx} | {label} | THIẾU (missing: {missing_pats}) | ✗ |")

if missing:
    print(f"\n=== THIẾU {len(missing)} MỤC ===")
    for label, pats, results in missing:
        print(f"  {label}:")
        for pat, nums in results:
            marker = "✓" if nums else "✗"
            print(f"    {marker} '{pat}': {nums if nums else 'không tìm thấy'}")
else:
    print("\n=== KHÔNG có mục THIẾU ===")
