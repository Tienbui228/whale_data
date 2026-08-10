"""KOMA: validate_written_pack + CASE_INDEX entry check."""
from __future__ import annotations
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(ROOT / "scripts"))
from case_guard import validate_written_pack

xlsx = ROOT / "docs" / "case_files" / "CASE_KOMA.xlsx"
print(f"=== KOMA Guard V2 ===")
print(f"File: {xlsx}")
print(f"Exists: {xlsx.exists()}")

if xlsx.exists():
    try:
        validate_written_pack(xlsx)
        print("Result: PASS")
    except RuntimeError as e:
        print(f"Result: FAIL")
        print(str(e))
    except Exception as e:
        print(f"Result: ERROR — {e}")
else:
    print("CASE_KOMA.xlsx NOT FOUND")

# Check CASE_INDEX
print()
print("=== CASE_INDEX KOMA row ===")
import openpyxl
idx = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
if idx.exists():
    wb = openpyxl.load_workbook(str(idx), read_only=True, data_only=True)
    ws = wb.active
    header = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = [str(c) if c else "" for c in row]
            continue
        if row[0] is None:
            continue
        token = str(row[0]).strip()
        if "KOMA" in token.upper():
            print(f"Row: {dict(zip(header, row))}")
    wb.close()
else:
    print("CASE_INDEX.xlsx NOT FOUND")
