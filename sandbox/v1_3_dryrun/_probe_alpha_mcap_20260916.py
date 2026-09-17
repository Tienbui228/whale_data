"""Query Alpha token-list · marketCap distribution."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = json.load(open(r'C:/Users/Hello/alpha_list.json', encoding='utf-8'))
data = d.get('data', d)
toks = data if isinstance(data, list) else []
print(f'Total Alpha tokens: {len(toks)}')

def f(v):
    try:
        return float(v) if v not in (None, '', 'null') else None
    except (TypeError, ValueError):
        return None

n_null = sum(1 for t in toks if f(t.get('marketCap')) is None)
mcaps = [f(t.get('marketCap')) for t in toks if f(t.get('marketCap')) is not None]
print(f'  marketCap null/missing: {n_null}')
print(f'  marketCap known: {len(mcaps)}')
print()

for cap in [50e6, 100e6, 200e6, 500e6, 1e9, 5e9]:
    n_under = sum(1 for m in mcaps if m < cap)
    pct = n_under * 100 / len(mcaps)
    total_incl_null = n_under + n_null
    print(f'  < ${cap/1e6:>6.0f}M: {n_under:4d} tokens ({pct:2.0f}% of known) · plus null = {total_incl_null}')

print()
print('BSC-only:')
bsc = [t for t in toks if str(t.get('chainId')) == '56']
bsc_mcaps = [f(t.get('marketCap')) for t in bsc if f(t.get('marketCap')) is not None]
n_bsc_null = len(bsc) - len(bsc_mcaps)
print(f'  total BSC: {len(bsc)}')
print(f'  mcap known: {len(bsc_mcaps)} · null: {n_bsc_null}')
for cap in [100e6, 200e6, 500e6]:
    n_under = sum(1 for m in bsc_mcaps if m < cap)
    print(f'  BSC < ${cap/1e6:.0f}M: {n_under}')

print()
print('Top 15 largest mcap toàn 677:')
sorted_toks = sorted([t for t in toks if f(t.get('marketCap'))], key=lambda t: -f(t.get('marketCap')))[:15]
for t in sorted_toks:
    m = f(t.get('marketCap'))
    print(f'  {t.get("symbol",""):15s} mcap=${m/1e6:9.1f}M · alphaId={t.get("alphaId")}')
