#!/usr/bin/env python3
"""PROBE: Binance Alpha internal API.
Auth: session cookie từ browser (đăng nhập Binance web → F12 → Network → copy headers).

CÁCH LẤY COOKIE:
1. Mở https://www.binance.com/vi/alpha → đăng nhập
2. F12 → Network → filter "bapi/alpha"
3. Click vào bất kỳ request nào → Headers → Request Headers
4. Copy toàn bộ Cookie header vào BNC_COOKIE bên dưới
5. Copy Csrftoken vào BNC_CSRF

Endpoints thử:
- /bapi/alpha/v1/friendly/alpha/asset/list   → danh sách Alpha tokens
- /bapi/alpha/v1/friendly/alpha/asset/detail → chi tiết 1 token (IDOL?)
- /bapi/alpha/v1/friendly/alpha/market/kline → klines data
"""
import sys, io, json, time, uuid, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz

WHALE = Path(r'D:\Data back test\whale_data')
OUT   = WHALE / 'docs' / 'reports' / '_probe_binance_alpha_api.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

# ─── OPERATOR: paste session cookie từ browser ────────────────────────────────
BNC_COOKIE = ""   # paste full Cookie header tại đây
BNC_CSRF   = ""   # paste Csrftoken value tại đây
# ─────────────────────────────────────────────────────────────────────────────

IDOL_CONTRACT = "0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07"  # BSC contract IDOL
BASE = "https://www.binance.com"

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

def fetch_alpha(path, params=None, method='GET', body=None, timeout=15):
    """Call Binance Alpha internal API."""
    if params:
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        url = f'{BASE}{path}?{qs}'
    else:
        url = f'{BASE}{path}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.binance.com',
        'Referer': 'https://www.binance.com/vi/alpha',
        'X-Trace-Id': str(uuid.uuid4()),
        'X-Ui-Request-Trace': str(uuid.uuid4()),
    }
    if BNC_COOKIE:
        headers['Cookie'] = BNC_COOKIE
    if BNC_CSRF:
        headers['Csrftoken'] = BNC_CSRF
        headers['X-Csrf-Token'] = BNC_CSRF
    if body:
        headers['Content-Type'] = 'application/json'

    data_bytes = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, headers=headers, method=method, data=data_bytes)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:    return json.loads(raw), r.status
            except: return raw.decode(errors='replace')[:400], r.status
    except urllib.error.HTTPError as e:
        try:    body_e = e.read().decode(errors='replace')[:200]
        except: body_e = ''
        return body_e, e.code
    except Exception as ex:
        return None, str(ex)

