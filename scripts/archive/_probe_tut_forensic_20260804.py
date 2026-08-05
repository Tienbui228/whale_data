#!/usr/bin/env python3
"""Probe: TUT forensic khung dai 01/05->04/08 — V1 chuoi, V2 gom, V3 campaign, V4 monetize."""
import sys, io, csv, json, subprocess, os
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP  = Path(r"D:\Check onchain fresh wallets\data\export")
ALPH = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")
OUT  = Path(r"D:\Data back test\whale_data\scratch\tut_forensic_20260804.txt")
OUT.parent.mkdir(exist_ok=True)

lines = []
def p(*a):
    s = " ".join(str(x) for x in a)
    print(s); lines.append(s)

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

def ts_to_date(ts_ms):
    return datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')

def ts_to_dt(ts_ms):
    return datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')

# ── 0. VPS STORE CHECK (PROBE STORE TƯỚC) ────────────────────────────────────
p("\n=== NGUON 0: VPS klines_1h TUTUSDT ===")
try:
    r = subprocess.run(
        ['ssh', 'root@5.223.67.21',
         'ls /root/Data_back_test/whale_data/data/raw/klines_1h/TUTUSDT/ 2>/dev/null | head -5; '
         'ls /root/Data_back_test/whale_data/data/raw/klines_1h/TUTUSDT/ 2>/dev/null | wc -l'],
        capture_output=True, text=True, timeout=20
    )
    p("VPS TUT klines_1h:", r.stdout.strip() or "(no output)")
    if r.stderr: p("  stderr:", r.stderr[:100])
except Exception as e:
    p(f"SSH error: {e}")

# Check VPS freshwatch-equivalent
try:
    r2 = subprocess.run(
        ['ssh', 'root@5.223.67.21',
         'ls /root/Data_back_test/whale_data/data/export/ 2>/dev/null | head -10'],
        capture_output=True, text=True, timeout=20
    )
    p("VPS export dir:", r2.stdout.strip() or "(no output)")
except Exception as e:
    p(f"SSH error 2: {e}")

# ── 1. FRESHWATCH TUT (NGUON 3) ───────────────────────────────────────────────
p("\n=== NGUON 3: freshwatch TUT ===")
fw = {}
for f in sorted(EXP.glob("freshwatch_daily_2026-*.csv")):
    for row in csv.DictReader(open(f, encoding="utf-8-sig")):
        if row.get("symbol","") == "TUTUSDT":
            fw[row["date"]] = row

dates_fw = sorted(fw.keys())
p(f"freshwatch: {len(fw)} rows, {dates_fw[0] if dates_fw else 'NONE'} -> {dates_fw[-1] if dates_fw else 'NONE'}")

p(f"\n{'date':<12} {'px':>9} {'OI(M)':>8} {'vol(M)':>7} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'fav':>9} {'fn':>3}")
for d in dates_fw:
    r = fw[d]
    px = gv(r,'px_avg'); oi = gv(r,'oi_usd'); vol = gv(r,'vol_quote')
    pr = gv(r,'lsr_pos_r'); ar = gv(r,'lsr_acc_r'); gl = gv(r,'lsr_global_r')
    fav= gv(r,'funding_avg'); fn = gv(r,'funding_n')
    px_s  = f"{px:.5f}"       if px  else "—"
    oi_s2 = f"{oi/1e6:.3f}"  if oi  else "—"
    v_s   = f"{vol/1e6:.2f}" if vol else "—"
    pr_s  = f"{pr:.3f}"      if pr  else "—"
    ar_s  = f"{ar:.3f}"      if ar  else "—"
    gl_s2 = f"{gl:.4f}"      if gl  else "—"
    fav_s = f"{fav:.5f}"     if fav else "—"
    fn_s  = str(int(fn))     if fn  else "—"
    p(f"  {d:<12} {px_s:>9} {oi_s2:>8} {v_s:>7} {pr_s:>7} {ar_s:>7} {gl_s2:>7} {fav_s:>9} {fn_s:>3}")

