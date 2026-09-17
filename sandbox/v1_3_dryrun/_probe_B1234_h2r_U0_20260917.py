"""B1-B4 · h2r → U0 · READ-ONLY sandbox.

U0 (unhedge cross · def SOPH ledger):
  div_avg3(t) vượt 0.5→0.7 trong ≤3 ngày · acc_r rơi ≥30% cùng cửa sổ
  → tag `[UNHEDGE-EVENT do crowd rời]`.

div_avg3(t) = mean(pos_r/acc_r) trailing 3 ngày.
"""
from __future__ import annotations
import sys, os, csv, json, math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()

with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}

# Load freshwatch_daily CSV multi-month
def _load_fw_daily():
    """Return sym → {date → {pos_r, acc_r, glsr}}"""
    store = defaultdict(dict)
    for month in ['2026-06', '2026-07', '2026-08', '2026-09']:
        p = REPO / f'data/export/freshwatch_daily_{month}.csv'
        if not p.exists(): continue
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                sym = r.get('symbol', '')
                d = r.get('date', '')
                if not sym or not d: continue
                try:
                    pos = float(r.get('lsr_pos_r', 'nan'))
                    acc = float(r.get('lsr_acc_r', 'nan'))
                except: continue
                if math.isnan(pos) or math.isnan(acc): continue
                store[sym][d] = {'pos_r': pos, 'acc_r': acc}
    return store

print('[LOAD freshwatch_daily · pos_r/acc_r]')
fw_daily = _load_fw_daily()
print(f'  distinct symbols in freshwatch_daily: {len(fw_daily)}')


def _div_avg3(sym_data, target_d_str):
    """div_avg3(target) = mean(pos_r/acc_r) trailing 3d [T-2, T-1, T]"""
    td = datetime.strptime(target_d_str, '%Y-%m-%d').date()
    ratios = []
    for k in range(3):
        d = (td - timedelta(days=2-k)).isoformat()
        row = sym_data.get(d)
        if not row: continue
        if row['acc_r'] <= 0: continue
        ratios.append(row['pos_r'] / row['acc_r'])
    if len(ratios) < 3: return None
    return sum(ratios) / len(ratios)


def _detect_u0_crosses(sym):
    """Detect U0 events: div_avg3 crosses 0.5→0.7 in ≤3d AND acc_r drops ≥30%.
    Returns list of D_cross dates (T when div_avg3 first hits ≥0.7)."""
    sym_data = fw_daily.get(sym, {})
    if not sym_data: return []
    dates_sorted = sorted(sym_data.keys())
    if len(dates_sorted) < 10: return []

    crosses = []
    for i in range(3, len(dates_sorted)):
        d_t = dates_sorted[i]
        div_t = _div_avg3(sym_data, d_t)
        if div_t is None or div_t < 0.7: continue

        # Check trailing 3d for div ≤ 0.5
        cross_found = False
        for lookback in range(1, 4):
            if i - lookback < 0: continue
            d_prev = dates_sorted[i - lookback]
            div_prev = _div_avg3(sym_data, d_prev)
            if div_prev is None: continue
            if div_prev <= 0.5:
                # Check acc_r drop ≥30% in same window
                acc_t = sym_data[d_t]['acc_r']
                acc_prev = sym_data[d_prev]['acc_r']
                if acc_prev > 0 and (acc_prev - acc_t) / acc_prev >= 0.30:
                    cross_found = True
                    break
        if cross_found:
            # avoid double-detect within 7d
            if not crosses or (datetime.strptime(d_t, '%Y-%m-%d').date() -
                               datetime.strptime(crosses[-1], '%Y-%m-%d').date()).days > 7:
                crosses.append(d_t)
    return crosses


# Reuse h2r + close from previous probes — recompute
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

