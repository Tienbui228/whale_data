"""W1-W4 · Đo tải nếu mở universe sang toàn perp · READ-ONLY.

Chạy trên VPS. Dùng shadow signals làm proxy 'vào sổ':
  A · vol spike: quote_vol[D] > 3 × median(D-15:D-1)
  B · OI surge:  oi[D] > 1.5 × oi[D-14]
  C · taker imbalance: mean(buy_sell_ratio 24h) > 2.0 hoặc < 0.5

Bất kỳ A/B/C fire = 'vào sổ' đêm đó.
"""
from __future__ import annotations
import sys, os, json, csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import statistics as _st

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]

with open(REPO/'data/config/freshwatch_symbols.txt', encoding='utf-8') as f:
    fw_syms = {l.strip() for l in f if l.strip()}
um = list(csv.DictReader(open(REPO/'data/config/universe_master.csv', encoding='utf-8')))
um_active = {r['symbol'] for r in um if r.get('status') == 'active'}
excluded = um_active - fw_syms
print(f'perp_active: {len(um_active)} · freshwatch: {len(fw_syms)} · excluded 385: {len(excluded)}')

import pyarrow.parquet as pq
import math as _m


def _load_klines_45d():
    """Load klines_1h 45d, aggregate to daily quote_vol per symbol."""
    daily_vol = defaultdict(lambda: defaultdict(float))   # sym → date → quote_vol_sum
    daily_close = defaultdict(dict)                         # sym → date → close_at_00
    for i in range(1, 46):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/klines_1h/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for sym, grp in tab.groupby('symbol'):
            daily_vol[sym][d] = float(grp['quote_volume'].sum())
            # last hour close = daily close (approximation)
            last = grp.sort_values('as_of_ts_ms').iloc[-1]
            daily_close[sym][d] = float(last['close'])
    return daily_vol, daily_close


def _load_oi_45d():
    daily_oi = defaultdict(dict)
    for i in range(1, 46):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/oi_hist_1d/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for _, r in tab.iterrows():
            sym = str(r['symbol'])
            oi = None
            for k in ('sum_open_interest_value', 'open_interest_value', 'oi_usd', 'oi_value'):
                if k in tab.columns:
                    oi = float(r[k])
                    break
            if oi is not None and oi > 0:
                daily_oi[sym][d] = oi
    return daily_oi


def _load_taker_ratio_30d():
    """Aggregate hourly buy_sell_ratio to daily mean."""
    daily_ratio = defaultdict(dict)
    for i in range(1, 31):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/taker_ratio_1h/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for sym, grp in tab.groupby('symbol'):
            r = grp['buy_sell_ratio'].mean()
            if not _m.isnan(r): daily_ratio[sym][d] = float(r)
    return daily_ratio


print('\n[LOAD 45d klines + oi + 30d taker · ~2 min]')
daily_vol, daily_close = _load_klines_45d()
print(f'  klines symbols loaded: {len(daily_vol)}')
daily_oi = _load_oi_45d()
print(f'  oi symbols loaded: {len(daily_oi)}')
daily_ratio = _load_taker_ratio_30d()
print(f'  taker symbols loaded: {len(daily_ratio)}')


def _median(xs):
    xs = [x for x in xs if x is not None and not _m.isnan(x) and x > 0]
    if not xs: return None
    return _st.median(xs)


def _shadow_fire(sym, target_date):
    """Return (fire_bool, axes_hit)."""
    d = target_date.isoformat()
    axes = []

    # A · vol spike
    v_today = daily_vol.get(sym, {}).get(d)
    v_hist = [daily_vol[sym].get((target_date - timedelta(days=k)).isoformat())
              for k in range(1, 16)]
    v_med = _median(v_hist)
    if v_today is not None and v_med is not None and v_med > 0 and v_today > 3 * v_med:
        axes.append('VOL')

    # B · OI surge
    oi_today = daily_oi.get(sym, {}).get(d)
    oi_14 = daily_oi.get(sym, {}).get((target_date - timedelta(days=14)).isoformat())
    if oi_today is not None and oi_14 is not None and oi_14 > 0 and oi_today > 1.5 * oi_14:
        axes.append('OI')

    # C · taker imbalance
    r = daily_ratio.get(sym, {}).get(d)
    if r is not None and (r > 2.0 or r < 0.5):
        axes.append('TAKER')

    return (len(axes) > 0, axes)


