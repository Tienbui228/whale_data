#!/usr/bin/env python3
"""VPS probe: spot_klines_1d venue=binance_spot_bsc + collect_alpha_spot logs.
Chạy trên VPS: python /root/Data_back_test/whale_data/_probe_vps_alpha_store.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz
import pyarrow.parquet as pq
import pandas as pd

RAW  = Path('/root/Data_back_test/whale_data/data/raw')
LOGS = Path('/root/Data_back_test/whale_data/data/logs')
OUT  = Path('/root/Data_back_test/whale_data/scratch/probe_vps_alpha_store.txt')
OUT.parent.mkdir(exist_ok=True)

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

emit('=' * 70)
emit('PROBE vps_alpha_store —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit('=' * 70)

# ── 1. spot_klines_1d partitions ─────────────────────────────────────────────
emit('\n[1] spot_klines_1d — tất cả date partitions:')
skl = RAW / 'spot_klines_1d'
if not skl.exists():
    emit('  ERROR: spot_klines_1d NOT FOUND')
else:
    dates = sorted(d.name for d in skl.glob('date=*'))
    emit(f'  Total date partitions: {len(dates)}')
    emit(f'  First: {dates[0] if dates else "—"}')
    emit(f'  Last:  {dates[-1] if dates else "—"}')

    # Check venue=binance_spot_bsc in recent dates
    emit('\n[1b] venue=binance_spot_bsc — scan 7 ngày gần nhất:')
    bsc_dates = []
    for date_name in dates[-7:]:
        p = skl / date_name / 'part-0.parquet'
        if not p.exists():
            continue
        df = pq.read_table(str(p), columns=['symbol','venue','quote_vol','close']).to_pandas()
        bsc = df[df['venue'] == 'binance_spot_bsc']
        if len(bsc) > 0:
            bsc_dates.append(date_name)
            d_str = date_name.replace('date=', '')
            emit(f'\n  {d_str}: {len(bsc)} BSC symbols')
            # Sample 3 rows
            sample = bsc[['symbol','venue','quote_vol','close']].head(3)
            for _, row in sample.iterrows():
                emit(f'    {row["symbol"]:<20} venue={row["venue"]}  '
                     f'quote_vol={float(row["quote_vol"] or 0):>14,.0f}  '
                     f'close={float(row["close"] or 0):.6f}')
        else:
            d_str = date_name.replace('date=', '')
            emit(f'\n  {d_str}: 0 binance_spot_bsc rows')
            # Show what venues exist
            venues = df['venue'].value_counts().to_dict()
            emit(f'    venues present: {dict(list(venues.items())[:5])}')

    emit(f'\n  → Dates with binance_spot_bsc data: {len(bsc_dates)}')
    for d in bsc_dates:
        emit(f'    {d}')

    # Full count on latest BSC date
    if bsc_dates:
        latest = bsc_dates[-1]
        p = skl / latest / 'part-0.parquet'
        df = pq.read_table(str(p), columns=['symbol','venue','quote_vol']).to_pandas()
        bsc = df[df['venue'] == 'binance_spot_bsc']
        emit(f'\n[1c] Latest BSC date ({latest}): {len(bsc)} symbols')
        emit(f'  Symbols: {sorted(bsc["symbol"].tolist())[:20]} ...')
        # Check IDOL
        idol = bsc[bsc['symbol'] == 'IDOLUSDT']
        emit(f'  IDOLUSDT present: {len(idol) > 0}')
        if len(idol):
            r = idol.iloc[0]
            emit(f'  IDOL: quote_vol={float(r["quote_vol"] or 0):,.0f}  close={float(r.get("close",0) or 0):.6f}')

# ── 2. collect_alpha_spot logs ───────────────────────────────────────────────
emit('\n\n[2] collect_alpha_spot logs:')
log_candidates = [
    LOGS / 'collect_alpha_spot.log',
    LOGS / 'collect_alpha_spot.jsonl',
]
# Also search for any alpha log
alpha_logs = list(LOGS.glob('*alpha*')) if LOGS.exists() else []
emit(f'  LOGS dir exists: {LOGS.exists()}')
emit(f'  Alpha log files found: {[f.name for f in alpha_logs]}')

for lf in alpha_logs[:3]:
    lines_log = lf.read_text(encoding='utf-8', errors='replace').splitlines()
    emit(f'\n  {lf.name}: {len(lines_log)} lines')
    # Show last 20 lines
    for l in lines_log[-20:]:
        emit(f'    {l[:120]}')

# Check fetch_log parquet
fetch_log = Path('/root/Data_back_test/whale_data/data/meta/fetch_log_alpha_spot.parquet')
if fetch_log.exists():
    emit(f'\n[2b] fetch_log_alpha_spot.parquet:')
    df = pq.read_table(str(fetch_log)).to_pandas()
    emit(f'  Total rows: {len(df)}')
    emit(f'  Columns: {list(df.columns)}')
    if len(df):
        emit(f'  Last 5 rows:')
        for _, r in df.tail(5).iterrows():
            emit(f'    {r.to_dict()}')
else:
    emit(f'\n  fetch_log_alpha_spot.parquet: NOT FOUND at {fetch_log}')

emit('\n' + '=' * 70)
emit('PROBE DONE')
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
