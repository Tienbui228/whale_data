"""
_task_cookie_c8_register_20260809.py
COOKIE C-8: Register CASE_COOKIE.xlsx in CASE_INDEX + update INDEX.md
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
DATE_TAG = "20260809"
CASE_DIR = ROOT / "docs" / "case_files"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-8 REGISTER  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

try:
    import openpyxl
except ImportError:
    log("ERROR: openpyxl not available")
    sys.exit(1)

# ── Step 1: Verify CASE_COOKIE.xlsx exists ─────────────────────────────────────
case_xlsx = CASE_DIR / "CASE_COOKIE.xlsx"
log(f"\n=== Step 1: Verify CASE_COOKIE.xlsx ===")
if not case_xlsx.exists():
    log(f"  MISSING: {case_xlsx}")
    sys.exit(1)
log(f"  Found: {case_xlsx.name} ({case_xlsx.stat().st_size:,} bytes)")

# ── Step 2: Update CASE sheet Status ──────────────────────────────────────────
log(f"\n=== Step 2: Update CASE_COOKIE.xlsx status ===")
wb_case = openpyxl.load_workbook(str(case_xlsx))
cs = wb_case["CASE"]
# Find Status row and update
for row in cs.iter_rows():
    cell = row[0]
    if cell.value and "Status" in str(cell.value):
        val_cell = row[1]
        old_val = val_cell.value
        val_cell.value = "OPEN — audit-collect complete, awaiting operator verdict"
        log(f"  Status: '{old_val}' → '{val_cell.value}'")
        break

wb_case.save(str(case_xlsx))
log(f"  Saved: {case_xlsx.name}")

# ── Step 3: CASE_INDEX.xlsx — add COOKIE row ──────────────────────────────────
log(f"\n=== Step 3: CASE_INDEX.xlsx — add COOKIE row ===")
idx_path = CASE_DIR / "CASE_INDEX.xlsx"
if not idx_path.exists():
    log(f"  MISSING: {idx_path}")
    sys.exit(1)

wb_idx = openpyxl.load_workbook(str(idx_path))
ws_idx = wb_idx["INDEX"]

# Read headers
headers = [c.value for c in next(ws_idx.iter_rows(min_row=1, max_row=1))]
log(f"  Headers: {headers}")

# Check if COOKIE already exists
cookie_row_num = None
for i, row in enumerate(ws_idx.iter_rows(min_row=2, values_only=True), start=2):
    if row and row[0] and "COOKIE" in str(row[0]).upper():
        cookie_row_num = i
        log(f"  COOKIE already in INDEX at row {cookie_row_num}")
        break

# Build new row data
new_row = {}
for h in headers:
    if h is None:
        continue
    h_lower = str(h).lower().strip()
    if "symbol" in h_lower or "case" in h_lower:
        new_row[h] = "CASE_COOKIE"
    elif "token" in h_lower:
        new_row[h] = "COOKIE"
    elif "date" in h_lower and "open" in h_lower:
        new_row[h] = NOW.strftime("%Y-%m-%d")
    elif "date" in h_lower:
        new_row[h] = NOW.strftime("%Y-%m-%d")
    elif "status" in h_lower:
        new_row[h] = "OPEN"
    elif "track" in h_lower:
        new_row[h] = "gom_c"
    elif "question" in h_lower or "cau" in h_lower:
        new_row[h] = "fire hợp lệ spec v1.5? gom thật? bao nhiêu? pha nào?"
    elif "verdict" in h_lower:
        new_row[h] = ""  # blank — operator fills
    elif "alpha" in h_lower:
        new_row[h] = "ALPHA_33"
    elif "note" in h_lower or "ghi" in h_lower:
        new_row[h] = "fullyDelisted=True; Q1=0(chain); oi_cycle=0.289; ATH-97.9%"

if cookie_row_num is None:
    # Append new row
    next_row = ws_idx.max_row + 1
    for col_i, h in enumerate(headers, start=1):
        if h in new_row:
            ws_idx.cell(row=next_row, column=col_i, value=new_row[h])
        else:
            # Try to fill by position based on likely column meaning
            pass
    log(f"  Appended COOKIE to row {next_row}")
    log(f"  Values written: {new_row}")
else:
    log(f"  COOKIE already exists at row {cookie_row_num} — skipping append")

wb_idx.save(str(idx_path))
log(f"  Saved: {idx_path.name}")

# ── Step 4: Regenerate INDEX.md (docs/case_files/INDEX.md) ────────────────────
log(f"\n=== Step 4: Regenerate INDEX.md ===")
# Read current INDEX from xlsx
wb_idx2 = openpyxl.load_workbook(str(idx_path), read_only=True)
ws2 = wb_idx2["INDEX"]
all_rows = list(ws2.iter_rows(values_only=True))
headers2 = all_rows[0]
wb_idx2.close()

# Generate markdown table
index_md = CASE_DIR / "INDEX.md"
lines = ["# CASE INDEX\n", f"Generated: {NOW.strftime('%Y-%m-%d %H:%M UTC')}\n\n"]

# Truncated header row
h_display = [str(h) if h else "" for h in headers2]
lines.append("| " + " | ".join(h_display) + " |\n")
lines.append("|" + "|".join([" --- " for _ in headers2]) + "|\n")

for row in all_rows[1:]:
    if any(v is not None for v in row):
        cells = [str(v) if v is not None else "" for v in row]
        lines.append("| " + " | ".join(cells) + " |\n")

index_md.write_text("".join(lines), encoding="utf-8")
log(f"  Written: {index_md.name} ({index_md.stat().st_size:,} bytes)")
log(f"  Rows: {len(all_rows)-1} cases")

# Show last 3 rows for verification
log(f"  Last 3 rows:")
for row in all_rows[-3:]:
    if any(v is not None for v in row):
        log(f"    {[str(v)[:30] if v else '' for v in row[:6]]}")

log(f"\n[C-8 DONE]")