# ═════ W1 · 385 excluded · 30 đêm ═════
print('\n' + '=' * 78)
print('W1 · 385 excluded tokens · 30 đêm gần · shadow fire count')
print('=' * 78)

fires_by_night = {}
fires_by_sym_date = defaultdict(list)   # sym → list of dates fired
for d in reversed(LAST_30D):
    fired = []
    for sym in excluded:
        ok, axes = _shadow_fire(sym, d)
        if ok:
            fired.append((sym, axes))
            fires_by_sym_date[sym].append(d.isoformat())
    fires_by_night[d.isoformat()] = fired

print(f'\n{"date":12s} {"n_fired":>8s}  sample tokens (first 5)')
print('-' * 78)
counts = []
for d in [x.isoformat() for x in reversed(LAST_30D)]:
    n = len(fires_by_night[d])
    counts.append(n)
    sample = ','.join(s for s, _ in fires_by_night[d][:5])
    print(f'{d:12s} {n:>8d}  {sample}')

counts.sort()
p50 = counts[len(counts)//2]
p95 = counts[int(len(counts)*0.95)] if counts else 0
mx = max(counts) if counts else 0
mn = min(counts) if counts else 0
print(f'\nSummary 30 đêm · min={mn} · p50={p50} · p95={p95} · max={mx}')


# ═════ W2 · so 139 chọn-tay ═════
print('\n' + '=' * 78)
print('W2 · So fire-rate: 139 chọn-tay vs 385 chưa-chọn (30 đêm)')
print('=' * 78)

fw_counts = []
excl_counts = counts   # already computed above
fw_fires_by_sym_date = defaultdict(list)
for d in reversed(LAST_30D):
    fw_fired = 0
    for sym in fw_syms:
        ok, axes = _shadow_fire(sym, d)
        if ok:
            fw_fired += 1
            fw_fires_by_sym_date[sym].append(d.isoformat())
    fw_counts.append(fw_fired)

fw_counts_s = sorted(fw_counts)
fw_p50 = fw_counts_s[len(fw_counts_s)//2]
fw_p95 = fw_counts_s[int(len(fw_counts_s)*0.95)] if fw_counts_s else 0
fw_mx = max(fw_counts_s); fw_mn = min(fw_counts_s)

print(f'\nfreshwatch 139: min={fw_mn} · p50={fw_p50} · p95={fw_p95} · max={fw_mx}')
print(f'                sum 30 đêm = {sum(fw_counts)}  · fires/token/đêm = {sum(fw_counts)/(139*30):.3f}')
print(f'excluded 385:   min={mn} · p50={p50} · p95={p95} · max={mx}')
print(f'                sum 30 đêm = {sum(excl_counts)}  · fires/token/đêm = {sum(excl_counts)/(len(excluded)*30):.3f}')

fw_rate = sum(fw_counts)/(139*30) if fw_counts else 0
excl_rate = sum(excl_counts)/(len(excluded)*30) if excl_counts else 0
print(f'\nfw fire-rate ÷ excl fire-rate = {fw_rate/excl_rate:.2f}x' if excl_rate else '')


# ═════ W3 · Signal thật · ×2 trong 30d sau fire ═════
print('\n' + '=' * 78)
print('W3 · Trong 385 · token nào ×2 trong 30d sau đêm fire?')
print('=' * 78)

hits = []
for sym, dates in fires_by_sym_date.items():
    close_by_date = daily_close.get(sym, {})
    if not close_by_date: continue
    for d_str in dates:
        c_fire = close_by_date.get(d_str)
        if not c_fire or c_fire <= 0: continue
        # Check next 30 days (some fall outside window)
        fire_date = datetime.strptime(d_str, '%Y-%m-%d').date()
        max_close = c_fire
        max_date = None
        for k in range(1, 31):
            d2 = (fire_date + timedelta(days=k)).isoformat()
            c2 = close_by_date.get(d2)
            if c2 is not None and c2 > max_close:
                max_close = c2
                max_date = d2
        ratio = max_close / c_fire
        if ratio >= 2.0:
            hits.append((sym, d_str, c_fire, max_close, ratio, max_date))

hits.sort(key=lambda x: -x[4])
print(f'\nn hits ×2 sau fire: {len(hits)}')
print(f'{"sym":20s} {"fire_date":12s} {"c_fire":>10s} {"c_max":>10s} {"ratio":>7s} {"max_date":12s}')
print('-' * 78)
for h in hits[:30]:
    print(f'{h[0]:20s} {h[1]:12s} {h[2]:>10.4g} {h[3]:>10.4g} {h[4]:>7.2f}x {h[5] or "N/A":12s}')

if len(hits) > 30:
    print(f'... + {len(hits)-30} more')


# ═════ W4 · Ước dung lượng master body ═════
print('\n' + '=' * 78)
print('W4 · Ước dung lượng master body nếu mở universe')
print('=' * 78)

# Current 09-14 body: 3666B (from log)
BASELINE_BYTES = 3666
BASELINE_TOKENS = 40   # V1.3 layout: species blocks + XẢ + POST + WATCH tokens

# Assume p50 additional fires per night
avg_new_fires_per_night = sum(counts) / 30
print(f'\navg new fires/đêm từ 385 excluded: {avg_new_fires_per_night:.1f}')

# Line format: `   [B] SYMBOL N-trục (AXES) DATES · ret+X% dd-Y% → PRE\n`
# Avg length ~ 120 chars (measured from real body)
CHARS_PER_LINE = 120

# V1.2 (with TOP_K compression per block, TOP_K=6, tail line ~80 chars):
#   If <=6 fires: N lines
#   If >6: 6 + 1 tail = 7 lines (but tail can be long if many names)
#
# V1.3 LAYOUT-ONLY (no TOP_K per block, render-all): N lines
n_extra = int(avg_new_fires_per_night)

# V1.2 estimate: fires distributed across blocks (say ~4 species blocks)
# per-block avg = n_extra / 4 · if >6 truncate + tail
v12_extra_lines = 0
for _b in range(4):
    per = n_extra / 4
    if per <= 6: v12_extra_lines += per
    else: v12_extra_lines += 7 + len(str(int(per-6))) / 10   # rough
v12_extra_bytes = int(v12_extra_lines * CHARS_PER_LINE)
print(f'\nV1.2 (TOP_K=6 truncate/block): +{v12_extra_lines:.1f} lines · +{v12_extra_bytes}B')

# V1.3 LAYOUT-ONLY (render-all per block)
v13_extra_bytes = n_extra * CHARS_PER_LINE
print(f'V1.3 (render-all, no cap):     +{n_extra} lines · +{v13_extra_bytes}B')

print(f'\nBaseline body: {BASELINE_BYTES}B (~{BASELINE_TOKENS} tokens rendered)')
print(f'V1.2 estimate (mở universe): {BASELINE_BYTES + v12_extra_bytes}B (~{(BASELINE_BYTES+v12_extra_bytes)/1024:.1f} KB)')
print(f'V1.3 estimate (mở universe): {BASELINE_BYTES + v13_extra_bytes}B (~{(BASELINE_BYTES+v13_extra_bytes)/1024:.1f} KB)')

# Telegram message limit: 4096 chars
if BASELINE_BYTES + v13_extra_bytes > 4096:
    print(f'\n⚠ V1.3 render-all vượt Telegram 4096B limit · phải split hoặc trim')
    print(f'  Cần cap TOP_K/block hoặc grand-cap N lines/body')

# p95 (worst-case night)
p95_extra = int(p95)
p95_v13_bytes = BASELINE_BYTES + p95_extra * CHARS_PER_LINE
print(f'\np95 worst-case (n={p95_extra} fires): V1.3 body = {p95_v13_bytes}B ({p95_v13_bytes/1024:.1f}KB)')
print(f'Max worst-case (n={mx} fires): V1.3 body = {BASELINE_BYTES + mx * CHARS_PER_LINE}B ({(BASELINE_BYTES + mx * CHARS_PER_LINE)/1024:.1f}KB)')

print('\n' + '=' * 78)
