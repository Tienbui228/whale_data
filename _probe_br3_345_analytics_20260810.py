"""
_probe_br3_345_analytics_20260810.py
BR3-3: §3 ba phương pháp (Q1/Q2/Q3/VWAP/GOM rechấm)
BR3-4: Phase context (ATH/ATL/nền/5 flags/pin_streak/oi_cycle_pos)
BR3-5a: BAPI verify + on-chain status + depth snap #1
"""
import sys, io, json, csv, math, statistics, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"BR3-345 ANALYTICS  |  {NOW.strftime('%Y-%m-%d %H:%M:%S UTC')}")

def read_csv(path):
    if not path.exists(): log(f"  MISSING: {path.name}"); return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def gf(d, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "" and v != "None":
            try: return float(v)
            except: pass
    return None

def fetch_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"  ERROR: {url[:80]}: {e}"); return None

perp = read_csv(SCRATCH / f"br3_perp_{DATE_TAG}.csv")
lsr  = read_csv(SCRATCH / f"br3_lsr_raw_{DATE_TAG}.csv")
oi   = read_csv(SCRATCH / f"br3_oi_hist_{DATE_TAG}.csv")
fund_json_path = SCRATCH / f"br3_funding_{DATE_TAG}.json"
fund_data = json.loads(fund_json_path.read_text(encoding="utf-8")) if fund_json_path.exists() else []

perp_by_d = {r["date"]: r for r in perp}
lsr_by_d  = {r["date"]: r for r in lsr}
oi_by_d   = {r["date"]: gf(r, "oi_usd") for r in oi}
all_dates = sorted(perp_by_d.keys())

# Compute ret_1d
date_ret = {}
prev_c = None
for dt in all_dates:
    c = gf(perp_by_d[dt], "close")
    if c and prev_c:
        date_ret[dt] = (c - prev_c)/prev_c
    prev_c = c

# Fund per day
fund_by_d = {}
for r in fund_data:
    ts = int(r.get("fundingTime", 0))
    dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    fr = float(r.get("fundingRate", 0))
    if dt not in fund_by_d:
        fund_by_d[dt] = []
    fund_by_d[dt].append(fr)

# ═══════════════════════════════════════════════════════════════════════════
# BR3-3: §3 BA PHƯƠNG PHÁP
# ═══════════════════════════════════════════════════════════════════════════
log("\n" + "="*70)
log("BR3-3: §3 BA PHƯƠNG PHÁP")
log("="*70)

# Window selection: use last 30d of LSR (window with data for all 3 methods)
lsr_dates = sorted(lsr_by_d.keys())
WIN_START = "2026-07-12"  # first OI hist date
WIN_END   = "2026-08-09"  # L-21: last complete perp candle
log(f"\n  Chain/window: {WIN_START} → {WIN_END}")
log(f"  Rationale: OI hist available from 07-12 (30d window)")
log(f"  L-21: today=2026-08-10, last complete candle = 2026-08-09")

# ── Q1: ΔOI⁺ nến đỏ/phẳng ─────────────────────────────────────────────────
log("\n=== Q1: ΔOI⁺ nến đỏ/phẳng ===")
log(f"  {'date':12s} {'ret%':>7s} {'OI($)':>14s} {'ΔOI($)':>12s} {'ΔOI⁺':>12s} {'counts?':>8s} {'Q1_add':>12s}")
q1_gross = 0.0; q1_net = 0.0; prev_oi = None
for dt in sorted(d for d in all_dates if WIN_START <= d <= WIN_END):
    oi_v = oi_by_d.get(dt)
    ret = date_ret.get(dt)
    delta = (oi_v - prev_oi) if (oi_v and prev_oi) else None
    delta_pos = max(delta, 0) if delta is not None else 0
    counts = (ret is not None and ret <= 0.01)
    q1_add = delta_pos if counts else 0.0
    q1_gross += delta_pos
    q1_net += q1_add
    flag = "YES" if counts else "NO"
    if oi_v:
        log(f"  {dt:12s} {f'{ret*100:+.2f}%' if ret else 'N/A':>7s} "
            f"${oi_v:>13,.0f} "
            f"{f'${delta:+,.0f}' if delta is not None else 'N/A':>12s} "
            f"${delta_pos:>11,.0f} {flag:>8s} ${q1_add:>11,.0f}")
    prev_oi = oi_v if oi_v else prev_oi

