"""
_probe_koma_345b_pinsnap_20260810.py
Fix: pin_streak/oi_cycle (load funding for f_avg) + depth snap #1 + BAPI detail
"""
import sys, io, json, csv, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_PERP = "KOMAUSDT"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-345b PIN+SNAP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR {url[:80]}: {e}")
        return None

# Load LSR and OI
with open(SCRATCH / f"koma_lsr_raw_{DATE_TAG}.csv", encoding="utf-8") as f:
    lsr_rows = list(csv.DictReader(f))
with open(SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv", encoding="utf-8") as f:
    oi_rows = list(csv.DictReader(f))
lsr_by_date = {r["date"]: r for r in lsr_rows}
oi_by_date  = {r["date"]: r for r in oi_rows}

# Load funding — compute daily f_avg
log("\n=== Loading funding for daily f_avg ===")
fund_by_date = {}
fund_csv = SCRATCH / f"koma_funding_{DATE_TAG}.csv"
if fund_csv.exists():
    with open(fund_csv, encoding="utf-8") as f:
        fund_rows_raw = list(csv.DictReader(f))
    for r in fund_rows_raw:
        d = r.get("date","")[:10]
        rate = float(r.get("fundingRate",0) or 0)
        if d not in fund_by_date:
            fund_by_date[d] = []
        fund_by_date[d].append(rate)
    for d in fund_by_date:
        rates = fund_by_date[d]
        fund_by_date[d] = {"f_avg": sum(rates)/len(rates), "f_min": min(rates), "f_max": max(rates), "fn": len(rates)}
    log(f"  Funding dates: {len(fund_by_date)}, range: {min(fund_by_date)}→{max(fund_by_date)}")

def fv(r, *keys, default=None):
    for k in keys:
        v = r.get(k)
        if v is not None and str(v).strip() not in ("","None","nan"):
            try: return float(v)
            except: return v
    return default

# ── pin_streak + oi_cycle_pos (last 14d) ─────────────────────────────────
log(f"\n=== BR3-4d: PIN_STREAK + OI_CYCLE_POS (last 14d) ===")
oi_all = [fv(r,"oi_usd") for r in oi_rows if fv(r,"oi_usd") is not None]
oi_min30 = min(oi_all) if oi_all else None
oi_max30 = max(oi_all) if oi_all else None
oi_dates = sorted(oi_by_date.keys())
lsr_dates_sorted = sorted(lsr_by_date.keys())
last14_dates = lsr_dates_sorted[-14:]

log(f"  PIN = f_avg ∈ [4e-5, 6e-5]")
log(f"  {'date':12s} {'f_avg':>12s} {'f_n':>4s} {'PIN?':>5s} {'oi_usd':>14s} {'oi_cycle':>10s}")
pin_streak_cur = 0
for d in last14_dates:
    f_info = fund_by_date.get(d, {})
    f_avg_v = f_info.get("f_avg")
    f_n_v   = f_info.get("fn", "?")
    oi_r = oi_by_date.get(d, {})
    oi_v = fv(oi_r,"oi_usd")
    pin = (f_avg_v is not None and 4e-5 <= f_avg_v <= 6e-5)
    oi_cycle = None
    if oi_v and oi_min30 and oi_max30 and (oi_max30 - oi_min30) > 0:
        oi_cycle = (oi_v - oi_min30) / (oi_max30 - oi_min30)
    f_str   = f"{f_avg_v:.6f}" if f_avg_v is not None else "         N/A"
    oi_str  = f"${oi_v:>12,.0f}" if oi_v is not None else "           N/A"
    cyc_str = f"{oi_cycle:.3f}" if oi_cycle is not None else "    N/A"
    log(f"  {d:12s} {f_str:>12s} {f_n_v!s:>4s} {'YES' if pin else ' — ':>5s} {oi_str:>14s} {cyc_str:>10s}")
    if pin: pin_streak_cur += 1
    else: pin_streak_cur = 0

log(f"\n  pin_streak (last date): {pin_streak_cur}")
log(f"  OI_min30: ${oi_min30:,.0f}")
log(f"  OI_max30: ${oi_max30:,.0f}  {'*** UNCALIBRATED (>$18M) ***' if oi_max30 > 18e6 else ''}")
last_oi_dt = oi_dates[-1]
last_oi_v  = fv(oi_by_date.get(last_oi_dt,{}),"oi_usd")
if last_oi_v and oi_min30 and oi_max30 and (oi_max30-oi_min30)>0:
    log(f"  oi_cycle_pos ({last_oi_dt}): {(last_oi_v-oi_min30)/(oi_max30-oi_min30):.3f}")

# ── GOM-C rehcấm with funding data ────────────────────────────────────────
log(f"\n=== GOM-C rechấm (last 14d, with proper f_avg from funding) ===")
WIN_START = "2026-07-12"; WIN_END = "2026-08-09"
with open(SCRATCH / f"koma_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    perp_rows = list(csv.DictReader(f))
perp_by_date = {r["date"]: r for r in perp_rows}
win_dates = [d for d in sorted(perp_by_date.keys()) if WIN_START <= d <= WIN_END]
NEUTRAL = 5e-5; C2_THRESH = 2 * NEUTRAL
log(f"  Spec: C2_quiet(|f_avg|≤{C2_THRESH:.0e}) ∧ C3(taker∈[40,55]) ∧ d_pos≥0; C1=PROVISIONAL")
log(f"  {'date':12s} {'f_avg':>12s} {'taker%':>8s} {'pos_r':>7s} {'Δpos_r':>8s} {'C2':>3s} {'C3':>3s} {'C1hint':>7s} GOM-C")
gom_c_dates = []; prev_pos_r = None
for d in win_dates:
    pr  = perp_by_date.get(d, {}); lsr = lsr_by_date.get(d, {})
    f_info = fund_by_date.get(d, {})
    f_avg_v = f_info.get("f_avg")
    taker = fv(pr,"taker_pct")
    pos_r = fv(lsr,"pos_r")
    d_pos = (pos_r - prev_pos_r) if (pos_r is not None and prev_pos_r is not None) else None
    prev_pos_r = pos_r
    glsr = fv(lsr,"glsr_raw")
    c1_hint = "HIGH" if (glsr and glsr > 3.0) else ("low" if (glsr and glsr < 1.5) else "mid")
    c2 = (abs(f_avg_v) <= C2_THRESH) if f_avg_v is not None else None
    c3 = (0.40 <= taker <= 0.55) if taker is not None else None
    dp_ok = (d_pos >= 0) if d_pos is not None else None
    gom_c = "YES" if (c2 and c3 and dp_ok) else "—"
    if gom_c == "YES": gom_c_dates.append(d)
    f_str = f"{f_avg_v:.6f}" if f_avg_v is not None else "         N/A"
    t_str = f"{taker*100:.1f}%" if taker is not None else "  N/A"
    p_str = f"{pos_r:.4f}" if pos_r is not None else "  N/A"
    dp_str = f"{d_pos:+.4f}" if d_pos is not None else "   N/A"
    c2s = "✓" if c2 else ("?" if c2 is None else "✗")
    c3s = "✓" if c3 else ("?" if c3 is None else "✗")
    log(f"  {d:12s} {f_str:>12s} {t_str:>8s} {p_str:>7s} {dp_str:>8s} {c2s:>3s} {c3s:>3s} {c1_hint:>7s} {gom_c}")

log(f"\n  GOM-C pass days (C2∧C3∧d_pos≥0): {len(gom_c_dates)}")
if gom_c_dates:
    log(f"  Dates: {gom_c_dates}")
    log(f"  GOM-C PROVISIONAL — nhập hồ sơ gate 15/08/2026")
else:
    log(f"  No GOM-C fire in window")

# ── Perp info ─────────────────────────────────────────────────────────────
log(f"\n=== Perp info ===")
perp_info = json.loads((SCRATCH / f"koma_perp_info_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  symbol:       {perp_info.get('symbol')}")
log(f"  status:       {perp_info.get('status')}")
onb = perp_info.get("onboardDate")
if onb: log(f"  onboard:      {datetime.fromtimestamp(int(onb)/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  baseAsset:    {perp_info.get('baseAsset')}")

# ── BAPI status ───────────────────────────────────────────────────────────
log(f"\n=== BAPI status ===")
bapi_data = json.loads((SCRATCH / f"koma_bapi_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  alphaId:       {bapi_data.get('alphaId')} = ALPHA_1")
log(f"  fullyDelisted: {bapi_data.get('fullyDelisted')} — ACTIVE")
log(f"  offsell:       {bapi_data.get('offsell')}")
log(f"  offline:       {bapi_data.get('offline')}")
log(f"  holders:       {bapi_data.get('holders'):,}")
lt = bapi_data.get("listingTime")
if lt: log(f"  listingTime:   {datetime.fromtimestamp(int(lt)/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  price:         {float(bapi_data.get('price',0)):.8f}")
log(f"  marketCap:     ${float(bapi_data.get('marketCap',0)):,.0f}")
log(f"  contract:      {bapi_data.get('contractAddress')}")
log(f"  totalSupply:   {float(bapi_data.get('totalSupply',0)):,.0f}")
log(f"  circSupply:    {float(bapi_data.get('circulatingSupply',0)):,.0f}")
log(f"  taker_alpha:   ABSTAIN (bapi klines9==klines5, L48 spec)")

# ── Depth snap #1 ─────────────────────────────────────────────────────────
log(f"\n=== Depth snap #1 ===")
FAPI = "https://fapi.binance.com"
depth_data = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYM_PERP}&limit=1000")
snap_time = datetime.now(timezone.utc)
if depth_data:
    bids = [(float(p), float(q)) for p, q in depth_data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in depth_data.get("asks", [])]
    if bids and asks:
        bid_top = bids[0][0]; ask_top = asks[0][0]
        mid = (bid_top + ask_top) / 2
        spread_pct = (ask_top - bid_top) / mid * 100
        bid2_full = sum(p*q for p,q in bids)
        ask2_full = sum(p*q for p,q in asks)
        ratio_full = bid2_full/ask2_full if ask2_full > 0 else None
        log(f"  Time:    {snap_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        log(f"  mid:     ${mid:.8f}")
        log(f"  bid_top: ${bid_top:.8f} ask_top: ${ask_top:.8f}")
        log(f"  spread:  {spread_pct:.3f}%")
        log(f"  bid2(full book): ${bid2_full:,.0f}")
        log(f"  ask2(full book): ${ask2_full:,.0f}")
        log(f"  ratio bid/ask: {ratio_full:.4f}")
        log(f"\n  Depth buckets:")
        for pct_b in [0.01, 0.02, 0.05]:
            bb = sum(p*q for p,q in bids if p >= mid*(1-pct_b))
            ab = sum(p*q for p,q in asks if p <= mid*(1+pct_b))
            rb = bb/ab if ab > 0 else None
            log(f"    ±{pct_b*100:.0f}%: bid=${bb:,.0f} ask=${ab:,.0f} ratio={rb:.3f if rb else 'N/A'}")
        snap = {
            "symbol": SYM_PERP, "time": snap_time.isoformat(), "mid": mid,
            "bid_top": bid_top, "ask_top": ask_top, "spread_pct": spread_pct,
            "bid2_full_usd": bid2_full, "ask2_full_usd": ask2_full, "ratio_full": ratio_full,
            "buckets": {
                "1pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.99), "ask": sum(p*q for p,q in asks if p<=mid*1.01)},
                "2pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.98), "ask": sum(p*q for p,q in asks if p<=mid*1.02)},
                "5pct": {"bid": sum(p*q for p,q in bids if p>=mid*0.95), "ask": sum(p*q for p,q in asks if p<=mid*1.05)},
            }
        }
        (SCRATCH / f"koma_depth_snap1_{DATE_TAG}.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
        log(f"\n  Saved: koma_depth_snap1_{DATE_TAG}.json")
        snap2_gate_dt = datetime.fromtimestamp(snap_time.timestamp() + 4*3600, tz=timezone.utc)
        log(f"  SNAP #2 GATE: ≥{snap2_gate_dt.strftime('%Y-%m-%d %H:%M UTC')}")
else:
    log(f"  Depth fetch FAILED")

log(f"\n[K-345b DONE]")
