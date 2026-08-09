"""
_probe_ff_f3_q123_20260808.py
F-3: Tái lập độc lập "$2M" — ba phương pháp §3 + bảng đối chất.
"""
import sys, io, json, csv, math, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXP = Path(r"D:\Check onchain fresh wallets\data\export")
DATE_TAG = "20260808"

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"FF F-3 Q1/Q2/Q3 REPLICATION  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

# ── Load freshwatch FF data ───────────────────────────────────────────────────
fw_rows = []
for fw_f in [
    SCRATCH / "freshwatch_daily_2026-06.csv",
    SCRATCH / "freshwatch_daily_2026-07.csv",
    SCRATCH / "freshwatch_daily_2026-08.csv",
    VPS_EXP / "freshwatch_daily_2026-06.csv",
    VPS_EXP / "freshwatch_daily_2026-07.csv",
    VPS_EXP / "freshwatch_daily_2026-08.csv",
]:
    if not fw_f.exists(): continue
    with open(fw_f, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("symbol","").upper() == "FFUSDT":
                fw_rows.append(r)

# Deduplicate by date
fw_by_date = {}
for r in fw_rows:
    dt = r.get("date","")
    if dt and dt not in fw_by_date:
        fw_by_date[dt] = r
fw_rows = sorted(fw_by_date.values(), key=lambda r: r.get("date",""))
log(f"  Freshwatch FF rows loaded: {len(fw_rows)}")

def sf(v, d=None):
    try: return float(v) if v not in (None, "", "nan", "None") else d
    except: return d

# ── Identify cửa sổ build ứng viên ───────────────────────────────────────────
log("\n=== CỬA SỔ BUILD ỨNG VIÊN ===")
log("  Căn cứ xác định: gom_state_v8.json chain start=2026-08-01, last=2026-08-07")
log("  Bằng chứng bổ sung từ freshwatch series:")
log("  - OI jump event: 07-29→07-30 (+$2.4M: 27.6M→30.0M) — pre-window")
log("  - OI post-jump plateau: 07-31→08-07 (~27.4M→29.0M range)")
log("  - pos_r leo: 2.97 (07-30) → 3.27 (08-07)")
log("  - gLSR trũng: 0.46 (07-30) → 0.53 (08-07) [shorts dominant]")
log("  → Cửa sổ build chính: 2026-08-01 → 2026-08-07 (7 days)")
log("  → Cửa sổ mở rộng: 2026-07-30 → 2026-08-07 (9 days, bao gồm OI spike)")

WIN_START = "2026-08-01"
WIN_END   = "2026-08-07"
WIN_START_BROAD = "2026-07-29"  # ngay sau OI spike onset

window_rows = [r for r in fw_rows if WIN_START <= r.get("date","") <= WIN_END]
log(f"\n  Window rows (08-01→08-07): {len(window_rows)}")

# ── Q1 [DATA-BOUND]: ΔOI⁺ trong nến ret ≤ 1% ───────────────────────────────
log("\n=== Q1 [DATA-BOUND] — ΔOI⁺ cho ret ≤ 1% (công thức bot) ===")
log(f"  Công thức: Σ max(OI_d - OI_{{d-1}}, 0) khi ret_1d ≤ 1%")
log(f"  Nguồn: freshwatch daily oi_usd")
log()
log(f"  {'Date':<12} {'OI_USD':>14} {'ΔOI':>12} {'ΔOI⁺':>12} {'ret_1d':>8} {'Count?'}")
log(f"  {'-'*12} {'-'*14} {'-'*12} {'-'*12} {'-'*8} {'-'*6}")

all_dates_fw = sorted(fw_by_date.keys())
q1_main = 0.0
q1_broad = 0.0
n_days_q1 = 0
prev_oi = None
prev_px = None

q1_rows = []
for dt in all_dates_fw:
    r = fw_by_date[dt]
    oi_now = sf(r.get("oi_usd"))
    px_now = sf(r.get("px_avg"))

    delta_oi = None
    ret_1d = None
    if prev_oi is not None and oi_now is not None:
        delta_oi = oi_now - prev_oi
    if prev_px is not None and px_now is not None and prev_px > 0:
        ret_1d = (px_now - prev_px) / prev_px

    in_main = WIN_START <= dt <= WIN_END
    in_broad = WIN_START_BROAD <= dt <= WIN_END

    if delta_oi is not None and ret_1d is not None and in_main:
        delta_oi_pos = max(delta_oi, 0.0)
        counts = ret_1d <= 0.01
        if counts:
            q1_main += delta_oi_pos
            n_days_q1 += 1
        flag = "✓" if (counts and delta_oi_pos > 0) else ("skip-ret" if not counts else "ΔOI=0")
        log(f"  {dt:<12} {oi_now:>14,.0f} {delta_oi:>+12,.0f} {delta_oi_pos:>12,.0f} {ret_1d:>+8.3%} {flag}")
        q1_rows.append({"date":dt,"oi_usd":oi_now,"delta_oi":delta_oi,
                        "delta_oi_pos":delta_oi_pos,"ret_1d":ret_1d,"counts":counts})
    elif in_broad and delta_oi is not None:
        delta_oi_pos = max(delta_oi, 0.0)
        q1_broad += delta_oi_pos if (ret_1d is not None and ret_1d <= 0.01) else 0.0

    prev_oi = oi_now
    prev_px = px_now

log(f"\n  Q1 (window 08-01→08-07):  ${q1_main:>12,.0f}  n_days={n_days_q1}")
log(f"  BOT number (gom_state_v8): $  1,988,262")
diff = q1_main - 1_988_262
log(f"  Diff vs bot:               ${diff:>+12,.0f} ({diff/1_988_262*100:+.1f}%)")

# ── Q2 [INFERENCE]: OI × share_top_long (r/(1+r)) ────────────────────────────
log("\n=== Q2 [INFERENCE] — OI × top-long share ===")
log("  Công thức: share_top_long = pos_r / (1 + pos_r)")
log("  Q2_net = OI_end × share_end - OI_start × share_start")
log("  Trần cứng sổ = OI_max × share_end")

row_start = fw_by_date.get(WIN_START)
row_end   = fw_by_date.get(WIN_END)

if row_start and row_end:
    oi_start  = sf(row_start.get("oi_usd"))
    pos_start = sf(row_start.get("lsr_pos_r"))
    oi_end    = sf(row_end.get("oi_usd"))
    pos_end   = sf(row_end.get("lsr_pos_r"))
    oi_max    = max(sf(r.get("oi_usd"), 0) for r in window_rows)
    oi_min    = min((sf(r.get("oi_usd")) for r in window_rows if sf(r.get("oi_usd"))), default=None)

    sh_start = pos_start / (1 + pos_start) if pos_start else None
    sh_end   = pos_end   / (1 + pos_end)   if pos_end   else None

    log(f"\n  Window start ({WIN_START}): OI=${oi_start:,.0f}, pos_r={pos_start:.4f}, share={sh_start:.4f}")
    log(f"  Window end   ({WIN_END}): OI=${oi_end:,.0f}, pos_r={pos_end:.4f}, share={sh_end:.4f}")
    log(f"  OI min: ${oi_min:,.0f}  OI max: ${oi_max:,.0f}")

    if sh_start and sh_end and oi_start and oi_end:
        long_start = oi_start * sh_start
        long_end   = oi_end   * sh_end
        q2_net     = long_end - long_start
        q2_ceiling = oi_max * sh_end

        log(f"\n  Implied long (start): ${long_start:,.0f}")
        log(f"  Implied long (end):   ${long_end:,.0f}")
        log(f"  Q2_net (accumulation implied): ${q2_net:>12,.0f}")
        log(f"  Q2 ceiling (trần cứng): ${q2_ceiling:>12,.0f}")
    else:
        q2_net, q2_ceiling = None, None
        log("  Q2: N/A (missing data)")

    # Q2 via GOM-C formula (gom_scan.py line 1088): div_raw=pos_r/acc_r, gate div≥3 & acc_r≤1
    acc_end = sf(row_end.get("lsr_acc_r"))
    if acc_end and pos_end:
        div_raw = pos_end / acc_end
        log(f"\n  GOM-C Q2 gate check (08-07): pos_r={pos_end:.4f}, acc_r={acc_end:.4f}")
        log(f"  div_raw = {div_raw:.3f}  (gate: div≥3 AND acc_r≤1)")
        if div_raw >= 3.0 and acc_end <= 1.0:
            tilt = (pos_end - 1) / (pos_end + 1)
            q2_lo_gomc = oi_end * 0.5 * tilt
            q2_hi_gomc = oi_end * 0.8 * tilt
            log(f"  Gate PASS: tilt={tilt:.4f}")
            log(f"  GOM-C Q2_lo = ${q2_lo_gomc:,.0f}  Q2_hi = ${q2_hi_gomc:,.0f}")
        else:
            log(f"  Gate FAIL (div={div_raw:.2f} {'<3' if div_raw<3 else 'ok'}, acc={'≤1' if acc_end<=1 else '>1'})")
            q2_lo_gomc, q2_hi_gomc = None, None

# ── Q3 [SPOT CAPACITY] ────────────────────────────────────────────────────────
log("\n=== Q3 [SPOT CAPACITY] ===")
log("  Công thức: spot vol × 10-30% + taker_spot (Binance spot có)")

# Load spot klines
spot_csv = SCRATCH / f"ff_spot_{DATE_TAG}.csv"
spot_rows_w = []
if spot_csv.exists():
    with open(spot_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if WIN_START <= r.get("date","") <= WIN_END:
                spot_rows_w.append(r)

if spot_rows_w:
    log(f"  Spot rows in window: {len(spot_rows_w)}")
    total_spot_vol = sum(sf(r.get("vol_spot_usd"), 0) for r in spot_rows_w)
    avg_taker = None
    taker_vals = [sf(r.get("taker_spot_pct")) for r in spot_rows_w if sf(r.get("taker_spot_pct"))]
    if taker_vals: avg_taker = sum(taker_vals)/len(taker_vals)
    log(f"  Total spot vol (window): ${total_spot_vol:,.0f}")
    log(f"  Avg taker_spot_pct: {avg_taker:.4f}" if avg_taker else "  Avg taker_spot_pct: N/A")
    q3_lo = total_spot_vol * 0.10
    q3_hi = total_spot_vol * 0.30
    log(f"  Q3 range (10-30% of vol): ${q3_lo:,.0f} — ${q3_hi:,.0f}")
    log(f"\n  {'Date':<12} {'vol_spot':>14} {'taker_pct':>10}")
    for r in spot_rows_w:
        log(f"  {r['date']:<12} {sf(r.get('vol_spot_usd'),0):>14,.0f} {sf(r.get('taker_spot_pct'),0):>10.4f}")
else:
    log("  No spot data in window (spot_csv empty or missing)")
    total_spot_vol = 0
    q3_lo, q3_hi = None, None

# ── VWAP build ────────────────────────────────────────────────────────────────
log("\n=== VWAP BUILD ===")
log("  VWAP = Σ(ΔOI⁺ × px_avg) / Σ(ΔOI⁺)  [ΔOI⁺-weighted, from gom_scan]")
log("  Fallback: vol-weighted for seat-rotation days (ΔOI⁺=0)")

vwap_num, vwap_den = 0.0, 0.0
for row in q1_rows:
    px = sf(fw_by_date[row["date"]].get("px_avg"))
    dop = row["delta_oi_pos"]
    if dop > 0 and px:
        vwap_num += dop * px
        vwap_den += dop
    elif dop == 0 and row["counts"] and px:
        vol = sf(fw_by_date[row["date"]].get("vol_quote"), 0)
        if vol and vol > 0:
            vwap_num += vol * px
            vwap_den += vol

vwap_calc = vwap_num / vwap_den if vwap_den > 0 else None
px_current = sf(fw_by_date.get(WIN_END, {}).get("px_avg"))
log(f"  VWAP (recalculated): ${vwap_calc:.8f}" if vwap_calc else "  VWAP: N/A")
log(f"  VWAP (gom_state_v8): $0.06407586")
log(f"  Current px ({WIN_END}): ${px_current:.8f}" if px_current else f"  Current px: N/A")
if vwap_calc and px_current:
    px_vs_vwap = (px_current - vwap_calc) / vwap_calc * 100
    log(f"  px vs VWAP: {px_vs_vwap:+.2f}%")

# ── BẢNG ĐỐI CHẤT (F-3e) ─────────────────────────────────────────────────────
log("\n=== F-3e: BẢNG ĐỐI CHẤT ===")
log(f"  Cửa sổ: {WIN_START} → {WIN_END}")
log()
log(f"  {'Phương pháp':<35} {'Số USD':>15} {'Ghi chú'}")
log(f"  {'-'*35} {'-'*15} {'-'*30}")

# Bot number
log(f"  {'Bot (gom_state_v8 Q1_cum)':<35} {'$1,988,262':>15} Σ ΔOI⁺ ret≤1%, gom_scan.py formula")

# Q1 recalculate
q1_str = f"${q1_main:>,.0f}" if q1_main else "N/A"
q1_note = "Σ ΔOI⁺ ret≤1% — freshwatch oi_usd"
log(f"  {'Q1 (DATA tái lập)':<35} {q1_str:>15} {q1_note}")

# Q2 net range
if q2_net is not None:
    log(f"  {'Q2_net (INFERENCE — OI×share)':<35} ${q2_net:>14,.0f} pos_r/(1+pos_r) × OI boundary")
    log(f"  {'Q2 ceiling (trần cứng sổ)':<35} ${q2_ceiling:>14,.0f} OI_max × share_end")
else:
    log(f"  {'Q2_net (INFERENCE)':<35} {'N/A':>15} missing LSR data")

# Q3
if q3_lo is not None:
    log(f"  {'Q3 spot lo (10% × vol_spot)':<35} ${q3_lo:>14,.0f} FFUSDT spot TRADING")
    log(f"  {'Q3 spot hi (30% × vol_spot)':<35} ${q3_hi:>14,.0f}")
else:
    log(f"  {'Q3 (spot capacity)':<35} {'N/A':>15} no spot data in window")

log()
log("  ⟹ KHÔNG BÌNH LUẬN — bảng số thô để ANALYSIS đọc")

# ── OI nở analysis ───────────────────────────────────────────────────────────
log("\n=== OI NỞ ANALYSIS ===")
log(f"  OI đầu cửa sổ ({WIN_START}): ${sf(fw_by_date.get(WIN_START,{}).get('oi_usd'),0):,.0f}")
log(f"  OI cuối cửa sổ ({WIN_END}): ${sf(fw_by_date.get(WIN_END,{}).get('oi_usd'),0):,.0f}")
oi_s = sf(fw_by_date.get(WIN_START,{}).get("oi_usd"))
oi_e = sf(fw_by_date.get(WIN_END,{}).get("oi_usd"))
if oi_s and oi_e:
    log(f"  Net OI change: ${oi_e-oi_s:+,.0f} ({(oi_e-oi_s)/oi_s*100:+.1f}%)")
    log(f"  OI trạng thái: {'NỞ' if oi_e > oi_s else 'THU'}")

log("\n[F-3 DONE]")