# ── 2. ALPHA SPOT KLINES TUT (NGUON 3b) ──────────────────────────────────────
p("\n=== NGUON 3b: Alpha spot klines TUT (local store) ===")
import glob, os
alpha_files = sorted(glob.glob(str(ALPH / "date=2026-*" / "*.parquet")))
p(f"Alpha store total partitions: {len(alpha_files)}")
# Check TUT in a sample partition
try:
    import pandas as pd
    tut_alpha = []
    for fp in alpha_files:
        df = pd.read_parquet(fp)
        tut = df[df.get('symbol', pd.Series()).eq('TUT') | df.get('alpha_id', pd.Series()).eq('ALPHA_117')] if 'symbol' in df.columns else pd.DataFrame()
        if len(tut) > 0:
            for _, row2 in tut.iterrows():
                tut_alpha.append(row2)
    if tut_alpha:
        p(f"TUT in alpha store: {len(tut_alpha)} rows")
        # Show columns from first
        p(f"Columns: {list(tut_alpha[0].index)[:15]}")
        # Show first and last 5
        for t in tut_alpha[:5]:
            d = str(t.get('date','?'))[:10]
            px_c = t.get('close', t.get('px_close', None))
            vol_q = t.get('volume_quote', t.get('vol_quote', None))
            p(f"  alpha {d}: close={px_c} vol_quote={vol_q}")
        p("  ...")
        for t in tut_alpha[-5:]:
            d = str(t.get('date','?'))[:10]
            px_c = t.get('close', t.get('px_close', None))
            vol_q = t.get('volume_quote', t.get('vol_quote', None))
            p(f"  alpha {d}: close={px_c} vol_quote={vol_q}")
    else:
        p("TUT not found in alpha store partitions sampled")
        # Print a sample row from first partition to see schema
        if alpha_files:
            df0 = pd.read_parquet(alpha_files[0])
            p(f"Sample partition cols: {list(df0.columns)}")
            p(f"Sample symbols: {df0.get('symbol', df0.get('alpha_id', pd.Series())).unique()[:10].tolist()}")
except Exception as e:
    p(f"Alpha parquet error: {e}")

