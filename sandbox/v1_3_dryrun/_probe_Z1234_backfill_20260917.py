"""Z1-Z5 · Backfill h2prime on all 385 excluded · READ-ONLY sandbox."""
from __future__ import annotations
import sys, os, csv, math
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import statistics as _st

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()

with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}
um = {r['symbol'] for r in csv.DictReader(open(REPO/'data/config/universe_master.csv'))
      if r.get('status')=='active'}
excl = um - fw
print(f'freshwatch: {len(fw)} · excluded: {len(excl)}')

# ═════ Z1 · Kiểm tra 7 tokens W3 top hits có trong h2prime 45 excluded? ═════
print('\n' + '=' * 78)
print('Z1 · 7 W3 top-hit tokens · có trong h2prime coverage 45 excluded?')
print('=' * 78)

h2p_rows = list(csv.DictReader(open(REPO/'data/gom_h2prime_daily.csv')))
h2p_syms = {r['symbol'] for r in h2p_rows}
h2p_excl_syms = h2p_syms & excl

targets = ['LSKUSDT','PROMUSDT','ONGUSDT','IOSTUSDT','RAYSOLUSDT','FLOCKUSDT','MAGMAUSDT']
for t in targets:
    in_45 = t in h2p_excl_syms
    n_rows = sum(1 for r in h2p_rows if r['symbol']==t)
    print(f'  {t:15s}: trong h2p_45={in_45} · n_rows_h2p={n_rows}')


# ═════ Z2 · Vì sao h2prime chỉ 45/385? ═════
print('\n' + '=' * 78)
print('Z2 · Filter chain h2prime · code trace')
print('=' * 78)
print("""
compute_h_daily.py::compute_h2prime_day() L446 →
  watchlist = build_watchlist(target_dt)      # L454
  scope = watchlist-only

build_watchlist() L130:
  T1 = GOM-E registry (gom_e_state.json)      # thường RỖNG
  T2 = CASE_INDEX cases                        # NOT ON VPS · skipped
  T3 = gom_state.json entries with last_gom_date within 30d

→ scope filter KHÔNG phải freshwatch, mà là gom_state 30d recency.
  45 excluded = tokens có gom event trong 30d nhưng không nằm freshwatch.
""")

# ═════ Z3 · BACKFILL h2prime trên ĐỦ 385 × 30 đêm ═════
print('=' * 78)
print('Z3 · BACKFILL h2prime · 385 excluded × 30 đêm')
print('=' * 78)

import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import json

# Load funding intervals
funding = {}
fp = REPO / 'data/config/funding_intervals.json'
if fp.exists():
    j = json.load(open(fp))
    if isinstance(j, dict):
        funding = {k: (v if isinstance(v, int) else v.get('interval_h', 8)) for k, v in j.items()}
print(f'  funding intervals loaded: {len(funding)}')