log(f"\n  Q1_GROSS (all ΔOI⁺): ${q1_gross:,.0f}")
log(f"  Q1_NET   (nến đỏ/phẳng only): ${q1_net:,.0f}")

# ── Q2: OI×share ──────────────────────────────────────────────────────────
log("\n=== Q2: OI × share (net long estimate) ===")
d_start_ls = lsr_by_d.get(WIN_START, {})
d_end_ls   = lsr_by_d.get(WIN_END, {})
oi_s = oi_by_d.get(WIN_START)
oi_e = oi_by_d.get(WIN_END)
pos_s = gf(d_start_ls, "pos_r")
pos_e = gf(d_end_ls,   "pos_r")

if pos_s and pos_e and oi_s and oi_e:
    share_s = pos_s/(1+pos_s)
    share_e = pos_e/(1+pos_e)
    long_s = oi_s * share_s
    long_e = oi_e * share_e
    q2_net  = long_e - long_s
    q2_ceil = long_e
    log(f"  Start {WIN_START}: OI=${oi_s:,.0f} pos_r={pos_s:.4f} share={share_s:.4f} → long=${long_s:,.0f}")
    log(f"  End   {WIN_END}: OI=${oi_e:,.0f} pos_r={pos_e:.4f} share={share_e:.4f} → long=${long_e:,.0f}")
    log(f"  Q2_net:     ${q2_net:+,.0f}")
    log(f"  Q2_ceiling: ${q2_ceil:,.0f}")
    oi_max = max(v for v in oi_by_d.values() if v)
    log(f"  OI_max (30d): ${oi_max:,.0f} {'UNCALIBRATED(>$18M)' if oi_max>18_000_000 else 'within calib(<$18M)'}")
else:
    log(f"  Missing data: oi_s={oi_s} oi_e={oi_e} pos_s={pos_s} pos_e={pos_e}")
    q2_net = q2_ceil = None

# ── Q3: spot capacity ─────────────────────────────────────────────────────
log("\n=== Q3: spot capacity ===")
log(f"  No spot pair for BROCCOLIF3B (HTTP 400 on api.binance.com)")
log(f"  Q3: N/A (no spot vol data)")

# ── VWAP: M2 two-tier ─────────────────────────────────────────────────────
log("\n=== VWAP M2 (window) ===")
# Method 1: pure ΔOI⁺ VWAP (for Q1 days)
num_oi = 0.0; den_oi = 0.0
# Method 2: vw-vol VWAP (all days with vol)
num_vol = 0.0; den_vol = 0.0
for dt in sorted(d for d in all_dates if WIN_START <= d <= WIN_END):
    c = gf(perp_by_d.get(dt, {}), "close")
    vol = gf(perp_by_d.get(dt, {}), "vol_quote_usd")
    if c and vol:
        num_vol += vol  # vol_quote = price * tokens → VWAP = Σvol / Σtokens
        den_vol += vol / c  # tokens ≈ vol_quote/price
if den_vol > 0:
    vwap_vol = num_vol / den_vol
    log(f"  VWAP [vw-vol] window: ${vwap_vol:.8f}")
    c_last = gf(perp_by_d.get(WIN_END, {}), "close")
    log(f"  px {WIN_END}: ${c_last:.8f}")
    log(f"  px vs VWAP: {(c_last/vwap_vol-1)*100:+.2f}%")

