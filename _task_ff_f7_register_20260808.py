"""
_task_ff_f7_register_20260808.py
F-7: Fix CASE_FF.xlsx Status → "COLD_START — AUDIT PENDING" +
     Register trong CASE_INDEX.xlsx + INDEX.md.
"""
import sys, io, json, shutil, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-7 REGISTER  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

# ── L-34 Backup ───────────────────────────────────────────────────────────────
log("\n=== L-34 BACKUP ===")
XLSX = CASE_DIR / "CASE_FF.xlsx"
bkp = SCRATCH / f"CASE_FF_bak_{NOW_UTC.strftime('%Y%m%d_%H%M%S')}.xlsx"
shutil.copy2(XLSX, bkp)
log(f"  Backup: {bkp.name}")

# ── Fix CASE_FF.xlsx Status ────────────────────────────────────────────────────
log("\n=== FIX CASE STATUS ===")
wb = openpyxl.load_workbook(str(XLSX))
cs = wb["CASE"]

# Find and fix Status row
for r in range(1, cs.max_row+1):
    k = cs.cell(r,1).value
    if k and "Status" in str(k):
        old_v = cs.cell(r,2).value
        cs.cell(r,2).value = "COLD_START — AUDIT PENDING"
        log(f"  Status: '{old_v}' → 'COLD_START — AUDIT PENDING' (row {r})")
        break

# Also fix Verdict = blank (should already be)
for r in range(1, cs.max_row+1):
    k = cs.cell(r,1).value
    if k and "Verdict" in str(k):
        cs.cell(r,2).value = None
        log(f"  Verdict: set to blank (row {r})")
        break

# Fix Câu hỏi mở (Vietnamese proper)
for r in range(1, cs.max_row+1):
    k = cs.cell(r,1).value
    if k and ("Cau hoi" in str(k) or "câu hỏi" in str(k).lower() or "Cau" in str(k)):
        cs.cell(r,2).value = ("Bot báo gom ~$2M trên perp — số này tái lập được không, "
                               "bằng công thức nào, và có đứng vững qua ba phương pháp §3 độc lập không?")
        log(f"  Câu hỏi mở: updated (row {r})")
        break

wb.save(str(XLSX))
wb.close()
log(f"  Saved: {XLSX.name}")

# ── Register trong CASE_INDEX.xlsx ────────────────────────────────────────────
log("\n=== CASE_INDEX.xlsx REGISTER ===")
INDEX_XL = CASE_DIR / "CASE_INDEX.xlsx"
if INDEX_XL.exists():
    wb_idx = openpyxl.load_workbook(str(INDEX_XL))
    # Find the main sheet (likely first or named "INDEX")
    ws_idx = wb_idx.active
    max_r = ws_idx.max_row

    # Check if FF already registered
    ff_row = None
    for r in range(1, max_r+1):
        v = ws_idx.cell(r,1).value
        if v and "FF" in str(v).upper() and "FFUSDT" in str(v).upper():
            ff_row = r
            break

    if ff_row:
        log(f"  FF already in CASE_INDEX at row {ff_row}")
    else:
        # Append new row
        next_r = max_r + 1
        ws_idx.cell(next_r, 1).value = "FFUSDT"
        ws_idx.cell(next_r, 2).value = "FF"
        ws_idx.cell(next_r, 3).value = "COLD_START — AUDIT PENDING"
        ws_idx.cell(next_r, 4).value = "ALPHA_398"
        ws_idx.cell(next_r, 5).value = "2026-08-08"
        ws_idx.cell(next_r, 6).value = ("Bot báo gom ~$2M trên perp — tái lập số, "
                                          "ba phương pháp §3 độc lập")
        log(f"  Added FF row at row {next_r}")
        # Show what's there
        log(f"  Row: {[ws_idx.cell(next_r,c).value for c in range(1,8)]}")

    # L-34 backup for INDEX
    bkp_idx = SCRATCH / f"CASE_INDEX_bak_{NOW_UTC.strftime('%Y%m%d_%H%M%S')}.xlsx"
    import shutil
    shutil.copy2(str(INDEX_XL), str(bkp_idx))
    wb_idx.save(str(INDEX_XL))
    wb_idx.close()
    log(f"  CASE_INDEX.xlsx saved")
else:
    log("  CASE_INDEX.xlsx not found")

# ── Update INDEX.md ───────────────────────────────────────────────────────────
log("\n=== INDEX.md UPDATE ===")
index_md = ROOT / "INDEX.md"
if index_md.exists():
    content = index_md.read_text(encoding="utf-8", errors="replace")
    if "FFUSDT" in content or "CASE_FF" in content:
        log("  FF already in INDEX.md")
    else:
        # Append FF line after last CASE entry
        ff_line = (f"| FFUSDT | FF | COLD_START — AUDIT PENDING | ALPHA_398 | {NOW_UTC.strftime('%Y-%m-%d')} | "
                   f"Bot ~$2M perp gom audit |\n")
        # Find table and append
        lines = content.splitlines(keepends=True)
        # Insert before last non-empty line that's in the table section
        # Simple append at end
        new_content = content.rstrip() + "\n" + ff_line
        index_md.write_text(new_content, encoding="utf-8")
        log(f"  Added FF row to INDEX.md")
else:
    log("  INDEX.md not found")

log("\n[F-7 DONE]")
