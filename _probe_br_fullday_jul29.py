"""
Probe: keo TRON ngay Jul29 BR@Gate qua from/to filter.
Muc tieu:
  1. Dem trades nhan duoc, kiem timestamp phu 00:00 → 23:59 UTC
  2. Tinh sum(size * price) = vol_usdt
  3. Lay kline BR_USDT Jul29 tu Gate, lay vol_quote tu kline
  4. So sanh: phai khop +-5% → one-shot hop le

Output: docs/reports/_probe_br_fullday_jul29.txt
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("D:/Data back test/whale_data/docs/reports/_probe_br_fullday_jul29.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

BASE = "https://api.gateio.ws/api/v4"
PAIR = "BR_USDT"
LIMIT = 1000

# Jul 29 2026 UTC window
DAY_START = int(datetime(2026, 7, 29, 0, 0, 0, tzinfo=timezone.utc).timestamp())
DAY_END   = int(datetime(2026, 7, 29, 23, 59, 59, tzinfo=timezone.utc).timestamp())


def gate_get(path, params):
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}{path}?{qs}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "probe/1.0",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


lines = []
log = lambda s: (lines.append(s), print(s))

log(f"Probe: BR_USDT full-day Jul29 2026")
log(f"DAY_START: {datetime.fromtimestamp(DAY_START, timezone.utc)}")
log(f"DAY_END:   {datetime.fromtimestamp(DAY_END, timezone.utc)}")
log("")

# --- Pull all trades via page pagination ---
all_trades = []
page = 1
while True:
    params = {
        "currency_pair": PAIR,
        "limit": LIMIT,
        "from": DAY_START,
        "to": DAY_END,
        "reverse": "false",  # oldest first
        "page": page,
    }
    batch = gate_get("/spot/trades", params)
    log(f"  page {page}: {len(batch)} trades")
    if not batch:
        break
    all_trades.extend(batch)
    if len(batch) < LIMIT:
        break
    page += 1
    time.sleep(0.3)  # polite

log(f"\nTotal trades pulled: {len(all_trades)}")

if not all_trades:
    log("ERROR: no trades returned")
else:
    times_s = [float(t.get("create_time", 0)) for t in all_trades]
    t_min = min(times_s)
    t_max = max(times_s)

    log(f"Timestamp range:")
    log(f"  Oldest: {datetime.fromtimestamp(t_min, timezone.utc)} (epoch {t_min:.0f})")
    log(f"  Newest: {datetime.fromtimestamp(t_max, timezone.utc)} (epoch {t_max:.0f})")
    log(f"  Window coverage: {(t_max - t_min)/3600:.2f}h")

    # Check coverage
    gap_start = t_min - DAY_START
    gap_end   = DAY_END - t_max
    log(f"  Gap from day start: {gap_start:.0f}s ({gap_start/60:.1f} min)")
    log(f"  Gap to day end:     {gap_end:.0f}s ({gap_end/60:.1f} min)")

    in_window = sum(1 for ts in times_s if DAY_START <= ts <= DAY_END)
    log(f"  Trades within Jul29 window: {in_window}/{len(all_trades)}")

    # Compute tape vol
    vol_tape = 0.0
    for t in all_trades:
        try:
            size  = float(t.get("amount", 0))
            price = float(t.get("price", 0))
            vol_tape += size * price
        except (ValueError, TypeError):
            pass

    log(f"\nTape vol (sum size*price): ${vol_tape:,.2f} USDT")

# --- Kline vol for Jul29 ---
log("\n--- Kline cross-check ---")
try:
    # /spot/candlesticks: interval=1d, from=DAY_START, to=DAY_END+1
    klines = gate_get("/spot/candlesticks", {
        "currency_pair": PAIR,
        "interval": "1d",
        "from": DAY_START,
        "to": DAY_END + 1,
        "limit": 2,
    })
    log(f"Klines returned: {len(klines)}")
    for k in klines:
        # Gate kline format: [timestamp, vol_quote, open, high, low, close, vol_base, ...]
        ts   = float(k[0])
        vol_q = float(k[1])   # quote vol (USDT)
        close = float(k[5])
        dt   = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
        log(f"  {dt}: vol_quote=${vol_q:,.2f} USDT  close={close}")

    # Pick Jul29 kline
    jul29_kline = next((k for k in klines
                        if datetime.fromtimestamp(float(k[0]), timezone.utc).date().isoformat() == "2026-07-29"),
                       None)

    if jul29_kline and all_trades:
        vol_kline = float(jul29_kline[1])
        diff_pct  = abs(vol_tape - vol_kline) / vol_kline * 100
        log(f"\n=== COMPARISON ===")
        log(f"  Tape vol  (probe):  ${vol_tape:,.2f}")
        log(f"  Kline vol (Gate):   ${vol_kline:,.2f}")
        log(f"  Difference: {diff_pct:.1f}%")
        if diff_pct <= 5:
            log(f"  VERDICT: PASS — diff {diff_pct:.1f}% ≤ 5% → one-shot daily la du cho BR")
        else:
            log(f"  VERDICT: FAIL — diff {diff_pct:.1f}% > 5% → one-shot co the bi thieu trade")
    elif not jul29_kline:
        log("  WARNING: Jul29 kline not found in response")

except Exception as e:
    log(f"  Kline ERROR: {e}")

text = "\n".join(lines)
OUT.write_text(text, encoding="utf-8")
print(f"\nWritten: {OUT}")