emit('=' * 72)
emit('PROBE binance_alpha_api —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit(f'Cookie present: {bool(BNC_COOKIE)}')
emit('=' * 72)

if not BNC_COOKIE:
    emit('\n[WARN] BNC_COOKIE rỗng — một số endpoint có thể trả 401/403')
    emit('Các endpoint public (không cần login) vẫn được thử.')

# ── 1. Asset list (public?) ────────────────────────────────────────────────────
emit('\n[1] Alpha asset list — tất cả tokens trên Binance Alpha:')
ASSET_LIST_ENDPOINTS = [
    '/bapi/alpha/v1/friendly/alpha/asset/list',
    '/bapi/alpha/v2/friendly/alpha/asset/list',
    '/bapi/alpha/v1/public/alpha/asset/list',
]
for ep in ASSET_LIST_ENDPOINTS:
    d, s = fetch_alpha(ep, params={'pageSize': 50, 'pageIndex': 1})
    emit(f'  {ep}: status={s}')
    if s == 200 and isinstance(d, dict):
        code = d.get('code', '?')
        emit(f'    code={code}')
        data = d.get('data', {})
        if isinstance(data, dict):
            total = data.get('total', '?')
            items = data.get('list', data.get('items', data.get('data', [])))
            emit(f'    total={total}, items_returned={len(items) if isinstance(items, list) else "?"}')
            if isinstance(items, list) and items:
                # Find IDOL
                for item in items:
                    sym = item.get('symbol','') or item.get('assetCode','')
                    if 'IDOL' in str(sym).upper():
                        emit(f'    *** IDOL FOUND: {json.dumps(item)[:200]}')
                emit(f'    Sample first item: {json.dumps(items[0])[:200]}')
        elif isinstance(data, list):
            emit(f'    items={len(data)}')
            for item in data:
                sym = item.get('symbol','') or item.get('assetCode','')
                if 'IDOL' in str(sym).upper():
                    emit(f'    *** IDOL FOUND: {json.dumps(item)[:200]}')
        break
    elif isinstance(d, str):
        emit(f'    Response: {d[:150]}')
    time.sleep(0.3)

time.sleep(0.5)

# ── 2. Search by contract address ────────────────────────────────────────────
emit('\n[2] Search IDOL by contract address:')
SEARCH_ENDPOINTS = [
    ('/bapi/alpha/v1/friendly/alpha/asset/detail', {'contractAddress': IDOL_CONTRACT}),
    ('/bapi/alpha/v1/friendly/alpha/asset/search', {'keyword': 'IDOL', 'pageSize': 10}),
    ('/bapi/alpha/v1/friendly/alpha/asset/search', {'keyword': IDOL_CONTRACT, 'pageSize': 10}),
    ('/bapi/alpha/v2/friendly/alpha/asset/detail', {'contractAddress': IDOL_CONTRACT}),
    ('/bapi/alpha/v1/friendly/alpha/market/asset',
     {'network': 'BSC', 'contractAddress': IDOL_CONTRACT}),
]
for ep, params in SEARCH_ENDPOINTS:
    d, s = fetch_alpha(ep, params=params)
    emit(f'  {ep}')
    emit(f'    params={params}  status={s}')
    if s == 200 and isinstance(d, dict):
        emit(f'    code={d.get("code","?")} data={str(d.get("data",""))[:150]}')
        if d.get('data'):
            emit(f'    *** DATA FOUND')
    elif isinstance(d, str):
        emit(f'    {d[:100]}')
    time.sleep(0.3)

time.sleep(0.5)

# ── 3. Klines endpoint ────────────────────────────────────────────────────────
emit('\n[3] Alpha klines (price/vol) — thử với IDOL:')
import time as time_mod
now_ms = int(time_mod.time() * 1000)
DAY_MS = 86_400_000
start_ms = now_ms - 7 * DAY_MS

KLINE_ENDPOINTS = [
    ('/bapi/alpha/v1/friendly/alpha/market/kline', {
        'contractAddress': IDOL_CONTRACT,
        'network': 'BSC',
        'interval': '1d',
        'startTime': start_ms,
        'endTime': now_ms,
        'limit': 7
    }),
    ('/bapi/alpha/v1/friendly/alpha/market/kline', {
        'symbol': 'IDOL',
        'interval': '1d',
        'limit': 7
    }),
]
for ep, params in KLINE_ENDPOINTS:
    d, s = fetch_alpha(ep, params=params)
    emit(f'  {ep}: status={s}')
    if s == 200 and isinstance(d, dict):
        emit(f'    code={d.get("code","?")}')
        data = d.get('data')
        if data:
            emit(f'    klines found: {len(data) if isinstance(data, list) else "?"}')
            if isinstance(data, list) and data:
                emit(f'    Sample: {json.dumps(data[0])[:150]}')
    elif isinstance(d, str):
        emit(f'    {d[:120]}')
    time.sleep(0.3)

# ── 4. Trade/order flow (cần login) ──────────────────────────────────────────
emit('\n[4] Thử endpoint cần auth (sẽ 401/403 nếu không có cookie):')
AUTH_ENDPOINTS = [
    '/bapi/alpha/v1/private/alpha/trade/order/history',
    '/bapi/alpha/v1/private/alpha/user/balance',
    '/bapi/alpha/v1/friendly/alpha/user/alpha/list',
]
for ep in AUTH_ENDPOINTS:
    d, s = fetch_alpha(ep)
    emit(f'  {ep}: status={s}')
    if isinstance(d, dict):
        emit(f'    code={d.get("code","?")} msg={str(d.get("message",""))[:60]}')
    elif isinstance(d, str):
        emit(f'    {d[:80]}')
    time.sleep(0.3)

emit('\n' + '=' * 72)
emit('TÓM TẮT kết quả (xem chi tiết bên trên):')
emit('Nếu status=401/403 và cookie rỗng → cần login session')
emit('Nếu status=200 code="000000" → endpoint public, không cần auth')
emit('Nếu IDOL FOUND → token có trên Binance Alpha')
emit('Nếu IDOL NOT FOUND + 200 → IDOL không có trên Binance Alpha (confirmed)')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
