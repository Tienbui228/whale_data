"""X1-X4 · Đóng 3 lỗ trong W3 · READ-ONLY."""
from __future__ import annotations
import sys, os, json, csv, math
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import statistics as _st

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
ALPHA_FILE = Path('/tmp/alpha_list.json')
TODAY = datetime.now(timezone.utc).date()
LAST_30D = [(TODAY - timedelta(days=i)) for i in range(1, 31)]

# ═════ Load ═════
with open(REPO/'data/config/freshwatch_symbols.txt', encoding='utf-8') as f:
    fw_syms = {l.strip() for l in f if l.strip()}
um_active = {r['symbol'] for r in csv.DictReader(open(REPO/'data/config/universe_master.csv', encoding='utf-8'))
             if r.get('status') == 'active'}
excluded = um_active - fw_syms

d_alpha = json.load(open(ALPHA_FILE, encoding='utf-8'))
alpha_toks = d_alpha if isinstance(d_alpha, list) else d_alpha.get('data', [])
alpha_by_sym = {t['symbol']: t for t in alpha_toks if t.get('symbol')}

# mcap lookup: bare_sym → mcap USD (only for Alpha-listed tokens)
alpha_mcap = {}
for s, t in alpha_by_sym.items():
    m = t.get('marketCap')
    try:
        alpha_mcap[s] = float(m) if m not in (None, '', 'null') else None
    except: pass  # L-66-OK (sandbox probe · benign catch-all)
import pyarrow.parquet as pq

def _load_klines_daily(n_back=60):
    """Load n_back days of klines_1h · aggregate daily quote_vol + close."""
    daily_vol = defaultdict(dict)
    daily_close = defaultdict(dict)
    for i in range(1, n_back + 1):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/klines_1h/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for sym, grp in tab.groupby('symbol'):
            daily_vol[sym][d] = float(grp['quote_volume'].sum())
            last = grp.sort_values('as_of_ts_ms').iloc[-1]
            daily_close[sym][d] = float(last['close'])
    return daily_vol, daily_close


def _load_oi_daily(n_back=45):
    daily_oi = defaultdict(dict)
    for i in range(1, n_back + 1):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/oi_hist_1d/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for _, r in tab.iterrows():
            sym = str(r['symbol'])
            for k in ('sum_open_interest_value', 'open_interest_value', 'oi_usd'):
                if k in tab.columns and r[k] is not None:
                    try:
                        v = float(r[k])
                        if not math.isnan(v) and v > 0:
                            daily_oi[sym][d] = v
                            break
                    except: pass  # L-66-OK (sandbox probe · benign catch-all)
    return daily_oi


def _load_taker_ratio(n_back=30):
    daily_ratio = defaultdict(dict)
    for i in range(1, n_back + 1):
        d = (TODAY - timedelta(days=i)).isoformat()
        p = REPO / f'data/raw/taker_ratio_1h/date={d}/part-0.parquet'
        if not p.exists(): continue
        tab = pq.read_table(str(p)).to_pandas()
        for sym, grp in tab.groupby('symbol'):
            r = grp['buy_sell_ratio'].mean()
            if not math.isnan(r): daily_ratio[sym][d] = float(r)
    return daily_ratio


print('[LOAD 60d klines + 45d oi + 30d taker]')
daily_vol, daily_close = _load_klines_daily(60)
daily_oi = _load_oi_daily(45)
daily_ratio = _load_taker_ratio(30)
print(f'  klines symbols: {len(daily_close)} · oi: {len(daily_oi)} · taker: {len(daily_ratio)}')


def _shadow_fire(sym, target_date):
    d = target_date.isoformat()
    axes = []
    v_today = daily_vol.get(sym, {}).get(d)
    v_hist = [daily_vol[sym].get((target_date - timedelta(days=k)).isoformat())
              for k in range(1, 16)]
    v_hist = [v for v in v_hist if v is not None and v > 0]
    if v_today and v_hist and v_today > 3 * _st.median(v_hist):
        axes.append('VOL')
    oi_today = daily_oi.get(sym, {}).get(d)
    oi_14 = daily_oi.get(sym, {}).get((target_date - timedelta(days=14)).isoformat())
    if oi_today and oi_14 and oi_today > 1.5 * oi_14:
        axes.append('OI')
    r = daily_ratio.get(sym, {}).get(d)
    if r is not None and (r > 2.0 or r < 0.5):
        axes.append('TAKER')
    return axes


def _forward_max_ratio(sym, target_date, days=30):
    """Return max_close_next_days / close_at_target · None if no data."""
    d_str = target_date.isoformat()
    c0 = daily_close.get(sym, {}).get(d_str)
    if not c0 or c0 <= 0: return None
    max_c = c0; max_d = None
    for k in range(1, days + 1):
        d_next = (target_date + timedelta(days=k)).isoformat()
        c = daily_close.get(sym, {}).get(d_next)
        if c is not None and c > max_c:
            max_c = c; max_d = d_next
    return (max_c / c0, max_d)


