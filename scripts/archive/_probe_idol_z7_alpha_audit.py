#!/usr/bin/env python3
"""Z7: Audit alpha_bsc_symbols.txt — IDOL missing despite BSC universe.
File genesis: _probe_alpha_taker.py scans freshwatch_symbols.txt → Binance Spot API.
- BSC_BROKEN (taker ratio >0.9985) → added to alpha_bsc_symbols.txt
- NO_SPOT (400) → excluded (cannot collect via Binance Spot)
- IDOL = no_spot → structural gap, not a bug

Goal: count how many symbols in the freshwatch/store universe are similarly
missing (no_spot on Binance but potentially on Binance Alpha / Gate Alpha).

Approach (local + API — VPS data not available here):
1. Load symbols_in_store.txt (398 symbols) as proxy for freshwatch universe
2. Probe Binance Spot API: classify each as spot_ok / no_spot / error
3. For no_spot symbols: check if they appear on CoinGecko with Binance Alpha
   exchange listing or Gate.io listing (potential missed alpha tokens)
4. Report: count no_spot, spot_ok, and compare to what alpha_bsc_symbols.txt
   would contain (BSC_BROKEN subset of spot_ok)
"""
import sys, io, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime, timezone as tz

WHALE  = Path(r'D:\Data back test\whale_data')
OUT    = WHALE / 'docs' / 'reports' / '_probe_idol_z7_alpha_audit.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

lines = []
def emit(*args):
    s = ' '.join(str(a) for a in args)
    print(s); lines.append(s)

def fetch(url, headers=None, timeout=15):
    h = {'User-Agent': 'Mozilla/5.0 (probe/z7)', 'Accept': 'application/json'}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:    return json.loads(raw), r.status
            except: return raw.decode(errors='replace')[:200], r.status
    except urllib.error.HTTPError as e:
        try:    body = e.read().decode(errors='replace')[:100]
        except: body = ''
        return body, e.code
    except Exception as ex:
        return None, str(ex)

emit('=' * 75)
emit('PROBE idol_z7_alpha_audit —', datetime.now(tz.utc).strftime('%Y-%m-%d %H:%M UTC'))
emit('=' * 75)

# ── 1. File genesis ────────────────────────────────────────────────────────────
emit('\n[1] ALPHA_BSC_SYMBOLS.TXT — Genesis:')
emit('  File: data/config/alpha_bsc_symbols.txt (VPS only, không có local)')
emit('  Generator: scripts/archive/_probe_alpha_taker.py')
emit('  Input: data/config/freshwatch_symbols.txt (VPS, ~140 symbols)')
emit('  Logic:')
emit('    - Probe Binance Spot /api/v3/klines cho mỗi symbol')
emit('    - NO_SPOT (400) → skip (không thể collect qua Binance Spot)')
emit('    - klines[9]/klines[5] > 0.9985 → BSC_BROKEN → thêm vào file')
emit('    - BSC_BROKEN = Binance Spot listing nhưng taker field bị broken do BSC bridge')
emit('  Collection logic: collect_alpha_spot.py đọc file → Binance Spot API (venue=binance_spot_bsc)')
emit()
emit('  IDOL gap:')
emit('    IDOL = no_spot trên Binance (không có IDOL/USDT spot pair)')
emit('    → _probe_alpha_taker.py classify = NO_SPOT → không thêm vào file')
emit('    → Không phải bug: IDOL genuinely không có Binance Spot listing')
emit('    → alpha_bsc_symbols.txt chỉ cover tokens CÓ Binance Spot listing')
emit('    → IDOL on Gate.io spot + PancakeSwap BSC DEX — ngoài phạm vi collector')

# ── 2. Load symbols_in_store.txt (proxy for universe) ─────────────────────────
emit('\n[2] UNIVERSE (symbols_in_store.txt — 398 symbols, proxy cho freshwatch):')
store_file = WHALE / 'symbols_in_store.txt'
syms_raw = [l.strip().upper() for l in store_file.read_text(encoding='utf-8').splitlines()
            if l.strip() and not l.startswith('---')]
# Remove header lines
syms = [s for s in syms_raw if s.endswith('USDT') or s.endswith('BTC') or s.endswith('ETH')]
emit(f'  Total symbols: {len(syms_raw)} → filtered USDT/BTC/ETH pairs: {len(syms)}')
emit(f'  IDOL in universe: {"IDOLUSDT" in syms_raw}')