# ── GOM rechấm ────────────────────────────────────────────────────────────
log("\n=== GOM-A/B/C rechấm (window) ===")
log("  GOM-A spec v1.5: A1∧A2∧A3∧(A4∨A5)")
log("  GOM-A conditions for BROCCOLIF3B (using DAILY data from build):")
log("  GOM-A fires: 0 (from build_case.py output)")
log("  GOM-B fires: 0")
log("  → No GOM-A or GOM-B fire in 30d window")
log("")
log("  GOM-C rechấm (window, daily granularity):")
log(f"  Spec: C1(stealth_grind) ∧ C2_quiet(|f_avg|≤2×neutral) ∧ C3_lax(taker∈[40,55]) ∧ d_pos≥0")
log(f"  {'date':12s} {'f_avg':>10s} {'taker%':>8s} {'pos_r':>7s} {'Δpos_r':>8s} {'C2':>4s} {'C3':>4s} {'C1hint':>8s} {'GOM-C?':>7s}")
prev_pos = None
gomc_days = []
lsr_dates_win = sorted(d for d in lsr_by_d if WIN_START <= d <= WIN_END)
for dt in lsr_dates_win:
    ls = lsr_by_d[dt]
    pos = gf(ls, "pos_r")
    glsr = gf(ls, "glsr_raw")
    p = perp_by_d.get(dt, {})
    taker = gf(p, "taker_pct")
    f_rates = fund_by_d.get(dt, [])
    f_avg = statistics.mean(f_rates) if f_rates else None
    c2 = (f_avg is not None and abs(f_avg) <= 1e-4)
    c3 = (taker is not None and 0.40 <= taker <= 0.55)
    d_pos = (pos - prev_pos) if (pos and prev_pos) else None
    dpos_ok = (d_pos is not None and d_pos >= 0)
    # C1 hint: gLSR "quiet" — gLSR < 2 (provisional, exact spec gate 15/08)
    c1_hint = "low" if (glsr and glsr < 2.0) else ("mid" if (glsr and glsr < 4.0) else "HIGH")
    gomc = c2 and c3 and dpos_ok
    if gomc:
        gomc_days.append(dt)
    log(f"  {dt:12s} {f_avg:>10.6f} {f'{taker*100:.1f}%' if taker else 'N/A':>8s} "
        f"{pos:>7.4f} {f'{d_pos:+.4f}' if d_pos is not None else 'N/A':>8s} "
        f"{'✓' if c2 else '✗':>4s} {'✓' if c3 else '✗':>4s} {c1_hint:>8s} "
        f"{'YES' if gomc else '—':>7s}"
        if f_avg is not None and pos else f"  {dt:12s} (missing data)")
    prev_pos = pos if pos else prev_pos

log(f"\n  GOM-C pass days (C2∧C3∧d_pos≥0): {len(gomc_days)}")
if gomc_days:
    log(f"  Dates: {gomc_days}")
log(f"  Note: C1 spec = PROVISIONAL gate 15/08/2026 — mark as PROVISIONAL if filing")

# ═══════════════════════════════════════════════════════════════════════════
# BR3-4: PHASE CONTEXT
# ═══════════════════════════════════════════════════════════════════════════
log("\n" + "="*70)
log("BR3-4: PHASE CONTEXT")
log("="*70)

closes = [(dt, gf(perp_by_d[dt], "close")) for dt in all_dates if gf(perp_by_d[dt], "close")]
prices = [c for _,c in closes]
ath = max(prices); ath_dt = closes[prices.index(ath)][0]
atl = min(prices); atl_dt = closes[prices.index(atl)][0]
c_last = closes[-1][1]; dt_last = closes[-1][0]

log(f"\n=== C-4a: Bối cảnh pha vòng đời ===")
log(f"  Listing perp: 2025-03-21 (onboardDate)")
log(f"  ATH:          ${ath:.6f} on {ath_dt}")
log(f"  ATL:          ${atl:.6f} on {atl_dt}")
log(f"  Last close ({dt_last}): ${c_last:.6f}")
log(f"  px vs ATH:    {(c_last/ath-1)*100:+.1f}%")
log(f"  px vs ATL:    {(c_last/atl-1)*100:+.1f}%")