def compute_h2_prime(sk, so):
    NaN = float('nan')
    empty = {"h2r": NaN}
    if sk.empty or so.empty: return empty
    sk = sk.sort_values('as_of_ts_ms').copy()
    so = so.sort_values('as_of_ts_ms').copy()
    sk['ret'] = sk['close'].pct_change()
    oi_col = None
    for c in ('sum_open_interest_value', 'open_interest_value', 'oi_usd'):
        if c in so.columns: oi_col = c; break
    if not oi_col: return empty
    so['delta_oi_usd'] = so[oi_col].diff()
    merged = pd.merge_asof(sk[['as_of_ts_ms', 'ret']], so[['as_of_ts_ms', 'delta_oi_usd']],
                            on='as_of_ts_ms', direction='nearest', tolerance=30*60*1000)
    merged = merged.dropna()
    if merged.empty: return empty
    neg = merged[merged['ret'] < 0]
    pos = merged[merged['ret'] > 0]
    n_neg = len(neg); n_pos = len(pos)
    if n_neg < 3 or n_pos < 3: return empty
    rate_neg = neg[neg['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_neg
    rate_pos = pos[pos['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_pos
    if rate_pos <= 0 or rate_neg <= 0: return empty
    return {"h2r": rate_neg/rate_pos}


LAST_60D = [(TODAY - timedelta(days=i)) for i in range(1, 61)]
LAST_90D = [(TODAY - timedelta(days=i)) for i in range(1, 91)]
h2r_by_sym_date = defaultdict(dict)
close_by_sym_date = defaultdict(dict)

print('[LOAD h2r + close 60d]')
for d in LAST_60D:
    d_str = d.isoformat()
    p_k = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    p_o = REPO / f'data/raw/oi_hist_1h/date={d_str}/part-0.parquet'
    if not p_k.exists(): continue
    dk = pq.read_table(str(p_k)).to_pandas()
    for sym, grp in dk.groupby('symbol'):
        last = grp.sort_values('as_of_ts_ms').iloc[-1]
        close_by_sym_date[sym][d_str] = float(last['close'])
    if p_o.exists():
        do = pq.read_table(str(p_o)).to_pandas()
        for sym in fw:
            sk = dk[dk['symbol'] == sym]
            so = do[do['symbol'] == sym]
            res = compute_h2_prime(sk, so)
            if not math.isnan(res['h2r']):
                h2r_by_sym_date[sym][d_str] = res['h2r']

print(f'  h2r symbols: {len(h2r_by_sym_date)} · close symbols: {len(close_by_sym_date)}')


# ═════ B1 · h2r trước D_cross đích danh ═════
print('\n' + '=' * 78)
print('B1 · h2r TRƯỚC D_cross đích danh')
print('=' * 78)

KNOWN_U0 = {
    'BTR':    ['2026-08-12'],
    'BULLA':  ['2026-07-16'],
    'UAI':    ['2026-07-07'],
}

# Detect crosses for other proven tokens automatically
for token in ['LIGHT', 'SOPH', 'BROCCOLIF3B', 'AKE', 'HEMI', 'ON', 'CAP', 'PROM', 'LOBSTER']:
    perp = f'{token}USDT'
    if token == 'BROCCOLIF3B': perp = 'BROCCOLIF3BUSDT'
    detected = _detect_u0_crosses(perp)
    if detected:
        KNOWN_U0[token] = detected

print(f'\n  Total tokens with U0 dates: {len(KNOWN_U0)}')
print(f'\n  {"Token":15s} {"D_cross":12s} {"h2r@D-14":>10s} {"D-7":>8s} {"D-3":>8s} {"D-1":>8s}')
print('  ' + '-' * 70)
for token, dates in sorted(KNOWN_U0.items()):
    perp = f'{token}USDT'
    for d_cross in dates:
        d = datetime.strptime(d_cross, '%Y-%m-%d').date()
        vals = []
        for offset in [-14, -7, -3, -1]:
            d_lookup = (d + timedelta(days=offset)).isoformat()
            h = h2r_by_sym_date.get(perp, {}).get(d_lookup)
            vals.append(f'{h:8.2f}' if h is not None else '     N/A')
        print(f'  {token:15s} {d_cross:12s} ' + '  '.join(vals))


# ═════ B2 · h2r ≥ q90 → U0 trong 30d ═════
print('\n' + '=' * 78)
print('B2 · h2r ≥ q90 (4.135) → U0 trong 30d · freshwatch cohort')
print('=' * 78)

# Detect all U0 crosses in fw · store by date
all_u0_by_sym_date = defaultdict(set)  # sym → set of D_cross dates
for sym in fw:
    for d_cross in _detect_u0_crosses(sym):
        all_u0_by_sym_date[sym].add(d_cross)

total_u0 = sum(len(v) for v in all_u0_by_sym_date.values())
n_syms_with_u0 = sum(1 for v in all_u0_by_sym_date.values() if v)
print(f'\n  Total U0 crosses detected in fw: {total_u0} events · {n_syms_with_u0} distinct symbols')

# Build fw table (sym, date, h2r) 30 đêm gần
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]
n_hi_fires = 0
n_hi_with_u0 = 0
n_all_pairs = 0
n_all_with_u0 = 0
Q90 = 4.135

for sym in fw:
    for d_str, h2r in h2r_by_sym_date.get(sym, {}).items():
        # limit to fires within LAST_30D window
        fd = datetime.strptime(d_str, '%Y-%m-%d').date()
        if fd not in LAST_30D: continue
        n_all_pairs += 1
        # Check any U0 in next 30d
        u0_dates = all_u0_by_sym_date.get(sym, set())
        has_u0 = any(
            0 < (datetime.strptime(u0, '%Y-%m-%d').date() - fd).days <= 30
            for u0 in u0_dates
        )
        if has_u0: n_all_with_u0 += 1
        if h2r >= Q90:
            n_hi_fires += 1
            if has_u0: n_hi_with_u0 += 1

prec_hi = n_hi_with_u0/n_hi_fires*100 if n_hi_fires else 0
base_u0 = n_all_with_u0/n_all_pairs*100 if n_all_pairs else 0
print(f'\n  h2r ≥ q90 (4.135) fires: {n_hi_fires}')
print(f'  trong đó có U0 trong 30d: {n_hi_with_u0} · precision = {prec_hi:.2f}%')
print(f'  Nền: token-nights BẤT KỲ có U0 trong 30d = {n_all_with_u0}/{n_all_pairs} = {base_u0:.2f}%')
lift_u0 = prec_hi/base_u0 if base_u0 else 0
print(f'  Lift: {lift_u0:.2f}x' + (' ★ ≥2x có tin' if lift_u0 >= 2 else ' YẾU'))


# ═════ B3 · 3-step chain: h2r cao → U0 → ×2 ═════
print('\n' + '=' * 78)
print('B3 · Chain: h2r ≥ q90 → U0 trong 30d → ×2 trong 30d sau U0')
print('=' * 78)

def _fw_max(sym, d_str, days=30):
    c0 = close_by_sym_date.get(sym, {}).get(d_str)
    if not c0 or c0 <= 0: return None
    fd = datetime.strptime(d_str, '%Y-%m-%d').date()
    mc = c0
    for k in range(1, days+1):
        c = close_by_sym_date.get(sym, {}).get((fd + timedelta(days=k)).isoformat())
        if c and c > mc: mc = c
    return mc / c0

n_chain = 0
n_chain_x2 = 0
chain_cases = []
for sym in fw:
    for d_str, h2r in h2r_by_sym_date.get(sym, {}).items():
        if h2r < Q90: continue
        fd = datetime.strptime(d_str, '%Y-%m-%d').date()
        if fd not in LAST_30D: continue
        u0_dates = all_u0_by_sym_date.get(sym, set())
        for u0 in u0_dates:
            u0d = datetime.strptime(u0, '%Y-%m-%d').date()
            if 0 < (u0d - fd).days <= 30:
                # chain OK. Now check ×2 from U0 in 30d
                ratio = _fw_max(sym, u0, 30)
                if ratio is not None:
                    n_chain += 1
                    if ratio >= 2.0:
                        n_chain_x2 += 1
                        chain_cases.append((sym, d_str, h2r, u0, ratio))

prec_chain = n_chain_x2/n_chain*100 if n_chain else 0
print(f'\n  Full chain (h2r≥q90 → U0 trong 30d → ×2 kiểm được): {n_chain}')
print(f'  Có ×2: {n_chain_x2} · precision = {prec_chain:.2f}%')
print(f'  Nền freshwatch ×2 (any): 4.88%')
lift_chain = prec_chain/4.88 if 4.88 else 0
print(f'  Lift: {lift_chain:.2f}x' + (' ★ ≥2x thesis xác nhận' if lift_chain >= 2 else ' YẾU'))

if chain_cases:
    chain_cases.sort(key=lambda x: -x[4])
    print(f'\n  Top chain hits:')
    for c in chain_cases[:15]:
        print(f'    {c[0]:15s} h2r_fire={c[1]}(h={c[2]:.2f}) → U0={c[3]} → ratio={c[4]:.2f}x')


# ═════ B4 · A4 REDO with D_cross ═════
print('\n' + '=' * 78)
print('B4 · h2r quanh D_cross (thay D0) cho 13 proven')
print('=' * 78)

PROVEN13 = ['AKE','BANK','BTR','BTW','BULLA','CAP','CYS','HEMI','LOBSTER','ON','PROM','TUT','UAI']
COUNTER2 = ['APR','SOPH']
Q95 = 6.364
Q90_2 = 4.135

print(f'\n  {"Token":9s} {"D_cross":12s} {"h2r@-14":>9s} {"-7":>7s} {"-3":>7s} {"-1":>7s} {"D":>7s} {"vùng":>15s}')
print('  ' + '-' * 82)

for token in PROVEN13 + COUNTER2:
    perp = 'LOBSTER' if token == 'LOBSTER' else token
    perp_sym = 'PROMUSDT' if token == 'PROM' else f'{token}USDT'
    if token == 'LOBSTER': perp_sym = '龙虾USDT'
    crosses = KNOWN_U0.get(token, [])
    if not crosses:
        crosses = _detect_u0_crosses(perp_sym)
    if not crosses:
        print(f'  {token:9s} {"N/A":12s} — không detect được U0 cross')
        continue

    for d_cross in crosses[:2]:
        d = datetime.strptime(d_cross, '%Y-%m-%d').date()
        vals = []
        max_h = 0
        for offset in [-14, -7, -3, -1, 0]:
            d_lookup = (d + timedelta(days=offset)).isoformat()
            h = h2r_by_sym_date.get(perp_sym, {}).get(d_lookup)
            vals.append(f'{h:7.2f}' if h is not None else '    N/A')
            if h is not None and h > max_h: max_h = h
        hi = '★>q95' if max_h >= Q95 else ('q90-q95' if max_h >= Q90_2 else '<q90')
        print(f'  {token:9s} {d_cross:12s} ' + ' '.join(vals) + f'  {hi:>13s}')

print('\n' + '=' * 78)
