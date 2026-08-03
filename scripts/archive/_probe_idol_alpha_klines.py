#!/usr/bin/env python3
"""PROBE: IDOL Binance Alpha klines via public endpoint.
Endpoint: /bapi/defi/v1/public/alpha-trade/klines (PUBLIC — no auth)
IDOL alpha_id = ALPHA_223  (từ _calib_alpha_daily.py trong Check onchain project)
CAUTION: taker field broken (klines[9]==klines[5]) — dùng vol only.
"""
import sys, io, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz, timedelta

WHALE = Path(r'D:\Data back test\whale_data')
OUT   = WHALE / 'docs' / 'reports' / '_probe_idol_alpha_klines.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

ALPHA_ID  = 'ALPHA_223'          # IDOL
SYMBOL    = f'{ALPHA_ID}USDT'
BASE      = 'https://www.binance.com'
ENDPOINT  = '/bapi/defi/v1/public/alpha-trade/klines'

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

def fetch_klines(symbol, interval='1d', start_ms=None, limit=60):
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_ms: params['startTime'] = start_ms
    qs  = '&'.join(f'{k}={v}' for k, v in params.items())
    url = f'{BASE}{ENDPOINT}?{qs}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.binance.com/vi/alpha',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            d = json.loads(raw)
            return d if isinstance(d, list) else d.get('data', [])
    except urllib.error.HTTPError as e:
        emit(f'  HTTP {e.code}: {e.read().decode(errors="replace")[:100]}')
        return []
    except Exception as ex:
        emit(f'  Error: {ex}')
        return []

