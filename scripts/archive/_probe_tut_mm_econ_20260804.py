#!/usr/bin/env python3
"""Probe: TUT MM-ECON forward analysis data — U1→U6."""
import csv, io, sys, json, time
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
STORE_DIR = Path(r"D:\Check onchain fresh wallets\data")

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ── 1. Load ALL TUT freshwatch rows ─────────────────────────────────────────
tut_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol","") == "TUTUSDT":
            tut_rows[r["date"]] = r

dates_fw = sorted(tut_rows.keys())
print(f"=== TUT freshwatch: {len(tut_rows)} rows ({dates_fw[0]} → {dates_fw[-1]})")

series_fw = []
for d in dates_fw:
    r = tut_rows[d]
    series_fw.append({
        'd': d,
        'px': gv(r,'px_avg'),
        'vol': gv(r,'vol_quote'),
        'oi': gv(r,'oi_usd'),
        'pr': gv(r,'lsr_pos_r'),
        'ar': gv(r,'lsr_acc_r'),
        'gl': gv(r,'lsr_global_r'),
        'fav': gv(r,'funding_avg'),
        'fn': gv(r,'funding_n'),
    })

print("\nFULL SERIES:")
for x in series_fw:
    oi_s = f"{x['oi']/1e6:.3f}M" if x['oi'] else "—"
    pr_s = f"{x['pr']:.3f}" if x['pr'] else "—"
    gl_s = f"{x['gl']:.4f}" if x['gl'] else "—"
    px_s = f"{x['px']:.5f}" if x['px'] else "—"
    vol_s = f"{x['vol']/1e6:.1f}M" if x['vol'] else "—"
    fav_s = f"{x['fav']:.5f}" if x['fav'] else "—"
    fn_s = str(int(x['fn'])) if x['fn'] else "—"
    print(f"  {x['d']}: px={px_s} OI={oi_s} pos_r={pr_s} gLSR={gl_s} vol={vol_s} f={fav_s} fn={fn_s}")

# OI delta series for U1
print("\n=== U1: OI DELTA SERIES (for B calculation) ===")
prev_oi = None
for x in series_fw:
    if x['oi'] and prev_oi:
        delta = x['oi'] - prev_oi
        sign = "+" if delta > 0 else ""
        px_s = f"{x['px']:.5f}" if x['px'] else "—"
        print(f"  {x['d']}: OI={x['oi']/1e6:.3f}M dOI={sign}{delta/1e6:.3f}M px={px_s}")
    prev_oi = x['oi']

# gLSR fuel-reload for U3
print("\n=== U3: gLSR fuel-reload analysis ===")
gl_vals = [(x['d'], x['gl']) for x in series_fw if x['gl']]
gl_min = min(gl_vals, key=lambda x: x[1])
print(f"gLSR min: {gl_min[1]:.4f} on {gl_min[0]}")
# Find where rebuild started (gLSR rising after min)
min_idx = next(i for i, x in enumerate(series_fw) if x['d'] == gl_min[0])
print(f"gLSR around min (±3 rows):")
for i in range(max(0, min_idx-3), min(len(series_fw), min_idx+4)):
    x = series_fw[i]
    gl_s = f"{x['gl']:.4f}" if x['gl'] else "—"
    oi_s = f"{x['oi']/1e6:.3f}M" if x['oi'] else "—"
    px_s = f"{x['px']:.5f}" if x['px'] else "—"
    print(f"  {'→' if i==min_idx else ' '} {x['d']}: gLSR={gl_s} OI={oi_s} px={px_s}")

# ── 2. Binance fapi native OI daily ─────────────────────────────────────────
print("\n=== U2: Binance fapi native OI (daily) ===")
url_oi_1d = "https://fapi.binance.com/fapi/v1/openInterestHist?symbol=TUTUSDT&period=1d&limit=60"
oi_1d = fetch_json(url_oi_1d)
if isinstance(oi_1d, list):
    print(f"Got {len(oi_1d)} daily OI rows")
    for row in oi_1d:
        ts = int(row['timestamp'])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        oi_usd = float(row['sumOpenInterestValue'])
        print(f"  {d}: OI={oi_usd/1e6:.3f}M (raw={row['sumOpenInterest']})")
else:
    print(f"Error: {oi_1d}")

