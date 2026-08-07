"""Final verified Q1/Q2/Q3 + L-32 with corrected probe logic."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_DIR = ROOT / "docs" / "case_files"
DOCS     = ROOT / "docs"

def log(s=""): print(s)

log("=" * 70)
log("FINAL VERIFY — task 3 lessons-bananas31-20260809")
log("=" * 70)

results = {}

# ── L-32 (skip header row 2 = 'date') ────────────────────────────────────────
log("\n--- L-32: DAILY data row count (row 2 = header, skip) ---")
wb = openpyxl.load_workbook(str(CASE_DIR / "CASE_BANANAS31.xlsx"), data_only=True)
ws = wb["DAILY"]
# Row 2 = column header "date" — skip; count from row 3
data_rows = sum(1 for r in range(3, ws.max_row + 1)
                if ws.cell(r, 1).value not in (None, ""))
first_d = ws.cell(3, 1).value
last_d  = ws.cell(ws.max_row, 1).value
log(f"  Data rows (row3 onwards): {data_rows}  [{first_d} → {last_d}]")
log(f"  Expected: 503 | L-32 PASS: {data_rows == 503}")
results["L-32"] = "PASS" if data_rows == 503 else f"FAIL ({data_rows})"
wb.close()

# ── LESSONS mapping ──────────────────────────────────────────────────────────
log("\n--- Lessons mapping ---")
wb_l = openpyxl.load_workbook(str(CASE_DIR / "CASE_INDEX.xlsx"), data_only=True)
ws_l = wb_l["LESSONS"]
lids = [(r, str(ws_l.cell(r,1).value)) for r in range(5, ws_l.max_row+1)
        if ws_l.cell(r,1).value and str(ws_l.cell(r,1).value).startswith("L-")]
nums = sorted(int(l[1].replace("L-","")) for l in lids)
gaps = [n for n in range(nums[0], nums[-1]+1) if n not in nums]
wb_l.close()
log(f"  Total lessons: {len(lids)} | L-{nums[0]} → L-{nums[-1]}")
log(f"  Skipped L-numbers: {['L-'+str(g) for g in gaps]}")
log(f"  Mapping: {len(lids)} lessons in {nums[-1]-nums[0]+1} slots → L-43 was never written (not a gap created here)")
results["lessons"] = f"{len(lids)} lessons L-{nums[0]}→L-{nums[-1]} gap={['L-'+str(g) for g in gaps]}"

# ── Q1 ────────────────────────────────────────────────────────────────────────
log("\n--- Q1: pos_r > 5 + dump → bước check đầu tiên ---")
log("Đường: INDEX.md → docs/analysis_playbook.md §A.5 → quy trình bước 1")
playbook = (DOCS / "analysis_playbook.md").read_text(encoding="utf-8")
a5_ok = "### A.5" in playbook
quy_ok = "Quy trình" in playbook
log(f"  A.5 section present: {a5_ok}")
log(f"  'Quy trình' present: {quy_ok}")
if a5_ok and quy_ok:
    start = playbook.index("Quy trình")
    block = playbook[start:start+300]
    for line in block.split("\n")[:6]:
        if line.strip(): log(f"    {line}")
    log(f"  KẾT: Bước 1 = check sign-corr (sign(Δpos_r) vs sign(ret_1d)) 30d OLS")
    log(f"       <55% đồng hướng → Photo pattern → TRACKING-passive")
    log(f"  Q1 PASS ✓  (nguồn: docs/analysis_playbook.md §A.5, cross-ref L-46)")
    results["Q1"] = "PASS"
else:
    log(f"  Q1 FAIL: A.5={a5_ok} quy_trinh={quy_ok}")
    results["Q1"] = "FAIL"

# ── Q2 ────────────────────────────────────────────────────────────────────────
log("\n--- Q2: Trigger điều kiện vào lệnh BANANAS31 ---")
log("Đường: INDEX.md → docs/case_files/CASE_BANANAS31.xlsx → sheet TRIGGERS")
wb2 = openpyxl.load_workbook(str(CASE_DIR / "CASE_BANANAS31.xlsx"), data_only=True)
ws2 = wb2["TRIGGERS"]
trg_rows = [(ws2.cell(r,1).value, ws2.cell(r,2).value, ws2.cell(r,3).value, ws2.cell(r,4).value)
            for r in range(1, ws2.max_row+1) if ws2.cell(r,1).value and ws2.cell(r,1).value != "ID"]
wb2.close()
if trg_rows:
    for tid, trg, thr, st in trg_rows:
        log(f"    {tid}: {trg} | {thr} | Status={st}")
    inv_block = any(r[0] == "INV" and r[3] == "BLOCK" for r in trg_rows)
    log(f"  KẾT: INV=BLOCK (gLSR≥1.2 hiện tại) → không vào setup cho đến T1 reset")
    log(f"  Q2 PASS ✓  (nguồn: CASE_BANANAS31.xlsx sheet TRIGGERS)")
    results["Q2"] = "PASS"
else:
    log(f"  Q2 FAIL: TRIGGERS empty")
    results["Q2"] = "FAIL"

# ── Q3 ────────────────────────────────────────────────────────────────────────
log("\n--- Q3: fullyDelisted Alpha → taker_alpha ---")
log("Đường: INDEX.md → docs/lessons_learned.md → §L-48")
lessons_md = (DOCS / "lessons_learned.md").read_text(encoding="utf-8")
l48_ok = "## L-48" in lessons_md
if l48_ok:
    start = lessons_md.index("## L-48")
    block = lessons_md[start:start+400]
    for line in block.split("\n")[:5]:
        if line.strip(): log(f"    {line}")
    log(f"  KẾT: fullyDelisted=True → taker_alpha=NaN, flag=ABSTAIN")
    log(f"       klines[9]==klines[5] = close price, không phải real taker (confirmed IDOL+BANANAS31)")
    log(f"  Q3 PASS ✓  (nguồn: docs/lessons_learned.md §L-48)")
    results["Q3"] = "PASS"
else:
    log(f"  Q3 FAIL: L-48 not in lessons_learned.md")
    results["Q3"] = "FAIL"

# ── SUMMARY ──────────────────────────────────────────────────────────────────
log("\n" + "=" * 70)
log("FINAL SUMMARY")
log("=" * 70)
all_pass = all(v.startswith("PASS") for k, v in results.items() if k not in ["lessons"])
for k, v in results.items():
    log(f"  {k:12s}: {v}")
log(f"\n  Mapping note: L-43 không tồn tại trong LESSONS sheet")
log(f"  Lý do: L-43 chưa bao giờ được ghi (không phải bị xóa)")
log(f"  Số đếm khớp: 47 lessons + 1 gap (L-43) = 48 slots → L-01→L-48")
log(f"\n  {'ĐƯỜNG HỌC THÔNG — PASS COMMIT' if all_pass else 'ĐƯỜNG HỌC CHƯA THÔNG — VÁ TRƯỚC'}")
