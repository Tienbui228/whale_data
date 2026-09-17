"""C1-C4 · Backfill h2prime từ 05-18 cho 139 freshwatch · READ-ONLY."""
from __future__ import annotations
import sys, os, csv, json, math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()
START = datetime(2026, 5, 18).date()   # oi_hist_1h earliest
DAYS_BACK = (TODAY - START).days
print(f'[BACKFILL WINDOW] {START} → {TODAY} · {DAYS_BACK} days')

with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}

# Load freshwatch_daily multi-month (05..09)
def _load_fw_daily():
    store = defaultdict(dict)
    for month in ['2026-05', '2026-06', '2026-07', '2026-08', '2026-09']:
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

fw_daily = _load_fw_daily()
print(f'  fw_daily symbols: {len(fw_daily)}')
# Earliest date in fw_daily
all_dates = set()
for sym_data in fw_daily.values():
    all_dates.update(sym_data.keys())
if all_dates:
    dsort = sorted(all_dates)
    print(f'  fw_daily date range: {dsort[0]} → {dsort[-1]}')


def _div_avg3(sym_data, target_d_str):
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


def _detect_u0(sym):
    """Return list of D_cross dates."""
    sym_data = fw_daily.get(sym, {})
    if not sym_data: return []
    dates_sorted = sorted(sym_data.keys())
    if len(dates_sorted) < 10: return []
    crosses = []
    for i in range(3, len(dates_sorted)):
        d_t = dates_sorted[i]
        div_t = _div_avg3(sym_data, d_t)
        if div_t is None or div_t < 0.7: continue
        for lookback in range(1, 4):
            if i - lookback < 0: continue
            d_prev = dates_sorted[i - lookback]
            div_prev = _div_avg3(sym_data, d_prev)
            if div_prev is None: continue
            if div_prev <= 0.5:
                acc_t = sym_data[d_t]['acc_r']
                acc_prev = sym_data[d_prev]['acc_r']
                if acc_prev > 0 and (acc_prev - acc_t) / acc_prev >= 0.30:
                    if not crosses or (datetime.strptime(d_t, '%Y-%m-%d').date() -
                                       datetime.strptime(crosses[-1], '%Y-%m-%d').date()).days > 7:
                        crosses.append(d_t)
                    break
    return crosses


