"""N2 · alpha listingTime + fapi onboardDate cho 83 tokens (Alpha∩perp, chưa fw)."""
from __future__ import annotations
import sys, os, csv, json, urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
REPO = Path('/root/Data_back_test/whale_data')
TODAY = datetime.now(timezone.utc).date()
ALPHA_FILE = Path('/tmp/alpha_list.json')

# Load Alpha
d = json.load(open(ALPHA_FILE, encoding='utf-8'))
alpha_toks = d if isinstance(d, list) else d.get('data', [])
alpha_by_sym = {t['symbol']: t for t in alpha_toks if t.get('symbol')}

# Alpha listing dates
alpha_listings = {}
for sym, tok in alpha_by_sym.items():
    lt = tok.get('listingTime')
    if lt:
        try: alpha_listings[sym] = datetime.fromtimestamp(int(lt)/1000, tz=timezone.utc).date()
        except: pass  # L-66-OK (sandbox probe · benign catch-all)
print(f'Alpha listings: {len(alpha_listings)}/{len(alpha_by_sym)}')

# Load universe_master + freshwatch
um = list(csv.DictReader(open(REPO/'data/config/universe_master.csv')))
um_active = {r['symbol'] for r in um if r.get('status')=='active'}
with open(REPO/'data/config/freshwatch_symbols.txt') as f:
    fw = {l.strip() for l in f if l.strip()}

alpha_perp_syms = {f'{s}USDT' for s in alpha_by_sym.keys()}
group_b = (alpha_perp_syms & um_active) - fw
print(f'(b) Alpha∩perp chưa fw sau N1: {len(group_b)}')   # was 83, now depends on fw=147


# Fetch fapi exchangeInfo · onboardDate per symbol
print('\n[Fetch fapi exchangeInfo]')
try:
    req = urllib.request.Request(
        'https://fapi.binance.com/fapi/v1/exchangeInfo',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        ei = json.loads(r.read())
    fapi_onboard = {}
    for s in ei.get('symbols', []):
        sym = s['symbol']
        ob = s.get('onboardDate')
        if ob:
            try:
                fapi_onboard[sym] = datetime.fromtimestamp(int(ob)/1000, tz=timezone.utc).date()
            except: pass  # L-66-OK (sandbox probe · benign catch-all)
    print(f'  fapi onboardDate loaded: {len(fapi_onboard)} symbols')
except Exception as e:
    print(f'  ERROR: {type(e).__name__}: {e}')
    fapi_onboard = {}


# Bảng 83 (or new count after fw update)
print('\n' + '=' * 78)
print('N2 · Bảng cohort (b) · alpha_age · perp_age · thoả >14d cả hai?')
print('=' * 78)
print()
print(f'{"symbol":15s} {"alpha_age":>10s} {"perp_age":>10s} {"thoả >14d cả hai":>18s}')
print('-' * 80)

n_thoa = 0
n_missing = 0
rows = []
for sym in sorted(group_b):
    bare = sym[:-4] if sym.endswith('USDT') else sym
    alpha_ld = alpha_listings.get(bare)
    perp_ob = fapi_onboard.get(sym)
    if not alpha_ld or not perp_ob:
        n_missing += 1
        rows.append((sym, alpha_ld, perp_ob, 'MISSING-DATE'))
        continue
    alpha_age = (TODAY - alpha_ld).days
    perp_age = (TODAY - perp_ob).days
    thoa = alpha_age > 14 and perp_age > 14
    if thoa: n_thoa += 1
    rows.append((sym, alpha_age, perp_age, thoa))

for sym, ala, ppa, thoa in rows:
    if isinstance(ala, (int,)) or isinstance(ppa, (int,)):
        thoa_s = '✅' if thoa is True else ('❌' if thoa is False else str(thoa))
        print(f'{sym:15s} {str(ala):>10s} {str(ppa):>10s} {thoa_s:>18s}')
    else:
        print(f'{sym:15s} {str(ala or "N/A"):>10s} {str(ppa or "N/A"):>10s} {str(thoa):>18s}')

print(f'\n★ Summary: n_thoa={n_thoa}/{len(group_b)} · n_missing_date={n_missing}')
print(f'\nSample distribution:')
ages_a = [r[1] for r in rows if isinstance(r[1], int)]
ages_p = [r[2] for r in rows if isinstance(r[2], int)]
if ages_a:
    ages_a.sort()
    print(f'  alpha_age: min={min(ages_a)}d · median={ages_a[len(ages_a)//2]}d · max={max(ages_a)}d')
if ages_p:
    ages_p.sort()
    print(f'  perp_age:  min={min(ages_p)}d · median={ages_p[len(ages_p)//2]}d · max={max(ages_p)}d')

# save 83 → will pass to N3
with open('/tmp/N2_group_b.txt', 'w', encoding='utf-8') as f:
    for sym, ala, ppa, thoa in rows:
        if thoa is True:
            f.write(f'{sym}\n')
print(f'\n[SAVED] /tmp/N2_group_b.txt · {n_thoa} tokens thoả rule → dùng cho N3')
