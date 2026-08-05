"""Read CASE_BANK.xlsx DAILY sheet column headers."""
import openpyxl

wb = openpyxl.load_workbook("docs/case_files/CASE_BANK.xlsx", read_only=True)
print("Sheets:", wb.sheetnames)

for sh_name in wb.sheetnames:
    ws = wb[sh_name]
    print(f"\n=== {sh_name} ===")
    rows = list(ws.iter_rows(min_row=1, max_row=3, values_only=True))
    for i, row in enumerate(rows):
        print(f"  row{i+1}: {row}")
    dims = (ws.max_row, ws.max_column)
    print(f"  dims: {dims}")

wb.close()
