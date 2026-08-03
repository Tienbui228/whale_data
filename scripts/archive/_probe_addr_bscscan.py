#!/usr/bin/env python3
"""Probe: identify 0x73d8...946db on BSC — pool or bot?
Sources: BscScan free (0-credit).
- Check contract vs EOA (eth_getCode)
- First/last tx, tx count
- Token transfers involving IDOL
- Contract name/ABI if verified
"""
import sys, io, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz

WHALE  = Path(r'D:\Data back test\whale_data')
OUT    = WHALE / 'docs' / 'reports' / '_probe_addr_bscscan.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

ADDR = '0x73d8bd54f7cf5fab43fe4ef40a62d390644946db'
IDOL = '0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07'  # IDOL BSC contract
BSCSCAN_BASE = 'https://api.bscscan.com/api'

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'probe/z8'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:    return json.loads(raw), r.status
            except: return raw.decode(errors='replace')[:300], r.status
    except urllib.error.HTTPError as e:
        try:    body = e.read().decode(errors='replace')[:150]
        except: body = ''
        return body, e.code
    except Exception as ex:
        return None, str(ex)

emit('=' * 72)
emit('PROBE addr_bscscan —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit(f'Target: {ADDR}')
emit('=' * 72)

# ── 1. Contract or EOA? ────────────────────────────────────────────────────────
emit('\n[1] Contract check (eth_getCode):')
d, s = fetch(f'{BSCSCAN_BASE}?module=proxy&action=eth_getCode&address={ADDR}&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict):
    code = d.get('result', '0x')
    is_contract = code != '0x' and len(code) > 4
    emit(f'  is_contract: {is_contract}')
    if is_contract:
        emit(f'  bytecode length: {(len(code)-2)//2} bytes')
    else:
        emit(f'  → EOA (externally owned account = bot/wallet, không phải pool contract)')
else:
    emit(f'  status={s}, fallback to tx probe')
time.sleep(0.3)

# ── 2. Transaction count + first/last tx ──────────────────────────────────────
emit('\n[2] Transaction list (last 10 txs, no key):')
d, s = fetch(f'{BSCSCAN_BASE}?module=account&action=txlist'
             f'&address={ADDR}&startblock=0&endblock=99999999'
             f'&page=1&offset=10&sort=desc&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  Recent tx count (sample): {len(txs)}')
    for tx in txs[:5]:
        ts = int(tx.get('timeStamp', 0))
        dt = datetime.fromtimestamp(ts, tz.utc).strftime('%Y-%m-%d %H:%M') if ts else '?'
        method = tx.get('methodId', '?')
        to_addr = tx.get('to', '?')
        value = int(tx.get('value', 0)) / 1e18
        emit(f'    {dt}  method={method}  to={to_addr[:20]}...  BNB={value:.4f}')
elif s == 200 and isinstance(d, dict):
    emit(f'  BscScan: status={d.get("status")} msg={d.get("message","?")} result={str(d.get("result",""))[:100]}')
else:
    emit(f'  status={s} response={str(d)[:100]}')
time.sleep(0.3)

# ── 3. BEP20 token transfers (IDOL) ──────────────────────────────────────────
emit(f'\n[3] BEP20 token transfers — IDOL ({IDOL[:12]}...) involving {ADDR[:12]}...:')
d, s = fetch(f'{BSCSCAN_BASE}?module=account&action=tokentx'
             f'&address={ADDR}&contractaddress={IDOL}'
             f'&page=1&offset=50&sort=desc&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  IDOL transfers found: {len(txs)}')
    if txs:
        emit(f'  {"Date":<18} {"From":<16} {"To":<16} {"IDOL amount":>16} {"direction"}')
        emit('  ' + '-' * 75)
        for tx in txs[:15]:
            ts = int(tx.get('timeStamp', 0))
            dt = datetime.fromtimestamp(ts, tz.utc).strftime('%Y-%m-%d %H:%M') if ts else '?'
            from_a = tx.get('from', '')
            to_a   = tx.get('to', '')
            decimals = int(tx.get('tokenDecimal', 18))
            val = int(tx.get('value', 0)) / (10 ** decimals)
            direction = 'IN ' if to_a.lower() == ADDR.lower() else 'OUT'
            emit(f'  {dt:<18} {from_a[:16]:<16} {to_a[:16]:<16} {val:>16,.2f}  {direction}')
elif s == 200 and isinstance(d, dict):
    emit(f'  BscScan: status={d.get("status")} msg={d.get("message")} → {str(d.get("result",""))[:80]}')
else:
    emit(f'  status={s} → {str(d)[:100]}')
time.sleep(0.3)

# ── 4. All BEP20 transfers (any token) — top tokens ──────────────────────────
emit(f'\n[4] All BEP20 token transfers (any token) — {ADDR[:16]}...:')
d, s = fetch(f'{BSCSCAN_BASE}?module=account&action=tokentx'
             f'&address={ADDR}&page=1&offset=50&sort=desc&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    txs = d.get('result', [])
    emit(f'  Total token transfers (recent 50): {len(txs)}')
    # Count by token
    token_counts = {}
    for tx in txs:
        sym = tx.get('tokenSymbol', '?')
        token_counts[sym] = token_counts.get(sym, 0) + 1
    for sym, cnt in sorted(token_counts.items(), key=lambda x: -x[1])[:10]:
        emit(f'    {sym:<12}: {cnt} transfers')
    # Show last 5 across all tokens
    emit(f'\n  Last 5 token transfers:')
    for tx in txs[:5]:
        ts = int(tx.get('timeStamp', 0))
        dt = datetime.fromtimestamp(ts, tz.utc).strftime('%Y-%m-%d %H:%M') if ts else '?'
        sym = tx.get('tokenSymbol', '?')
        from_a = tx.get('from', '')
        to_a   = tx.get('to', '')
        decimals = int(tx.get('tokenDecimal', 18))
        val = int(tx.get('value', 0)) / (10 ** decimals)
        direction = 'IN ' if to_a.lower() == ADDR.lower() else 'OUT'
        emit(f'    {dt}  {sym:<10} {val:>14,.2f}  {direction}  from={from_a[:14]}...')
elif s == 200 and isinstance(d, dict):
    emit(f'  BscScan: {d.get("status")} {d.get("message")} {str(d.get("result",""))[:80]}')
else:
    emit(f'  status={s} → {str(d)[:100]}')
time.sleep(0.3)

# ── 5. Contract ABI (if verified) ────────────────────────────────────────────
emit('\n[5] Contract ABI (nếu verified):')
d, s = fetch(f'{BSCSCAN_BASE}?module=contract&action=getabi'
             f'&address={ADDR}&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict):
    if d.get('status') == '1':
        abi_str = d.get('result', '')
        try:
            abi = json.loads(abi_str)
            funcs = [x['name'] for x in abi if x.get('type') == 'function']
            events = [x['name'] for x in abi if x.get('type') == 'event']
            emit(f'  Contract VERIFIED. Functions ({len(funcs)}): {funcs[:10]}')
            emit(f'  Events ({len(events)}): {events[:5]}')
        except:
            emit(f'  ABI found but parse error: {abi_str[:100]}')
    else:
        emit(f'  Not verified: {d.get("message","?")}')
else:
    emit(f'  status={s}')
time.sleep(0.3)

# ── 6. Contract source name ──────────────────────────────────────────────────
emit('\n[6] Contract source + name:')
d, s = fetch(f'{BSCSCAN_BASE}?module=contract&action=getsourcecode'
             f'&address={ADDR}&apikey=YourApiKeyToken')
if s == 200 and isinstance(d, dict) and d.get('status') == '1':
    res = d.get('result', [{}])
    if res:
        r = res[0]
        emit(f'  ContractName: {r.get("ContractName","?")}')
        emit(f'  CompilerVersion: {r.get("CompilerVersion","?")}')
        impl = r.get('Implementation', '')
        if impl:
            emit(f'  Implementation (proxy): {impl}')
else:
    emit(f'  status={s} {str(d)[:80]}')

emit('\n' + '=' * 72)
emit('PROBE DONE')
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
