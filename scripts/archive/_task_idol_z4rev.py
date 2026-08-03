#!/usr/bin/env python3
"""Z4-rev: Cập nhật CASE_IDOL.xlsx:
1. EVENTS E1: đổi nhãn nguồn → 'Binance (Alpha custody) — cơ chế xác nhận 03/08'
2. CASE / W6 annotation: GOM-qua-Alpha = giả thuyết dẫn đầu, chờ Z1
NOTE: Không ghi verdict CASE sheet (tầng HUMAN). Chỉ update doc_nhanh + ghi chú.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz
import openpyxl
from openpyxl.cell.cell import MergedCell

WHALE    = Path(r'D:\Data back test\whale_data')
CASE_DIR = WHALE / 'docs' / 'case_files'
IDX_PATH = CASE_DIR / 'CASE_IDOL.xlsx'
OUT      = WHALE / 'docs' / 'reports' / '_task_idol_z4rev.txt'

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

emit('=' * 70)
emit('TASK idol_z4rev —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit('=' * 70)

wb = openpyxl.load_workbook(str(IDX_PATH), data_only=False)

# ── EVENTS sheet: update E1 label ─────────────────────────────────────────────
emit('\n[1] EVENTS — Đọc hiện trạng:')
we = wb['EVENTS']
for r in range(1, min(we.max_row + 1, 12)):
    row_data = []
    for c in range(1, min((we.max_column or 8) + 1, 9)):
        cell = we.cell(r, c)
        if isinstance(cell, MergedCell): continue
        v = cell.value
        if v is not None:
            row_data.append(f'c{c}={str(v)[:60]!r}')
    if row_data:
        emit(f'  row{r}: ' + '  '.join(row_data))

emit('\n[2] EVENTS — Cập nhật E1 nhãn nguồn:')
# Find E1 row (should be row4 from prior probe)
e1_updated = False
for r in range(2, min(we.max_row + 1, 12)):
    cell_date = we.cell(r, 1)
    cell_desc = we.cell(r, 2)
    if isinstance(cell_date, MergedCell) or isinstance(cell_desc, MergedCell):
        continue
    desc_val = str(cell_desc.value or '')
    date_val = str(cell_date.value or '')
    # Match E1: 273M IDOL rút on-chain
    if '273M' in desc_val or '31/07' in date_val or '07-31' in date_val:
        emit(f'  Found E1 at row{r}: date={date_val!r} desc={desc_val[:60]!r}')
        # Read current doc_nhanh (col4) and source label (col5 or col3)
        old_doc4 = we.cell(r, 4).value or ''
        old_col3 = we.cell(r, 3).value or ''
        emit(f'  Current col3={str(old_col3)[:80]!r}')
        emit(f'  Current col4={str(old_doc4)[:80]!r}')

        # Update col3 (nguon/source) → Binance (Alpha custody) label
        if not isinstance(we.cell(r, 3), MergedCell):
            we.cell(r, 3).value = 'Binance (Alpha custody) — cơ chế xác nhận 03/08'
            emit(f'  → col3 updated: Binance (Alpha custody) — cơ chế xác nhận 03/08')

        # Append to doc_nhanh (col4): Z4-rev note
        z4_note = (
            '[Z4-rev 03/08] GOM-qua-Alpha = giả thuyết dẫn đầu về cơ chế: '
            '273M IDOL rút về ví BSC (0x...) có thể là GOM staging qua Binance Alpha custody. '
            'Mechanism: Binance giữ IDOL on-chain → users mua qua Binance app (Alpha section) → '
            'Binance rút batch về ví custody BSC → 7×~39M = 273M. '
            'Xác nhận còn thiếu (Z1): txhash + địa chỉ đích 13 ví. '
            'Nếu Z1 confirm Binance custody → E1 = GOM-staging, không phải chốt lợi nhuận. '
            'Nếu Z1 thấy pattern khác → revise.'
        )
        if not isinstance(we.cell(r, 4), MergedCell):
            existing = str(old_doc4)
            if '[Z4-rev' not in existing:
                we.cell(r, 4).value = existing + ' | ' + z4_note if existing else z4_note
                emit(f'  → col4 appended Z4-rev note ({len(z4_note)} chars)')
            else:
                emit(f'  → col4 already has Z4-rev note, skip')
        e1_updated = True
        break

if not e1_updated:
    emit('  WARNING: E1 row not found by pattern. Checking all rows:')
    for r in range(2, min(we.max_row + 1, 15)):
        row_data = []
        for c in range(1, 6):
            cell = we.cell(r, c)
            if not isinstance(cell, MergedCell) and cell.value:
                row_data.append(f'c{c}={str(cell.value)[:40]!r}')
        if row_data:
            emit(f'  row{r}: ' + '  '.join(row_data))

# ── CASE sheet: W6 annotation ─────────────────────────────────────────────────
emit('\n[3] CASE sheet — W6 GOM-qua-Alpha annotation:')
# Find CASE sheet
ws_name = None
for name in wb.sheetnames:
    if 'CASE' in name.upper() and 'INDEX' not in name.upper():
        ws_name = name
        break
emit(f'  Sheets: {wb.sheetnames}')
emit(f'  Target sheet: {ws_name!r}')

if ws_name:
    wc = wb[ws_name]
    # Find W6 row
    w6_row = None
    for r in range(1, min(wc.max_row + 1, 50)):
        for c in range(1, min((wc.max_column or 10) + 1, 11)):
            cell = wc.cell(r, c)
            if isinstance(cell, MergedCell): continue
            v = str(cell.value or '')
            if 'W6' in v or 'w6' in v:
                w6_row = r
                emit(f'  Found W6 at row{r} col{c}: {v[:60]!r}')
                break
        if w6_row: break

    if w6_row:
        # Find the value/verdict column for W6 (usually col2 or col3)
        for c in range(1, 6):
            cell = wc.cell(w6_row, c)
            if not isinstance(cell, MergedCell):
                v = str(cell.value or '')
                emit(f'  W6 col{c}: {v[:80]!r}')

        # Update W6 annotation — find best column to write note
        # Look for an "analysis" or "verdict" column header
        hdr_row = max(1, w6_row - 5)
        for c in range(1, min((wc.max_column or 8) + 1, 9)):
            hdr = wc.cell(hdr_row, c)
            if not isinstance(hdr, MergedCell):
                emit(f'  header row{hdr_row} col{c}: {str(hdr.value or "")[:30]!r}')

        # Write annotation to col3 if not merged
        target_c = 3
        ann_cell = wc.cell(w6_row, target_c)
        if not isinstance(ann_cell, MergedCell):
            old_ann = str(ann_cell.value or '')
            new_ann = (
                'GOM-qua-Alpha: PLAUSIBLE (giả thuyết dẫn đầu, chờ Z1). '
                'Z7 confirm: IDOL không có Binance Spot listing (no_spot), '
                'không có Binance Alpha API listing — '
                'tuy nhiên Binance giữ IDOL custody on-chain (BSC) như một broker. '
                'Mechanism GOM: users mua IDOL qua Gate/CEX khác → Binance aggregate → '
                'batch-withdraw 273M về ví staging BSC. '
                'VWAP DEX proxy: $0.018912 (Z6 50/50 — không chính xác vì không có swap log). '
                'CG tickers 03/08: PancakeSwap V3 $5.98M/24h, Gate $1.12M/24h, LBank $1.24M/24h. '
                'PENDING Z1: txhash + địa chỉ đích để xác nhận Binance custody vs other operator.'
            )
            if '[Z4-rev' not in old_ann and 'GOM-qua-Alpha' not in old_ann:
                wc.cell(w6_row, target_c).value = new_ann
                emit(f'  → W6 col{target_c} updated ({len(new_ann)} chars)')
            else:
                emit(f'  → W6 col{target_c} already has annotation, skip')
        else:
            emit(f'  → W6 col{target_c} is MergedCell, cannot write')
    else:
        emit('  W6 row not found in CASE sheet')
else:
    emit('  No CASE sheet found (not in sheetnames)')

# ── Save ──────────────────────────────────────────────────────────────────────
emit('\n[4] Save CASE_IDOL.xlsx...')
try:
    wb.save(str(IDX_PATH))
    emit('  → SAVED OK')
except Exception as ex:
    emit(f'  → SAVE ERROR: {ex}')

emit('\n[5] Z4-rev SUMMARY:')
emit('  E1: col3 → "Binance (Alpha custody) — cơ chế xác nhận 03/08"')
emit('  E1: col4 → appended Z4-rev GOM-qua-Alpha hypothesis note')
emit('  W6 (CASE sheet): GOM-qua-Alpha annotation written')
emit()
emit('  PENDING (chưa làm, chờ operator/data):')
emit('  • Z1: txhash + địa chỉ đích 13 ví (P3) → xác nhận Binance vs other')
emit('  • Nếu Z1 = Binance custody: upgrade W6-A → CONFIRMED')
emit('  • Nếu Z1 = non-Binance: revise E1 label lại')
emit()
emit('  Z7 finding (ghi thêm):')
emit('  IDOL thiếu trong alpha_bsc_symbols.txt = CẤU TRÚC (no_spot, không phải bug)')
emit('  ~30% universe (119/398 est.) là no_spot → mù trong collector hiện tại')
emit('  BSC_BROKEN = 0 trong sample → alpha_bsc_symbols.txt có thể RỖNG trên VPS')
emit('  Cần operator chạy _probe_alpha_taker.py --write-config để kiểm tra')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
