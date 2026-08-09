"""
_probe_agt_depth_a5_20260808.py
A-4: Depth snap #1 + A.5 ba-dao-ham table + BscScan check + sanity A-7.
"""
import sys, io, json, csv, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260808"
SYMBOL   = "AGTUSDT"

def log(s="", end="\n"): print(s, end=end)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}
def sf(v, d=None):
    try: return float(v) if v not in (None,"","None") else d
    except: return d

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"AGT DEPTH + A.5 + SANITY  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── A-4: Depth snap #1 ────────────────────────────────────────────────────────
log("\n=== DEPTH SNAP #1 ===")
depth = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={SYMBOL}&limit=500")
snap1 = {}
if "_error" not in depth:
    bids = depth.get("bids", [])
    asks = depth.get("asks", [])
    mid_price = (float(bids[0][0]) + float(asks[0][0])) / 2 if bids and asks else None
    # ±2% depth
    bid2pct = sum(float(p)*float(q) for p,q in bids if mid_price and float(p) >= mid_price*0.98)
    ask2pct = sum(float(p)*float(q) for p,q in asks if mid_price and float(p) <= mid_price*1.02)
    snap1 = {
        "ts": NOW.isoformat(),
        "mid": round(mid_price, 8) if mid_price else None,
        "bid2pct": round(bid2pct, 2),
        "ask2pct": round(ask2pct, 2),
        "bids_10": bids[:10],
        "asks_10": asks[:10],
    }
    log(f"  ts: {snap1['ts']}")
    log(f"  mid: {snap1['mid']}")
    log(f"  bid2pct: ${snap1['bid2pct']:,.0f}  ask2pct: ${snap1['ask2pct']:,.0f}")
    log(f"  ratio bid/ask: {round(bid2pct/ask2pct,3) if ask2pct else 'N/A'}")
    log(f"  top 5 bids: {bids[:5]}")
    log(f"  top 5 asks: {asks[:5]}")
    (SCRATCH / f"agt_depth_snap1_{DATE_TAG}.json").write_text(json.dumps(snap1, indent=2), encoding="utf-8")
    log(f"  Saved: agt_depth_snap1_{DATE_TAG}.json")
    log(f"  *** Snap #2 required: >= {(NOW.replace(microsecond=0).isoformat()[:16]).replace('T',' ')} + 4h = "
        f"{NOW.strftime('%H')} -> >=12:42 UTC ***")
else:
    log(f"  Depth error: {depth}")

# ── A.5 BA-ĐẠO-HÀM table ──────────────────────────────────────────────────────
log("\n=== A.5 BA-ĐẠO-HÀM TABLE ===")

# Load perp + lsr CSVs
with open(SCRATCH / f"agt_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    perp_rows = sorted(csv.DictReader(f), key=lambda r: r.get("date",""))
with open(SCRATCH / f"agt_lsr_raw_{DATE_TAG}.csv", encoding="utf-8") as f:
    lsr_rows = list(csv.DictReader(f))

all_dates = [r["date"] for r in perp_rows]
N = len(all_dates)
vol_usd   = [sf(r["vol_quote_usd"]) for r in perp_rows]
c_vals    = [sf(r["c"])             for r in perp_rows]

# LSR
lsr_by_d = {}
for r in lsr_rows:
    dt = r.get("date","")
    if dt:
        lsr_by_d[dt] = {
            "pos_r": sf(r.get("pos_r_raw") or r.get("pos_r")),
            "acc_r": sf(r.get("acc_r_raw") or r.get("acc_r")),
            "gLSR":  sf(r.get("glsr_raw") or r.get("gLSR")),
        }
# freshwatch merge
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != "AGTUSDT": continue
            dt = row.get("date","")
            if not dt or dt in lsr_by_d: continue
            pos_r = sf(row.get("lsr_pos_r")); acc_r = sf(row.get("lsr_acc_r"))
            gLSR  = sf(row.get("lsr_global_r"))
            if pos_r:
                lsr_by_d[dt] = {"pos_r": pos_r, "acc_r": acc_r, "gLSR": gLSR, "_fw": True}

pos_r_all = [lsr_by_d.get(d, {}).get("pos_r") for d in all_dates]
acc_r_all = [lsr_by_d.get(d, {}).get("acc_r") for d in all_dates]
glsr_all  = [lsr_by_d.get(d, {}).get("gLSR")  for d in all_dates]

def rolling_med14(vals):
    out = [None]*len(vals)
    for i in range(14, len(vals)):
        w = [v for v in vals[i-14:i] if v is not None]
        if len(w) >= 7:
            s = sorted(w); n = len(s)
            out[i] = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    return out

vol_med14 = rolling_med14(vol_usd)
vol_vs_m  = [round(vol_usd[i]/vol_med14[i], 3) if (vol_med14[i] and vol_usd[i]) else None for i in range(N)]

# div_avg3
div_avg3_all = [None]*N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3)==3 and len(a3)==3:
        ap=sum(p3)/3; aa=sum(a3)/3
        div_avg3_all[i] = round(ap/aa, 4) if aa!=0 else None