# ── 3. Binance fapi native OI 1h from 28/07 ─────────────────────────────────
print("\n=== U2: Binance fapi native OI (1h, from 28/07) ===")
# startTime = 2026-07-28 00:00 UTC
start_ts = int(datetime(2026, 7, 28, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_oi_1h = f"https://fapi.binance.com/fapi/v1/openInterestHist?symbol=TUTUSDT&period=1h&startTime={start_ts}&limit=500"
oi_1h = fetch_json(url_oi_1h)
if isinstance(oi_1h, list):
    print(f"Got {len(oi_1h)} 1h OI rows (28/07→now)")
    # Print daily summary
    daily_oi = {}
    for row in oi_1h:
        ts = int(row['timestamp'])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        oi_usd = float(row['sumOpenInterestValue'])
        hr = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%H')
        if d not in daily_oi:
            daily_oi[d] = {'open': oi_usd, 'high': oi_usd, 'low': oi_usd, 'close': oi_usd, 'rows': []}
        daily_oi[d]['high'] = max(daily_oi[d]['high'], oi_usd)
        daily_oi[d]['low'] = min(daily_oi[d]['low'], oi_usd)
        daily_oi[d]['close'] = oi_usd
        daily_oi[d]['rows'].append((hr, oi_usd))
    print("Daily OI summary (1h data):")
    for d in sorted(daily_oi.keys()):
        v = daily_oi[d]
        print(f"  {d}: open={v['open']/1e6:.3f}M high={v['high']/1e6:.3f}M low={v['low']/1e6:.3f}M close={v['close']/1e6:.3f}M")
    # Last 24h detail
    print("\nLast 24h detail (1h):")
    for row in oi_1h[-24:]:
        ts = int(row['timestamp'])
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:00')
        oi_usd = float(row['sumOpenInterestValue'])
        print(f"  {dt}: OI={oi_usd/1e6:.3f}M")
else:
    print(f"Error: {oi_1h}")

# ── 4. Binance fapi klines daily 01/07→now (for OHLC + px ΔOI analysis) ─────
print("\n=== U1/U2: Binance fapi klines daily (01/07→now) ===")
start_ts2 = int(datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_klines_1d = f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT&interval=1d&startTime={start_ts2}&limit=60"
klines_1d = fetch_json(url_klines_1d)
if isinstance(klines_1d, list):
    print(f"Got {len(klines_1d)} daily klines")
    # columns: 0=open_time, 1=open, 2=high, 3=low, 4=close, 5=volume, 6=close_time, 7=quote_vol, 8=trades, 9=taker_buy_base, 10=taker_buy_quote
    for k in klines_1d:
        ts = int(k[0])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        color = "RED" if c < o else "GRN"
        ret = (c-o)/o*100
        print(f"  {d} [{color}] O={o:.5f} H={h:.5f} L={lo:.5f} C={c:.5f} ret={ret:+.1f}% vol={vol_usd/1e6:.1f}M")
else:
    print(f"Error: {klines_1d}")

# ── 5. Check VPS for 24-26/07 TUT data (U4) ─────────────────────────────────
print("\n=== U4: VPS store check for TUT 24-26/07 ===")
import subprocess
try:
    r = subprocess.run(
        ['ssh', 'root@5.223.67.21',
         'python3 -c "import pandas as pd, glob; '
         'files = glob.glob(\'/root/Data_back_test/whale_data/data/raw/klines_1h/TUTUSDT/2026-07-2*.parquet\'); '
         'print(\'Files:\', files); '
         '[print(pd.read_parquet(f).tail(3).to_string()) for f in files[:3]]"'],
        capture_output=True, text=True, timeout=20
    )
    print(r.stdout or "(no output)")
    if r.stderr: print("stderr:", r.stderr[:300])
except Exception as e:
    print(f"SSH error: {e}")

# Also check local store
print("\nLocal store check:")
local_raw = Path(r"D:\Check onchain fresh wallets\data\raw")
if local_raw.exists():
    tut_klines = list(local_raw.glob("**/TUTUSDT/**2026-07-2*.parquet")) + \
                 list(local_raw.glob("**/*TUTUSDT*2026-07-2*.parquet"))
    print(f"Local klines TUT Jul24-26: {tut_klines}")
else:
    print("local_raw not found at expected path")

# ── 6. Binance fapi klines 4h 01/07 (for build bucket analysis) ─────────────
print("\n=== U1 BUCKET: 4h klines TUT 06-22/07 ===")
start_ts3 = int(datetime(2026, 7, 6, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
end_ts3 = int(datetime(2026, 7, 23, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_4h = f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT&interval=4h&startTime={start_ts3}&endTime={end_ts3}&limit=200"
k4h = fetch_json(url_4h)
if isinstance(k4h, list):
    print(f"Got {len(k4h)} 4h klines (06-22/07)")
    total_vol = sum(float(k[7]) for k in k4h)
    # Red candle taker-weighted VWAP (build VWAP on red candles)
    red_vol_weighted = 0.0
    red_vol = 0.0
    grn_vol_weighted = 0.0
    grn_vol = 0.0
    print("Sample 4h candles (first 10 + last 10):")
    for i, k in enumerate(k4h):
        ts = int(k[0])
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        color = "RED" if c < o else "GRN"
        vwap = (h + lo + c) / 3  # typical price
        if c < o:
            red_vol_weighted += vwap * vol_usd
            red_vol += vol_usd
        else:
            grn_vol_weighted += vwap * vol_usd
            grn_vol += vol_usd
        if i < 10 or i >= len(k4h)-10:
            print(f"  {dt} [{color}] O={o:.5f} H={h:.5f} C={c:.5f} vol={vol_usd/1e6:.2f}M")
    print(f"\nRed candle VWAP (06-22/07): {red_vol_weighted/red_vol:.6f if red_vol else 'N/A'} (vol={red_vol/1e6:.1f}M)")
    print(f"Green candle VWAP (06-22/07): {grn_vol_weighted/grn_vol:.6f if grn_vol else 'N/A'} (vol={grn_vol/1e6:.1f}M)")
    print(f"Overall VWAP: {(red_vol_weighted+grn_vol_weighted)/(red_vol+grn_vol):.6f} (total vol={total_vol/1e6:.1f}M)")
else:
    print(f"Error: {k4h}")

print("\nDONE")
