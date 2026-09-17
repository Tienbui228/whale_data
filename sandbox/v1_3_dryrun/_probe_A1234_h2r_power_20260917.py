"""A1-A4 · Sức thật h2r · lift theo ngưỡng · READ-ONLY sandbox."""
from __future__ import annotations
import sys, os, csv, json, math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]

with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}
um = {r['symbol'] for r in csv.DictReader(open(REPO/'data/config/universe_master.csv'))
      if r.get('status')=='active'}
excl = um - fw

# Reuse backfill h2r results (redo compute)
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

funding = {}
fp = REPO / 'data/config/funding_intervals.json'
if fp.exists():
    j = json.load(open(fp))
    if isinstance(j, dict):
        funding = {k: (v if isinstance(v, int) else v.get('interval_h', 8)) for k, v in j.items()}

def compute_h2_prime(sk, so):
    NaN = float('nan')
    empty = {"h2r": NaN, "n_neg": 0, "n_pos": 0}
    if sk.empty or so.empty:
        return empty
    sk = sk.sort_values('as_of_ts_ms').copy()
    so = so.sort_values('as_of_ts_ms').copy()
    sk['ret'] = sk['close'].pct_change()
    oi_col = None
    for c in ('sum_open_interest_value', 'open_interest_value', 'oi_usd'):
        if c in so.columns:
            oi_col = c; break
    if not oi_col: return empty
    so['delta_oi_usd'] = so[oi_col].diff()
    merged = pd.merge_asof(sk[['as_of_ts_ms', 'ret']], so[['as_of_ts_ms', 'delta_oi_usd']],
                            on='as_of_ts_ms', direction='nearest',
                            tolerance=30 * 60 * 1000)
    merged = merged.dropna()
    if merged.empty: return empty
    neg = merged[merged['ret'] < 0]
    pos = merged[merged['ret'] > 0]
    n_neg = len(neg); n_pos = len(pos)
    if n_neg < 3 or n_pos < 3:
        return {"h2r": NaN, "n_neg": n_neg, "n_pos": n_pos}
    rate_neg = neg[neg['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_neg
    rate_pos = pos[pos['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_pos
    if rate_pos <= 0 or rate_neg <= 0:
        return {"h2r": NaN, "n_neg": n_neg, "n_pos": n_pos}
    return {"h2r": rate_neg/rate_pos, "n_neg": n_neg, "n_pos": n_pos}


# Load klines + oi per date · compute h2r + close per (sym, date)
print('[LOAD 30d klines_1h + oi_hist_1h · compute h2r]')
h2r_by_sym_date = defaultdict(dict)  # sym → date → h2r
close_by_sym_date = defaultdict(dict)  # sym → date → close

for d in LAST_30D + [TODAY - timedelta(days=i) for i in range(31, 61)]:
    d_str = d.isoformat()
    p_k = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    if not p_k.exists(): continue
    dk = pq.read_table(str(p_k)).to_pandas()
    for sym, grp in dk.groupby('symbol'):
        last = grp.sort_values('as_of_ts_ms').iloc[-1]
        close_by_sym_date[sym][d_str] = float(last['close'])

for d in LAST_30D:
    d_str = d.isoformat()
    p_k = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    p_o = REPO / f'data/raw/oi_hist_1h/date={d_str}/part-0.parquet'
    if not p_k.exists() or not p_o.exists(): continue
    dk = pq.read_table(str(p_k)).to_pandas()
    do = pq.read_table(str(p_o)).to_pandas()
    for sym in um:
        sk = dk[dk['symbol'] == sym]
        so = do[do['symbol'] == sym]
        res = compute_h2_prime(sk, so)
        if not math.isnan(res['h2r']):
            h2r_by_sym_date[sym][d_str] = res['h2r']

print(f'  h2r computed · symbols: {len(h2r_by_sym_date)}')


def _fw_max(sym, d_str, days=30):
    c0 = close_by_sym_date.get(sym, {}).get(d_str)
    if not c0 or c0 <= 0: return None
    fd = datetime.strptime(d_str, '%Y-%m-%d').date()
    mc = c0
    for k in range(1, days+1):
        c = close_by_sym_date.get(sym, {}).get((fd + timedelta(days=k)).isoformat())
        if c and c > mc: mc = c
    return mc / c0


# Build token-night table with h2r + x2 flag for both cohorts
def build_table(cohort):
    """Returns list of (sym, date, h2r, x2_flag). Only rows with both h2r AND forward-close data."""
    rows = []
    for sym in cohort:
        for d_str, h2r in h2r_by_sym_date.get(sym, {}).items():
            fwd = _fw_max(sym, d_str, 30)
            if fwd is None: continue
            rows.append((sym, d_str, h2r, fwd >= 2.0))
    return rows

print('[BUILD tables]')
excl_table = build_table(excl)
fw_table = build_table(fw)
print(f'  excluded token-nights: {len(excl_table)} · freshwatch: {len(fw_table)}')


# ═════ A1 · NỀN NỘI BỘ · non-fire precision ═════
print('\n' + '=' * 78)
print('A1 · NỀN NỘI BỘ · precision non-fire (h2r<0.5) vs fire')
print('=' * 78)

def cohort_summary(table, name):
    fires = [r for r in table if r[2] >= 0.5]
    nofires = [r for r in table if r[2] < 0.5]
    prec_fire = sum(1 for r in fires if r[3])/len(fires)*100 if fires else 0
    prec_nofire = sum(1 for r in nofires if r[3])/len(nofires)*100 if nofires else 0
    prec_all = sum(1 for r in table if r[3])/len(table)*100 if table else 0
    print(f'\n  [{name}] n_total={len(table)}')
    print(f'    all: ×2 rate = {sum(1 for r in table if r[3])}/{len(table)} = {prec_all:.2f}%')
    print(f'    fire (h2r>=0.5): {sum(1 for r in fires if r[3])}/{len(fires)} = {prec_fire:.2f}%')
    print(f'    non-fire (h2r<0.5): {sum(1 for r in nofires if r[3])}/{len(nofires)} = {prec_nofire:.2f}%')
    if prec_nofire > 0:
        print(f'    fire ÷ non-fire lift: {prec_fire/prec_nofire:.2f}x')
    return prec_all, prec_fire, prec_nofire

fw_all, fw_fire, fw_nofire = cohort_summary(fw_table, 'freshwatch 139')
excl_all, excl_fire, excl_nofire = cohort_summary(excl_table, 'excluded 385')


# ═════ A2 · LIFT theo ngưỡng · FRESHWATCH ═════
print('\n' + '=' * 78)
print('A2 · LIFT theo ngưỡng · freshwatch 139 · nền {:.2f}%'.format(fw_all))
print('=' * 78)

THRESHOLDS = [0.5, 1.36, 2.03, 2.67, 4.135, 6.364, 8.747, 18.678]
print(f'\n  {"h2r>=":>10s}  {"n_fire":>7s}  {"%":>6s}  {"n_x2":>6s}  {"prec":>7s}  {"lift":>6s}')
print('  ' + '-' * 60)
for thr in THRESHOLDS:
    fires = [r for r in fw_table if r[2] >= thr]
    n_x2 = sum(1 for r in fires if r[3])
    pct = len(fires)/len(fw_table)*100 if fw_table else 0
    prec = n_x2/len(fires)*100 if fires else 0
    lift = prec/fw_all if fw_all > 0 else 0
    mark = ' ★' if lift >= 2.0 else ('  ' if lift >= 1.5 else '')
    print(f'  {thr:>10.3f}  {len(fires):>7d}  {pct:>5.1f}%  {n_x2:>6d}  {prec:>6.2f}%  {lift:>5.2f}x{mark}')


# ═════ A3 · LIFT theo ngưỡng · EXCLUDED ═════
print('\n' + '=' * 78)
print('A3 · LIFT theo ngưỡng · excluded 385 · nền {:.2f}%'.format(excl_all))
print('=' * 78)

print(f'\n  {"h2r>=":>10s}  {"n_fire":>7s}  {"%":>6s}  {"n_x2":>6s}  {"prec":>7s}  {"lift":>6s}')
print('  ' + '-' * 60)
for thr in THRESHOLDS:
    fires = [r for r in excl_table if r[2] >= thr]
    n_x2 = sum(1 for r in fires if r[3])
    pct = len(fires)/len(excl_table)*100 if excl_table else 0
    prec = n_x2/len(fires)*100 if fires else 0
    lift = prec/excl_all if excl_all > 0 else 0
    mark = ' ★' if lift >= 2.0 else ('  ' if lift >= 1.5 else '')
    print(f'  {thr:>10.3f}  {len(fires):>7d}  {pct:>5.1f}%  {n_x2:>6d}  {prec:>6.2f}%  {lift:>5.2f}x{mark}')


# ═════ A4 · 13 PROVEN · h2r quanh D0 ═════
print('\n' + '=' * 78)
print('A4 · 13 PROVEN · h2r quanh D0 · vùng cao hay không?')
print('=' * 78)

# Approximate D0 from ledger docs (best-effort)
PROVEN_D0 = {
    'BANK':   '2026-07-20',
    'TUT':    '2026-07-09',   # approx
    'BTW':    '2026-06-05',
    'BTR':    '2026-08-26',
    'CAP':    '2026-08-17',
    'ON':     '2026-07-02',
    'AKE':    '2026-07-11',   # approx
    'CYS':    '2026-08-04',
    'HEMI':   '2026-09-03',
    'APR':    '2026-09-07',   # đối chứng, không proven
    'BULLA':  '2026-09-05',
    'PROM':   '2026-08-29',
    'LOBSTER':'2026-09-04',
    'UAI':    '2026-09-09',
    'SOPH':   '2026-09-07',   # đối chứng, không proven
}

def _get_perp_sym(bare):
    if bare == 'LOBSTER': return '龙虾USDT'
    return f'{bare}USDT'

print(f'\n  Token    D0          h2r@D0-3  D0-2  D0-1  D0    D0+1  D0+2  in-vùng-cao?')
print('  ' + '-' * 88)
def _q95(): return 6.364

for token, d0_str in PROVEN_D0.items():
    perp = _get_perp_sym(token)
    d0 = datetime.strptime(d0_str, '%Y-%m-%d').date()
    row_vals = []
    max_h = 0
    for offset in [-3, -2, -1, 0, 1, 2]:
        d = (d0 + timedelta(days=offset)).isoformat()
        h = h2r_by_sym_date.get(perp, {}).get(d)
        row_vals.append(f'{h:6.2f}' if h is not None else '   N/A')
        if h is not None and h > max_h: max_h = h
    hi = ' ★>q95(6.36)' if max_h >= 6.364 else (' q90-q95' if max_h >= 4.135 else ' <q90')
    print(f'  {token:9s} {d0_str}  ' + '  '.join(row_vals) + f'  {hi}')

# Đối chứng: mean h2r cohort quanh cùng cửa sổ (baseline)
print(f'\n  Baseline h2r mean quanh window (excluded, 30d gần): ', end='')
all_h2r_vals = [h for sym_d in h2r_by_sym_date.values() for h in sym_d.values()]
if all_h2r_vals:
    all_h2r_vals.sort()
    print(f'median={all_h2r_vals[len(all_h2r_vals)//2]:.3f} · mean={sum(all_h2r_vals)/len(all_h2r_vals):.3f}')

print('\n' + '=' * 78)