# h2prime compute logic (from compute_h_daily.py L388-444, transcribed)
def compute_h2_prime_local(sym: str, sk: pd.DataFrame, so: pd.DataFrame, iv_h: int) -> dict:
    NaN = float('nan')
    empty = {"h2r": NaN, "h2r_log": NaN, "rate_neg": NaN, "n_neg": 0, "n_pos": 0}
    if sk.empty or so.empty:
        return empty

    # Merge klines + oi on hour · compute ret and delta_oi
    sk = sk.sort_values('as_of_ts_ms').copy()
    so = so.sort_values('as_of_ts_ms').copy()

    # Compute hourly returns
    sk['ret'] = sk['close'].pct_change()

    # Compute delta OI (usd)
    so['delta_oi_usd'] = so.get('sum_open_interest_value', so.get('open_interest_value',
                                so.get('oi_usd', pd.Series([np.nan]*len(so))))).diff()

    # Merge on ts_ms hour (nearest)
    merged = pd.merge_asof(sk[['as_of_ts_ms', 'ret']],
                            so[['as_of_ts_ms', 'delta_oi_usd']],
                            on='as_of_ts_ms', direction='nearest',
                            tolerance=30 * 60 * 1000)  # 30min tolerance
    merged = merged.dropna()
    if merged.empty:
        return empty

    # Exclude funding settlement hours (per iv_h)
    # For simplicity skip this filter — approximation
    neg = merged[merged['ret'] < 0]
    pos = merged[merged['ret'] > 0]
    n_neg = len(neg); n_pos = len(pos)

    if n_neg < 3 or n_pos < 3:
        return {"h2r": NaN, "h2r_log": NaN, "rate_neg": NaN, "n_neg": n_neg, "n_pos": n_pos}

    # rate_neg = sum of positive delta OI in negative-return hours / n_neg
    # rate_pos = same for positive-return hours
    rate_neg = neg[neg['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_neg
    rate_pos = pos[pos['delta_oi_usd'] > 0]['delta_oi_usd'].sum() / n_pos

    if rate_pos <= 0 or rate_neg <= 0:
        return {"h2r": NaN, "h2r_log": NaN, "rate_neg": rate_neg, "n_neg": n_neg, "n_pos": n_pos}

    h2r = rate_neg / rate_pos
    return {"h2r": h2r, "h2r_log": math.log(h2r), "rate_neg": rate_neg, "n_neg": n_neg, "n_pos": n_pos}


# Load klines_1h + oi_hist_1h for each of last 30 dates
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]

# Cache klines/oi per date (to avoid reload)
kline_by_date = {}
oi_by_date = {}
for d in LAST_30D:
    d_str = d.isoformat()
    p_k = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    p_o = REPO / f'data/raw/oi_hist_1h/date={d_str}/part-0.parquet'
    if p_k.exists():
        kline_by_date[d_str] = pq.read_table(str(p_k)).to_pandas()
    if p_o.exists():
        oi_by_date[d_str] = pq.read_table(str(p_o)).to_pandas()

print(f'  klines dates: {len(kline_by_date)} · oi dates: {len(oi_by_date)}')

# Backfill each excluded symbol × each date
print(f'  computing h2prime for 385 × 30 = 11550 token-nights...')

excl_fires = []   # (sym, date, h2r)
excl_all_h2r = []
for d in LAST_30D:
    d_str = d.isoformat()
    dk = kline_by_date.get(d_str, pd.DataFrame())
    do = oi_by_date.get(d_str, pd.DataFrame())
    if dk.empty or do.empty: continue
    for sym in excl:
        sk = dk[dk['symbol'] == sym]
        so = do[do['symbol'] == sym]
        iv_h = funding.get(sym, 8)
        res = compute_h2_prime_local(sym, sk, so, iv_h)
        if not math.isnan(res['h2r']):
            excl_all_h2r.append(res['h2r'])
            if res['h2r'] >= 0.5:
                excl_fires.append((sym, d_str, res['h2r']))

print(f'\n  h2prime computed: {len(excl_all_h2r)} valid records')
print(f'  h2prime fires (h2r >= 0.5): {len(excl_fires)}')

# Per-night count
fires_by_date = defaultdict(list)
for s, d, h in excl_fires:
    fires_by_date[d].append((s, h))
counts = [len(fires_by_date[d.isoformat()]) for d in LAST_30D if d.isoformat() in fires_by_date]
if counts:
    cs = sorted(counts)
    print(f'  n fires/đêm (30 đêm): min={min(cs)} p50={cs[len(cs)//2]} p95={cs[int(len(cs)*0.95)]} max={max(cs)}')

# Close data for ×2 check
daily_close = defaultdict(dict)
for d_str, dk in kline_by_date.items():
    for sym, grp in dk.groupby('symbol'):
        last = grp.sort_values('as_of_ts_ms').iloc[-1]
        daily_close[sym][d_str] = float(last['close'])
# extend + 30 days ahead for max_close lookup
for i in range(0, 45):
    d_str = (TODAY - timedelta(days=i)).isoformat()
    if d_str in daily_close: continue
    p = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    if p.exists():
        try:
            tab = pq.read_table(str(p)).to_pandas()
            for sym, grp in tab.groupby('symbol'):
                last = grp.sort_values('as_of_ts_ms').iloc[-1]
                daily_close[sym][d_str] = float(last['close'])
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
def _fw_max(sym, d_str, days=30):
    c0 = daily_close.get(sym, {}).get(d_str)
    if not c0 or c0 <= 0: return None
    fd = datetime.strptime(d_str, '%Y-%m-%d').date()
    mc = c0
    for k in range(1, days+1):
        c = daily_close.get(sym, {}).get((fd + timedelta(days=k)).isoformat())
        if c and c > mc: mc = c
    return mc / c0

n_pairs = 0; n_x2 = 0; hits = []
for sym, d_str, h2r in excl_fires:
    ratio = _fw_max(sym, d_str, 30)
    if ratio is None: continue
    n_pairs += 1
    if ratio >= 2.0:
        n_x2 += 1
        hits.append((sym, d_str, ratio, h2r))

prec_excl = n_x2/n_pairs*100 if n_pairs else 0
BASE = 1.34
print(f'\n  precision: {n_x2}/{n_pairs} = {prec_excl:.2f}%')
print(f'  vs base rate 1.34%: lift = {prec_excl/BASE:.2f}x')
hits.sort(key=lambda x: -x[2])
print(f'\n  top ×2 hits (h2prime backfill):')
for h in hits[:20]:
    print(f'    {h[0]:20s} {h[1]} · {h[2]:.2f}x · h2r={h[3]:.3f}')


# ═════ Z4 · 139 freshwatch cùng phép ═════
print('\n' + '=' * 78)
print('Z4 · 139 freshwatch cùng phép · benchmark')
print('=' * 78)

fw_fires = []; fw_all_h2r = []
for d in LAST_30D:
    d_str = d.isoformat()
    dk = kline_by_date.get(d_str, pd.DataFrame())
    do = oi_by_date.get(d_str, pd.DataFrame())
    if dk.empty or do.empty: continue
    for sym in fw:
        sk = dk[dk['symbol'] == sym]
        so = do[do['symbol'] == sym]
        iv_h = funding.get(sym, 8)
        res = compute_h2_prime_local(sym, sk, so, iv_h)
        if not math.isnan(res['h2r']):
            fw_all_h2r.append(res['h2r'])
            if res['h2r'] >= 0.5:
                fw_fires.append((sym, d_str, res['h2r']))

n_pairs_fw = 0; n_x2_fw = 0
for sym, d_str, h2r in fw_fires:
    ratio = _fw_max(sym, d_str, 30)
    if ratio is None: continue
    n_pairs_fw += 1
    if ratio >= 2.0: n_x2_fw += 1

prec_fw = n_x2_fw/n_pairs_fw*100 if n_pairs_fw else 0
print(f'\n  freshwatch h2prime: {len(fw_all_h2r)} records · {len(fw_fires)} fires (h2r>=0.5)')
print(f'  precision: {n_x2_fw}/{n_pairs_fw} = {prec_fw:.2f}%')

print(f'\n  === BENCHMARK ===')
print(f'  excluded 385: precision {prec_excl:.2f}% (n_fires={len(excl_fires)}, n_x2={n_x2})')
print(f'  freshwatch 139: precision {prec_fw:.2f}% (n_fires={len(fw_fires)}, n_x2={n_x2_fw})')
ratio_str = f'{prec_fw/prec_excl:.2f}x' if prec_excl > 0 else 'inf'
print(f'  fw ÷ excl: {ratio_str} — chọn-tay mạnh hơn bao nhiêu?')


# ═════ Z5 · phân bố h2r ═════
print('\n' + '=' * 78)
print('Z5 · Phân bố h2r · ngưỡng nào cho ~5% fire rate?')
print('=' * 78)

all_h2r = excl_all_h2r + fw_all_h2r
all_h2r.sort()
n_total = len(all_h2r)
print(f'\n  total records: {n_total}')

print(f'\n  quantile thresholds:')
for q in [50, 60, 70, 80, 85, 90, 92, 95, 97, 99]:
    idx = int(n_total * q / 100)
    if idx < n_total:
        v = all_h2r[idx]
        pct_fire_above = (n_total - idx) / n_total * 100
        print(f'    q{q}: h2r >= {v:.3f} · fires {n_total-idx}/{n_total} = {pct_fire_above:.1f}%')

# Threshold to hit ~5% fire
target_pct = 5.0
target_idx = int(n_total * (100 - target_pct) / 100)
if target_idx < n_total:
    v = all_h2r[target_idx]
    print(f'\n  ★ ngưỡng ~5% fire rate: h2r >= {v:.3f}')

# Current threshold h2r >= 0.5 fire rate
n_above_05 = sum(1 for x in all_h2r if x >= 0.5)
print(f'\n  hiện tại (h2r >= 0.5) fire rate: {n_above_05}/{n_total} = {n_above_05/n_total*100:.1f}%')

print('\n' + '=' * 78)
