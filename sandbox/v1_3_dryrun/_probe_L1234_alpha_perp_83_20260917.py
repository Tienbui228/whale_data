"""L1-L4 · Đo 3 nhóm: fw 139 · Alpha∩perp∉fw 83 · perp-only 302 · READ-ONLY."""
from __future__ import annotations
import sys, os, csv, json, math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()
ALPHA_FILE = Path('/tmp/alpha_list.json')

# Load Alpha
d_alpha = json.load(open(ALPHA_FILE, encoding='utf-8'))
alpha_toks = d_alpha if isinstance(d_alpha, list) else d_alpha.get('data', [])
alpha_by_sym = {t['symbol']: t for t in alpha_toks if t.get('symbol')}
alpha_syms = set(alpha_by_sym.keys())
alpha_perp_syms = {f'{s}USDT' for s in alpha_syms}
print(f'Alpha unique symbols: {len(alpha_syms)} · as USDT: {len(alpha_perp_syms)}')

# Load universe_master
um = list(csv.DictReader(open(REPO/'data/config/universe_master.csv')))
um_active = {r['symbol'] for r in um if r.get('status')=='active'}
print(f'perp active: {len(um_active)}')

# Load freshwatch
with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}
print(f'freshwatch: {len(fw)}')

# Compute 3 cohorts (all in USDT format)
group_a = fw & um_active                             # freshwatch ∩ perp
group_b = (alpha_perp_syms & um_active) - fw         # Alpha ∩ perp, chưa fw
group_c = um_active - alpha_perp_syms - fw           # perp-only, không Alpha

print(f'\n  (a) fw ∩ perp: {len(group_a)}')
print(f'  (b) Alpha∩perp chưa fw: {len(group_b)}')
print(f'  (c) perp-only, không Alpha: {len(group_c)}')


# Load klines_1h close 60d
import pyarrow.parquet as pq
LAST_60D = [(TODAY - timedelta(days=i)) for i in range(1, 61)]
daily_close = defaultdict(dict)
print('\n[LOAD klines_1h close 60d]')
for d in LAST_60D:
    d_str = d.isoformat()
    p = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    if not p.exists(): continue
    tab = pq.read_table(str(p)).to_pandas()
    for sym, grp in tab.groupby('symbol'):
        last = grp.sort_values('as_of_ts_ms').iloc[-1]
        daily_close[sym][d_str] = float(last['close'])
print(f'  symbols loaded: {len(daily_close)}')


def _fw_max_ratio(sym, target_date, days=30):
    d_str = target_date.isoformat()
    c0 = daily_close.get(sym, {}).get(d_str)
    if not c0 or c0 <= 0: return None
    mc = c0
    for k in range(1, days+1):
        c = daily_close.get(sym, {}).get((target_date + timedelta(days=k)).isoformat())
        if c and c > mc: mc = c
    return mc / c0


# ═════ L1 · Base rate ×2 mỗi nhóm ═════
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]

def _base_rate(cohort):
    n_pairs = 0; n_x2 = 0
    for sym in cohort:
        for d in LAST_30D:
            r = _fw_max_ratio(sym, d)
            if r is None: continue
            n_pairs += 1
            if r >= 2.0: n_x2 += 1
    return n_pairs, n_x2

print('\n' + '=' * 78)
print('L1 · ×2/token-ngày trên 3 nhóm · 30 đêm gần')
print('=' * 78)

results_l1 = {}
for label, cohort in [('(a) fw ∩ perp', group_a),
                       ('(b) Alpha∩perp chưa fw', group_b),
                       ('(c) perp-only không Alpha', group_c)]:
    n_pairs, n_x2 = _base_rate(cohort)
    rate = n_x2/n_pairs*100 if n_pairs else 0
    results_l1[label] = (len(cohort), n_pairs, n_x2, rate)
    print(f'  {label:35s}: n_token={len(cohort):>4d} · n_pairs={n_pairs:>6d} · ×2={n_x2:>4d} · rate={rate:>5.2f}%')

print()
# Comparison
a_rate = results_l1['(a) fw ∩ perp'][3]
b_rate = results_l1['(b) Alpha∩perp chưa fw'][3]
c_rate = results_l1['(c) perp-only không Alpha'][3]
print(f'  (b) ÷ (a) = {b_rate/a_rate:.2f}x')
print(f'  (b) ÷ (c) = {b_rate/c_rate:.2f}x' if c_rate > 0 else '  (b) ÷ (c) = N/A')


# ═════ L3 · ">14 days trên CẢ Alpha VÀ perp" ═════
print('\n' + '=' * 78)
print('L3 · Rule ">14 ngày trên CẢ Alpha VÀ perp" · count hôm nay')
print('=' * 78)

# Alpha listing date: từ token-list · listingTime (ms since epoch)
alpha_listings = {}
for sym, tok in alpha_by_sym.items():
    lt = tok.get('listingTime')
    if lt:
        try:
            alpha_listings[sym] = datetime.fromtimestamp(int(lt)/1000, tz=timezone.utc).date()
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
print(f'\n  Alpha listing dates known: {len(alpha_listings)}/{len(alpha_syms)}')

# Sample listings
sample_syms = list(sorted(alpha_syms))[:5]
for s in sample_syms:
    ld = alpha_listings.get(s)
    if ld:
        age = (TODAY - ld).days
        print(f'    {s:12s} listed {ld} ({age}d ago)')

# Perp listing date: earliest klines_1h date per symbol (proxy)
perp_first_seen = {}
for sym, closes in daily_close.items():
    if closes:
        perp_first_seen[sym] = min(closes.keys())

