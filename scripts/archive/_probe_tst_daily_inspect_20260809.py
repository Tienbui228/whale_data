"""Inspect CASE_TST DAILY sheet structure and existing data."""
import openpyxl
from pathlib import Path

path = Path("docs/case_files/CASE_TST.xlsx")
wb = openpyxl.load_workbook(path, read_only=True)
print("Sheets:", wb.sheetnames)
print()

if "DAILY" in wb.sheetnames:
    ws = wb["DAILY"]
    # Read header row and first few data rows
    rows = list(ws.iter_rows(values_only=True))
    print(f"DAILY sheet: {ws.max_row} rows x {ws.max_column} cols")
    print()
    if rows:
        print("Header row:", rows[0])
        print()
        print("Last 5 data rows:")
        for r in rows[-5:]:
            print(" ", r)
else:
    print("No DAILY sheet found")

wb.close()
