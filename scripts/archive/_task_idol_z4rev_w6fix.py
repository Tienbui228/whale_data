#!/usr/bin/env python3
"""Z4-rev part 2: Ghi W6 GOM-qua-Alpha vào CASE sheet row11 (Tom tat input)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz
import openpyxl
from openpyxl.cell.cell import MergedCell

IDX_PATH = Path(r'D:\Data back test\whale_data\docs\case_files\CASE_IDOL.xlsx')
OUT      = Path(r'D:\Data back test\whale_data\docs\reports\_task_idol_z4rev.txt')

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

emit('Z4-rev-W6fix —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))

wb = openpyxl.load_workbook(str(IDX_PATH), data_only=False)
wc = wb['CASE']

# Row 11: Tom tat input
r = 11
cell = wc.cell(r, 2)
if isinstance(cell, MergedCell):
    emit(f'  row{r} col2 = MergedCell — cannot write')
else:
    old = str(cell.value or '')
    emit(f'  row{r} col2 current: {old[:120]!r}')
    w6_note = (
        ' | [Z4-rev 03/08] W6 GOM-qua-Alpha = PLAUSIBLE (giả thuyết dẫn đầu). '
        'Z7: IDOL no_spot Binance, no Binance Alpha listing — nhưng Binance '
        'có thể là broker/custodian BSC. VWAP DEX proxy $0.018912 (Z6, 50/50). '
        'CG 03/08: PSv3-BSC $5.98M, Gate $1.12M, LBank $1.24M/24h. '
        'PENDING Z1: txhash 13 ví đích → confirm cơ chế.'
    )
    if 'Z4-rev' not in old:
        cell.value = old + w6_note
        emit(f'  → appended W6 note ({len(w6_note)} chars)')
    else:
        emit(f'  → already has Z4-rev note, skip')

wb.save(str(IDX_PATH))
emit('SAVED OK')

# Append to existing report
existing = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
OUT.write_text(existing + '\n' + '\n'.join(lines), encoding='utf-8')
print(f'Appended to {OUT}')
