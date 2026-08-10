"""
_probe_btw_3b_fix_20260810.py
W-3b: Fix f_avg (from DAILY not raw CSV) + vol + Q1 + GOM-C rechấm.
"""
import sys, io, csv, json, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
XLSX = ROOT / "docs" / "case_files" / "CASE_BTW.xlsx"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"W-3b FIX  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def sf(v, d=None):
    try: return float(v) if v not in (None,"","None","nan") else d
    except: return d

# ── Load DAILY sheet ─────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws_d = wb["DAILY"]
rows_raw = list(ws_d.iter_rows(values_only=True))

# Find header row (has "date" in col 0)
hdr_idx = None; headers = []
for i, row in enumerate(rows_raw):
    if str(row[0] or "").lower().strip() == "date":
        hdr_idx = i; headers = [str(c or "").strip() for c in row]; break

log(f"  DAILY headers ({len(headers)} cols):")
for ci in range(0, len(headers), 10):
    log(f"    [{ci}–{ci+9}]: {headers[ci:ci+10]}")

daily = []
for row in rows_raw[hdr_idx+1:]:
    if not row[0]: continue
    d = {}
    for k, v in zip(headers, row):
        if k: d[k] = v
    daily.append(d)
log(f"  Rows: {len(daily)} | Range: {daily[0]['date']} → {daily[-1]['date']}")

# Read all 50 cols for last row
log(f"\n  Last row keys with values:")
for k, v in daily[-1].items():
    if v is not None and v != "": log(f"    {k}: {v}")

# ── Load freshwatch LSR ───────────────────────────────────────────────────────
fw_by_d = {}
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != SYM: continue
            d = str(row.get("date",""))[:10]
            fw_by_d[d] = {
                "pos_r": sf(row.get("lsr_pos_r") or row.get("pos_r")),
                "acc_r": sf(row.get("lsr_acc_r") or row.get("acc_r")),
                "glsr":  sf(row.get("lsr_global_r") or row.get("gLSR")),
            }
fw_dates = sorted(fw_by_d.keys())
log(f"\n  FW dates: {len(fw_dates)} ({fw_dates[0]} → {fw_dates[-1]})")

# Build per-day arrays from DAILY + FW merge
dates = [str(r["date"])[:10] for r in daily]
pos_r_arr, acc_r_arr, glsr_arr = [], [], []
f_avg_arr, taker_arr, vol_arr, close_arr, oi_arr = [], [], [], [], []

for i, r in enumerate(daily):
    d = dates[i]
    fw = fw_by_d.get(d, {})
    pos_r_arr.append(sf(r.get("pos_r") or r.get("lsr_pos_r")) or fw.get("pos_r"))
    acc_r_arr.append(sf(r.get("acc_r") or r.get("lsr_acc_r")) or fw.get("acc_r"))
    glsr_arr.append(sf(r.get("glsr") or r.get("lsr_global_r")) or fw.get("glsr"))
    # f_avg from DAILY (correct column)
    f_avg_arr.append(sf(r.get("f_avg")))
    # taker — handle column name with suffix
    tk = None
    for k in r:
        if "taker" in k.lower() or "taker_buy" in k.lower():
            tk = sf(r[k]); break
    taker_arr.append(tk)
    # vol — handle column name with suffix
    vol = None
    for k in r:
        if "vol_perp" in k.lower() or "vol_quote" in k.lower():
            vol = sf(r[k]); break
    vol_arr.append(vol)
    close_arr.append(sf(r.get("c")))
    oi_arr.append(sf(r.get("oi_usd")))

log(f"\n=== Sanity check arrays ===")
f_valid = [(dates[i], f_avg_arr[i]) for i in range(len(daily)) if f_avg_arr[i] is not None]
log(f"  f_avg non-null: {len(f_valid)}")
if f_valid: log(f"  Last 5 f_avg: {[(d, round(v,6)) for d,v in f_valid[-5:]]}")
vol_valid = sum(1 for v in vol_arr if v)
log(f"  vol non-null: {vol_valid}")
close_valid = sum(1 for v in close_arr if v)
log(f"  close non-null: {close_valid}")

# ── div_avg3 ─────────────────────────────────────────────────────────────────
div_avg3_arr = []
for i in range(len(daily)):
    pw = [pos_r_arr[j] for j in range(max(0,i-2), i+1) if pos_r_arr[j] is not None]
    aw = [acc_r_arr[j] for j in range(max(0,i-2), i+1) if acc_r_arr[j] is not None]
    if len(pw) >= 2 and len(aw) >= 2:
        ap = sum(pw)/len(pw); aa = sum(aw)/len(aw)
        div_avg3_arr.append(round(ap/aa, 4) if aa > 0 else None)
    else:
        div_avg3_arr.append(None)

recent_div = [(dates[i], div_avg3_arr[i]) for i in range(len(daily)) if div_avg3_arr[i] is not None]
cur_div = recent_div[-1][1] if recent_div else None
cur_d_div = round(recent_div[-1][1]-recent_div[-2][1], 4) if len(recent_div)>=2 else None
log(f"\n  div_avg3 current: {cur_div}")
log(f"  div_avg3 Δ (day): {cur_d_div}")

# ── GOM-C rechấm (f_avg from DAILY) ─────────────────────────────────────────
log("\n=== GOM-C rechấm (f_avg from DAILY) ===")
C2_THRESH = 2e-4; PIN_LO = 4e-5; PIN_HI = 6e-5
gomc_dates = []
for i, r in enumerate(daily):
    d = dates[i]
    f = f_avg_arr[i]
    tk = taker_arr[i]
    p = pos_r_arr[i]
    p_prev = pos_r_arr[i-1] if i > 0 else None
    d_pos = (p - p_prev) if (p is not None and p_prev is not None) else None
    c2 = abs(f) <= C2_THRESH if f is not None else False
    c3 = 40.0 <= tk <= 55.0 if tk is not None else False
    dp = (d_pos >= 0) if d_pos is not None else True
    if c2 and c3 and dp:
        gomc_dates.append(d)

