"""V1-V4 · Đo sâu trước chốt option · READ-ONLY."""
from __future__ import annotations
import sys, os, json, csv, time, urllib.request, urllib.parse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data')
ALPHA_FILE = Path('/tmp/alpha_list.json')
TODAY = datetime.now(timezone.utc).date()

def to_f(v):
    try: return float(v) if v not in (None,'','null') else None
    except (TypeError, ValueError): return None

# ═════ Load Alpha ═════
d = json.load(open(ALPHA_FILE, encoding='utf-8'))
alpha_toks = d if isinstance(d, list) else d.get('data', [])
alpha_by_sym = {t['symbol']: t for t in alpha_toks if t.get('symbol')}
alpha_syms = set(alpha_by_sym.keys())
alpha_perp_syms = {f'{s}USDT' for s in alpha_syms}
print(f'Alpha unique symbols: {len(alpha_syms)}')

# ═════ Load universe_master + freshwatch ═════
um = list(csv.DictReader(open(REPO/'data/config/universe_master.csv', encoding='utf-8')))
um_active = {r['symbol'] for r in um if r.get('status') == 'active'}
with open(REPO/'data/config/freshwatch_symbols.txt', encoding='utf-8') as f:
    fw_syms = {l.strip() for l in f if l.strip()}
print(f'universe_master active: {len(um_active)} · freshwatch: {len(fw_syms)}')

# ═════ V1 · TIMING REAL ═════
print('\n' + '=' * 78)
print('V1 · TIMING REAL · 300 sample calls to Alpha klines endpoint')
print('=' * 78)

sample_syms = list(sorted(alpha_syms))[:300]
url_base = 'https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines'

latencies = []
n_ok = 0
n_429 = 0
n_err = 0
n_retry = 0
t_total_start = time.time()

for i, sym in enumerate(sample_syms):
    aid = alpha_by_sym[sym].get('alphaId')
    if not aid: continue
    params = {'symbol': aid, 'interval': '1d', 'limit': 30}
    url = f'{url_base}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    attempt = 0
    while attempt < 2:
        attempt += 1
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                code = r.status
                body = r.read()
            dt = (time.time() - t0) * 1000
            latencies.append(dt)
            if code == 200: n_ok += 1
            elif code == 429:
                n_429 += 1
                if attempt < 2:
                    n_retry += 1
                    time.sleep(2)
                    continue
            break
        except Exception:
            dt = (time.time() - t0) * 1000
            n_err += 1
            if attempt < 2:
                n_retry += 1
                time.sleep(1)
                continue
            latencies.append(dt)
            break
    # No sleep between symbols — measure worst-case throughput
    if i % 50 == 49:
        print(f'  [{i+1}/300] ok={n_ok} · 429={n_429} · err={n_err} · retry={n_retry}')

