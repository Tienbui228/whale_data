"""Y1-Y4 · Tải thật từ detector, không từ proxy · READ-ONLY."""
from __future__ import annotations
import sys, os, csv, json, math
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()

with open(REPO/'data/config/freshwatch_symbols.txt', encoding='utf-8') as f:
    fw_syms = {l.strip() for l in f if l.strip()}
um_active = {r['symbol'] for r in csv.DictReader(open(REPO/'data/config/universe_master.csv', encoding='utf-8'))
             if r.get('status') == 'active'}
excluded = um_active - fw_syms
print(f'freshwatch: {len(fw_syms)} · excluded: {len(excluded)}')


# ═════ Y1 · gom_h_daily.csv ═════
print('\n' + '=' * 78)
print('Y1 · gom_h_daily.csv · TẢI THẬT theo đêm')
print('=' * 78)

gh_path = REPO / 'data/gom_h_daily.csv'
gh_rows = list(csv.DictReader(open(gh_path, encoding='utf-8')))
print(f'\ntotal rows: {len(gh_rows)}')
print(f'columns: {list(gh_rows[0].keys())[:12]}')

# Find date column
date_col = 'date' if 'date' in gh_rows[0] else ('as_of_date' if 'as_of_date' in gh_rows[0] else list(gh_rows[0].keys())[0])
sym_col = 'symbol' if 'symbol' in gh_rows[0] else list(gh_rows[0].keys())[1]
print(f'date_col={date_col} · sym_col={sym_col}')

# Per-date stats
by_date = defaultdict(list)
all_syms = set()
for r in gh_rows:
    d = r.get(date_col, '')
    s = r.get(sym_col, '')
    if d and s:
        by_date[d].append(s)
        all_syms.add(s)

dates_sorted = sorted(by_date.keys())
if dates_sorted:
    print(f'\nrange: {dates_sorted[0]} → {dates_sorted[-1]} · {len(dates_sorted)} distinct dates')

print(f'\n{"date":12s} {"n_rows":>7s} {"n_syms":>7s} {"in_excl":>8s} {"in_fw":>7s} {"fire?":>6s}  sample')
print('-' * 100)
last_30_dates = dates_sorted[-30:] if len(dates_sorted) >= 30 else dates_sorted
fire_col = None
for c in ('h1_skew', 'h1_fire', 'gom_fire', 'is_fire'):
    if c in gh_rows[0]:
        fire_col = c; break
for d in last_30_dates:
    syms = by_date[d]
    in_excl = [s for s in syms if s in excluded]
    in_fw = [s for s in syms if s in fw_syms]
    sample = ','.join(in_excl[:3])
    fire_info = fire_col or 'all-rows'
    print(f'{d:12s} {len(syms):>7d} {len(set(syms)):>7d} {len(in_excl):>8d} {len(in_fw):>7d} {fire_info:>6s}  {sample}')

# ═════ Y1b · What defines "fire" in gom_h_daily? ═════
print(f'\n[fire semantics gom_h_daily]')
if gh_rows:
    r0 = gh_rows[0]
    print(f'  sample row: {r0}')
    # Count non-null h1_skew, etc as "computed"
    for c in ['h1_skew', 'h2_oiw', 'h3_conc', 'h4_cloc']:
        if c in r0:
            n_non_null = sum(1 for r in gh_rows if r.get(c, '') not in ('', 'NaN', 'nan', 'null', None))
            print(f'  {c} non-null: {n_non_null}/{len(gh_rows)}')


# ═════ Y2 · gom_h2prime_daily.csv ═════
print('\n' + '=' * 78)
print('Y2 · gom_h2prime_daily.csv · TẢI THẬT theo đêm')
print('=' * 78)

h2p_path = REPO / 'data/gom_h2prime_daily.csv'
h2p_rows = list(csv.DictReader(open(h2p_path, encoding='utf-8')))
print(f'\ntotal rows: {len(h2p_rows)}')
print(f'columns: {list(h2p_rows[0].keys())[:12]}')

date_col_h2 = 'date' if 'date' in h2p_rows[0] else list(h2p_rows[0].keys())[0]
sym_col_h2 = 'symbol' if 'symbol' in h2p_rows[0] else list(h2p_rows[0].keys())[1]

by_date_h2 = defaultdict(list)
for r in h2p_rows:
    d = r.get(date_col_h2, '')
    s = r.get(sym_col_h2, '')
    if d and s:
        by_date_h2[d].append(s)

dates_h2_sorted = sorted(by_date_h2.keys())
if dates_h2_sorted:
    print(f'\nrange: {dates_h2_sorted[0]} → {dates_h2_sorted[-1]} · {len(dates_h2_sorted)} distinct dates')

print(f'\n{"date":12s} {"n_rows":>7s} {"n_syms":>7s} {"in_excl":>8s} {"in_fw":>7s}  sample')
print('-' * 100)
last_30_h2 = dates_h2_sorted[-30:] if len(dates_h2_sorted) >= 30 else dates_h2_sorted
for d in last_30_h2:
    syms = by_date_h2[d]
    in_excl = [s for s in syms if s in excluded]
    in_fw = [s for s in syms if s in fw_syms]
    sample = ','.join(in_excl[:3])
    print(f'{d:12s} {len(syms):>7d} {len(set(syms)):>7d} {len(in_excl):>8d} {len(in_fw):>7d}  {sample}')