# ═════ X1 · BASE RATE ═════
print('\n' + '=' * 78)
print('X1 · BASE RATE · toàn 385 token × 30 đêm')
print('=' * 78)

n_pairs_total = 0
n_pairs_x2 = 0
for sym in excluded:
    for d in LAST_30D:
        result = _forward_max_ratio(sym, d, days=30)
        if result is None: continue
        n_pairs_total += 1
        if result[0] >= 2.0: n_pairs_x2 += 1

base_rate = n_pairs_x2 / n_pairs_total * 100 if n_pairs_total else 0
print(f'\n  Base rate: {n_pairs_x2}/{n_pairs_total} token-nights ({base_rate:.2f}%)')

# Fire subset ratio (từ W3): 56 ×2 hits trong 1990 fires = 2.8%
FIRE_HITS = 56
FIRE_TOTAL = 1990
fire_rate = FIRE_HITS / FIRE_TOTAL * 100
print(f'  Fire-subset rate: {FIRE_HITS}/{FIRE_TOTAL} ({fire_rate:.2f}%)')
lift = fire_rate / base_rate if base_rate else float('inf')
print(f'  Fire ÷ Base lift: {lift:.2f}x')
if lift >= 2:
    print(f'  ✅ Proxy CÓ predictive power ({lift:.1f}x base rate)')
elif lift >= 1.3:
    print(f'  ⚠ Proxy YẾU (lift <2x)')
else:
    print(f'  ❌ Proxy KHÔNG dự báo · W3 vô nghĩa')


# ═════ X2 · DETECTOR THẬT · gom_h2prime + probe compute_h_daily on 385 ═════
print('\n' + '=' * 78)
print('X2 · DETECTOR THẬT · H1/H2/GOM-A · check nếu có trong store hiện')
print('=' * 78)

# gom_h2prime_daily.csv - has this run on 385 excluded?
h2p_path = REPO / 'data/gom_h2prime_daily.csv'
if h2p_path.exists():
    with open(h2p_path, encoding='utf-8') as f:
        h2p_rows = list(csv.DictReader(f))
    h2p_syms = {r.get('symbol','') for r in h2p_rows}
    h2p_excl = h2p_syms & excluded
    h2p_fw = h2p_syms & fw_syms
    print(f'\n  gom_h2prime_daily.csv rows: {len(h2p_rows)}')
    print(f'  distinct symbols: {len(h2p_syms)}')
    print(f'  ∩ excluded 385: {len(h2p_excl)}')
    print(f'  ∩ freshwatch 139: {len(h2p_fw)}')
    if h2p_excl:
        sample = sorted(h2p_excl)[:5]
        print(f'  excluded sample: {sample}')
else:
    print(f'  gom_h2prime_daily.csv: MISSING')

# Check nếu có detector output cho 385 excluded
gom_h_path = REPO / 'data/gom_h_daily.csv'
if gom_h_path.exists():
    with open(gom_h_path, encoding='utf-8') as f:
        gh_rows = list(csv.DictReader(f))
    gh_syms = {r.get('symbol','') for r in gh_rows}
    gh_excl = gh_syms & excluded
    gh_fw = gh_syms & fw_syms
    print(f'\n  gom_h_daily.csv rows: {len(gh_rows)}')
    print(f'  distinct symbols: {len(gh_syms)}')
    print(f'  ∩ excluded 385: {len(gh_excl)}')
    print(f'  ∩ freshwatch 139: {len(gh_fw)}')
    # Kiểm PROM
    prom_rows = [r for r in gh_rows if r.get('symbol') == 'PROMUSDT']
    print(f'  PROM rows: {len(prom_rows)}')
else:
    print(f'  gom_h_daily.csv: MISSING')

# Ledger events source distribution 30d for excluded
print(f'\n  ledger events 30d SOURCE nào scan excluded?')
src_hits_excl = Counter()
src_hits_fw = Counter()
for i in range(1, 31):
    d = (TODAY - timedelta(days=i)).isoformat()
    p = REPO / f'data/logs/event_ledger/events_{d}.jsonl'
    if not p.exists(): continue
    for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(line)
            sym = e.get('symbol', '')
            src = e.get('source', '?')
            if sym in excluded: src_hits_excl[src] += 1
            elif sym in fw_syms: src_hits_fw[src] += 1
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
print(f'    excluded 385 events by source:  {dict(src_hits_excl)}')
print(f'    freshwatch 139 events by source: {dict(src_hits_fw.most_common(5))}')

if not src_hits_excl:
    print(f'  ★ KHÔNG source production nào gen event cho 385 excluded 30d qua')
    print(f'    → real detector KHÔNG chạy trên excluded · proxy là con số duy nhất')


# ═════ X3 · Tách dân số · mcap < $200M ═════
print('\n' + '=' * 78)
print('X3 · TÁCH DÂN SỐ · mcap < $200M · nhóm profile thesis')
print('=' * 78)

