#!/usr/bin/env python3
"""Test: alpha-trade/klines có trả lịch sử 30/07 không?
Dùng BANK (ALPHA_146) — symbol trong calib config.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import datetime, timezone as tz

UA = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*',
      'Referer': 'https://www.binance.com/vi/alpha'}
BASE = 'https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines'

def fetch(symbol, start_ms, end_ms, interval='1d'):
    url = (f'{BASE}?symbol={symbol}&interval={interval}'
           f'&startTime={start_ms}&endTime={end_ms}&limit=10')
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    return d if isinstance(d, list) else d.get('data', [])

# Ngày 30/07 UTC: 00:00 → 23:59:59
D0 = datetime(2026, 7, 30, 0,  0,  0, tzinfo=tz.utc)
D1 = datetime(2026, 7, 30, 23, 59, 59, tzinfo=tz.utc)
start_ms = int(D0.timestamp() * 1000)
end_ms   = int(D1.timestamp() * 1000)

print(f'Test window: {D0.date()} 00:00→23:59 UTC')
print(f'startTime={start_ms}  endTime={end_ms}')
print()

for sym, alpha_id in [('BANK', 'ALPHA_146'), ('TAG', 'ALPHA_233'), ('IDOL', 'ALPHA_223')]:
    symbol = f'{alpha_id}USDT'
    try:
        rows = fetch(symbol, start_ms, end_ms)
        if not rows:
            print(f'{sym} ({symbol}): 0 candles → EMPTY')
        else:
            ts0 = datetime.fromtimestamp(int(rows[0][0])/1000, tz.utc)
            ts1 = datetime.fromtimestamp(int(rows[-1][0])/1000, tz.utc)
            print(f'{sym} ({symbol}): {len(rows)} candles')
            print(f'  first: {ts0.strftime("%Y-%m-%d %H:%M UTC")}  '
                  f'close={float(rows[0][4]):.6f}  vol_usd={float(rows[0][7]):,.0f}')
            print(f'  last:  {ts1.strftime("%Y-%m-%d %H:%M UTC")}  '
                  f'close={float(rows[-1][4]):.6f}  vol_usd={float(rows[-1][7]):,.0f}')
    except Exception as e:
        print(f'{sym}: ERROR {e}')
    print()
