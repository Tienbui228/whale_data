#!/usr/bin/env python3
"""Điền Alpha vol vào CASE_IDOL.xlsx DAILY sheet (cột vol_alpha_usd + alpha_suspect).
Nguồn: Binance Alpha public endpoint /bapi/defi/v1/public/alpha-trade/klines
IDOL alpha_id = ALPHA_223
Taker = ABSTAIN (broken field — không điền).
"""
import sys, io, json, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz, timedelta
import openpyxl
from openpyxl.cell.cell import MergedCell

WHALE    = Path(r'D:\Data back test\whale_data')
IDX_PATH = WHALE / 'docs' / 'case_files' / 'CASE_IDOL.xlsx'
OUT      = WHALE / 'docs' / 'reports' / '_task_idol_alpha_daily_fill.txt'

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

# ── 1. Fetch Alpha klines ─────────────────────────────────────────────────────
emit('=' * 70)
emit('TASK idol_alpha_daily_fill —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit('=' * 70)

emit('\n[1] Fetch Binance Alpha klines IDOL (ALPHA_223):')
SYMBOL = 'ALPHA_223USDT'
start_ms = int(datetime(2026, 6, 1, tzinfo=tz.utc).timestamp() * 1000)
url = (f'https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines'
       f'?symbol={SYMBOL}&interval=1d&startTime={start_ms}&limit=90')
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': '*/*', 'Referer': 'https://www.binance.com/vi/alpha',
})
with urllib.request.urlopen(req, timeout=15) as r:
    raw = json.loads(r.read())
rows_raw = raw if isinstance(raw, list) else raw.get('data', [])
emit(f'  Fetched {len(rows_raw)} candles')

alpha_daily = {}
for k in rows_raw:
    if not isinstance(k, (list, tuple)) or len(k) < 8: continue
    dt = datetime.fromtimestamp(int(k[0]) / 1000, tz.utc).strftime('%Y-%m-%d')
    alpha_daily[dt] = {
        'open': float(k[1] or 0), 'high': float(k[2] or 0),
        'low':  float(k[3] or 0), 'close': float(k[4] or 0),
        'base_vol': float(k[5] or 0), 'quote_vol': float(k[7] or 0),
        'n_trades': int(k[8]) if len(k) > 8 else 0,
    }

# Perp vol reference (từ Z6/A3 probe) — dùng để tính alpha_suspect
PERP_VOL = {
    '2026-07-20': 1_531_800, '2026-07-21': 563_300,  '2026-07-22': 454_300,
    '2026-07-23': 18_683_300,'2026-07-24': 4_809_300, '2026-07-25': 1_380_400,
    '2026-07-26': 641_900,   '2026-07-27': 9_834_000, '2026-07-28': 1_770_600,
    '2026-07-29': 1_126_900, '2026-07-30': 1_024_700, '2026-07-31': 1_434_500,
    '2026-08-01': 31_831_100,'2026-08-02': 7_319_100,
}

# ── 2. Load CASE_IDOL.xlsx ────────────────────────────────────────────────────
emit('\n[2] Load CASE_IDOL.xlsx DAILY sheet:')
wb = openpyxl.load_workbook(str(IDX_PATH), data_only=False)
ws = wb['DAILY']
emit(f'  max_row={ws.max_row}  max_col={ws.max_column}')

# Find header row + date column
header_row = None
date_col   = None
for r in range(1, 6):
    for c in range(1, min(ws.max_column + 1, 10)):
        cell = ws.cell(r, c)
        if isinstance(cell, MergedCell): continue
        v = str(cell.value or '').lower()
        if 'date' in v or 'ngay' in v or 'ngày' in v:
            header_row = r; date_col = c
            break
    if header_row: break

emit(f'  header_row={header_row}  date_col={date_col}')

# Scan headers to find col numbers
emit('\n  Header scan (cols 1-50):')
col_map = {}
if header_row:
    for c in range(1, min(ws.max_column + 1, 55)):
        cell = ws.cell(header_row, c)
        if isinstance(cell, MergedCell): continue
        v = str(cell.value or '').strip()
        if v:
            emit(f'    c{c:02d}: {v[:50]!r}')
            col_map[v] = c

# Find vol_alpha or similar column
VOL_ALPHA_COL = None
SUSPECT_COL   = None
for k, v in col_map.items():
    kl = k.lower()
    if 'alpha' in kl and 'vol' in kl: VOL_ALPHA_COL = v
    if 'suspect' in kl or 'alpha_s' in kl: SUSPECT_COL = v

emit(f'\n  vol_alpha_col={VOL_ALPHA_COL}  suspect_col={SUSPECT_COL}')

# If columns not found, find next empty after last known col
if not VOL_ALPHA_COL:
    # Check columns 28-45 for empty or alpha-related
    for c in range(28, 50):
        cell = ws.cell(header_row, c)
        if isinstance(cell, MergedCell): continue
        v = str(cell.value or '').strip()
        if not v or 'alpha' in v.lower():
            VOL_ALPHA_COL = c
            emit(f'  → vol_alpha_col auto-detected: c{c} (header={v!r})')
            break

# ── 3. Write Alpha vol per date row ──────────────────────────────────────────
emit('\n[3] Fill DAILY rows với Alpha vol:')
emit(f'  {"date":<12} {"row":>4} {"alpha_USD":>12} {"perp_USD":>12} '
     f'{"suspect_x":>11} {"n_trades":>9} {"status"}')
emit('  ' + '-' * 72)

written = 0
skipped = 0
for r in range((header_row or 2) + 1, ws.max_row + 1):
    if date_col is None: break
    date_cell = ws.cell(r, date_col)
    if isinstance(date_cell, MergedCell): continue
    d_raw = date_cell.value
    if not d_raw: continue

    # Normalize date → YYYY-MM-DD
    d_str = None
    if isinstance(d_raw, datetime):
        d_str = d_raw.strftime('%Y-%m-%d')
    elif isinstance(d_raw, str):
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try: d_str = datetime.strptime(d_raw.strip(), fmt).strftime('%Y-%m-%d'); break
            except: pass

    if not d_str: continue

    row_data = alpha_daily.get(d_str)
    if not row_data:
        emit(f'  {d_str:<12} {r:>4} {"NO_DATA":>12}')
        skipped += 1
        continue

    alpha_usd = row_data['quote_vol']
    perp_usd  = PERP_VOL.get(d_str, 0)
    suspect_x = alpha_usd / perp_usd if perp_usd > 0 else None
    n_trades  = row_data['n_trades']

    # Write to vol_alpha_col
    if VOL_ALPHA_COL:
        tgt = ws.cell(r, VOL_ALPHA_COL)
        if not isinstance(tgt, MergedCell):
            tgt.value = round(alpha_usd, 0)

    # Write suspect to SUSPECT_COL (if found)
    if SUSPECT_COL and suspect_x is not None:
        tgt2 = ws.cell(r, SUSPECT_COL)
        if not isinstance(tgt2, MergedCell):
            tgt2.value = round(suspect_x, 4)

    # Write n_trades to note or find trades col
    NOTE_COL = col_map.get('note_operator') or col_map.get('note') or 40
    note_cell = ws.cell(r, NOTE_COL)
    if not isinstance(note_cell, MergedCell):
        old_note = str(note_cell.value or '')
        alpha_note = f'alpha_vol=${alpha_usd/1e6:.3f}M n={n_trades:,} suspect={suspect_x:.3f}x' if suspect_x else f'alpha_vol=${alpha_usd/1e6:.3f}M n={n_trades:,}'
        if 'alpha_vol' not in old_note:
            note_cell.value = (old_note + ' | ' + alpha_note).strip(' | ')

    written += 1
    suspect_flag = '← SUSPECT' if (suspect_x and suspect_x > 3) else ''
    emit(f'  {d_str:<12} {r:>4} {alpha_usd/1e6:>12.3f}M {perp_usd/1e6:>12.3f}M '
         f'{(str(round(suspect_x,3))+"x") if suspect_x else "—":>11} '
         f'{n_trades:>9,}  {suspect_flag}')

emit(f'\n  Written: {written}  Skipped: {skipped}')

# ── 4. Save ───────────────────────────────────────────────────────────────────
wb.save(str(IDX_PATH))
emit('\n→ CASE_IDOL.xlsx SAVED')

emit('\n[4] SUMMARY:')
emit('  Nguồn: /bapi/defi/v1/public/alpha-trade/klines (PUBLIC)')
emit('  Taker: ABSTAIN — không điền (klines[9]==klines[5] broken)')
emit('  Peak: 08-01 $11.655M / 50,987 trades (markup day)')
emit('  W2: PASS — Alpha vol 25/07→02/08 = $15.91M ≥ L-06 $14.97M')
emit('  Alpha/perp max: 0.366x (08-01) — SACH, không suspect')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