t_total = time.time() - t_total_start
latencies.sort()
p50 = latencies[len(latencies)//2] if latencies else 0
p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
avg = sum(latencies)/len(latencies) if latencies else 0

print(f'\n  ★ TOTAL 300 tokens: {t_total:.1f}s = {t_total/60:.1f} min')
print(f'  ok={n_ok} · 429={n_429} · error={n_err} · retry={n_retry}')
print(f'  latency: p50={p50:.0f}ms · p95={p95:.0f}ms · avg={avg:.0f}ms')

extrap = t_total * 677 / 300
print(f'  ★ Ngoại suy 677 tuyến tính: {extrap:.1f}s = {extrap/60:.1f} min')
print(f'  Đệm hiện tại (alpha 01:30 → master 01:46): 16 phút')
if extrap/60 > 12:
    print(f'  ⚠ >12 phút · phải dời lịch trước')
elif extrap/60 > 10:
    print(f'  ⚠ >10 phút · sát đệm · cần theo dõi')
else:
    print(f'  ✅ trong đệm · an toàn')


# ═════ V2 · TRỤC ═════
print('\n' + '=' * 78)
print('V2 · 3 TRỤC (FRESH-CHAIN · KHO-SAN · PERP) · 677 tokens')
print('=' * 78)

# FRESH-CHAIN capable = có BSC contract (Nansen theo dõi được)
fresh_capable = {s for s in alpha_syms
                 if str(alpha_by_sym[s].get('chainId')) == '56'
                 and alpha_by_sym[s].get('contractAddress')}

# KHO-SAN tracked = xuất hiện trong ledger source exch_digest hoặc gomh_h1 30d gần
kho_tracked = set()
for i in range(1, 31):
    p = REPO / f'data/logs/event_ledger/events_{(TODAY-timedelta(days=i)).isoformat()}.jsonl'
    if not p.exists(): continue
    for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(line)
            if e.get('source') in ('exch_digest', 'gomh_h1'):
                kho_tracked.add(e.get('symbol', ''))
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
# FRESH tracked = xuất hiện trong ledger source fresh_digest
fresh_tracked = set()
for i in range(1, 31):
    p = REPO / f'data/logs/event_ledger/events_{(TODAY-timedelta(days=i)).isoformat()}.jsonl'
    if not p.exists(): continue
    for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(line)
            if e.get('source') == 'fresh_digest':
                fresh_tracked.add(e.get('symbol', ''))
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
# PERP active
perp_active = um_active

# Convert to comparable naming: fresh_tracked / kho_tracked stored as 'XUSDT'
# Alpha syms stored bare 'X'
fresh_tracked_bare = {s[:-4] if s.endswith('USDT') else s for s in fresh_tracked}
kho_tracked_bare = {s[:-4] if s.endswith('USDT') else s for s in kho_tracked}
perp_active_bare = {s[:-4] if s.endswith('USDT') else s for s in perp_active}

# For 677 Alpha tokens, count each axis
alpha_bare = alpha_syms
n_fresh = len(alpha_bare & fresh_capable)
n_kho   = len(alpha_bare & kho_tracked_bare)
n_perp  = len(alpha_bare & perp_active_bare)
n_all3  = len(alpha_bare & fresh_capable & kho_tracked_bare & perp_active_bare)
n_none  = len(alpha_bare - fresh_capable - kho_tracked_bare - perp_active_bare)

print(f'\nAlpha 677 · phân bố trục (không exclusive):')
print(f'  FRESH-CHAIN capable (chainId=56 + contract): {n_fresh}')
print(f'  KHO-SAN tracked (ledger exch_digest/gomh_h1 30d): {n_kho}')
print(f'  PERP active (universe_master): {n_perp}')
print(f'  giao 3 trục: {n_all3}')
print(f'  không thuộc trục nào: {n_none}')

# Union of axes
axis_union = fresh_capable | kho_tracked_bare | perp_active_bare
alpha_with_axis = alpha_bare & axis_union
print(f'  Alpha có ≥1 trục: {len(alpha_with_axis)} / 656 ({len(alpha_with_axis)*100//656}%)')

# 13 proven check
PROVEN13 = ['AKE','BANK','BTR','BTW','BULLA','CAP','CYS','HEMI','LOBSTER','ON','PROM','TUT','UAI']
print(f'\n13 PROVEN · trục thuộc:')
name_alt = {'LOBSTER': '龙虾'}
for x in PROVEN13:
    alt = name_alt.get(x, x)
    in_alpha = x in alpha_syms or alt in alpha_syms
    in_fresh = alt in fresh_capable or x in fresh_capable
    in_kho = x in kho_tracked_bare or alt in kho_tracked_bare
    in_perp = x in perp_active_bare or alt in perp_active_bare
    axes = []
    if in_fresh: axes.append('FRESH')
    if in_kho: axes.append('KHO')
    if in_perp: axes.append('PERP')
    print(f'  {x:10s} alpha={str(in_alpha):5s} FRESH={str(in_fresh):5s} KHO={str(in_kho):5s} PERP={str(in_perp):5s} · axes={",".join(axes) or "NONE"}')


# ═════ V3 · UNIVERSE UNION 3-WAY ═════
print('\n' + '=' * 78)
print('V3 · UNIVERSE UNION · Alpha ∪ perp_active ∪ freshwatch')
print('=' * 78)

alpha_p = alpha_perp_syms   # 656 as USDTX
perp_p = perp_active         # 524
fw_p = fw_syms                # 139

union = alpha_p | perp_p | fw_p
print(f'\n  |Alpha as-USDT|:      {len(alpha_p)}')
print(f'  |perp active|:        {len(perp_p)}')
print(f'  |freshwatch|:         {len(fw_p)}')
print(f'  |UNION 3-way|:        {len(union)}')

only_alpha = alpha_p - perp_p - fw_p
only_perp = perp_p - alpha_p - fw_p
only_fw = fw_p - alpha_p - perp_p
alpha_and_perp_not_fw = (alpha_p & perp_p) - fw_p
alpha_and_fw_not_perp = (alpha_p & fw_p) - perp_p
perp_and_fw_not_alpha = (perp_p & fw_p) - alpha_p
all_three = alpha_p & perp_p & fw_p

print(f'\n  chỉ Alpha (không perp, không fw): {len(only_alpha)}')
print(f'    sample: {sorted(only_alpha)[:10]}')
print(f'  chỉ perp (không Alpha, không fw): {len(only_perp)}  ← PROM-like')
print(f'    sample: {sorted(only_perp)[:10]}')
print(f'  chỉ freshwatch (không Alpha, không perp): {len(only_fw)}')
print(f'    sample: {sorted(only_fw)[:10]}')
print(f'  Alpha ∩ perp (không fw): {len(alpha_and_perp_not_fw)}')
print(f'  Alpha ∩ fw (không perp): {len(alpha_and_fw_not_perp)}  ← LOBSTER-like')
print(f'    sample: {sorted(alpha_and_fw_not_perp)[:10]}')
print(f'  perp ∩ fw (không Alpha): {len(perp_and_fw_not_alpha)}')
print(f'    sample: {sorted(perp_and_fw_not_alpha)[:10]}')
print(f'  3-way giao: {len(all_three)}')


# ═════ V4 · VOL từ PERP klines_1h (thay spot store) ═════
print('\n' + '=' * 78)
print('V4 · VOL từ PERP klines_1h · sum quote_volume 24h × 30d')
print('=' * 78)

try:
    import pyarrow.parquet as pq
    import math as _math
except ImportError:
    print('  pyarrow missing, skip')
    sys.exit(0)

sym_daily_vols = defaultdict(list)   # symbol → list of daily sum quote_volume
for i in range(1, 31):
    d_str = (TODAY - timedelta(days=i)).isoformat()
    p = REPO / f'data/raw/klines_1h/date={d_str}/part-0.parquet'
    if not p.exists(): continue
    tab = pq.read_table(str(p)).to_pandas()
    # Aggregate quote_volume per symbol per day (sum over 24 hours)
    for sym, grp in tab.groupby('symbol'):
        total = grp['quote_volume'].sum()
        if not _math.isnan(total) and total > 0:
            sym_daily_vols[sym].append(total)

print(f'\n  distinct symbols in klines_1h 30d: {len(sym_daily_vols)}')
sym_median_perp_vol = {s: sorted(vs)[len(vs)//2] for s, vs in sym_daily_vols.items() if vs}
print(f'  symbols with median vol computable: {len(sym_median_perp_vol)}')

# Coverage on perp_active
perp_with_vol = sym_median_perp_vol.keys() & perp_active
print(f'  perp_active coverage: {len(perp_with_vol)}/{len(perp_active)} ({len(perp_with_vol)*100//len(perp_active)}%)')

# Coverage on 13 proven perp names (LOBSTER = 龙虾USDT? or LOBSTERUSDT? — try both)
print(f'\n13 PROVEN · PERP vol median 30d:')
for x in PROVEN13:
    perp_sym_candidates = [f'{x}USDT']
    if x == 'LOBSTER': perp_sym_candidates.append('龙虾USDT')
    v = None
    for c in perp_sym_candidates:
        if c in sym_median_perp_vol:
            v = sym_median_perp_vol[c]; break
    print(f'  {x:10s}: perp vol median = {"$"+str(int(v))+"" if v else "N/A"}')

# Distribution on all perp
if sym_median_perp_vol:
    print(f'\nPhân bố vol median 30d trên perp_active (n={len(perp_with_vol)}):')
    for thr in [10_000, 100_000, 500_000, 1_000_000, 10_000_000]:
        n = sum(1 for s in perp_with_vol if sym_median_perp_vol[s] >= thr)
        pct = n * 100 / max(1, len(perp_with_vol))
        print(f'  ≥ ${thr/1000:>7.0f}k: {n:4d} ({pct:2.0f}%)')

print('\n' + '=' * 78)
print('DONE')