# For 385 excluded (BARE_SYMBOL suffix strip 'USDT'):
excl_bare = {s[:-4] if s.endswith('USDT') else s for s in excluded}
excl_with_alpha_mcap = 0
excl_under_200m = set()  # bare symbols
excl_over_200m = set()
excl_no_mcap = set()

for bare in excl_bare:
    m = alpha_mcap.get(bare)
    if m is None:
        excl_no_mcap.add(bare)
    elif m < 200_000_000:
        excl_under_200m.add(bare)
    else:
        excl_over_200m.add(bare)

print(f'\n  385 excluded (bare): {len(excl_bare)}')
print(f'  có Alpha mcap: {len(excl_bare) - len(excl_no_mcap)}')
print(f'    < $200M: {len(excl_under_200m)}')
print(f'    ≥ $200M: {len(excl_over_200m)} · sample: {sorted(excl_over_200m)[:10]}')
print(f'  không có Alpha mcap (302 only-perp + others): {len(excl_no_mcap)}')

under_200m_perp = {f'{s}USDT' for s in excl_under_200m}

# Re-run W1 fire count trên nhóm under_200m
print(f'\n  W1 shadow fire trên {len(under_200m_perp)} token < $200M · 30 đêm:')
counts_200 = []
fires_by_sym_date_200 = defaultdict(list)
for d in reversed(LAST_30D):
    n = 0
    for sym in under_200m_perp:
        axes = _shadow_fire(sym, d)
        if axes:
            n += 1
            fires_by_sym_date_200[sym].append(d.isoformat())
    counts_200.append(n)

counts_200_s = sorted(counts_200)
if counts_200_s:
    p50_200 = counts_200_s[len(counts_200_s)//2]
    p95_200 = counts_200_s[int(len(counts_200_s)*0.95)]
    print(f'    n={len(under_200m_perp)} · min={min(counts_200_s)} · p50={p50_200} · p95={p95_200} · max={max(counts_200_s)}')
    print(f'    sum 30 đêm = {sum(counts_200)} · fires/token/đêm = {sum(counts_200)/(len(under_200m_perp)*30):.3f}')

# ×2 hits trong nhóm này
hits_200 = []
for sym, dates in fires_by_sym_date_200.items():
    for d_str in dates:
        fdate = datetime.strptime(d_str, '%Y-%m-%d').date()
        res = _forward_max_ratio(sym, fdate, days=30)
        if res and res[0] >= 2.0:
            hits_200.append((sym, d_str, res[0], res[1]))

print(f'\n  ×2 hits trong {len(under_200m_perp)} under-$200M: {len(hits_200)}')
if hits_200:
    hits_200.sort(key=lambda x: -x[2])
    for h in hits_200[:15]:
        print(f'    {h[0]:20s} {h[1]} · {h[2]:.2f}x max={h[3]}')

# LSK/ONG/IOST/ZEN mcap
print(f'\n  Kiểm mcap các token trong W3 hits:')
for x in ['LSK','ONG','IOST','ZEN','PROM','RAYSOL','FLOCK','MAGMA']:
    m = alpha_mcap.get(x)
    if m is None:
        print(f'    {x:10s} NO Alpha mcap · (không trên Alpha)')
    else:
        icon = '< $200M' if m < 200_000_000 else '≥ $200M'
        print(f'    {x:10s} ${m/1e6:>8.1f}M · {icon}')


# ═════ X4 · PROM · kiểm chứng ═════
print('\n' + '=' * 78)
print('X4 · PROM · detector THẬT có bắt không?')
print('=' * 78)

# Search ledger events 30d for PROM
prom_events = []
for i in range(1, 31):
    d = (TODAY - timedelta(days=i)).isoformat()
    p = REPO / f'data/logs/event_ledger/events_{d}.jsonl'
    if not p.exists(): continue
    for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(line)
            if e.get('symbol', '') in ('PROM','PROMUSDT'):
                prom_events.append((d, e.get('source','?'), e.get('target_date','?'), e.get('axis','?')))
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
print(f'\n  PROM events trong ledger 30d: {len(prom_events)}')
if prom_events:
    for d, src, td, ax in prom_events[:20]:
        print(f'    scan {d}: source={src} target={td} axis={ax}')
else:
    print(f'  ❌ ZERO events · real detector KHÔNG bắt PROM')
    print(f'  (PROM không trong freshwatch → không được scan bởi source production)')

# Proxy: shadow fire trên PROM 30d
print(f'\n  Shadow proxy trên PROMUSDT 30d:')
prom_shadow = []
for d in LAST_30D:
    axes = _shadow_fire('PROMUSDT', d)
    if axes:
        prom_shadow.append((d.isoformat(), axes))
print(f'  Shadow fire count: {len(prom_shadow)}')
for d, ax in prom_shadow[:10]:
    print(f'    {d}: axes={ax}')

# PROM close trajectory
print(f'\n  PROM close 30d trajectory:')
prom_closes = daily_close.get('PROMUSDT', {})
for d in sorted(prom_closes.keys()):
    print(f'    {d}: {prom_closes[d]:.4f}')

print('\n' + '=' * 78)
print('DONE')