# Key ignition events BEFORE LSR window (pre-2026-07-12)
log(f"\n  Vol spikes BEFORE LSR window (ignition history):")
pre_win = sorted(d for d in all_dates if d < WIN_START)
vol_med_vals = []
for d in pre_win:
    v = gf(perp_by_d[d], "vol_quote_usd")
    if v: vol_med_vals.append(v)
if len(vol_med_vals) >= 14:
    import statistics as st
    # Show notable days >8× their local med14
    log(f"  (top vol spikes from build output — 26 total ≥8× med14):")
    notable_pre = ["2025-04-20","2025-05-15","2025-08-07","2025-08-18","2025-08-19",
                   "2025-09-10","2025-09-12","2025-10-07","2025-10-08","2025-10-09",
                   "2025-10-10","2025-10-11","2025-10-14","2025-12-30","2025-12-31",
                   "2026-02-25","2026-04-05","2026-04-14","2026-05-09","2026-05-20",
                   "2026-07-01","2026-07-02"]
    for d in notable_pre:
        p = perp_by_d.get(d, {})
        c = gf(p, "close"); vol = gf(p, "vol_quote_usd"); ret = date_ret.get(d)
        taker = gf(p, "taker_pct")
        if c and vol:
            log(f"    {d}: px=${c:.6f} vol=${vol/1e6:.2f}M {f'ret={ret*100:+.1f}%' if ret else ''} {f'taker={taker*100:.0f}%' if taker else ''}")

# Recent spikes (in LSR window)
log(f"\n  Vol spikes IN window (2026-07-12→):")
recent_spikes = ["2026-07-22","2026-07-23","2026-07-27","2026-07-28","2026-08-09"]
for d in recent_spikes:
    p = perp_by_d.get(d, {})
    c = gf(p, "close"); vol = gf(p, "vol_quote_usd"); ret = date_ret.get(d)
    taker = gf(p, "taker_pct")
    if c and vol:
        log(f"    {d}: px=${c:.6f} vol=${vol/1e6:.2f}M {f'ret={ret*100:+.1f}%' if ret else ''} {f'taker={taker*100:.0f}%' if taker else ''}")

# Nền analysis
log(f"\n  Phân tích nền/base (last 90d before 07-22 spike):")
base_range = sorted(d for d in all_dates if "2026-04-22" <= d < "2026-07-22")
base_closes = [gf(perp_by_d[d],"close") for d in base_range if gf(perp_by_d[d],"close")]
if base_closes:
    log(f"  Nền 04-22→07-21 ({len(base_closes)} ngày): avg=${statistics.mean(base_closes):.6f} "
        f"min=${min(base_closes):.6f} max=${max(base_closes):.6f}")

# ── 5 flags (last 30 LSR dates) ──────────────────────────────────────────
log(f"\n=== BR3-4c: 5 Cờ chẩn đoán (last 30 LSR dates) ===")
lsr_dates_30 = sorted(lsr_by_d.keys())[-30:]
flag_dist = flag_knife = flag_hedge = flag_neg_div = flag_decay = 0
for i, dt in enumerate(lsr_dates_30):
    ret = date_ret.get(dt)
    p = perp_by_d.get(dt, {})
    taker = gf(p, "taker_pct")
    ls = lsr_by_d.get(dt, {})
    pos = gf(ls, "pos_r"); acc = gf(ls, "acc_r"); glsr = gf(ls, "glsr_raw")
    div = pos/acc if (pos and acc and acc > 0) else None
    f = fund_by_d.get(dt, [])
    f_avg = statistics.mean(f) if f else None
    if taker and ret and taker >= 0.50 and ret < 0: flag_dist += 1
    if i > 0 and ret and glsr:
        prev_ls = lsr_by_d.get(lsr_dates_30[i-1], {})
        prev_glsr = gf(prev_ls, "glsr_raw")
        if prev_glsr and glsr > prev_glsr and ret < -0.03: flag_knife += 1
    if div is not None and div <= 0.5: flag_hedge += 1
    if f_avg is not None and f_avg <= -2e-4: flag_neg_div += 1
    if taker and taker < 0.45: flag_decay += 1