# ═════ Y3 · MASTER BODY nếu gỡ lọc · ước ═════
print('\n' + '=' * 78)
print('Y3 · MASTER BODY nếu mở scope · chars added')
print('=' * 78)

# Real load = median n_excl per night trong 30 nights gần
excl_daily = []
for d in last_30_dates:
    n = len([s for s in by_date[d] if s in excluded])
    excl_daily.append(n)
if excl_daily:
    excl_daily.sort()
    p50 = excl_daily[len(excl_daily)//2]
    p95 = excl_daily[int(len(excl_daily)*0.95)]
    mx = max(excl_daily)
    avg = sum(excl_daily) / len(excl_daily)
    print(f'\ngom_h_daily excluded fires/đêm 30d: avg={avg:.1f} · p50={p50} · p95={p95} · max={mx}')

    CHARS_PER_TOKEN_LINE = 120
    baseline = 2983  # V1.2 09-16 dry-render
    for scenario, n in [('avg', int(avg)), ('p50', p50), ('p95', p95), ('max', mx)]:
        new_chars = baseline + n * CHARS_PER_TOKEN_LINE
        icon = '❌ VƯỢT 4096' if new_chars > 4096 else '✅ OK'
        print(f'  scenario {scenario} (n={n}): baseline {baseline} + {n}×{CHARS_PER_TOKEN_LINE} = {new_chars} · {icon}')


# ═════ Y4 · DETECTOR THẬT × 2 rate ═════
print('\n' + '=' * 78)
print('Y4 · DETECTOR THẬT · fire → ×2 trong 30d · precision vs base rate')
print('=' * 78)

# Load klines close 60d
import pyarrow.parquet as pq
daily_close = defaultdict(dict)
for i in range(1, 61):
    d = (TODAY - timedelta(days=i)).isoformat()
    p = REPO / f'data/raw/klines_1h/date={d}/part-0.parquet'
    if not p.exists(): continue
    tab = pq.read_table(str(p)).to_pandas()
    for sym, grp in tab.groupby('symbol'):
        last = grp.sort_values('as_of_ts_ms').iloc[-1]
        daily_close[sym][d] = float(last['close'])

def _forward_max(sym, target_date, days=30):
    c0 = daily_close.get(sym, {}).get(target_date.isoformat())
    if not c0 or c0 <= 0: return None
    max_c = c0; max_d = None
    for k in range(1, days + 1):
        c = daily_close.get(sym, {}).get((target_date + timedelta(days=k)).isoformat())
        if c is not None and c > max_c:
            max_c = c; max_d = (target_date + timedelta(days=k)).isoformat()
    return (max_c / c0, max_d)

# Fire = symbol xuất hiện trong gom_h_daily cho ngày đó
# Filter to last 30 dates + excluded only
fires_real = []  # (sym, date)
for d_str in last_30_dates:
    for s in by_date[d_str]:
        if s in excluded:
            fires_real.append((s, d_str))

n_real = len(fires_real)
n_x2 = 0
hits_real = []
for sym, d_str in fires_real:
    fdate = datetime.strptime(d_str, '%Y-%m-%d').date()
    res = _forward_max(sym, fdate, days=30)
    if res is None: continue
    if res[0] >= 2.0:
        n_x2 += 1
        hits_real.append((sym, d_str, res[0], res[1]))

precision_real = n_x2 / n_real * 100 if n_real else 0
print(f'\nreal detector fires (excluded, 30 đêm gần trong CSV): {n_real}')
print(f'  ×2 hits: {n_x2}')
print(f'  precision: {precision_real:.2f}%')
BASE = 1.34
print(f'  vs base rate 1.34%: lift = {precision_real/BASE:.2f}x' if BASE else '')
print(f'  vs proxy 2.81% (lift 2.10x): {"HIGHER" if precision_real > 2.81 else "LOWER"}')

if hits_real:
    print(f'\n×2 hits list (top 15):')
    hits_real.sort(key=lambda x: -x[2])
    for h in hits_real[:15]:
        print(f'  {h[0]:20s} {h[1]} · {h[2]:.2f}x max={h[3]}')

# ═════ Y5 · BẢN ĐỒ SỬA ═════
print('\n' + '=' * 78)
print('Y5 · BẢN ĐỒ SỬA · freshwatch scope filter locations')
print('=' * 78)

import subprocess
# Grep for freshwatch loading in ledger backfill code
for f in ['scripts/ledger_backfill_30d_v3_5.py',
          'scripts/ledger_backfill_30d_v3_4.py',
          'scripts/gom_h_daily.py',
          'scripts/gom_scan.py',
          'scripts/collect_daily.py']:
    p = REPO / f
    if not p.exists(): continue
    print(f'\n[{f}]')
    for i, line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if 'freshwatch_symbols' in line or 'freshwatch_syms' in line or 'load_freshwatch' in line or 'FRESHWATCH' in line:
            print(f'  L{i}: {line.strip()[:120]}')
        elif 'symbols in fw' in line.lower() or 'in freshwatch' in line.lower():
            print(f'  L{i}: {line.strip()[:120]}')

print('\n' + '=' * 78)
print('DONE')