log(f"  GOM-C days: {len(gomc_dates)}")
if gomc_dates:
    log(f"  Range: {gomc_dates[0]} → {gomc_dates[-1]}")
    log(f"  Last 10: {gomc_dates[-10:]}")
gomc_post = [d for d in gomc_dates if d >= "2026-08-01"]
log(f"  Post-cooldown (≥08-01): {len(gomc_post)} | {gomc_post}")

# f_avg detail last 10 days
log(f"\n  f_avg last 14 days:")
for d, f in zip(dates[-14:], f_avg_arr[-14:]):
    if f is None: log(f"    {d}: N/A")
    else:
        status = "PIN" if PIN_LO<=f<=PIN_HI else ("HOT" if f>1e-3 else ("ABOVE" if f>PIN_HI else "BELOW/NEG"))
        log(f"    {d}: {f:.6f}  {status}")

# f_avg_3 (last 3 non-null)
last3_f = [f for f in f_avg_arr[-5:] if f is not None][-3:]
f_avg_3 = sum(last3_f)/len(last3_f) if last3_f else None
log(f"\n  f_avg_3: {f_avg_3:.6f}" if f_avg_3 else "  f_avg_3: N/A")

# ── Q1 from CASE sheet ────────────────────────────────────────────────────────
log("\n=== Q1 from CASE sheet ===")
ws_c = wb["CASE"]
for row in ws_c.iter_rows(values_only=True):
    row_str = [str(c or "") for c in row]
    log(f"  {row_str}")

# ── Q3 VWAP M2 (correct vol col) ─────────────────────────────────────────────
log("\n=== Q3 VWAP M2 ===")
num_vol = 0; denom_vw = 0
vw_entries = 0
for i in range(len(daily)):
    v = vol_arr[i]; c = close_arr[i]
    if v and c and c > 0:
        num_vol += v; denom_vw += v/c; vw_entries += 1
vwap_m2 = num_vol/denom_vw if denom_vw > 0 else None
px = close_arr[-1]
px_vs_vwap = ((px-vwap_m2)/vwap_m2*100) if (px and vwap_m2) else None
log(f"  Vol entries used: {vw_entries}")
log(f"  VWAP M2: ${vwap_m2:.6f}" if vwap_m2 else "  VWAP M2: N/A")
log(f"  Px: ${px:.6f}  vs VWAP: {px_vs_vwap:+.2f}%" if (px and px_vs_vwap) else f"  Px: {px}")
close_vals = [v for v in close_arr if v]
ath = max(close_vals) if close_vals else None
log(f"  ATH: ${ath:.6f}  dd_from_ath: {round((px-ath)/ath*100,2) if (px and ath) else 'N/A'}%")

# ── d_pos_28d ─────────────────────────────────────────────────────────────────
pos_pairs = [(dates[i], pos_r_arr[i]) for i in range(len(daily)) if pos_r_arr[i] is not None]
if len(pos_pairs) >= 2:
    d_latest, p_latest = pos_pairs[-1]
    cutoff28 = (datetime.strptime(d_latest, "%Y-%m-%d") - timedelta(days=28)).strftime("%Y-%m-%d")
    p28_pair = next(((d,p) for d,p in pos_pairs if d >= cutoff28), None)
    if p28_pair:
        d_pos_28d = round(p_latest - p28_pair[1], 4)
        log(f"\n  d_pos_28d: pos_r({d_latest})={p_latest:.4f} vs pos_r({p28_pair[0]})={p28_pair[1]:.4f} → {d_pos_28d:+.4f}")

# ── TRIAGE SUMMARY ────────────────────────────────────────────────────────────
log("\n=== TRIAGE SUMMARY ===")
glsr_valid = [(dates[i], glsr_arr[i]) for i in range(len(daily)) if glsr_arr[i] is not None]
cur_glsr = glsr_valid[-1][1] if glsr_valid else None

log(f"  div_avg3 = {cur_div:.4f} (HIGH_LONG, neg_div window Jul 22-30 cleared)")
log(f"  gLSR     = {cur_glsr:.4f} (BEAR, slope↓, retail SHORT-biased post-pump)")
log(f"  f_avg_3  = {f_avg_3:.6f}" if f_avg_3 else "  f_avg_3 = N/A")
log(f"  d_pos_28d = {d_pos_28d:+.4f} (RISING)" if 'd_pos_28d' in dir() else "")

log("\n=== TRIGGER-CHECK 3 ===")
c1 = f_avg_3 is not None and PIN_LO <= f_avg_3 <= PIN_HI
log(f"  C1 Pinned MỚI: f_avg_3={f_avg_3:.6f} → {'PASS' if c1 else 'FAIL'}")
c2_ok = ('d_pos_28d' in dir()) and d_pos_28d < 0 and (cur_d_div is not None and cur_d_div < 0)
log(f"  C2 Outflow TẠI NỀN: → {'PASS' if c2_ok else 'FAIL'}")
c3_ok = cur_d_div is not None and cur_d_div > 0.05 and cur_glsr is not None and cur_glsr > 1.05
log(f"  C3 Pos re-rate MỚI: → {'PASS' if c3_ok else 'FAIL'}")
log(f"  SCORE: {sum([c1,c2_ok,c3_ok])}/3  → {'TRIGGER' if all([c1,c2_ok,c3_ok]) else 'NO TRIGGER'}")

log(f"\n[W-3b DONE]")