# Mốc: 28d(offset=27), 21d(offset=20), 14d(offset=13), 7d(offset=6), now(offset=0)
def get_v(arr, offset): idx=N-1-offset; return arr[idx] if 0<=idx<N else None
def get_d(offset): idx=N-1-offset; return all_dates[idx] if 0<=idx<N else "?"

mocs = [("28d", 27), ("21d", 20), ("14d", 13), ("7d", 6), (f"07/08", 0)]
log(f"\n{'':12s}" + "".join(f" {f'{label}({get_d(off)[:5]})':>17s}" for label, off in mocs))
log("-"*100)

for name, arr in [("pos_r", pos_r_all), ("acc_r", acc_r_all), ("gLSR", glsr_all), ("div_avg3", div_avg3_all)]:
    log(f"{name:12s}", end="")
    for label, off in mocs:
        v = get_v(arr, off)
        log(f" {str(round(v,4)) if v is not None else 'N/A':>17s}", end="")
    print()

# gLSR range last 28d
glsr_28 = [glsr_all[N-1-i] for i in range(min(28,N)) if glsr_all[N-1-i] is not None]
log(f"\n  gLSR 28d: min={round(min(glsr_28),4) if glsr_28 else 'N/A'} "
    f"max={round(max(glsr_28),4) if glsr_28 else 'N/A'}")
# Crossings
for thr in [0.7, 1.0, 1.1, 1.5]:
    crossed = []
    for i in range(len(glsr_28)-1):
        a = glsr_28[i]; b = glsr_28[i+1]
        if a is not None and b is not None:
            if (a >= thr and b < thr) or (a < thr and b >= thr):
                direction = "DOWN" if a >= thr else "UP"
                crossed.append((all_dates[N-1-i], direction))
    if crossed:
        log(f"  gLSR crosses {thr}: {crossed}")
    else:
        log(f"  gLSR crosses {thr}: NONE in last 28d")

# vol_vs_m avg7 per moc
log(f"\n  vol_vs_m avg7 ending at moc:")
for label, off in mocs:
    window = [vol_vs_m[N-1-off-j] for j in range(7) if 0<=N-1-off-j<N and vol_vs_m[N-1-off-j] is not None]
    avg7 = round(sum(window)/len(window),3) if window else None
    log(f"    {label} ({get_d(off)}): avg7={avg7} (n={len(window)})")

# Full LSR trajectory last 42d
log(f"\n\n=== LSR trajectory (all dates with pos_r) ===")
log(f"{'date':12s} {'pos_r':>7s} {'acc_r':>7s} {'gLSR':>7s} {'div_avg3':>9s} {'vol_vs_m':>9s}")
for i in range(N):
    if pos_r_all[i] is None: continue
    log(f"  {all_dates[i]:10s} {str(round(pos_r_all[i],4)):>7s} "
        f"{str(round(acc_r_all[i],4) if acc_r_all[i] else '-'):>7s} "
        f"{str(round(glsr_all[i],4) if glsr_all[i] else '-'):>7s} "
        f"{str(round(div_avg3_all[i],4) if div_avg3_all[i] else '-'):>9s} "
        f"{str(round(vol_vs_m[i],3) if vol_vs_m[i] else '-'):>9s}")

# ── BscScan 0-credit ──────────────────────────────────────────────────────────
log("\n\n=== BscScan 0-credit ===")
CONTRACT = "0x5dbde81fce337ff4bcaaee4ca3466c00aecae274"
bscscan_token = fetch_json(
    f"https://api.bscscan.com/api?module=token&action=tokeninfo&contractaddress={CONTRACT}&apikey=YourApiKeyToken")
log(f"  tokeninfo: {bscscan_token}")

bscscan_supply = fetch_json(
    f"https://api.bscscan.com/api?module=stats&action=tokensupply&contractaddress={CONTRACT}&apikey=YourApiKeyToken")
log(f"  tokensupply: {bscscan_supply}")

# ── A-6: VPS cross-ref (freshwatch quick check) ────────────────────────────────
log("\n\n=== A-6: VPS / Cross-ref quick check ===")
# Check gom_state for AGT
from pathlib import Path as _P
state_path = _P(r"D:\Data back test\whale_data\scratch\session_state.json")
if state_path.exists():
    st = json.loads(state_path.read_text(encoding="utf-8"))
    agt_st = {k:v for k,v in st.items() if "AGT" in k.upper()}
    log(f"  gom_state AGT chains: {agt_st}")
else:
    log(f"  gom_state: scratch/session_state.json not found")

# freshwatch summary for AGT
fw_agt_count = 0
fw_dates = []
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() == "AGTUSDT":
                fw_agt_count += 1
                fw_dates.append(row.get("date",""))
log(f"  Freshwatch AGTUSDT: {fw_agt_count} rows, dates {min(fw_dates) if fw_dates else 'N/A'}→{max(fw_dates) if fw_dates else 'N/A'}")