# ═════ Compute h2r for fw × all dates in backfill window ═════
import pyarrow.parquet as pq
import pandas as pd

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
    if len(neg) < 3 or len(pos) < 3: return empty
    rate_neg = neg[neg['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / len(neg)
    rate_pos = pos[pos['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / len(pos)
    if rate_pos <= 0 or rate_neg <= 0: return empty
    return {"h2r": rate_neg/rate_pos}


ALL_DATES = [START + timedelta(days=i) for i in range(DAYS_BACK)]
print(f'[COMPUTE h2r for {len(fw)} freshwatch × {len(ALL_DATES)} dates]')

h2r_by_sym_date = defaultdict(dict)
close_by_sym_date = defaultdict(dict)
n_processed = 0
for d in ALL_DATES:
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
    n_processed += 1

n_records = sum(len(v) for v in h2r_by_sym_date.values())
print(f'  processed dates: {n_processed}')
print(f'  h2r records (fw): {n_records}')

# ═════ C1 · Detect U0 for freshwatch → count proven with D_cross now ═════
print('\n' + '=' * 78)
print('C1 · U0 coverage cho freshwatch với window rộng')
print('=' * 78)

all_u0 = defaultdict(list)
for sym in fw:
    for d in _detect_u0(sym):
        all_u0[sym].append(d)

total_u0 = sum(len(v) for v in all_u0.values())
n_syms_with = sum(1 for v in all_u0.values() if v)
print(f'\n  U0 crosses detected in fw: {total_u0} events · {n_syms_with}/139 syms')

# Check 15 case
PROVEN13 = ['AKE','BANK','BTR','BTW','BULLA','CAP','CYS','HEMI','LOBSTER','ON','PROM','TUT','UAI']
COUNTER2 = ['APR','SOPH']
COUNTER_NEG = ['LIGHT','BROCCOLIF3B']   # additional negative controls

print(f'\n  Proven + counter · U0 detected:')
def _perp(t):
    if t == 'LOBSTER': return '龙虾USDT'
    return f'{t}USDT'
for token in PROVEN13 + COUNTER2 + COUNTER_NEG:
    perp = _perp(token)
    dates = all_u0.get(perp, [])
    in_fw = perp in fw_daily
    in_h2r = perp in h2r_by_sym_date
    n_h2r_rec = len(h2r_by_sym_date.get(perp, {}))
    print(f'    {token:12s} in_fw_daily={str(in_fw):5s} · U0_events={len(dates)} · h2r_records={n_h2r_rec} · dates={dates[:3]}')


# ═════ C2 · B2/B3 lại với window mới ═════
print('\n' + '=' * 78)
print('C2 · B2/B3 relative với window rộng')
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

Q90 = 4.135
n_hi = 0
n_hi_u0 = 0
n_all = 0
n_all_u0 = 0
for sym in fw:
    for d_str, h2r in h2r_by_sym_date.get(sym, {}).items():
        n_all += 1
        fd = datetime.strptime(d_str, '%Y-%m-%d').date()
        u0_dates = all_u0.get(sym, [])
        has_u0 = any(
            0 < (datetime.strptime(u0, '%Y-%m-%d').date() - fd).days <= 30
            for u0 in u0_dates
        )
        if has_u0: n_all_u0 += 1
        if h2r >= Q90:
            n_hi += 1
            if has_u0: n_hi_u0 += 1

print(f'\nB2 · h2r ≥ q90 → U0 trong 30d:')
prec = n_hi_u0/n_hi*100 if n_hi else 0
base = n_all_u0/n_all*100 if n_all else 0
print(f'  h2r ≥ q90 fires: {n_hi}')
print(f'  → U0 trong 30d: {n_hi_u0} · precision {prec:.2f}%')
print(f'  Nền U0 rate: {n_all_u0}/{n_all} = {base:.2f}%')
lift = prec/base if base else 0
print(f'  Lift: {lift:.2f}x')
if n_hi_u0 < 40:
    print(f'  ⚠ THIẾU MẪU (n_hi_u0={n_hi_u0} < 40) — không kết luận')

# B3 chain
n_chain = 0
n_chain_x2 = 0
chain_cases = []
for sym in fw:
    for d_str, h2r in h2r_by_sym_date.get(sym, {}).items():
        if h2r < Q90: continue
        fd = datetime.strptime(d_str, '%Y-%m-%d').date()
        u0_dates = all_u0.get(sym, [])
        for u0 in u0_dates:
            u0d = datetime.strptime(u0, '%Y-%m-%d').date()
            if 0 < (u0d - fd).days <= 30:
                ratio = _fw_max(sym, u0, 30)
                if ratio is not None:
                    n_chain += 1
                    if ratio >= 2.0:
                        n_chain_x2 += 1
                        chain_cases.append((sym, d_str, h2r, u0, ratio))

print(f'\nB3 · Chain h2r→U0→×2:')
prec_ch = n_chain_x2/n_chain*100 if n_chain else 0
print(f'  n chain: {n_chain}')
print(f'  n ×2: {n_chain_x2}')
if n_chain < 40:
    print(f'  ⚠ THIẾU MẪU (n_chain={n_chain} < 40) — không kết luận về precision {prec_ch:.2f}%')
else:
    print(f'  precision: {prec_ch:.2f}% · nền 4.88%')
    print(f'  Lift: {prec_ch/4.88:.2f}x')
if chain_cases:
    for c in chain_cases[:10]:
        print(f'    {c[0]:15s} h2r_fire={c[1]}(h={c[2]:.2f}) → U0={c[3]} → ratio={c[4]:.2f}x')


# ═════ C3 · QUỸ ĐẠO h2r [D-10, D-2] / [D-1, D+1] ═════
print('\n' + '=' * 78)
print('C3 · QUỸ ĐẠO · h2r_max[D-10, D-2] / h2r_mean[D-1, D+1]')
print('=' * 78)

def _trajectory(sym, d_cross):
    """h2r_max[-10..-2] / h2r_mean[-1..+1]"""
    d = datetime.strptime(d_cross, '%Y-%m-%d').date()
    h_dict = h2r_by_sym_date.get(sym, {})
    prev_vals = []
    for offset in range(-10, -1):
        h = h_dict.get((d + timedelta(days=offset)).isoformat())
        if h is not None: prev_vals.append(h)
    peak_vals = []
    for offset in range(-1, 2):
        h = h_dict.get((d + timedelta(days=offset)).isoformat())
        if h is not None: peak_vals.append(h)
    if not prev_vals or not peak_vals: return None
    prev_max = max(prev_vals)
    peak_mean = sum(peak_vals) / len(peak_vals)
    if peak_mean <= 0: return None
    return prev_max / peak_mean

# Positive group: proven with U0 detected
POS_TOKENS = ['BTR','BULLA','UAI','AKE','ON','HEMI','CAP','CYS','LOBSTER','PROM','TUT','BTW','BANK']
NEG_TOKENS = ['SOPH','LIGHT','BROCCOLIF3B','APR']

def _analyze_group(tokens, label):
    print(f'\n  [{label}]')
    print(f'  {"token":12s} {"D_cross":12s} {"prev_max":>10s} {"peak_mean":>10s} {"ratio":>8s}')
    ratios = []
    for token in tokens:
        perp = _perp(token)
        crosses = all_u0.get(perp, [])
        for c in crosses:
            r = _trajectory(perp, c)
            if r is None:
                continue
            # get raw values for print
            d = datetime.strptime(c, '%Y-%m-%d').date()
            h_dict = h2r_by_sym_date.get(perp, {})
            prev = [h_dict.get((d+timedelta(days=o)).isoformat()) for o in range(-10,-1)]
            prev = [x for x in prev if x is not None]
            peak = [h_dict.get((d+timedelta(days=o)).isoformat()) for o in range(-1,2)]
            peak = [x for x in peak if x is not None]
            pmax = max(prev) if prev else 0
            pmean = sum(peak)/len(peak) if peak else 0
            print(f'  {token:12s} {c:12s} {pmax:>10.2f} {pmean:>10.2f} {r:>8.2f}')
            ratios.append(r)
    if ratios:
        ratios.sort()
        p50 = ratios[len(ratios)//2]
        print(f'  → n={len(ratios)} · median ratio={p50:.2f} · mean={sum(ratios)/len(ratios):.2f}')
    return ratios

pos_ratios = _analyze_group(POS_TOKENS, 'POSITIVE (proven)')
neg_ratios = _analyze_group(NEG_TOKENS, 'NEGATIVE (counter/đối chứng)')


# ═════ C4 · Baseline · same trajectory ratio cho token-ngày KHÔNG U0 ═════
print('\n' + '=' * 78)
print('C4 · BASELINE trajectory ratio · token-ngày không có U0 (random date)')
print('=' * 78)

import random
random.seed(42)
u0_set_by_sym = {sym: set(dates) for sym, dates in all_u0.items()}
baseline_ratios = []
# Sample 500 random (sym, date) not-in-U0
tries = 0
while len(baseline_ratios) < 500 and tries < 20000:
    tries += 1
    sym = random.choice(list(fw))
    dates_avail = sorted(h2r_by_sym_date.get(sym, {}).keys())
    if len(dates_avail) < 15: continue
    d_str = random.choice(dates_avail[10:-5])  # need window
    if d_str in u0_set_by_sym.get(sym, set()): continue
    r = _trajectory(sym, d_str)
    if r is not None:
        baseline_ratios.append(r)

print(f'\n  baseline n={len(baseline_ratios)} (random non-U0 token-nights)')
if baseline_ratios:
    baseline_ratios.sort()
    p25 = baseline_ratios[int(len(baseline_ratios)*0.25)]
    p50 = baseline_ratios[len(baseline_ratios)//2]
    p75 = baseline_ratios[int(len(baseline_ratios)*0.75)]
    mean = sum(baseline_ratios)/len(baseline_ratios)
    print(f'  quantiles: p25={p25:.2f} · p50={p50:.2f} · p75={p75:.2f} · mean={mean:.2f}')

# Summary compare
print(f'\n[COMPARE]')
if pos_ratios: print(f'  POSITIVE (n={len(pos_ratios)}): median {sorted(pos_ratios)[len(pos_ratios)//2]:.2f}')
if neg_ratios: print(f'  NEGATIVE (n={len(neg_ratios)}): median {sorted(neg_ratios)[len(neg_ratios)//2]:.2f}')
if baseline_ratios: print(f'  BASELINE (n={len(baseline_ratios)}): median {sorted(baseline_ratios)[len(baseline_ratios)//2]:.2f}')

# Sanity: distributions overlap or not?
if pos_ratios and baseline_ratios:
    n_pos_above_base_p75 = sum(1 for r in pos_ratios if r > sorted(baseline_ratios)[int(len(baseline_ratios)*0.75)])
    print(f'  POS above baseline p75: {n_pos_above_base_p75}/{len(pos_ratios)}')

print('\n' + '=' * 78)
