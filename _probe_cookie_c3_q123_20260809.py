"""
_probe_cookie_c3_q123_20260809.py
COOKIE C-3: §3 ba phương pháp tái lập + bảng đối chất
Reads from raw CSV files to avoid xlsx header complexity.
"""
import sys, io, json, csv, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260809"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"COOKIE C-3 Q1/Q2/Q3  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def read_csv(path):
    if not path.exists():
        log(f"  MISSING: {path.name}")
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def gf(d, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "" and v != "None":
            try: return float(v)
            except: pass
    return None

# ── Load raw CSVs ─────────────────────────────────────────────────────────────
perp_rows = read_csv(SCRATCH / f"cookie_perp_{DATE_TAG}.csv")      # date,close,vol_quote_usd,taker_pct
spot_rows = read_csv(SCRATCH / f"cookie_spot_{DATE_TAG}.csv")      # date,close,vol_quote_usd,taker_pct
lsr_rows  = read_csv(SCRATCH / f"cookie_lsr_raw_{DATE_TAG}.csv")   # date,pos_r,acc_r,glsr_raw,taker_lsr_r,oi_usd

log(f"  perp_rows: {len(perp_rows)}, spot_rows: {len(spot_rows)}, lsr_rows: {len(lsr_rows)}")

# Build per-date dicts
perp_by_d = {r["date"]: r for r in perp_rows}
spot_by_d = {r["date"]: r for r in spot_rows}
lsr_by_d  = {r["date"]: r for r in lsr_rows}

# OI from oi_hist CSV (prefer) or lsr CSV (fallback)
oi_rows = read_csv(SCRATCH / f"cookie_oi_hist_{DATE_TAG}.csv")
oi_by_d = {r["date"]: gf(r,"oi_usd") for r in oi_rows}
# Also try lsr_rows for oi_usd
for r in lsr_rows:
    dt = r["date"]
    if dt not in oi_by_d or oi_by_d[dt] is None:
        v = gf(r,"oi_usd")
        if v: oi_by_d[dt] = v

# ── Define window ─────────────────────────────────────────────────────────────
log("\n=== BUILD WINDOW ===")
CHAIN_START = "2026-08-03"
CHAIN_CLOSE = "2026-08-06"
WIN_START   = "2026-08-01"
WIN_END     = "2026-08-08"  # inclusive; 08-08 = last complete candle (L-21 from 08-09)
log(f"  Chain:   {CHAIN_START} → {CHAIN_CLOSE} (GOM-C fire start, close_reason=gom_gap>2d)")
log(f"  Audit:   {WIN_START} → {WIN_END}")
log(f"  Rationale: chain window + 3d context before/after; OI/LSR available throughout")

# All dates in perp (chronological)
all_dates = sorted(perp_by_d.keys())

# ── Display window table ──────────────────────────────────────────────────────
log("\n=== WINDOW DATA TABLE ===")
log(f"  {'date':12s} {'ret%':>7s} {'close':>9s} {'vol_perp$':>12s} {'oi_usd$':>12s} {'Δoi$':>10s} {'pos_r':>6s} {'gLSR':>6s}")
prev_oi = None
# Compute ret_1d from perp_rows
prev_close = None
for dt in sorted(d for d in all_dates if WIN_START <= d <= WIN_END):
    p = perp_by_d.get(dt, {})
    c = gf(p,"close")
    vol = gf(p,"vol_quote_usd")
    oi = oi_by_d.get(dt)
    ls = lsr_by_d.get(dt, {})
    pos = gf(ls,"pos_r")
    glsr = gf(ls,"glsr_raw")
    # ret from prev
    ret = (c - prev_close)/prev_close if (c and prev_close) else None
    delta_oi = (oi - prev_oi) if (oi and prev_oi) else None
    log(f"  {dt:12s} {f'{ret*100:+.2f}%' if ret is not None else 'N/A':>7s} "
        f"{c:>9.6f} ${vol:>11,.0f} ${oi:>11,.0f} "
        f"{f'${delta_oi:+,.0f}' if delta_oi is not None else 'N/A':>10s} "
        f"{pos:>6.4f} {glsr:>6.4f}"
        if (c and vol and oi and pos and glsr) else
        f"  {dt:12s} (partial data)")
    prev_close = c
    prev_oi = oi

# ── Q1 ────────────────────────────────────────────────────────────────────────
log("\n=== Q1: ΔOI⁺ nến đỏ/phẳng ===")
log("  Formula: Q1 = Σ max(OI_d - OI_{d-1}, 0) where ret_1d ≤ 1%")
log("  Source: OI from cookie_oi_hist (30d) for window + lsr_rows for dates before")
log("  Note: bot n=1, Q1=0 because 08-03 OI didn't increase vs 08-02")

# Compute ret_1d for all dates first
date_ret = {}
prev_c = None
for dt in sorted(all_dates):
    c = gf(perp_by_d.get(dt, {}),"close")
    if c and prev_c:
        date_ret[dt] = (c - prev_c)/prev_c
    prev_c = c

# Q1 by day for audit window
log(f"\n  Day-by-day Q1 ({WIN_START}→{WIN_END}):")
log(f"  {'date':12s} {'ret%':>7s} {'OI':>12s} {'ΔOI':>10s} {'ΔOI⁺':>10s} {'counts?':>8s} {'Q1_add':>10s}")
q1_chain = 0.0
q1_win = 0.0
prev_oi = None
prev_dt = None
for dt in sorted(d for d in all_dates if "2026-07-31" <= d <= WIN_END):
    oi = oi_by_d.get(dt)
    ret = date_ret.get(dt)
    delta = (oi - prev_oi) if (oi and prev_oi) else None
    delta_pos = max(delta, 0) if delta is not None else 0
    counts = (ret is not None and ret <= 0.01)
    q1_add = delta_pos if counts else 0.0
    if WIN_START <= dt <= WIN_END:
        q1_win += q1_add
        if CHAIN_START <= dt <= CHAIN_CLOSE:
            q1_chain += q1_add
    if "2026-07-31" <= dt <= WIN_END:
        flag = "YES" if counts else "NO"
        log(f"  {dt:12s} {f'{ret*100:+.2f}%' if ret is not None else 'N/A':>7s} "
            f"${oi if oi else 0:>11,.0f} "
            f"{f'${delta:+,.0f}' if delta is not None else 'N/A':>10s} "
            f"${delta_pos:>9,.0f} {flag:>8s} ${q1_add:>9,.0f}")
    prev_oi = oi if oi else prev_oi
    prev_dt = dt

log(f"\n  Q1 chain window ({CHAIN_START}→{CHAIN_CLOSE}): ${q1_chain:,.0f}")
log(f"  Q1 audit window ({WIN_START}→{WIN_END}):   ${q1_win:,.0f}")
log(f"  Bot Q1_cum_usd (gom_state_v8):          $0 (1 day, no OI buildup)")

# ── Q2 ────────────────────────────────────────────────────────────────────────
log("\n=== Q2: OI×share = net long position estimate ===")
d_start_ls = lsr_by_d.get(WIN_START, {})
d_end_ls   = lsr_by_d.get(WIN_END, {})
oi_s = oi_by_d.get(WIN_START)
oi_e = oi_by_d.get(WIN_END)
pos_s = gf(d_start_ls,"pos_r")
pos_e = gf(d_end_ls,"pos_r")

if pos_s and pos_e and oi_s and oi_e:
    share_s = pos_s/(1+pos_s)
    share_e = pos_e/(1+pos_e)
    q2_net = oi_e*share_e - oi_s*share_s
    q2_ceil = oi_e*share_e
    log(f"  Start {WIN_START}: OI=${oi_s:,.0f} pos_r={pos_s:.4f} share={share_s:.4f} → long=${oi_s*share_s:,.0f}")
    log(f"  End   {WIN_END}:   OI=${oi_e:,.0f} pos_r={pos_e:.4f} share={share_e:.4f} → long=${oi_e*share_e:,.0f}")
    log(f"  Q2_net:    ${q2_net:+,.0f}")
    log(f"  Q2_ceiling:${q2_ceil:,.0f}")
    log(f"  OI_max: ${max(oi_s,oi_e):,.0f} — {'UNCALIBRATED (>$18M)' if max(oi_s,oi_e)>18_000_000 else 'within calib (<$18M)'}")
else:
    log(f"  Missing LSR or OI data: oi_s={oi_s} oi_e={oi_e} pos_s={pos_s} pos_e={pos_e}")
    q2_net = q2_ceil = None

# ── Q3 ────────────────────────────────────────────────────────────────────────
log("\n=== Q3: spot capacity ===")
spot_vol_win = 0.0
for dt in sorted(d for d in all_dates if WIN_START <= d <= WIN_END):
    sv = gf(spot_by_d.get(dt,{}),"vol_quote_usd")
    if sv:
        spot_vol_win += sv
        log(f"  {dt}: spot_vol=${sv:,.0f} taker={gf(spot_by_d.get(dt,{}),'taker_pct'):.1%}" if gf(spot_by_d.get(dt,{}),"taker_pct") else f"  {dt}: spot_vol=${sv:,.0f}")
log(f"  Tổng spot vol window: ${spot_vol_win:,.0f}")
log(f"  Q3 low  (10%): ${spot_vol_win*0.10:,.0f}")
log(f"  Q3 high (30%): ${spot_vol_win*0.30:,.0f}")

# ── VWAP ─────────────────────────────────────────────────────────────────────
log("\n=== VWAP tái lập (M2 vw-vol fallback) ===")
d_0803 = perp_by_d.get("2026-08-03", {})
c_0803 = gf(d_0803,"close")
vol_0803 = gf(d_0803,"vol_quote_usd")
log(f"  08-03 (fire day): close={c_0803:.8f} vol_perp=${vol_0803:,.0f}")
log(f"  Bot: VWAP=$0.00773654 [vw-vol] (num=7705.89/den=996038.12)")
if c_0803 and vol_0803:
    tokens = vol_0803/c_0803
    log(f"  Manual: px_avg×tokens/tokens = {c_0803:.8f} (1-day = price = VWAP)")
    log(f"  vol_tokens_estimated: {tokens:,.0f}")
    log(f"  Cross-check: num/den={7705.89/996038.12:.8f} vs close={c_0803:.8f}")
    log(f"  Δ = {(c_0803/(7705.89/996038.12)-1)*100:+.2f}%")

# ── BẢNG ĐỐI CHẤT ─────────────────────────────────────────────────────────────
log("\n=== BẢNG ĐỐI CHẤT ===")
log(f"  {'Phương pháp':35s} {'Số':>18s} {'Ghi chú'}")
log(f"  {'-'*35} {'-'*18} {'-'*30}")
log(f"  {'Bot (gom_state_v8, Q1_cum)':35s} {'$0':>18s} n=1 ngày, OI không tăng 08-03")
log(f"  {'Q1 tái lập (chain 08-03→06)':35s} ${q1_chain:>17,.0f} ΔOI⁺ nến đỏ/phẳng")
log(f"  {'Q1 tái lập (window 08-01→08)':35s} ${q1_win:>17,.0f} full audit window")
if q2_net is not None:
    log(f"  {'Q2 net (OI×share, 08-01→08-08)':35s} ${q2_net:>+17,.0f}")
    log(f"  {'Q2 ceiling (OI_end × share_end)':35s} ${q2_ceil:>17,.0f}")
log(f"  {'Q3 spot low (10%)':35s} ${spot_vol_win*0.10:>17,.0f}")
log(f"  {'Q3 spot high (30%)':35s} ${spot_vol_win*0.30:>17,.0f}")
log(f"  {'VWAP (bot)':35s} {'$0.00774':>18s} [vw-vol] fallback, 1 day")
log(f"  {'px 08-08 (most recent close)':35s} {'$0.01304':>18s} +68% vs VWAP")

log(f"\n[C-3 DONE]")
