"""U1-U4 · Đo phễu universe · READ-ONLY · KHÔNG sửa gì.

Chạy trên VPS: cd /root/Data_back_test/whale_data && python3 <this file>
Cần: /tmp/alpha_list.json (đã curl trước) + universe_master.csv + store parquet 30d.
"""
from __future__ import annotations
import sys, os, json, csv, time
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except: pass  # L-66-OK (sandbox probe · benign catch-all)
REPO = Path('/root/Data_back_test/whale_data') if os.name != 'nt' else Path(r'D:/Data back test/whale_data')
ALPHA_FILE = Path('/tmp/alpha_list.json')

TODAY = datetime.now(timezone.utc).date()
LAST_30D = [(TODAY - timedelta(days=i)).isoformat() for i in range(1, 31)]

print('=' * 78)
print(f'U1-U4 · UNIVERSE FUNNEL · target 30d window ending {TODAY}')
print('=' * 78)


def to_f(v):
    try: return float(v) if v not in (None,'','null') else None
    except (TypeError, ValueError): return None


# ═════ Load sources ═════
print('\n[LOAD]')
d = json.load(open(ALPHA_FILE, encoding='utf-8'))
data = d.get('data', d)
alpha_toks = data if isinstance(data, list) else []
alpha_syms = {t['symbol'] for t in alpha_toks if t.get('symbol')}
print(f'  Alpha list: {len(alpha_toks)} tokens · unique symbols: {len(alpha_syms)}')

um_rows = list(csv.DictReader(open(REPO/'data/config/universe_master.csv', encoding='utf-8')))
um_active = {r['symbol'] for r in um_rows if r.get('status') == 'active'}
um_all = {r['symbol'] for r in um_rows}
print(f'  universe_master.csv: {len(um_rows)} total · {len(um_active)} active')

with open(REPO/'data/config/freshwatch_symbols.txt', encoding='utf-8') as f:
    fw_syms = {l.strip() for l in f if l.strip()}
print(f'  freshwatch_symbols.txt: {len(fw_syms)} symbols')

alpha_map = json.load(open(REPO/'data/config/alpha_id_map.json', encoding='utf-8'))
alpha_map_syms = {f'{k}USDT' for k in alpha_map.keys()}
print(f'  alpha_id_map.json: {len(alpha_map)} entries · as USDT: {len(alpha_map_syms)}')


# ═════ Load klines store for 30d · symbol → n_days, sum_vol_quote, median_vol ═════
print('\n[STORE SCAN · spot_klines_1d 30d]')
try:
    import pyarrow.parquet as pq
except ImportError:
    print('  pyarrow missing, skip store scan'); sys.exit(1)

sym_days = defaultdict(int)          # symbol → n distinct days klines
sym_vols = defaultdict(list)         # symbol → list of quote_vol per day

for d_str in LAST_30D:
    parq = REPO / f'data/raw/spot_klines_1d/date={d_str}/part-0.parquet'
    if not parq.exists(): continue
    try:
        tab = pq.read_table(str(parq)).to_pandas()
    except Exception as e:
        print(f'  read fail {d_str}: {e}')
        continue
    import math as _math
    for _, r in tab.iterrows():
        sym = str(r.get('symbol', ''))
        vol = to_f(r.get('quote_vol'))
        close = to_f(r.get('close'))
        if sym and close is not None:
            sym_days[sym] += 1
            if vol is not None and not _math.isnan(vol) and vol > 0:
                sym_vols[sym].append(vol)

