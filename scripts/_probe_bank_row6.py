"""
Probe: Kiểm tra CASE_BANK.xlsx chi tiết — tìm ô ghi 0.5046 và mapping fn=1.
"""
import openpyxl
from pathlib import Path

TARGET = Path("D:/Data back test/whale_data/docs/case_files/CASE_BANK.xlsx")
wb = openpyxl.load_workbook(TARGET, data_only=True)
ws = wb["DAILY"]

print(f"=== CASE_BANK.xlsx DAILY max_row={ws.max_row} max_col={ws.max_column} ===")
print()

# In header rows
h1 = [ws.cell(1, c).value for c in range(1, min(ws.max_column+1, 42))]
h2 = [ws.cell(2, c).value for c in range(1, min(ws.max_column+1, 42))]
print(f"Row 1 (section): {h1[:10]}")
print(f"Row 2 (col hdrs): {h2[:20]}")
print()

# In từng dòng data đầy đủ
for r in range(3, ws.max_row + 1):
    vals = [ws.cell(r, c).value for c in range(1, min(ws.max_column+1, 42))]
    non_none = [(i+1, v) for i, v in enumerate(vals) if v is not None]
    print(f"Row {r}: {non_none}")
    # Check comment on each cell
    for col_idx in range(1, min(ws.max_column+1, 42)):
        cell = ws.cell(r, col_idx)
        # data_only=True doesn't load comments, note this

print()
# Kiểm tra cột quan trọng: col 5 (taker), col 15 (pos_r), col 16 (acc_r), col 17 (gLSR)
print("=== Key columns (taker=5, pos_r=15, acc_r=16, gLSR=17) ===")
for r in range(3, ws.max_row + 1):
    date = ws.cell(r, 1).value
    taker = ws.cell(r, 5).value
    pos_r = ws.cell(r, 15).value
    acc_r = ws.cell(r, 16).value
    glsr  = ws.cell(r, 17).value
    if date is not None:
        print(f"  row {r}: date={date}  taker_buy_pct={taker}  pos_r={pos_r}  acc_r={acc_r}  gLSR={glsr}")

wb.close()

# Also probe CASE_BANK_NEW for comparison
print()
print("=== CASE_BANK_NEW.xlsx — last 3 rows + key cols ===")
TARGET2 = Path("D:/Data back test/whale_data/docs/case_files/CASE_BANK_NEW.xlsx")
wb2 = openpyxl.load_workbook(TARGET2, data_only=True)
ws2 = wb2["DAILY"]
mr2 = ws2.max_row
for r in range(max(3, mr2-2), mr2+1):
    date = ws2.cell(r, 1).value
    taker = ws2.cell(r, 5).value
    pos_r = ws2.cell(r, 15).value
    acc_r = ws2.cell(r, 16).value
    glsr  = ws2.cell(r, 17).value
    print(f"  row {r}: date={date}  taker={taker}  pos_r={pos_r}  acc_r={acc_r}  gLSR={glsr}")
wb2.close()
