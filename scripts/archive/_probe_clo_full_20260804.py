#!/usr/bin/env python3
"""Probe CLO: C1 series + C2 campaign hunt + C4 depth/overhang."""
import csv, io, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT = Path(r"D:\Data back test\whale_data\scratch\clo_probe_20260804.txt")
OUT.parent.mkdir(exist_ok=True)

lines = []
def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ── 1. Load ALL CLO freshwatch rows ─────────────────────────────────────────
clo_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol","") == "CLOUSDT":
            clo_rows[r["date"]] = r

dates_fw = sorted(clo_rows.keys())
p(f"=== CLO freshwatch: {len(clo_rows)} rows  ({dates_fw[0] if dates_fw else 'NONE'} → {dates_fw[-1] if dates_fw else 'NONE'})")

series_fw = []
for d in dates_fw:
    r = clo_rows[d]
    series_fw.append({
        'd': d,
        'px': gv(r,'px_avg'),
        'vol': gv(r,'vol_quote'),
        'tk': gv(r,'taker_pct'),
        'oi': gv(r,'oi_usd'),
        'pr': gv(r,'lsr_pos_r'),
        'ar': gv(r,'lsr_acc_r'),
        'gl': gv(r,'lsr_global_r'),
        'fav': gv(r,'funding_avg'),
        'fn': gv(r,'funding_n'),
        'div': gv(r,'div_avg3'),
        'slope': gv(r,'slope'),
        'dwall': gv(r,'dist_wall'),
        'ldist': gv(r,'lsr_dist'),
    })

p("\n=== C1: FULL SERIES (all freshwatch CLO) ===")
p(f"{'date':<12} {'px':>8} {'OI(M)':>8} {'vol(M)':>7} {'tk%':>6} {'pos_r':>6} {'acc_r':>6} {'gLSR':>7} {'fav':>8} {'fn':>3} {'dwall':>7} {'ldist':>7}")
for x in series_fw:
    px_s  = f"{x['px']:.5f}"  if x['px']   else "—"
    oi_s  = f"{x['oi']/1e6:.3f}" if x['oi'] else "—"
    vol_s = f"{x['vol']/1e6:.1f}" if x['vol'] else "—"
    tk_s  = f"{x['tk']:.1f}"  if x['tk']   else "—"
    pr_s  = f"{x['pr']:.3f}"  if x['pr']   else "—"
    ar_s  = f"{x['ar']:.3f}"  if x['ar']   else "—"
    gl_s  = f"{x['gl']:.4f}"  if x['gl']   else "—"
    fav_s = f"{x['fav']:.5f}" if x['fav']  else "—"
    fn_s  = str(int(x['fn'])) if x['fn']   else "—"
    dw_s  = f"{x['dwall']:.4f}" if x['dwall'] else "—"
    ld_s  = f"{x['ldist']:.4f}" if x['ldist'] else "—"
    p(f"{x['d']:<12} {px_s:>8} {oi_s:>8} {vol_s:>7} {tk_s:>6} {pr_s:>6} {ar_s:>6} {gl_s:>7} {fav_s:>8} {fn_s:>3} {dw_s:>7} {ld_s:>7}")

# C1 window 22/07→04/08
p("\n=== C1: WINDOW 22/07→04/08 (detailed) ===")
c1 = [x for x in series_fw if x['d'] >= "2026-07-22"]
for x in c1:
    div_s = f"{x['div']:.4f}" if x['div'] else "—"
    sl_s  = f"{x['slope']:.4f}" if x['slope'] else "—"
    px_s  = f"{x['px']:.5f}" if x['px'] else "—"
    oi_s  = f"{x['oi']/1e6:.3f}M" if x['oi'] else "—"
    gl_s  = f"{x['gl']:.4f}" if x['gl'] else "—"
    p(f"  {x['d']}: px={px_s} OI={oi_s} gLSR={gl_s} div={div_s} slope={sl_s}")