# ── 3. FAPI KLINES 1D 01/05->04/08 (NGUON 2) ─────────────────────────────────
p("\n=== NGUON 2: fapi klines 1d (01/05->04/08) ===")
start_may = int(datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
kd = fetch_json(
    f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT&interval=1d&startTime={start_may}&limit=200"
)
klines_1d = {}  # date -> dict
if isinstance(kd, list):
    p(f"Got {len(kd)} 1d klines (01/05->now)")
    prev_c = None
    for k in kd:
        d  = ts_to_date(int(k[0]))
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        tb_q    = float(k[10])
        tk_pct  = tb_q/vol_usd*100 if vol_usd > 0 else 0
        ret     = (c - prev_c)/prev_c*100 if prev_c else None
        klines_1d[d] = {'o':o,'h':h,'l':lo,'c':c,'vol':vol_usd,'tk':tk_pct,'ret':ret}
        color   = "GRN" if c >= o else "RED"
        ret_s   = f"{ret:+.1f}%" if ret is not None else "—"
        p(f"  {d} [{color}] O={o:.5f} H={h:.5f} L={lo:.5f} C={c:.5f} ret={ret_s} vol={vol_usd/1e6:.2f}M tk={tk_pct:.1f}%")
        prev_c = c
else:
    p(f"  Error: {kd}")

# ── 4. FAPI KLINES 4H 01/05->09/07 (GOM WINDOW) ──────────────────────────────
p("\n=== NGUON 2b: fapi klines 4h (01/05->22/07, for build analysis) ===")
end_j22 = int(datetime(2026, 7, 23, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
k4h = fetch_json(
    f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT&interval=4h&startTime={start_may}&endTime={end_j22}&limit=500"
)
klines_4h = []
if isinstance(k4h, list):
    p(f"Got {len(k4h)} 4h klines (01/05->22/07)")
    for k in k4h:
        d  = ts_to_dt(int(k[0]))
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        tb_q    = float(k[10])
        tk_pct  = tb_q/vol_usd*100 if vol_usd > 0 else 0
        color   = "GRN" if c >= o else "RED"
        klines_4h.append({'dt':d,'o':o,'h':h,'l':lo,'c':c,'vol':vol_usd,'tk':tk_pct,'color':color})
    # Print RED candles with high vol (>3M USD) — gom signal
    p("\nRED candles with vol > 2M USD (potential absorption on falls):")
    for k in klines_4h:
        if k['color']=='RED' and k['vol'] > 2e6:
            p(f"  {k['dt']} RED O={k['o']:.5f} C={k['c']:.5f} vol={k['vol']/1e6:.2f}M tk={k['tk']:.1f}%")
    # Print all candles around key dates: May buy zones
    p("\nAll 4h candles 01-14/05 (early accumulation check):")
    for k in klines_4h[:42]:  # first 42 = 7 days
        p(f"  {k['dt']} [{k['color']}] O={k['o']:.5f} C={k['c']:.5f} vol={k['vol']/1e6:.3f}M tk={k['tk']:.1f}%")
else:
    p(f"  Error: {k4h}")

# ── 5. FAPI FUNDING RATE 01/05 (NGUON 2) ─────────────────────────────────────
p("\n=== NGUON 2: fapi fundingRate 01/05->04/08 ===")
fund_raw = fetch_json(
    f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=TUTUSDT&startTime={start_may}&limit=1000"
)
fund_daily = {}
fund_all   = []
if isinstance(fund_raw, list):
    p(f"Got {len(fund_raw)} funding rows")
    daily = {}
    for row in fund_raw:
        ts = int(row['fundingTime'])
        d  = ts_to_date(ts)
        hr = datetime.fromtimestamp(ts/1000, tz=timezone.utc).hour
        fr = float(row['fundingRate'])
        fund_all.append({'d':d,'hr':hr,'fr':fr})
        if d not in daily: daily[d] = []
        daily[d].append(fr)
    p("\nDaily funding summary:")
    for d in sorted(daily.keys()):
        vals = daily[d]
        avg  = sum(vals)/len(vals)
        fund_daily[d] = {'avg':avg,'min':min(vals),'max':max(vals),'n':len(vals)}
        marker = " ***HOT***" if avg > 0.0002 else (" *NEG*" if avg < 0 else "")
        p(f"  {d}: avg={avg:.5f} n={len(vals)} [{min(vals):.5f},{max(vals):.5f}]{marker}")
else:
    p(f"  Error: {fund_raw}")

# ── 6. OI DAILY (futures/data, 31d retention) ────────────────────────────────
p("\n=== NGUON 2: fapi OI daily (31d retention = 04/07->04/08) ===")
oi_d = fetch_json(
    "https://fapi.binance.com/futures/data/openInterestHist?symbol=TUTUSDT&period=1d&limit=31"
)
oi_daily = {}
if isinstance(oi_d, list):
    p(f"Got {len(oi_d)} OI daily rows")
    for row in oi_d:
        d      = ts_to_date(int(row['timestamp']))
        oi_usd = float(row['sumOpenInterestValue'])
        oi_tok = float(row['sumOpenInterest'])
        oi_daily[d] = oi_usd
        p(f"  {d}: OI_USD={oi_usd/1e6:.3f}M tokens={oi_tok:.0f}")
else:
    p(f"  Error: {oi_d}")

# OI 1h from 01/07 (longer window)
p("\n=== OI 1h from 01/07 (for ΔOI tracking) ===")
start_j1 = int(datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
oi_1h = fetch_json(
    f"https://fapi.binance.com/futures/data/openInterestHist?symbol=TUTUSDT&period=1h&startTime={start_j1}&limit=500"
)
oi_1h_daily = {}
if isinstance(oi_1h, list):
    p(f"Got {len(oi_1h)} OI 1h rows")
    for row in oi_1h:
        ts = int(row['timestamp']); d = ts_to_date(ts)
        oi_usd = float(row['sumOpenInterestValue'])
        if d not in oi_1h_daily:
            oi_1h_daily[d] = {'open':oi_usd,'high':oi_usd,'low':oi_usd,'close':oi_usd}
        oi_1h_daily[d]['high'] = max(oi_1h_daily[d]['high'], oi_usd)
        oi_1h_daily[d]['low']  = min(oi_1h_daily[d]['low'],  oi_usd)
        oi_1h_daily[d]['close'] = oi_usd
    p("Daily OI from 1h data (01/07->now):")
    for d in sorted(oi_1h_daily.keys()):
        v = oi_1h_daily[d]
        p(f"  {d}: open={v['open']/1e6:.3f}M high={v['high']/1e6:.3f}M low={v['low']/1e6:.3f}M close={v['close']/1e6:.3f}M")
else:
    p(f"  Error: {oi_1h}")

# ── 7. GECKOTERMINAL TUT BSC ─────────────────────────────────────────────────
p("\n=== C4: GeckoTerminal TUT BSC/BNB pools ===")
gt = fetch_json("https://api.geckoterminal.com/api/v2/search/pools?query=TUT&network=bsc&page=1")
if isinstance(gt, dict) and "data" in gt:
    p(f"BSC pools found: {len(gt['data'])}")
    for pool in gt["data"][:8]:
        attrs = pool.get("attributes",{})
        name  = attrs.get("name","?")
        addr  = attrs.get("address","?")[:14]
        liq   = float(attrs.get("reserve_in_usd",0))
        vol24 = float(attrs.get("volume_usd",{}).get("h24",0))
        p(f"  {name} addr={addr}... liq=${liq:,.0f} vol24h=${vol24:,.0f}")
else:
    p(f"GT BSC: {str(gt)[:200]}")

# Also try token search
gt2 = fetch_json("https://api.geckoterminal.com/api/v2/search/pools?query=TUTUSDT&network=bsc&page=1")
if isinstance(gt2, dict) and "data" in gt2:
    p(f"BSC TUTUSDT pools: {len(gt2['data'])}")
    for pool in gt2["data"][:5]:
        attrs = pool.get("attributes",{})
        p(f"  {attrs.get('name','?')} liq=${float(attrs.get('reserve_in_usd',0)):,.0f}")
else:
    p(f"GT BSC TUTUSDT: {str(gt2)[:100]}")

# ── 8. V2 GOM ANALYSIS — ΔOI+ trên nen do/phang ─────────────────────────────
p("\n=== V2a: ΔOI+ on RED/FLAT candles (OI from freshwatch 01/07+) ===")
# Merge freshwatch OI with klines
fw_dates_sorted = sorted(fw.keys())
p("Date range with BOTH klines + OI data:")
merged = []
for d in sorted(set(list(klines_1d.keys()) + list(oi_daily.keys()) + list(oi_1h_daily.keys()))):
    k  = klines_1d.get(d,{})
    oi = oi_daily.get(d) or (oi_1h_daily.get(d,{}).get('close'))
    fw_r = fw.get(d,{})
    oi_fw = gv(fw_r,'oi_usd') if fw_r else None
    oi_final = oi_fw or oi  # prefer freshwatch canonical 00:00
    merged.append({'d':d,'k':k,'oi':oi_final,'fw':fw_r})

# Print OI series with ΔOI
prev_oi = None
p(f"\n{'date':<12} {'px_close':>9} {'color':>4} {'vol(M)':>7} {'tk%':>5} {'OI(M)':>8} {'ΔOI(M)':>9} {'gLSR':>7} {'pos_r':>7}")
for m in sorted(merged, key=lambda x: x['d']):
    d = m['d']
    k = m['k']
    if not k: continue
    oi = m['oi']
    fw_r = m['fw']
    gl   = gv(fw_r,'lsr_global_r') if fw_r else None
    pr   = gv(fw_r,'lsr_pos_r')    if fw_r else None
    color = 'GRN' if k.get('c',0) >= k.get('o',0) else 'RED'
    doi_s = f"{(oi-prev_oi)/1e6:+.3f}" if (oi and prev_oi) else "—"
    doi_flag = " ← GOM?" if (oi and prev_oi and (oi-prev_oi)>0 and color=='RED') else ""
    oi_s  = f"{oi/1e6:.3f}" if oi else "ABSTAIN"
    gl_s  = f"{gl:.4f}" if gl else "ABSTAIN"
    pr_s  = f"{pr:.3f}" if pr else "ABSTAIN"
    vol_s = f"{k.get('vol',0)/1e6:.2f}" if k.get('vol') else "—"
    p(f"  {d:<12} {k.get('c',0):.5f} {color:>4} {vol_s:>7} {k.get('tk',0):.1f}% {oi_s:>8} {doi_s:>9} {gl_s:>7} {pr_s:>7}{doi_flag}")
    if oi: prev_oi = oi

# ── 9. V3 MINI-CAMPAIGN CHECK (May-Jun) ──────────────────────────────────────
p("\n=== V3: MINI-CAMPAIGN / MARKUP scan (01/05->08/07) ===")
p("Check vol spikes (>2x median) and price runs ≥10% in 3d:")
may_jun = {d:v for d,v in klines_1d.items() if '2026-05' <= d < '2026-07-09'}
all_vol = [v['vol'] for v in may_jun.values()]
med_vol = sorted(all_vol)[len(all_vol)//2] if all_vol else 1
p(f"May-Jul08 median daily vol: ${med_vol/1e6:.2f}M")
for d in sorted(may_jun.keys()):
    k  = may_jun[d]
    if k['vol'] > 2*med_vol:
        ret_s = f"{k['ret']:+.1f}%" if k['ret'] else "—"
        color = 'GRN' if k['c'] >= k['o'] else 'RED'
        p(f"  VOL SPIKE {d} [{color}]: vol={k['vol']/1e6:.1f}M ({k['vol']/med_vol:.1f}×med) px={k['c']:.5f} ret={ret_s} tk={k['tk']:.1f}%")

# 3d rolling price run
p("\nRolling 3d price change ≥10%:")
dates_sorted = sorted(may_jun.keys())
for i in range(2, len(dates_sorted)):
    d0 = dates_sorted[i-2]; d2 = dates_sorted[i]
    p0 = may_jun[d0]['c']; p2 = may_jun[d2]['c']
    if p0 > 0 and abs(p2-p0)/p0 >= 0.10:
        run = (p2-p0)/p0*100
        p(f"  3d-run {d0}->{d2}: {run:+.1f}% ({p0:.5f} -> {p2:.5f})")

# ── 10. V4 MONETIZE: px+/OI- days post-peak ──────────────────────────────────
p("\n=== V4: MONETIZE SIGNALS (px+/OI- post markup) ===")
post_peak = {d:v for d,v in klines_1d.items() if d >= '2026-07-09'}
prev_oi2 = None
for d in sorted(post_peak.keys()):
    k  = post_peak[d]
    fw_r = fw.get(d,{})
    oi  = gv(fw_r,'oi_usd') if fw_r else oi_daily.get(d) or (oi_1h_daily.get(d,{}).get('close'))
    color = 'GRN' if k['c'] >= k['o'] else 'RED'
    ret_s = f"{k['ret']:+.1f}%" if k['ret'] else "—"
    doi_s = f"{(oi-prev_oi2)/1e6:+.3f}" if (oi and prev_oi2) else "—"
    flag  = " ← THOAT PERP?" if (oi and prev_oi2 and (oi-prev_oi2)<0 and k['c']>k['o']) else ""
    oi_s  = f"{oi/1e6:.3f}M" if oi else "ABSTAIN"
    p(f"  {d} [{color}] px={k['c']:.5f} ret={ret_s} vol={k['vol']/1e6:.2f}M tk={k['tk']:.1f}% OI={oi_s} dOI={doi_s}{flag}")
    if oi: prev_oi2 = oi

# ── 11. V2b SPOT GOM — controlled fill check ─────────────────────────────────
p("\n=== V2b: CONTROLLED FILL CHECK (taker 44-50.5%, vol anomaly, price stable) ===")
# Look for windows before ignition (09/07) where:
# - taker% in [44, 50.5] (not aggressive)
# - vol > 1.5× recent average
# - price doesn't fall (|ret| < 5%)
pre_ignition = {d:v for d,v in klines_1d.items() if '2026-05-01' <= d < '2026-07-09'}
dates_pre = sorted(pre_ignition.keys())
vols_pre = [pre_ignition[d]['vol'] for d in dates_pre]
avg_vol_pre = sum(vols_pre)/len(vols_pre) if vols_pre else 1

p(f"Pre-ignition avg daily vol: ${avg_vol_pre/1e6:.2f}M")
p("Controlled fill candidates (taker 44-51%, vol>1.5x avg, |ret|<6%):")
for d in dates_pre:
    k = pre_ignition[d]
    if (44.0 <= k['tk'] <= 51.5 and
        k['vol'] > 1.5*avg_vol_pre and
        k['ret'] is not None and abs(k['ret']) < 6.0):
        color = 'GRN' if k['c'] >= k['o'] else 'RED'
        p(f"  {d} [{color}] px={k['c']:.5f} ret={k['ret']:+.1f}% vol={k['vol']/1e6:.2f}M ({k['vol']/avg_vol_pre:.1f}x) tk={k['tk']:.1f}%")

# ── 12. V2c VWAP BUILD ESTIMATE ──────────────────────────────────────────────
p("\n=== V2c: BUILD VWAP — multiple windows ===")
# Window A: May accumulation (if any signal)
# Window B: Jun consolidation
# Window C: Jul 01-06 (known build window from previous analysis)

# C is already computed: 0.01285 (from mm_econ_tut_forward_20260804.md)
# Let me compute B: June consolidation window
# TUT klines June 01->July 06

# Find dates where gLSR data available (freshwatch from fw start)
fw_start = dates_fw[0] if dates_fw else "2026-07-01"
p(f"freshwatch OI/LSR available from: {fw_start}")
p(f"Pre-{fw_start}: OI/LSR ABSTAIN (VPS store empty for TUT)")

# Window B: Jun build (if klines show low vol, stable px before ignition)
jun_dates = [d for d in sorted(klines_1d.keys()) if '2026-06-01' <= d < '2026-07-07']
if jun_dates:
    p(f"\nJun01-Jul06 window ({len(jun_dates)} days):")
    for d in jun_dates:
        k = klines_1d[d]
        fw_r = fw.get(d,{})
        oi_s = f"OI={gv(fw_r,'oi_usd')/1e6:.3f}M" if fw_r and gv(fw_r,'oi_usd') else "OI=ABSTAIN"
        gl_s = f"gLSR={gv(fw_r,'lsr_global_r'):.3f}" if fw_r and gv(fw_r,'lsr_global_r') else "gLSR=ABSTAIN"
        color = 'GRN' if k['c'] >= k['o'] else 'RED'
        ret_s = f"{k['ret']:+.1f}%" if k['ret'] else "—"
        p(f"  {d} [{color}] C={k['c']:.5f} ret={ret_s} vol={k['vol']/1e6:.2f}M tk={k['tk']:.1f}% {oi_s} {gl_s}")

# VWAP calc: Jul 01-06 (Window C confirmed)
c_dates = [d for d in sorted(klines_1d.keys()) if '2026-07-01' <= d <= '2026-07-06']
if c_dates:
    wt = sum(((klines_1d[d]['h']+klines_1d[d]['l']+klines_1d[d]['c'])/3)*klines_1d[d]['vol'] for d in c_dates)
    tv = sum(klines_1d[d]['vol'] for d in c_dates)
    vwap_c = wt/tv if tv > 0 else 0
    p(f"\nWindow C VWAP (01-06/07): {vwap_c:.5f} (total vol={tv/1e6:.1f}M)")

# May VWAP if May shows any quiet accumulation
may_dates_q = [d for d in sorted(klines_1d.keys())
               if '2026-05-01' <= d < '2026-06-01'
               and klines_1d[d]['vol'] < avg_vol_pre * 1.2  # quiet vol
               and abs(klines_1d[d].get('ret',0) or 0) < 4.0]
if may_dates_q:
    wt_m = sum(((klines_1d[d]['h']+klines_1d[d]['l']+klines_1d[d]['c'])/3)*klines_1d[d]['vol'] for d in may_dates_q)
    tv_m = sum(klines_1d[d]['vol'] for d in may_dates_q)
    vwap_m = wt_m/tv_m if tv_m > 0 else 0
    p(f"May quiet accumulation VWAP ({len(may_dates_q)} quiet days): {vwap_m:.5f} (vol={tv_m/1e6:.1f}M)")

# ── Write output ──────────────────────────────────────────────────────────────
OUT.write_text("\n".join(lines), encoding="utf-8")
p(f"\nDONE — output: {OUT}")