print(f'  distinct symbols in 30d store: {len(sym_days)}')
sym_median_vol = {}
for s, vs in sym_vols.items():
    if vs:
        vs_sorted = sorted(vs)
        sym_median_vol[s] = vs_sorted[len(vs_sorted)//2]
print(f'  symbols with vol data (non-NaN, >0): {len(sym_median_vol)}')


# ═════ Helpers for Alpha → binance perp symbol join ═════
# Alpha uses bare `ARX`, binance perp uses `ARXUSDT`. Also some are non-ASCII (龙虾)
def alpha_to_perp(sym: str) -> str:
    return f'{sym}USDT' if not sym.endswith('USDT') else sym

alpha_perp_syms = {alpha_to_perp(s) for s in alpha_syms}


# ═════ U1 · FUNNEL ═════
print('\n' + '=' * 78)
print('U1 · FUNNEL')
print('=' * 78)

step1 = alpha_perp_syms
print(f'\n[Step 1] Alpha 677 → USDT-M perp candidates: {len(step1)}')

step2 = step1 & um_active
lost2 = step1 - um_active
print(f'\n[Step 2] ∩ universe_master ACTIVE: {len(step2)} (lost {len(lost2)})')
print(f'  lost sample: {sorted(lost2)[:10]}')

for MIN_D in [25, 20, 15, 10]:
    step3 = {s for s in step2 if sym_days.get(s, 0) >= MIN_D}
    lost3 = step2 - step3
    print(f'\n[Step 3 · ≥{MIN_D}d klines/30d window] ∩: {len(step3)} (lost {len(lost3)})')
    print(f'  lost sample n_days<{MIN_D}: {sorted(list(lost3))[:8]}')
    if MIN_D == 25:
        step3_final = step3

print(f'\n[Step 4 · median vol_quote (SPOT + Alpha) 30d ≥ threshold trên step3 ≥25d]:')
for thr in [10_000, 50_000, 100_000, 500_000, 1_000_000]:
    keep = {s for s in step3_final if sym_median_vol.get(s, 0) >= thr}
    lost = step3_final - keep
    lost_no_vol = {s for s in lost if s not in sym_median_vol}
    lost_low_vol = lost - lost_no_vol
    print(f'  ≥ ${thr/1000:>6.0f}k: {len(keep):4d} · lost {len(lost):3d} (no-vol-data {len(lost_no_vol)} · low-vol {len(lost_low_vol)})')
    print(f'    low-vol sample: {sorted(lost_low_vol)[:5]}')


# ═════ U2 · Reverse check 137 alpha_id_map + 139 freshwatch ═════
print('\n' + '=' * 78)
print('U2 · REVERSE CHECK · token đang theo dõi hiện tại')
print('=' * 78)

for name, s in [('alpha_id_map (137·as-USDT)', alpha_map_syms), ('freshwatch (139)', fw_syms)]:
    print(f'\n[{name}] {len(s)}')
    no_perp = s - um_active
    print(f'  KHÔNG có active perp: {len(no_perp)} · sample: {sorted(no_perp)[:10]}')
    have_perp = s & um_active
    print(f'  có active perp: {len(have_perp)}')
    for thr in [10_000, 50_000, 100_000, 500_000, 1_000_000]:
        below = {x for x in have_perp if sym_median_vol.get(x, 0) < thr}
        pct = len(below) * 100 / max(1, len(have_perp))
        print(f'    dưới ${thr/1000:>6.0f}k median vol 30d: {len(below):3d} ({pct:2.0f}%) · sample: {sorted(below)[:5]}')


# ═════ U3 · Proven + FP census · funnel position ═════
print('\n' + '=' * 78)
print('U3 · 13 PROVEN + 2 ĐỐI CHỨNG + 43 FP census · vị trí trong phễu')
print('=' * 78)

# 13 proven từ PATTERN_BOOK_v1_3
PROVEN13 = ['AKE','BANK','BTR','BTW','BULLA','CAP','CYS','HEMI','LOBSTER','ON','PROM','TUT','UAI']
COUNTER2 = ['APR','SOPH']

# 43 FP từ census v4
census_p = REPO / 'docs/case_files/census_63_grades/census_grades_v4_FULL85_20260831.csv'
FP43_syms = set()
if census_p.exists():
    with open(census_p, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r.get('grade') == 'FP':
                FP43_syms.add(r['token'])
print(f'\n[FP census v4 md5 8fdd0a74] 43 FP events · {len(FP43_syms)} distinct tokens: {sorted(FP43_syms)}')

# LOBSTER = 龙虾 in Alpha
NAME_MAP_ALT = {'LOBSTER': '龙虾'}

def sym_to_perp(x: str) -> str:
    return f'{x}USDT'

def in_alpha(x: str) -> bool:
    alt = NAME_MAP_ALT.get(x)
    return (x in alpha_syms) or (alt is not None and alt in alpha_syms)


def probe(pool, label):
    print(f'\n[{label}] n={len(pool)}')
    for x in pool:
        sym = sym_to_perp(x)
        in_a = in_alpha(x)
        in_u = sym in um_active
        in_30d = sym_days.get(sym, 0) >= 30
        n_d = sym_days.get(sym, 0)
        v = sym_median_vol.get(sym)
        v_str = f'${v/1000:.0f}k' if v else 'N/A'
        print(f'  {x:12s}: alpha={in_a} · active-perp={in_u} · ≥30d={in_30d} (n_days={n_d}) · median_vol={v_str}')

probe(PROVEN13, '13 PROVEN')
probe(COUNTER2, '2 ĐỐI CHỨNG')
probe(sorted(FP43_syms), '43 FP census (distinct tokens)')


# ═════ U4 · CHI PHÍ read-only sample ═════
print('\n' + '=' * 78)
print('U4 · CHI PHÍ · timing sample + estimate 677')
print('=' * 78)

# Đọc collect_alpha_daily.log để lấy avg time cho 84 tokens
log_p = REPO / 'data/logs/collect_alpha_daily.log'
if log_p.exists():
    # Tìm timestamp START và alpha_daily_complete gần nhất
    import re as _re
    ansi = _re.compile(r'\x1b\[[0-9;]*m')
    lines = [ansi.sub('', l) for l in log_p.read_text(encoding='utf-8', errors='replace').splitlines()]
    # Grab last full run: line pattern <ts> alpha_daily_complete
    complete_ts = None
    start_ts = None
    for l in reversed(lines):
        if 'alpha_daily_complete' in l and complete_ts is None:
            m = _re.match(r'^(\S+)', l)
            if m: complete_ts = m.group(1)
        elif 'alpha_daily_start' in l and complete_ts:
            m = _re.match(r'^(\S+)', l)
            if m:
                start_ts = m.group(1)
                break

    if start_ts and complete_ts:
        try:
            t0 = datetime.fromisoformat(start_ts.rstrip('Z')).replace(tzinfo=timezone.utc)
            t1 = datetime.fromisoformat(complete_ts.rstrip('Z')).replace(tzinfo=timezone.utc)
            elapsed = (t1 - t0).total_seconds()
            per_sym = elapsed / 84
            est677 = per_sym * 677
            print(f'\n  Last 84-token run: {elapsed:.1f}s · per-symbol: {per_sym:.2f}s')
            print(f'  Estimate 677 tokens: {est677:.1f}s = {est677/60:.1f} min')
            if est677 > 900:
                print(f'  ⚠ >15min · might trigger timeout ở step_render (120s)')
            else:
                print(f'  ✅ trong dải chấp nhận được')
        except Exception as e:
            print(f'  timestamp parse fail: {e}')
    else:
        print(f'  không tìm được cặp start/complete: start={start_ts} complete={complete_ts}')

# Live probe 10 alpha tokens · measure endpoint response
print('\n  Live probe 10 sample Alpha tokens · measure latency:')
import urllib.request, urllib.parse
sample = list(sorted(alpha_syms))[:10]
url_base = 'https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines'
total_t = 0
n_ok = 0
n_429 = 0

# Build ID lookup from Alpha list
alpha_id_lookup = {t['symbol']: t.get('alphaId') for t in alpha_toks}

for sym in sample:
    aid = alpha_id_lookup.get(sym)
    if not aid: continue
    params = {'symbol': aid, 'interval': '1d', 'limit': 30}
    url = f'{url_base}?{urllib.parse.urlencode(params)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.status
            body = r.read()
        dt = (time.time() - t0) * 1000
        total_t += dt
        if code == 200:
            n_ok += 1
            print(f'    {sym:12s} · {aid}: {code} · {dt:5.0f}ms · {len(body):>6d}B')
        elif code == 429:
            n_429 += 1
            print(f'    {sym:12s} · {aid}: ⚠ 429 rate-limit · {dt:.0f}ms')
        else:
            print(f'    {sym:12s} · {aid}: {code} · {dt:.0f}ms')
    except Exception as e:
        print(f'    {sym:12s} · {aid}: ERROR {type(e).__name__}: {e}')
    time.sleep(0.3)

if n_ok:
    avg_ms = total_t / n_ok
    est677 = avg_ms * 677 / 1000
    print(f'\n  Sample: {n_ok}/10 OK · avg {avg_ms:.0f}ms/call')
    print(f'  Est 677 sequential: {est677:.1f}s = {est677/60:.1f} min')
    print(f'  Rate-limit hit: {n_429}/10 · {"⚠ CẨN THẬN" if n_429 else "✅ OK"}')

# Parquet size estimate
print('\n  Parquet size estimate (per day):')
parq_today = REPO / f'data/raw/spot_klines_1d/date={(TODAY-timedelta(days=1)).isoformat()}/part-0.parquet'
if parq_today.exists():
    sz = parq_today.stat().st_size
    print(f'    Yesterday parquet: {sz:>10d} bytes = {sz/1024:.1f} KB · 608 rows')
    est_bytes = sz / 608 * (608 - 84 + 677)
    print(f'    Ước tính khi có 677 alpha (thay 84): {est_bytes:>10.0f} bytes = {est_bytes/1024:.1f} KB')
    print(f'    Δ mỗi ngày: +{(est_bytes-sz)/1024:.1f} KB · +{(est_bytes-sz)*365/1024/1024:.1f} MB/năm')

print('\n' + '=' * 78)
print('DONE')
print('=' * 78)