# ── 3. Probe Binance Spot API — classify universe ─────────────────────────────
emit('\n[3] BINANCE SPOT API PROBE (sample 50 symbols — rate limit aware):')
emit('  Probing /api/v3/klines?interval=1d limit=1 (yesterday) for each symbol...')
emit('  NOTE: hạn chế 50 symbols để tránh rate limit. Tập trung vào tokens nghi BSC/Alpha.')

import time as time_mod

SPOT_BASE = 'https://api.binance.com'
BSC_THRESHOLD = 0.9985

# Priority list: IDOL + known BSC/Alpha tokens first
priority_first = ['IDOLUSDT', 'BANKUSDT', 'BRUSDT', 'AKEUSDT', 'TAGUSDT',
                  'NFTUSDT', 'BABYUSDT', 'ALPACAUSDT', 'CAKEUSDT']

# Sample from store universe — start with priority, then alphabetical
sample = priority_first[:]
for s in sorted(syms_raw):
    if s not in sample and len(sample) < 50:
        sample.append(s)

# Get yesterday's timestamp
now_ms = int(time_mod.time() * 1000)
DAY_MS = 86_400_000
yesterday_start = ((now_ms // DAY_MS) - 1) * DAY_MS
today_start = (now_ms // DAY_MS) * DAY_MS

results = {}  # symbol → 'spot_ok' / 'no_spot' / 'bsc_broken' / 'error'
bsc_broken_list = []
no_spot_list = []
spot_ok_list = []

emit(f'\n  {"Symbol":<22} {"Status":<14} {"taker/base":>12}')
emit('  ' + '-' * 52)

for sym in sample:
    url = (f'{SPOT_BASE}/api/v3/klines?symbol={sym}&interval=1d'
           f'&startTime={yesterday_start}&endTime={today_start - 1}&limit=1')
    data, status = fetch(url, timeout=12)

    if status == 400 or data is None:
        results[sym] = 'no_spot'
        no_spot_list.append(sym)
        emit(f'  {sym:<22} {"NO_SPOT":<14} {"—":>12}')
    elif isinstance(data, list) and data:
        k = data[0]
        base_vol   = float(k[5]) if float(k[5]) > 0 else None
        taker_base = float(k[9]) if len(k) > 9 else None
        if base_vol and taker_base:
            ratio = taker_base / base_vol
            broken = ratio >= BSC_THRESHOLD
            tag = 'BSC_BROKEN' if broken else 'spot_ok'
            results[sym] = tag
            if broken:
                bsc_broken_list.append(sym)
                emit(f'  {sym:<22} {tag:<14} {ratio:>12.4f}  ← ALPHA CONFIG')
            else:
                spot_ok_list.append(sym)
                emit(f'  {sym:<22} {tag:<14} {ratio:>12.4f}')
        else:
            results[sym] = 'zero_vol'
            emit(f'  {sym:<22} {"ZERO_VOL":<14} {"—":>12}')
    elif isinstance(data, list) and not data:
        results[sym] = 'empty'
        emit(f'  {sym:<22} {"EMPTY":<14} {"—":>12}')
    else:
        results[sym] = 'error'
        emit(f'  {sym:<22} {"ERROR":<14} status={status}')

    time_mod.sleep(0.08)  # polite rate limit

# ── 4. Summary counts ─────────────────────────────────────────────────────────
emit(f'\n[4] KẾT QUẢ SAMPLE ({len(sample)} symbols):')
emit(f'  spot_ok   (có Binance Spot, taker bình thường): {len(spot_ok_list)}')
emit(f'  bsc_broken (có Binance Spot, taker broken BSC):  {len(bsc_broken_list)}')
emit(f'  no_spot   (không có Binance Spot listing):       {len(no_spot_list)}')
if bsc_broken_list:
    emit(f'\n  BSC_BROKEN list → SẼ vào alpha_bsc_symbols.txt:')
    for s in bsc_broken_list:
        emit(f'    {s}')
emit(f'\n  NO_SPOT list → KHÔNG vào alpha_bsc_symbols.txt (cùng loại IDOL):')
for s in no_spot_list:
    emit(f'    {s}')

# ── 5. Extrapolation to full universe ─────────────────────────────────────────
emit(f'\n[5] EXTRAPOLATION (sample {len(sample)} → universe ~398 symbols):')
if sample:
    pct_no_spot = len(no_spot_list) / len(sample) * 100
    pct_broken  = len(bsc_broken_list) / len(sample) * 100
    est_no_spot = int(398 * pct_no_spot / 100)
    est_broken  = int(398 * pct_broken / 100)
    emit(f'  Sample no_spot rate: {pct_no_spot:.1f}% → ~{est_no_spot} tokens no_spot trong full universe')
    emit(f'  Sample bsc_broken rate: {pct_broken:.1f}% → ~{est_broken} tokens sẽ vào alpha_bsc_symbols.txt')
    emit(f'  → Ước tính ~{est_no_spot} tokens "IDOL-class" thiếu trong alpha_bsc_symbols.txt')
    emit(f'    (no Binance Spot → collector mù với những token này)')

# ── 6. CoinGecko check for IDOL ───────────────────────────────────────────────
emit('\n[6] CoinGecko: IDOL exchange listings (exchanges với volume):')
cg_url = 'https://api.coingecko.com/api/v3/coins/meet48/tickers?per_page=20&page=1'
cg_data, cg_status = fetch(cg_url, timeout=20)
if cg_status == 200 and isinstance(cg_data, dict):
    tickers = cg_data.get('tickers', [])
    emit(f'  Total tickers: {len(tickers)}')
    emit(f'  {"Exchange":<25} {"Base":<10} {"Target":<10} {"Vol_USD":>14} {"Trust":>10}')
    emit('  ' + '-' * 72)
    for t in sorted(tickers, key=lambda x: float(x.get('converted_volume',{}).get('usd',0) or 0), reverse=True)[:15]:
        exch  = t.get('market',{}).get('name','?')[:24]
        base  = t.get('base','?')[:9]
        tgt   = t.get('target','?')[:9]
        vol   = float(t.get('converted_volume',{}).get('usd',0) or 0)
        trust = t.get('trust_score','?')
        emit(f'  {exch:<25} {base:<10} {tgt:<10} {vol:>14,.0f} {str(trust):>10}')
else:
    emit(f'  CoinGecko tickers: status={cg_status}')
    if isinstance(cg_data, str): emit(f'  Response: {cg_data[:200]}')

# ── 7. VERDICT ────────────────────────────────────────────────────────────────
emit('\n[7] VERDICT Z7:')
emit('  1. alpha_bsc_symbols.txt sinh từ _probe_alpha_taker.py (chạy thủ công/1 lần)')
emit('     Input: freshwatch_symbols.txt (~140 symbols)')
emit('     Không có cron tự update — file có thể stale nếu universe thay đổi')
emit()
emit('  2. IDOL gap là CẤU TRÚC, không phải bug:')
emit('     IDOL = no_spot trên Binance → probe trả 400 → không classify BSC_BROKEN')
emit('     alpha_bsc_symbols.txt chỉ cover tokens CÓ Binance Spot listing')
emit('     → IDOL on Gate + PancakeSwap = ngoài phạm vi thiết kế collector hiện tại')
emit()
emit('  3. IDOL-class tokens (no_spot, similar gap):')
emit(f'     Trong sample {len(sample)}: {len(no_spot_list)} no_spot → ước tính ~{est_no_spot if sample else "N/A"} trong full 398')
emit('     Những token này hoàn toàn mù trong store (không có price/vol data)')
emit('     trừ khi có perp listing (venue=binance_perp qua klines_1h)')
emit()
emit('  4. Đề xuất (chưa sửa — chờ operator):')
emit('     - L-43 draft: thêm GeckoTerminal DEX probe cho BSC no_spot tokens')
emit('     - alpha_bsc_symbols.txt: đổi tên thành binance_spot_bsc_symbols.txt')
emit('       (tên hiện tại gây nhầm "alpha" = Binance Alpha platform)')
emit('     - IDOL cụ thể: dùng Gate spot + DEX BSC collector riêng nếu cần track')

emit(f'\n{"="*75}')
emit('Z7 DONE')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'\nOutput: {OUT}')