emit('=' * 72)
emit('PROBE idol_alpha_klines —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit(f'Symbol: {SYMBOL}  (IDOL alpha_id={ALPHA_ID})')
emit(f'Endpoint: {BASE}{ENDPOINT}')
emit('CAUTION: taker = klines[9]==klines[5] always — NOT real signal')
emit('=' * 72)

# ── 1. Full history — tất cả ngày có alpha data ────────────────────────────
emit('\n[1] Full Alpha klines history (limit=90):')
WIN_START = datetime(2026, 6, 1, tzinfo=tz.utc)
start_ms  = int(WIN_START.timestamp() * 1000)

rows = fetch_klines(SYMBOL, interval='1d', start_ms=start_ms, limit=90)
emit(f'  Rows returned: {len(rows)}')

daily = {}
for k in rows:
    if not isinstance(k, (list, tuple)) or len(k) < 8:
        continue
    open_time_ms = int(k[0])
    dt = datetime.fromtimestamp(open_time_ms / 1000, tz.utc)
    d_str = dt.strftime('%Y-%m-%d')
    open_px  = float(k[1] or 0)
    high_px  = float(k[2] or 0)
    low_px   = float(k[3] or 0)
    close_px = float(k[4] or 0)
    base_vol = float(k[5] or 0)   # IDOL token vol
    quote_vol= float(k[7] or 0)   # USD vol
    n_trades = int(k[8]) if len(k) > 8 else 0
    # klines[9] = taker_buy_base_vol — BROKEN (==base_vol)
    daily[d_str] = {
        'open': open_px, 'high': high_px, 'low': low_px, 'close': close_px,
        'base_vol': base_vol, 'quote_vol': quote_vol, 'n_trades': n_trades
    }

emit(f'\n  {"date":<12} {"open":>9} {"high":>9} {"low":>9} {"close":>9} '
     f'{"vol_IDOL_M":>12} {"vol_USD_M":>10} {"n_trades":>9}')
emit('  ' + '-' * 80)

for d in sorted(daily):
    r = daily[d]
    emit(f'  {d:<12} {r["open"]:>9.5f} {r["high"]:>9.5f} {r["low"]:>9.5f} '
         f'{r["close"]:>9.5f} {r["base_vol"]/1e6:>12.3f}M '
         f'{r["quote_vol"]/1e6:>10.3f}M {r["n_trades"]:>9,}')

# ── 2. Focus window: 20/07→02/08 ─────────────────────────────────────────
emit('\n\n[2] WINDOW 20/07→02/08 — so sánh Alpha vol vs Perp vol:')
PERP_VOL = {
    '2026-07-20': 1_531_800, '2026-07-21': 563_300,  '2026-07-22': 454_300,
    '2026-07-23': 18_683_300,'2026-07-24': 4_809_300, '2026-07-25': 1_380_400,
    '2026-07-26': 641_900,   '2026-07-27': 9_834_000, '2026-07-28': 1_770_600,
    '2026-07-29': 1_126_900, '2026-07-30': 1_024_700, '2026-07-31': 1_434_500,
    '2026-08-01': 31_831_100,'2026-08-02': 7_319_100,
}

emit(f'\n  {"date":<12} {"alpha_USD_M":>12} {"perp_USD_M":>12} '
     f'{"alpha/perp":>11} {"suspect?":>10}')
emit('  ' + '-' * 62)

suspect_days = []
for d in sorted(PERP_VOL):
    row = daily.get(d)
    if not row:
        emit(f'  {d:<12} {"NO_DATA":>12} {PERP_VOL[d]/1e6:>12.3f}M {"—":>11} {"—":>10}')
        continue
    alpha_usd = row['quote_vol']
    perp_usd  = PERP_VOL[d]
    ratio = alpha_usd / perp_usd if perp_usd > 0 else 0
    # L-29: alpha_vol_suspect = alpha/perp > 3x → ABSTAIN flow conclusions
    suspect = ratio > 3.0
    if suspect: suspect_days.append(d)
    flag = '  ← SUSPECT(>3x)' if suspect else ''
    emit(f'  {d:<12} {alpha_usd/1e6:>12.3f}M {perp_usd/1e6:>12.3f}M '
         f'{ratio:>11.3f}x {"SUSPECT" if suspect else "SACH":>10}{flag}')

# ── 3. Sức chứa W2 re-run với alpha vol thực ──────────────────────────────
emit('\n\n[3] W2 SỨC CHỨA — re-run với Alpha vol thực (thay proxy perp):')
window = {d: v for d, v in daily.items()
          if '2026-07-25' <= d <= '2026-08-02'}
if window:
    total_alpha = sum(r['quote_vol'] for r in window.values())
    px_min = min(r['low'] for r in window.values())
    px_max = max(r['high'] for r in window.values())
    notional_low  = 273e6 * px_min
    notional_high = 273e6 * px_max
    emit(f'  Total Alpha vol (25/07→02/08): ${total_alpha/1e6:.3f}M')
    emit(f'  273M notional range: ${notional_low/1e6:.2f}M → ${notional_high/1e6:.2f}M')
    if total_alpha > 0:
        pct = notional_high / total_alpha * 100
        emit(f'  Notional/alpha_vol (worst case): {pct:.1f}%')
        if pct < 50:
            emit(f'  W2 verdict: ĐỦ SỨC CHỨA (notional < 50% vol)')
        elif pct < 100:
            emit(f'  W2 verdict: BIÊN (notional {pct:.0f}% vol — có thể chứa nhưng thin)')
        else:
            emit(f'  W2 verdict: MỎ NGỎNG (notional > vol — không thể gom đủ trên Alpha)')
    emit()
    # L-06 threshold: 2x notional = $8-12M
    l06_thresh = notional_high * 2
    emit(f'  L-06 threshold (2x notional high): ${l06_thresh/1e6:.2f}M')
    emit(f'  Alpha vol vs L-06: {"PASS" if total_alpha >= l06_thresh else "FAIL"} '
         f'(${total_alpha/1e6:.2f}M {"≥" if total_alpha >= l06_thresh else "<"} ${l06_thresh/1e6:.2f}M)')

# ── 4. Verdict ────────────────────────────────────────────────────────────
emit('\n\n[4] VERDICT:')
emit('  Nguồn: Binance Alpha public endpoint (không cần auth)')
emit('  Taker: ABSTAIN (broken, klines[9]==klines[5] luôn)')
emit(f'  Suspect days (alpha/perp > 3x): {suspect_days if suspect_days else "none"}')
if window:
    emit(f'  Alpha vol window 25/07→02/08: ${total_alpha/1e6:.3f}M')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