# gLSR check: reached 0.85?
p("\n=== C1: gLSR trend check ===")
gl_vals = [(x['d'], x['gl']) for x in series_fw if x['gl']]
if gl_vals:
    gl_min = min(gl_vals, key=lambda x: x[1])
    gl_max = max(gl_vals, key=lambda x: x[1])
    p(f"gLSR min: {gl_min[1]:.4f} on {gl_min[0]}")
    p(f"gLSR max: {gl_max[1]:.4f} on {gl_max[0]}")
    below85 = [(d, v) for d, v in gl_vals if v < 0.85]
    p(f"gLSR < 0.85: {len(below85)} rows: {below85[:5]}")
    # recent gLSR (last 14 days)
    recent_gl = [(x['d'], x['gl']) for x in series_fw[-14:] if x['gl']]
    p(f"Recent gLSR (last 14 rows): {[(d, f'{v:.4f}') for d,v in recent_gl]}")

# ── 2. Binance fapi klines daily 01/03→now ───────────────────────────────────
p("\n=== C2: Binance fapi klines daily 01/03→04/08 ===")
start_ts = int(datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_kd = f"https://fapi.binance.com/fapi/v1/klines?symbol=CLOUSDT&interval=1d&startTime={start_ts}&limit=200"
kd = fetch_json(url_kd)
if isinstance(kd, list):
    p(f"Got {len(kd)} daily klines (01/03→now)")
    for k in kd:
        ts = int(k[0]); d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        color = "RED" if c < o else "GRN"
        ret = (c-o)/o*100
        tb_q = float(k[10])   # taker buy quote
        tk_pct = tb_q/vol_usd*100 if vol_usd > 0 else 0
        p(f"  {d} [{color}] O={o:.5f} H={h:.5f} L={lo:.5f} C={c:.5f} ret={ret:+.1f}% vol={vol_usd/1e6:.2f}M tk={tk_pct:.1f}%")
else:
    p(f"Error klines daily: {kd}")

# ── 3. Binance fapi OI daily ─────────────────────────────────────────────────
p("\n=== C2: OI daily (futures/data endpoint) ===")
url_oi = "https://fapi.binance.com/futures/data/openInterestHist?symbol=CLOUSDT&period=1d&limit=90"
oi_d = fetch_json(url_oi)
if isinstance(oi_d, list):
    p(f"Got {len(oi_d)} OI daily rows")
    for row in oi_d:
        ts = int(row['timestamp']); d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        oi_usd = float(row['sumOpenInterestValue'])
        p(f"  {d}: OI={oi_usd/1e6:.3f}M tokens={row['sumOpenInterest']}")
else:
    p(f"Error OI daily: {oi_d}")

# ── 4. Binance fapi funding rate history ─────────────────────────────────────
p("\n=== C2: Funding rate history (01/04→04/08) ===")
# API: GET /fapi/v1/fundingRate - max 1000
start_fund = int(datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_fund = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=CLOUSDT&startTime={start_fund}&limit=1000"
fund = fetch_json(url_fund)
if isinstance(fund, list):
    p(f"Got {len(fund)} funding rows")
    # Daily aggregate
    daily_fund = {}
    for row in fund:
        ts = int(row['fundingTime']); d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        fr = float(row['fundingRate'])
        if d not in daily_fund: daily_fund[d] = []
        daily_fund[d].append(fr)
    p("Daily funding avg (all):")
    for d in sorted(daily_fund.keys()):
        vals = daily_fund[d]
        avg = sum(vals)/len(vals)
        p(f"  {d}: avg={avg:.5f} n={len(vals)} vals={[f'{v:.5f}' for v in vals]}")
else:
    p(f"Error funding: {fund}")

# ── 5. L-26 check: price direction vs gLSR ──────────────────────────────────
p("\n=== C1: L-26 check (gLSR direction vs price) ===")
# L-26 trigger = pos_r drop >=30% over 3d
# Check recent pos_r series
pos_series = [(x['d'], x['pr']) for x in series_fw if x['pr']]
if len(pos_series) >= 3:
    for i in range(2, len(pos_series)):
        d, pr = pos_series[i]
        d0, pr0 = pos_series[i-2]
        if pr0 > 0:
            drop = (pr0 - pr) / pr0 * 100
            if drop >= 30:
                p(f"  L-26 trigger: pos_r dropped {drop:.1f}% from {d0}({pr0:.3f}) to {d}({pr:.3f})")
    p(f"  Recent pos_r: {[(d, f'{v:.3f}') for d,v in pos_series[-5:]]}")
else:
    p(f"  Not enough pos_r data: {pos_series}")

# ── 6. VPS store check ───────────────────────────────────────────────────────
p("\n=== C2: VPS store check for CLO klines ===")
try:
    r = subprocess.run(
        ['ssh', 'root@5.223.67.21',
         'python3 -c "'
         'import os, glob; '
         'files = sorted(glob.glob(\"/root/Data_back_test/whale_data/data/raw/klines_1h/CLOUSDT/*.parquet\")); '
         'print(\"CLO klines_1h files:\", len(files)); '
         'print(\"First:\", files[0] if files else \"NONE\"); '
         'print(\"Last:\", files[-1] if files else \"NONE\")'
         '"'],
        capture_output=True, text=True, timeout=20
    )
    p(r.stdout.strip() or "(no output)")
    if r.stderr: p("stderr:", r.stderr[:200])
except Exception as e:
    p(f"SSH error: {e}")

# ── 7. GeckoTerminal DEX pool check ─────────────────────────────────────────
p("\n=== C4: GeckoTerminal DEX pool CLO ===")
# Try CLO on BSC/ETH via GeckoTerminal
url_gt = "https://api.geckoterminal.com/api/v2/search/pools?query=CLO&network=bsc&page=1"
gt = fetch_json(url_gt)
if isinstance(gt, dict) and "data" in gt:
    pools = gt["data"][:5]
    p(f"GeckoTerminal BSC CLO pools: {len(gt['data'])} total, showing 5:")
    for pool in pools:
        attrs = pool.get("attributes", {})
        p(f"  {attrs.get('name','?')} addr={attrs.get('address','?')[:12]}... "
          f"liq=${float(attrs.get('reserve_in_usd',0)):,.0f} "
          f"vol24h=${float(attrs.get('volume_usd',{}).get('h24',0)):,.0f}")
else:
    p(f"GeckoTerminal BSC: {str(gt)[:200]}")

# Also try ETH
url_gt2 = "https://api.geckoterminal.com/api/v2/search/pools?query=CLO&network=eth&page=1"
gt2 = fetch_json(url_gt2)
if isinstance(gt2, dict) and "data" in gt2:
    pools2 = gt2["data"][:3]
    p(f"GeckoTerminal ETH CLO pools: {len(gt2['data'])} total:")
    for pool in pools2:
        attrs = pool.get("attributes", {})
        p(f"  {attrs.get('name','?')} liq=${float(attrs.get('reserve_in_usd',0)):,.0f} "
          f"vol24h=${float(attrs.get('volume_usd',{}).get('h24',0)):,.0f}")
else:
    p(f"GeckoTerminal ETH: {str(gt2)[:200]}")

# ── 8. Binance spot klines for price context ─────────────────────────────────
p("\n=== C2/C4: Spot klines daily 01/04→now ===")
start_spot = int(datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
url_spot = f"https://api.binance.com/api/v3/klines?symbol=CLOUSDT&interval=1d&startTime={start_spot}&limit=200"
kspot = fetch_json(url_spot)
if isinstance(kspot, list):
    p(f"Got {len(kspot)} spot daily klines (01/04→now)")
    for k in kspot:
        ts = int(k[0]); d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        color = "RED" if c < o else "GRN"
        ret = (c-o)/o*100
        p(f"  {d} [{color}] O={o:.5f} C={c:.5f} ret={ret:+.1f}% vol=${vol_usd/1e6:.2f}M")
else:
    p(f"Error spot klines: {kspot}")

# ── Write output ─────────────────────────────────────────────────────────────
OUT.write_text("\n".join(lines), encoding="utf-8")
p(f"\nDONE — written to {OUT}")