log(f"  Window: last 30 LSR dates ({lsr_dates_30[0]}→{lsr_dates_30[-1]})")
log(f"  {'Flag':40s} {'Count':>6s} {'Rate':>8s}")
log(f"  {'flag_dist_wall (taker≥50+ret<0)':40s} {flag_dist:>6d} {flag_dist/30:.1%}")
log(f"  {'flag_knife (gLSR↑+ret<-3%)':40s} {flag_knife:>6d} {flag_knife/30:.1%}")
log(f"  {'flag_hedge_struct (div≤0.5)':40s} {flag_hedge:>6d} {flag_hedge/30:.1%}")
log(f"  {'flag_neg_div (f_avg≤-2e-4)':40s} {flag_neg_div:>6d} {flag_neg_div/30:.1%}")
log(f"  {'flag_decay (taker<45%)':40s} {flag_decay:>6d} {flag_decay/30:.1%}")

# ── Pin streak + OI cycle pos (last 14d) ─────────────────────────────────
log(f"\n=== BR3-4d: PIN_STREAK + OI_CYCLE_POS (last 14d) ===")
log(f"  PIN = f_avg ∈ [4e-5, 6e-5]")
oi_30d = [v for dt,v in sorted(oi_by_d.items()) if v is not None][-30:]
oi_min30 = min(oi_30d) if oi_30d else None
oi_max30 = max(oi_30d) if oi_30d else None
pin_streak = 0
oi_dates = sorted(oi_by_d.keys())[-14:]
log(f"  {'date':12s} {'f_avg':>10s} {'f_n':>5s} {'PIN?':>6s} {'oi_usd':>14s} {'oi_cycle':>9s}")
for dt in oi_dates:
    f = fund_by_d.get(dt, [])
    f_avg = statistics.mean(f) if f else None
    f_n = len(f)
    oi_v = oi_by_d.get(dt)
    oi_cycle = (oi_v - oi_min30)/(oi_max30 - oi_min30) if (oi_v and oi_min30 and oi_max30 and oi_max30 > oi_min30) else None
    pin = (f_avg is not None and 4e-5 <= f_avg <= 6e-5)
    if pin: pin_streak += 1
    else: pin_streak = 0
    log(f"  {dt:12s} {f_avg:>10.6f} {f_n:>5d} {'PIN✓' if pin else '—':>6s} "
        f"${oi_v:>13,.0f} {oi_cycle:>9.3f}"
        if f_avg is not None and oi_v and oi_cycle is not None
        else f"  {dt:12s} (missing)")

log(f"\n  pin_streak (last date): {pin_streak}")
log(f"  OI_min30: ${oi_min30:,.0f}"); log(f"  OI_max30: ${oi_max30:,.0f}")
if oi_by_d.get(WIN_END) and oi_min30 and oi_max30 and oi_max30 > oi_min30:
    cp = (oi_by_d[WIN_END]-oi_min30)/(oi_max30-oi_min30)
    log(f"  oi_cycle_pos ({WIN_END}): {cp:.3f}")

# ═══════════════════════════════════════════════════════════════════════════
# BR3-5a: BAPI + PERP INFO + DEPTH SNAP #1
# ═══════════════════════════════════════════════════════════════════════════
log("\n" + "="*70)
log("BR3-5a: BAPI + PERP INFO + DEPTH SNAP #1")
log("="*70)