# Rule: >14 days ON BOTH
n_thoa = 0
proxy_diff_samples = []
for sym in group_b:
    perp_sym = sym
    bare_sym = sym[:-4] if sym.endswith('USDT') else sym
    alpha_ld = alpha_listings.get(bare_sym)
    perp_first_str = perp_first_seen.get(perp_sym)
    if not alpha_ld:
        continue
    if not perp_first_str:
        continue
    perp_first = datetime.strptime(perp_first_str, '%Y-%m-%d').date()
    alpha_age = (TODAY - alpha_ld).days
    perp_age_proxy = (TODAY - perp_first).days
    if alpha_age > 14 and perp_age_proxy > 14:
        n_thoa += 1
    proxy_diff_samples.append((bare_sym, alpha_age, perp_age_proxy, perp_age_proxy - alpha_age))

print(f'\n  Trong (b) 83 tokens: {n_thoa} thoả rule >14d trên CẢ Alpha VÀ perp')
print(f'\n  Proxy sai lệch (perp_age_proxy - alpha_listing_age) · sample 10:')
proxy_diff_samples.sort(key=lambda x: abs(x[3]), reverse=True)
for sym, ala, ppa, diff in proxy_diff_samples[:10]:
    print(f'    {sym:12s} alpha_age={ala:>4d}d · perp_first_klines={ppa:>4d}d · diff={diff:+d}d')

n_no_alpha_date = len(group_b) - sum(1 for s in group_b if s[:-4] in alpha_listings)
n_no_perp_first = sum(1 for s in group_b if s not in perp_first_seen)
print(f'\n  Không có Alpha listing date: {n_no_alpha_date}')
print(f'  Không có perp klines: {n_no_perp_first}')

# Perp listing date NOT available directly — proxy = earliest klines_1h date in store (60d window)
# Sai lệch: nếu perp listed >60d ago, proxy = 60d (limited by store retention).
# Real listing date requires binance fapi exchangeInfo endpoint (onboardDate field).
print(f'\n  ⚠ Proxy perp_first_klines chỉ đúng khi token listed trong 60d window ·')
print(f'     tokens listed >60d ago → proxy underestimates age (max=60d)')
print(f'     Real fix: call binance fapi/exchangeInfo → onboardDate field (external API)')


# ═════ L4 · Chi phí bản tin nếu thêm 83 vào sổ ═════
print('\n' + '=' * 78)
print('L4 · Chi phí bản tin nếu thêm 83 vào sổ')
print('=' * 78)

# Current: freshwatch 139 → ~38 tokens/night in ledger (estimate from stars files)
# Load stars_YYYY-MM-DD.jsonl for recent nights to count
n_stars_by_night = {}
for d in LAST_30D:
    d_str = d.isoformat()
    p = REPO / f'data/logs/event_ledger/stars_{d_str}.jsonl'
    if p.exists():
        n_stars_by_night[d_str] = sum(1 for _ in open(p, encoding='utf-8'))

if n_stars_by_night:
    counts = sorted(n_stars_by_night.values())
    p50 = counts[len(counts)//2]
    p95 = counts[int(len(counts)*0.95)] if len(counts) > 3 else counts[-1]
    avg = sum(counts)/len(counts)
    print(f'\n  fw hiện tại · stars per night 30d: avg={avg:.1f} · p50={p50} · p95={p95} · max={max(counts)}')

# Estimate: 83 tokens with similar profile as fw 139
# fw rate = ~38/139 = 27% each night (approximation)
# 83 * 0.27 ≈ 22 extra stars/night
scaling = len(group_b) / len(group_a) if len(group_a) else 0
extra_stars = int(p50 * scaling) if n_stars_by_night else 0
print(f'\n  Extrapolate: 83 tokens ≈ +{extra_stars} stars/night (linear scale từ fw rate)')

# Character impact estimate:
# Each token line ~ 100-130 chars
# But 3-tier cap will cut CHUA XEP dynamically
# Extra stars distribute across species blocks
CHARS_PER_LINE = 110
extra_chars = extra_stars * CHARS_PER_LINE
print(f'  Extra chars ước (nếu render tất cả): +{extra_chars}')

# Actual body current ~ 3745 (T1) · adding stars pushes toward T2/T3
# Predict number of nights hitting T2/T3
# Sample 6 nights body sizes from J3:
J3_BODIES = {'2026-09-11':3745,'2026-09-12':3703,'2026-09-13':3740,'2026-09-14':3760,'2026-09-15':3814,'2026-09-16':3705}
n_t2 = n_t3 = n_t1 = 0
for t, cur in J3_BODIES.items():
    projected = cur + extra_chars
    if projected > 4096: n_t3 += 1
    elif projected > 3800: n_t2 += 1
    else: n_t1 += 1

print(f'\n  Projection nếu thêm 83 vào ledger (body +{extra_chars}):')
print(f'    T1 (<3800): {n_t1}/6')
print(f'    T2 (3800-4096): {n_t2}/6')
print(f'    T3 (>4096, D3 chặn): {n_t3}/6')

# Realistic: 3-tier cap will absorb some · CHUA XEP grows most since new tokens = unclassified
# But at some point CHUA XEP cap → tail line grows huge · then EXCEEDED
print(f'\n  Note: 3-tier cap sẽ cắt CHUA XEP dynamic · mất tin token cụ thể (chỉ tên trong tail)')
print(f'  Đa số 83 tokens mới có thể vào CHUA XEP (không đủ tell để classify) → tăng cắt')

print('\n' + '=' * 78)