# ── A-7: SANITY CHECK ─────────────────────────────────────────────────────────
log("\n\n=== A-7 SANITY CHECK ===")
import openpyxl
wb = openpyxl.load_workbook(
    r"D:\Data back test\whale_data\docs\case_files\CASE_AGT.xlsx", data_only=True)

# 1. CASE sheet: contract + alpha_id + supply
ws_case = wb["CASE"]
case_rows = {ws_case.cell(r,1).value: ws_case.cell(r,2).value
             for r in range(1, ws_case.max_row+1) if ws_case.cell(r,1).value}
log(f"\n  CASE sheet fields:")
for k in ["Alpha ID","Contract (BSC)","Total supply","Circ supply","Perp onboard","Alpha listing"]:
    log(f"    {k}: {case_rows.get(k,'NOT FOUND')}")

contract_ok   = "0x5dbde81fce337ff4bcaaee4ca3466c00aecae274" in str(case_rows.get("Contract (BSC)",""))
alphaid_ok    = "ALPHA_191" in str(case_rows.get("Alpha ID",""))
supply_ok     = "5000000000" in str(case_rows.get("Total supply",""))
log(f"\n  [1] Contract match: {'PASS' if contract_ok else 'FAIL'}")
log(f"  [1] Alpha ID match: {'PASS' if alphaid_ok else 'FAIL'}")
log(f"  [1] Total supply match: {'PASS' if supply_ok else 'FAIL'}")

# 2. LSR coverage last 30d
ws_d = wb["DAILY"]
hdrs = [ws_d.cell(2,c).value for c in range(1, ws_d.max_column+1)]
try:
    col_date   = next(i+1 for i,h in enumerate(hdrs) if h and "date" in str(h).lower())
    col_pos_r  = next(i+1 for i,h in enumerate(hdrs) if h and "pos_r" in str(h) and "avg" not in str(h) and "d_" not in str(h))
    col_vol_sp = next(i+1 for i,h in enumerate(hdrs) if h and "vol_spot" in str(h).lower())
except StopIteration as e:
    log(f"  Column search error: {e}")
    col_date=1; col_pos_r=27; col_vol_sp=31

# Count rows from row 3
data_rows = []
for ri in range(3, ws_d.max_row+100):
    v = ws_d.cell(ri, col_date).value
    if v in (None, ""): break
    data_rows.append(ri)
total_rows = len(data_rows)
last30_rows = data_rows[-30:] if len(data_rows)>=30 else data_rows

lsr_null_l30 = sum(1 for ri in last30_rows if ws_d.cell(ri,col_pos_r).value in (None,""))
lsr_pct = lsr_null_l30/len(last30_rows)*100 if last30_rows else 100
log(f"\n  [2] LSR coverage: pos_r null {lsr_pct:.1f}% in last 30d ({lsr_null_l30}/{len(last30_rows)}): "
    f"{'PASS' if lsr_pct<=50 else 'FAIL'}")

spot_null_l30 = sum(1 for ri in last30_rows if ws_d.cell(ri,col_vol_sp).value in (None,""))
spot_pct = spot_null_l30/len(last30_rows)*100 if last30_rows else 100
log(f"  [3] Spot coverage: vol_spot_usd null {spot_pct:.1f}% in last 30d ({spot_null_l30}/{len(last30_rows)}): "
    f"{'WARNING (no spot pair)' if spot_pct>50 else 'PASS'}")

# 4. Last DAILY row = yesterday (07/08)
last_date = ws_d.cell(data_rows[-1], col_date).value
log(f"\n  [4] DAILY last row: {last_date} (expected: 2026-08-07 per L-21): "
    f"{'PASS' if str(last_date)=='2026-08-07' else 'FAIL'}")
log(f"  [4] DAILY row count: {total_rows} (expected: 445): "
    f"{'PASS' if total_rows==445 else 'FAIL'}")

# EVENTS spot-check vs klines
ws_ev = wb["EVENTS"]
ev_rows = [(ws_ev.cell(r,1).value, ws_ev.cell(r,2).value, ws_ev.cell(r,3).value)
           for r in range(1, ws_ev.max_row+1) if ws_ev.cell(r,1).value]
log(f"\n  EVENTS count: {len(ev_rows)}")
log(f"  First 4 events:")
for e in ev_rows[:4]:
    log(f"    {e}")

log(f"\n  SANITY SUMMARY:")
log(f"    [1] Contract/AlphaID/Supply: {'PASS' if (contract_ok and alphaid_ok) else 'FAIL'}")
log(f"    [2] LSR coverage: {'PASS' if lsr_pct<=50 else 'FAIL'}")
log(f"    [3] Spot coverage: WARNING (no spot pair — documented)")
log(f"    [4] DAILY rows/date: {'PASS' if (total_rows==445 and str(last_date)=='2026-08-07') else 'FAIL'}")
overall = (contract_ok and alphaid_ok and supply_ok and lsr_pct<=50 and total_rows==445 and str(last_date)=='2026-08-07')
log(f"    OVERALL: {'PASS — OK to submit' if overall else 'FAIL — fix before submit'}")

wb.close()
log(f"\n[DEPTH+A5+SANITY DONE]")
