#!/usr/bin/env python3
"""Probe v2: 0x73d8...946db — BscScan V2 API + GeckoTerminal."""
import sys, io, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz

WHALE = Path(r'D:\Data back test\whale_data')
OUT   = WHALE / 'docs' / 'reports' / '_probe_addr_bscscan.txt'

ADDR  = '0x73d8bd54f7cf5fab43fe4ef40a62d390644946db'
IDOL  = '0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07'
# BscScan V2 (chainid=56)
BSC_V2 = 'https://api.etherscan.io/v2/api?chainid=56'
BSC_V1 = 'https://api.bscscan.com/api'

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

def fetch(url, timeout=15, headers=None):
    h = {'User-Agent': 'Mozilla/5.0 probe/z8', 'Accept': 'application/json'}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:    return json.loads(raw), r.status
            except: return raw.decode(errors='replace')[:300], r.status
    except urllib.error.HTTPError as e:
        try:    body = e.read().decode(errors='replace')[:200]
        except: body = ''
        return body, e.code
    except Exception as ex:
        return None, str(ex)

emit('=' * 72)
emit('PROBE addr_bscscan v2 —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit(f'Target: {ADDR}')
emit('=' * 72)

# ── 1. Contract check (already confirmed: 54 bytes bytecode) ─────────────────
emit('\n[1] Contract confirmed từ probe trước:')
emit('  is_contract = True')
emit('  bytecode = 54 bytes → RẤT NHỎ')
emit('  54 bytes phổ biến nhất: EIP-1167 minimal proxy clone (45 bytes + overhead)')
emit('  Hoặc: simple forwarding / beacon proxy')
emit('  → ĐÂY KHÔNG PHẢI full DEX pool (pool contract = 10-50KB+)')

# ── 2. TX list via V2 (no key — 5req/sec) ────────────────────────────────────
emit('\n[2] Transaction list — BscScan V2 (no API key):')
url_txlist = (f'{BSC_V2}&module=account&action=txlist'
              f'&address={ADDR}&startblock=0&endblock=99999999'
              f'&page=1&offset=20&sort=desc')
d, s = fetch(url_txlist)
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  Transactions found: {len(txs)}')
    if txs:
        first_ts = int(txs[-1].get('timeStamp', 0))
        last_ts  = int(txs[0].get('timeStamp', 0))
        first_dt = datetime.fromtimestamp(first_ts, tz.utc).strftime('%Y-%m-%d %H:%M')
        last_dt  = datetime.fromtimestamp(last_ts, tz.utc).strftime('%Y-%m-%d %H:%M')
        emit(f'  Oldest in sample: {first_dt}')
        emit(f'  Most recent: {last_dt}')
        emit(f'\n  {"Date":<18} {"Method":>12} {"To":<20} {"BNB":>10} {"Status"}')
        emit('  ' + '-' * 70)
        for tx in txs[:10]:
            ts = int(tx.get('timeStamp', 0))
            dt = datetime.fromtimestamp(ts, tz.utc).strftime('%Y-%m-%d %H:%M') if ts else '?'
            method = tx.get('methodId', '?')[:10]
            to_a   = tx.get('to', '?')
            value  = int(tx.get('value', 0)) / 1e18
            status = 'OK' if tx.get('isError','0') == '0' else 'FAIL'
            emit(f'  {dt:<18} {method:>12} {to_a[:20]:<20} {value:>10.4f} {status}')
elif s == 200 and isinstance(d, dict):
    emit(f'  status={d.get("status")} msg={d.get("message")} → {str(d.get("result",""))[:120]}')
else:
    emit(f'  HTTP status={s} response={str(d)[:120]}')
time.sleep(0.5)

# ── 3. Token transfers — IDOL ────────────────────────────────────────────────
emit(f'\n[3] BEP20 IDOL transfers (V2):')
url_tok = (f'{BSC_V2}&module=account&action=tokentx'
           f'&address={ADDR}&contractaddress={IDOL}'
           f'&page=1&offset=50&sort=desc')
d, s = fetch(url_tok)
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  IDOL transfers: {len(txs)}')
    if txs:
        emit(f'  {"Date":<18} {"Direction":<10} {"IDOL amount":>18} {"Counterpart"}')
        emit('  ' + '-' * 68)
        for tx in txs[:15]:
            ts = int(tx.get('timeStamp', 0))
            dt = datetime.fromtimestamp(ts, tz.utc).strftime('%Y-%m-%d %H:%M') if ts else '?'
            from_a = tx.get('from', '')
            to_a   = tx.get('to', '')
            decimals = int(tx.get('tokenDecimal', 18))
            val = int(tx.get('value', 0)) / (10 ** decimals)
            if to_a.lower() == ADDR.lower():
                direction = 'IN '
                counterpart = from_a
            else:
                direction = 'OUT'
                counterpart = to_a
            emit(f'  {dt:<18} {direction:<10} {val:>18,.2f}  {counterpart[:26]}')
elif s == 200 and isinstance(d, dict):
    emit(f'  {d.get("status")} {d.get("message")} → {str(d.get("result",""))[:100]}')
else:
    emit(f'  HTTP {s}: {str(d)[:100]}')
time.sleep(0.5)

# ── 4. All token transfers ────────────────────────────────────────────────────
emit(f'\n[4] All BEP20 token transfers (V2, last 20):')
url_all = (f'{BSC_V2}&module=account&action=tokentx'
           f'&address={ADDR}&page=1&offset=20&sort=desc')
d, s = fetch(url_all)
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  Token transfers: {len(txs)}')
    token_counts = {}
    for tx in txs:
        sym = tx.get('tokenSymbol', '?')
        token_counts[sym] = token_counts.get(sym, 0) + 1
    emit('  Tokens involved:')
    for sym, cnt in sorted(token_counts.items(), key=lambda x: -x[1]):
        emit(f'    {sym:<14}: {cnt} transfers')
elif s == 200 and isinstance(d, dict):
    emit(f'  {d.get("status")} {d.get("message")} → {str(d.get("result",""))[:100]}')
else:
    emit(f'  HTTP {s}: {str(d)[:100]}')
time.sleep(0.5)

# ── 5. Contract ABI / source ─────────────────────────────────────────────────
emit('\n[5] Contract ABI (V2):')
url_abi = f'{BSC_V2}&module=contract&action=getabi&address={ADDR}'
d, s = fetch(url_abi)
if s == 200 and isinstance(d, dict):
    if d.get('status') == '1':
        try:
            abi = json.loads(d['result'])
            funcs  = [x['name'] for x in abi if x.get('type') == 'function']
            events = [x['name'] for x in abi if x.get('type') == 'event']
            emit(f'  VERIFIED. Functions: {funcs[:8]}')
            emit(f'  Events: {events[:5]}')
        except:
            emit(f'  ABI raw: {str(d.get("result",""))[:150]}')
    else:
        emit(f'  Not verified: {d.get("message","?")}')
else:
    emit(f'  HTTP {s}: {str(d)[:80]}')
time.sleep(0.5)

# ── 6. GeckoTerminal — pool check ────────────────────────────────────────────
emit('\n[6] GeckoTerminal — check if this address is a known pool:')
gt_url = f'https://api.geckoterminal.com/api/v2/networks/bsc/pools/{ADDR}'
d, s = fetch(gt_url, headers={'Accept': 'application/json;version=20230302'})
if s == 200 and isinstance(d, dict):
    attrs = d.get('data', {}).get('attributes', {})
    emit(f'  Pool found on GeckoTerminal!')
    emit(f'  Name: {attrs.get("name","?")}')
    emit(f'  Vol 24h: ${float(attrs.get("volume_usd",{}).get("h24",0) or 0):,.0f}')
    emit(f'  Created: {attrs.get("pool_created_at","?")}')
    rel = d.get('data', {}).get('relationships', {})
    emit(f'  DEX: {rel.get("dex",{}).get("data",{}).get("id","?")}')
elif s == 404:
    emit(f'  NOT a known pool address on GeckoTerminal (404)')
    emit(f'  → Address có thể là router, bot, hoặc proxy contract')
else:
    emit(f'  GeckoTerminal: status={s} {str(d)[:100]}')

# ── 7. VERDICT ───────────────────────────────────────────────────────────────
emit('\n' + '=' * 72)
emit('VERDICT:')
emit(f'  Address: {ADDR}')
emit('  Bytecode: 54 bytes → minimal proxy (EIP-1167 clone) hoặc simple forwarder')
emit('  → KHÔNG phải full DEX pool contract (pool = 10-50KB bytecode)')
emit('  → Có thể là: Binance Alpha router, aggregator proxy, hoặc MEV bot proxy')
emit()
emit('  Để xác định chắc chắn cần thêm:')
emit('  a) BscScan verified ABI → function signatures → biết contract làm gì')
emit('  b) Nansen label → nếu labeled "Binance Alpha" / "Exchange" / "MEV"')
emit('  c) Implementation address (nếu proxy) → trace đến contract thực')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
