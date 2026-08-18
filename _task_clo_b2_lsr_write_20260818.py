"""_task_clo_b2_lsr_write_20260818.py
B2 combined: LSR check pre-Aug04 rows + fetch top/global LSR for Aug04-17 (fapi has both)
          + append 14 new DAILY rows + recompute derived + write (post-guard).
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
EXPORT  = ROOT / "data" / "export"
CASES   = ROOT / "docs" / "case_files"
XLSX    = CASES / "CASE_CLO.xlsx"

SYM    = "CLO"
TICKER = "CLOUSDT"
START  = "2026-08-04"
END    = "2026-08-17"

def safe_float(v):
    if v in (None,"","None"): return None
    try: return float(v)
    except: return None

def fetch_json(url, params=None, timeout=15):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

def ms_to_date(ms):
    return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# ── 1. Fetch top-trader position/account ratio (fapi) — CLO likely covered ──
print("="*70)
print("[Fetch top-trader LSR endpoints for CLOUSDT last 30d]")
print("="*70)

def fetch_lsr(endpoint):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{endpoint}",
                   {"symbol": TICKER, "period":"1d", "limit": 30})
    time.sleep(0.3)
    if not isinstance(d, list): return {}
    by_date = {}
    for it in d:
        ts = int(it.get("timestamp", 0))
        d_str = ms_to_date(ts)
        by_date[d_str] = it
    return by_date

lsr_pos = fetch_lsr("topLongShortPositionRatio")
lsr_acc = fetch_lsr("topLongShortAccountRatio")
lsr_glo = fetch_lsr("globalLongShortAccountRatio")

print(f"  topLongShortPositionRatio:  {len(lsr_pos)} days, sample last:")
if lsr_pos:
    last = sorted(lsr_pos.keys())[-1]
    print(f"    {last}: {lsr_pos[last]}")
print(f"  topLongShortAccountRatio:   {len(lsr_acc)} days, sample last:")
if lsr_acc:
    last = sorted(lsr_acc.keys())[-1]
    print(f"    {last}: {lsr_acc[last]}")
print(f"  globalLongShortAccountRatio: {len(lsr_glo)} days, sample last:")
if lsr_glo:
    last = sorted(lsr_glo.keys())[-1]
    print(f"    {last}: {lsr_glo[last]}")

# Build LSR by date from fapi
lsr_fapi = {}
all_dates = set(lsr_pos.keys()) | set(lsr_acc.keys()) | set(lsr_glo.keys())
for d in all_dates:
    p = lsr_pos.get(d, {})
    a = lsr_acc.get(d, {})
    g = lsr_glo.get(d, {})
    lsr_fapi[d] = {
        "lsr_pos_r": safe_float(p.get("longShortRatio")),  # top trader POSITION ratio
        "lsr_acc_r": safe_float(a.get("longShortRatio")),  # top trader ACCOUNT ratio
        "lsr_global_r": safe_float(g.get("longShortRatio")),  # global account ratio
        "src": "fapi_LSR_30d",
    }

# ── 2. Freshwatch check (optional) ──
print("\n" + "="*70)
print("[Freshwatch store check for CLOUSDT]")
print("="*70)
lsr_fw = {}
for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = safe_float(row.get("lsr_pos_r"))
            if d_str and pr:
                lsr_fw[d_str] = {
                    "lsr_pos_r": pr,
                    "lsr_acc_r": safe_float(row.get("lsr_acc_r")),
                    "lsr_global_r": safe_float(row.get("lsr_global_r")),
                    "taker_ratio": safe_float(row.get("taker_ratio")),
                    "src": "freshwatch_store",
                }
print(f"  freshwatch CLO rows: {len(lsr_fw)}, "
      f"range={min(lsr_fw)}→{max(lsr_fw)}" if lsr_fw else "  (none)")

# ── 3. Load existing CASE_CLO DAILY ──
print("\n" + "="*70)
print("[Load CASE_CLO DAILY current state]")
print("="*70)
wb = openpyxl.load_workbook(XLSX)
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
print(f"  cols: {len(row2)}, key: date={ci.get('date')} "
      f"lsr_pos_r={ci.get('lsr_pos_r')} div_avg3={ci.get('div_avg3')}")

# load all rows
data_by_date = {}
data_dates = []
last_row = 0
for r in range(3, ws.max_row+1):
    d = ws.cell(r, ci["date"]).value
    if not d: continue
    d_str = str(d)[:10]
    rd = {"__row": r, "date": d_str}
    for n, cix in ci.items():
        if n == "date": continue
        rd[n] = ws.cell(r, cix).value
    data_by_date[d_str] = rd
    data_dates.append(d_str)
    last_row = max(last_row, r)
data_dates.sort()
print(f"  existing rows: {len(data_dates)}, range={data_dates[0]}→{data_dates[-1]}, last_row={last_row}")

# LSR null check (existing rows)
n_null_pos = sum(1 for d in data_dates if safe_float(data_by_date[d].get("lsr_pos_r")) is None)
n_null_glo = sum(1 for d in data_dates if safe_float(data_by_date[d].get("lsr_global_r")) is None)
print(f"  existing LSR null: pos_r={n_null_pos}, global_r={n_null_glo}")

# ── 4. Build 14 NEW rows (Aug04-Aug17) — append to xlsx ──
print("\n" + "="*70)
print(f"[Build 14 new rows {START}→{END}]")
print("="*70)

# Load scratch CSVs
def load_csv(p):
    if not p.exists(): return []
    with open(p, encoding="utf-8") as f: return list(csv.DictReader(f))

perp = {r["date"]: r for r in load_csv(SCRATCH / "clo_perp_aug04_17_20260818.csv")}
fund_flat = load_csv(SCRATCH / "clo_funding_aug04_17_20260818.csv")
fund_by_d = {}
for f in fund_flat:
    fund_by_d.setdefault(f["date"], []).append(f)
oi_by_d = {r["date"]: r for r in load_csv(SCRATCH / "clo_oi_hist_20260818.csv")}

# Build dates Aug04-Aug17
from datetime import date as _date, timedelta
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
new_dates = []
cur = d0
while cur <= d1:
    new_dates.append(cur.isoformat()); cur += timedelta(days=1)

def build_row(d_str):
    p = perp.get(d_str)
    if not p: return None
    frs = [float(x["fundingRate"]) for x in fund_by_d.get(d_str, [])]
    fn = len(frs)
    f_avg = round(sum(frs)/fn, 8) if fn else None
    f_min = min(frs) if frs else None
    f_max = max(frs) if frs else None
    # funding_regime: WARM (>=5e-5 & <5e-4), PINNED ([4e-5,6e-5]), COLD (<4e-5)
    if f_avg is None: regime = None
    elif 4e-5 <= f_avg <= 6e-5: regime = "PINNED"
    elif f_avg > 6e-5:          regime = "WARM"
    else:                       regime = "COLD"
    oi = oi_by_d.get(d_str, {})
    oi_usd = safe_float(oi.get("oi_usd"))
    lsr = lsr_fw.get(d_str) or lsr_fapi.get(d_str) or {}
    row = {
        "date": d_str,
        "px_avg": round((float(p["high"])+float(p["low"])+float(p["close"]))/3, 8),
        "vol_perp_usd": safe_float(p["vol_quote_usd"]),
        "taker_buy_pct": safe_float(p["taker_buy_pct"]),
        "f_avg": f_avg, "f_min": f_min, "f_max": f_max, "f_n": fn,
        "funding_regime": regime,
        "oi_usd": oi_usd,
        "lsr_pos_r":    lsr.get("lsr_pos_r"),
        "lsr_acc_r":    lsr.get("lsr_acc_r"),
        "lsr_global_r": lsr.get("lsr_global_r"),
    }
    return row

new_rows = {}
for d_str in new_dates:
    r = build_row(d_str)
    if r: new_rows[d_str] = r

print(f"  new rows built: {len(new_rows)}")
for d in sorted(new_rows):
    r = new_rows[d]
    print(f"    {d}: c(px_avg)={r['px_avg']:.5f} vol={r['vol_perp_usd']:.0f} "
          f"f_avg={r['f_avg']} fn={r['f_n']} oi={r['oi_usd']:.0f} "
          f"pos_r={r['lsr_pos_r']} glo_r={r['lsr_global_r']}")

# ── 5. Merge into data_by_date (append) + compute ret_1d ────────────────
combined_dates = sorted(set(data_dates) | set(new_rows.keys()))
next_row = last_row
for d_str in sorted(new_rows.keys()):
    if d_str in data_by_date:
        # already exists; overwrite fields
        data_by_date[d_str].update(new_rows[d_str])
    else:
        next_row += 1
        rd = {"__row": next_row, **new_rows[d_str]}
        data_by_date[d_str] = rd

# compute ret_1d for new rows
for i, d_str in enumerate(combined_dates):
    if d_str not in new_rows or i == 0: continue
    prev = data_by_date[combined_dates[i-1]]
    cur  = data_by_date[d_str]
    p_prev = safe_float(prev.get("px_avg"))
    p_cur  = safe_float(cur.get("px_avg"))
    if p_prev and p_cur and p_prev != 0:
        cur["ret_1d"] = round((p_cur - p_prev)/p_prev * 100, 4)

# pin_streak
prev_pin = 0
for d_str in combined_dates:
    r = data_by_date[d_str]
    regime = r.get("funding_regime")
    if regime == "PINNED":
        prev_pin += 1
    else:
        prev_pin = 0
    r["pin_streak"] = prev_pin

# derived cols: div_raw, div_avg3, glsr_slope_5d, d_pos_3d, d_acc_3d
pos_arr = [safe_float(data_by_date[d].get("lsr_pos_r")) for d in combined_dates]
acc_arr = [safe_float(data_by_date[d].get("lsr_acc_r")) for d in combined_dates]
glo_arr = [safe_float(data_by_date[d].get("lsr_global_r")) for d in combined_dates]

for i, d_str in enumerate(combined_dates):
    r = data_by_date[d_str]
    p, a = pos_arr[i], acc_arr[i]
    r["div_raw"] = round(p/a, 4) if (p and a) else None
    if i >= 2:
        p3 = [v for v in pos_arr[i-2:i+1] if v is not None]
        a3 = [v for v in acc_arr[i-2:i+1] if v is not None]
        if len(p3)==3 and len(a3)==3:
            aa = sum(a3)/3
            r["div_avg3"] = round((sum(p3)/3)/aa, 4) if aa else None
    if i >= 5:
        g, gp = glo_arr[i], glo_arr[i-5]
        r["glsr_slope_5d"] = round(g/gp, 4) if (g and gp and gp > 0) else None
    if i >= 3:
        pp, pn = pos_arr[i-3], pos_arr[i]
        ap, an = acc_arr[i-3], acc_arr[i]
        r["d_pos_3d"] = round((pn-pp)/pp*100, 4) if (pn and pp) else None
        r["d_acc_3d"] = round((an-ap)/ap*100, 4) if (an and ap) else None

# oi_cycle_pos (30d rolling)
oi_arr = [safe_float(data_by_date[d].get("oi_usd")) for d in combined_dates]
for i, d_str in enumerate(combined_dates):
    if i < 29: continue
    w = [v for v in oi_arr[i-29:i+1] if v is not None]
    cur = oi_arr[i]
    if len(w) >= 10 and cur is not None:
        mn, mx = min(w), max(w)
        if mx > mn:
            data_by_date[d_str]["oi_cycle_pos"] = round((cur-mn)/(mx-mn), 4)

# oi_vs_med14 (14d rolling median)
for i, d_str in enumerate(combined_dates):
    if i < 13: continue
    w = sorted(v for v in oi_arr[i-13:i+1] if v is not None)
    if len(w) >= 8 and oi_arr[i]:
        med = w[len(w)//2]
        if med > 0:
            data_by_date[d_str]["oi_vs_med14"] = round(oi_arr[i]/med, 4)

# ── 6. GUARD before write ──
print("\n" + "="*70)
print("[GUARD before write]")
print("="*70)

# Sanity: all new rows have px_avg, f_avg, oi_usd, and (LSR either from fapi or fw)
n_missing = 0
for d in sorted(new_rows.keys()):
    r = data_by_date[d]
    for k in ["px_avg","vol_perp_usd","oi_usd","f_avg","lsr_pos_r","lsr_global_r"]:
        if r.get(k) in (None, ""):
            print(f"  ! {d} missing: {k}")
            n_missing += 1
if n_missing > 0:
    print(f"  {n_missing} missing values across new rows — proceed with warning")

# Verify pre-existing rows LSR still present (repair didn't nuke)
n_null_after = sum(1 for d in data_dates if safe_float(data_by_date[d].get("lsr_pos_r")) is None)
print(f"  existing rows lsr_pos_r null after processing: {n_null_after} (before: {n_null_pos})")
if n_null_after > n_null_pos:
    sys.exit("GUARD FAIL: pre-existing LSR nulled by processing")

# ── 7. WRITE cells ──
print("\n" + "="*70)
print("[WRITE cells post-guard]")
print("="*70)
write_count = 0
for d_str in sorted(data_by_date):
    r = data_by_date[d_str]
    row_num = r["__row"]
    # write date
    if ws.cell(row_num, ci["date"]).value != r["date"]:
        ws.cell(row_num, ci["date"]).value = r["date"]
        write_count += 1
    for k, val in r.items():
        if k in ("__row","date"): continue
        if k not in ci: continue
        cur = ws.cell(row_num, ci[k]).value
        if cur != val:
            ws.cell(row_num, ci[k]).value = val
            write_count += 1
print(f"  cell writes: {write_count}")

# save
wb.save(XLSX)
print(f"  SAVED: {XLSX}")

# Summary for report
print("\n=== NEW rows summary (Aug04-Aug17) ===")
print(f"{'date':<12} {'px':>8} {'ret%':>6} {'oi':>9} {'f_avg':>10} {'fn':>3} "
      f"{'reg':>6} {'pos_r':>6} {'acc_r':>6} {'glo':>6} {'div':>7} {'tk%':>6}")
for d in sorted(new_rows.keys()):
    r = data_by_date[d]
    print(f"{d:<12} {r.get('px_avg') or '':>8.5f} {r.get('ret_1d') or 0:>6.2f} "
          f"{r.get('oi_usd') or 0:>9.0f} {r.get('f_avg') or 0:>10.6f} {str(r.get('f_n')):>3} "
          f"{str(r.get('funding_regime')):>6} {r.get('lsr_pos_r') or 0:>6.3f} "
          f"{r.get('lsr_acc_r') or 0:>6.3f} {r.get('lsr_global_r') or 0:>6.3f} "
          f"{r.get('div_raw') or 0:>7.4f} {r.get('taker_buy_pct') or 0:>6.2f}")

print("\n[DONE B2+append+write]")