log("\n=== Perp info ===")
pi_path = SCRATCH / f"br3_perp_info_{DATE_TAG}.json"
if pi_path.exists():
    pi = json.loads(pi_path.read_text(encoding="utf-8"))
    log(f"  symbol:      {pi.get('symbol')}")
    log(f"  status:      {pi.get('status')}")
    onb = pi.get("onboardDate")
    if onb:
        log(f"  onboard:     {datetime.fromtimestamp(int(onb)/1000,tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log(f"  contractType:{pi.get('contractType')}")
    log(f"  quoteAsset:  {pi.get('quoteAsset')}")

log(f"\n=== BAPI status ===")
log(f"  BROCCOLIF3B is NOT an Alpha-listed token")
log(f"  Not found in BAPI token list (660 tokens)")
log(f"  No Alpha ID, no fullyDelisted status applicable")
log(f"  taker_alpha: N/A (not Alpha token)")

log(f"\n=== Depth snap #1 ===")
depth_url = "https://fapi.binance.com/fapi/v1/depth?symbol=BROCCOLIF3BUSDT&limit=1000"
depth_raw = fetch_json(depth_url)
snap1_time = datetime.now(timezone.utc)
snap1_str = snap1_time.strftime("%Y-%m-%d %H:%M:%S UTC")
if depth_raw:
    bids = [(float(p), float(q)) for p,q in depth_raw.get("bids",[])]
    asks = [(float(p), float(q)) for p,q in depth_raw.get("asks",[])]
    if bids and asks:
        mid = (bids[0][0]+asks[0][0])/2
        spread_pct = (asks[0][0]-bids[0][0])/mid*100
        bid2 = sum(p*q for p,q in bids)
        ask2 = sum(p*q for p,q in asks)
        ratio = bid2/ask2 if ask2>0 else None
        log(f"  Time:    {snap1_str}")
        log(f"  mid:     ${mid:.8f}")
        log(f"  bid_top: ${bids[0][0]:.8f} ask_top: ${asks[0][0]:.8f}")
        log(f"  spread:  {spread_pct:.3f}%")
        log(f"  bid2(full book): ${bid2:,.0f}")
        log(f"  ask2(full book): ${ask2:,.0f}")
        log(f"  ratio bid/ask: {ratio:.4f}" if ratio else "  ratio: N/A")
        log(f"\n  Depth buckets:")
        for pct in [0.01, 0.02, 0.05]:
            bid_b = sum(p*q for p,q in bids if p >= mid*(1-pct))
            ask_b = sum(p*q for p,q in asks if p <= mid*(1+pct))
            r_b = bid_b/ask_b if ask_b > 0 else None
            log(f"    ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=${ask_b:,.0f} ratio={r_b:.3f}" if r_b else f"    ±{pct*100:.0f}%: bid=${bid_b:,.0f} ask=0")
        snap1_out = SCRATCH / f"br3_depth_snap1_{DATE_TAG}.json"
        snap1_out.write_text(json.dumps({
            "snap":1,"time":snap1_str,"symbol":"BROCCOLIF3BUSDT",
            "mid":mid,"bid_top":bids[0][0],"ask_top":asks[0][0],
            "spread_pct":spread_pct,"bid2_usd":bid2,"ask2_usd":ask2,"ratio":ratio,
        },indent=2),encoding="utf-8")
        log(f"\n  Saved: {snap1_out.name}")
        snap2_gate = datetime.fromtimestamp(snap1_time.timestamp()+4*3600, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        log(f"  SNAP #2 GATE: ≥{snap2_gate}")
else:
    log(f"  Depth fetch failed")

# ── Alpha vol / on-chain note ─────────────────────────────────────────────
log(f"\n=== On-chain / chain note ===")
log(f"  BscScan: NOTOK V1 — CẦN OPERATOR")
log(f"  Nansen: LOCKED — CẦN OPERATOR")
log(f"  Chain: BSC (from exchangeInfo baseAsset=BROCCOLIF3B)")
log(f"  Contract: UNKNOWN — CẦN OPERATOR (no BAPI entry)")

log(f"\n[BR3-345 DONE]")
