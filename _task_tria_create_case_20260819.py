"""_task_tria_create_case_20260819.py
Create docs/case_files/CASE_TRIA.xlsx từ template CASE_GUA.xlsx (v2 schema 50 cols).
Populate: CASE meta + DAILY (Jul20-Aug18, 30 rows) + EVENTS + UNLOCK skeleton.
No verdict. Follows §B0 backup convention: save fresh, no overwrite risk.
"""
import sys, io, shutil, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
import openpyxl

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
EXPORT   = ROOT / "data" / "export"
CASES    = ROOT / "docs" / "case_files"

TEMPLATE = CASES / "CASE_GUA.xlsx"
TARGET   = CASES / "CASE_TRIA.xlsx"

SYM      = "TRIA"
TICKER   = "TRIAUSDT"
ALPHA_ID = "ALPHA_669"
START    = "2026-07-20"
END      = "2026-08-18"

def fetch_json(url, params=None, timeout=20):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

def to_ms(d): return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
def safe_float(v):
    if v in (None,"","None"): return None
    try: return float(v)
    except: return None

# ── 1. Copy template ─────────────────────────────────────────────────────
assert not TARGET.exists(), f"CASE_TRIA.xlsx đã tồn tại — abort"
assert TEMPLATE.exists(), f"template missing: {TEMPLATE}"
shutil.copy2(TEMPLATE, TARGET)
print(f"COPIED template: {TEMPLATE.name} → {TARGET.name}")

wb = openpyxl.load_workbook(TARGET)
print(f"Sheets: {wb.sheetnames}")

# ── 2. Clear DAILY data rows (row 3+) — keep row 1 section titles + row 2 field names ─
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
max_col = len(row2)

# Delete all data rows (row 3+)
old_last = ws.max_row
if old_last >= 3:
    ws.delete_rows(3, old_last - 2)
print(f"Cleared DAILY data rows 3-{old_last}")

# ── 3. Fetch TRIA data (perp/funding/OI/LSR) ─────────────────────────────
print("\n" + "="*60)
print("FETCH DATA")
print("="*60)

s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1

# perp klines
d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval": "1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 40})
time.sleep(0.3)
perp = {}
for k in d if isinstance(d, list) else []:
    d_str = ms_to_date(int(k[0]))
    if d_str < START or d_str > END: continue
    vol_q = float(k[7]); taker_q = float(k[10])
    perp[d_str] = {
        "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
        "vol_quote_usd": round(vol_q, 2),
        "taker_buy_pct": round(taker_q/vol_q*100, 4) if vol_q > 0 else None,
    }
print(f"  perp: {len(perp)} days")

# funding (paginate)
fund_all = []; cur = s_ms
while cur <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": TICKER, "startTime": cur, "endTime": e_ms, "limit": 1000})
    time.sleep(0.3)
    if not isinstance(d, list) or not d: break
    fund_all.extend(d)
    last = int(d[-1]["fundingTime"])
    if last <= cur or last >= e_ms: break
    cur = last + 1
fund_by_d = {}
for it in fund_all:
    ts = int(it["fundingTime"]); d_str = ms_to_date(ts)
    if START <= d_str <= END:
        fund_by_d.setdefault(d_str, []).append(float(it["fundingRate"]))
print(f"  funding: {len(fund_by_d)} days, {sum(len(v) for v in fund_by_d.values())} entries")

# OI
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period":"1d", "limit": 30})
time.sleep(0.3)
oi_by_d = {}
seen = set()
for it in d if isinstance(d, list) else []:
    ts = int(it["timestamp"]); d_str = ms_to_date(ts)
    key = (d_str, str(ts))
    if key in seen: continue
    seen.add(key)
    oi_by_d[d_str] = {
        "oi_usd": float(it["sumOpenInterestValue"] or 0),
        "oi_token": float(it["sumOpenInterest"] or 0),
    }
print(f"  OI: {len(oi_by_d)} days")

# LSR from freshwatch data/export
lsr_fw = {}
for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = safe_float(row.get("lsr_pos_r"))
            if not d_str or not pr: continue
            lsr_fw[d_str] = {
                "pos_r": pr, "acc_r": safe_float(row.get("lsr_acc_r")),
                "gLSR":  safe_float(row.get("lsr_global_r")),
                "taker_lsr": safe_float(row.get("taker_ratio")),
                "src": "freshwatch_store",
            }
print(f"  freshwatch LSR: {len(lsr_fw)} days")

# LSR fapi fallback (for Aug18 which freshwatch doesn't have)
def fetch_lsr_ep(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol": TICKER, "period":"1d", "limit": 30})
    time.sleep(0.3)
    by_d = {}
    for it in d if isinstance(d, list) else []:
        ts = int(it["timestamp"]); by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d
lsr_top_pos = fetch_lsr_ep("topLongShortPositionRatio")
lsr_top_acc = fetch_lsr_ep("topLongShortAccountRatio")
lsr_glo     = fetch_lsr_ep("globalLongShortAccountRatio")

# ── 4. Build 30 rows ─────────────────────────────────────────────────────
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
days = []
cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)

rows_data = []
prev_c = None
for d_str in days:
    p = perp.get(d_str)
    if not p: continue
    frs = fund_by_d.get(d_str, [])
    fn = len(frs)
    f_avg = round(sum(frs)/fn, 8) if fn else None
    f_min = min(frs) if frs else None
    f_max = max(frs) if frs else None
    oi = oi_by_d.get(d_str, {})
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r, acc_r, gl, tk_lsr, src = fw["pos_r"], fw["acc_r"], fw["gLSR"], fw["taker_lsr"], fw["src"]
    else:
        pos_r = lsr_top_pos.get(d_str); acc_r = lsr_top_acc.get(d_str); gl = lsr_glo.get(d_str)
        tk_lsr = None; src = "fapi_LSR_30d"

    c = p["c"]
    ret_1d = round((c - prev_c)/prev_c*100, 4) if prev_c else None
    prev_c = c

    px_avg = round((p["h"]+p["l"]+c)/3, 8)
    row = {
        "date": d_str, "px_avg (H+L+C)/3": px_avg,
        "o": p["o"], "h": p["h"], "l": p["l"], "c": c,
        "vol_perp_usd": p["vol_quote_usd"],
        "taker_buy_pct (k[10]/k[7])": p["taker_buy_pct"],
        "f_avg": f_avg, "f_min": f_min, "f_max": f_max, "fn (4h=6/day)": fn,
        "oi_usd": oi.get("oi_usd"), "oi_token": oi.get("oi_token"),
        "data_ok (fn>=6)": (fn >= 6), "low_conf (fn<6)": (fn < 6),
        "ret_1d (close-to-close)": ret_1d,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl, "taker_lsr": tk_lsr,
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr":  src,
    }
    rows_data.append(row)

print(f"\n  built {len(rows_data)} rows for DAILY")

# derived cols
pos_arr = [r["pos_r"] for r in rows_data]
acc_arr = [r["acc_r"] for r in rows_data]
gl_arr  = [r["gLSR"]  for r in rows_data]

for i, r in enumerate(rows_data):
    p, a, g = pos_arr[i], acc_arr[i], gl_arr[i]
    r["div_raw (pos_r/acc_r)"] = round(p/a, 4) if (p and a) else None
    if i >= 2:
        p3 = [v for v in pos_arr[i-2:i+1] if v]
        a3 = [v for v in acc_arr[i-2:i+1] if v]
        if len(p3)==3 and len(a3)==3:
            aa = sum(a3)/3
            r["div_avg3 (avg3p/avg3a)"] = round((sum(p3)/3)/aa, 4) if aa else None
    if i >= 5:
        gp = gl_arr[i-5]
        r["glsr_slope_5d (ratio t/t-5)"] = round(g/gp, 4) if (g and gp and gp>0) else None
    if i >= 3:
        pp, ap = pos_arr[i-3], acc_arr[i-3]
        r["d_pos_3d (%chg)"] = round((p-pp)/pp*100,4) if (p and pp) else None
        r["d_acc_3d (%chg)"] = round((a-ap)/ap*100,4) if (a and ap) else None

# ── 5. Write DAILY ───────────────────────────────────────────────────────
for ridx, r in enumerate(rows_data, start=3):
    for name, ciix in ci.items():
        v = r.get(name)
        if v is not None:
            ws.cell(ridx, ciix).value = v
print(f"  Wrote {len(rows_data)} rows to DAILY (row 3-{2+len(rows_data)})")

# ── 6. Populate CASE sheet ───────────────────────────────────────────────
ws_case = wb["CASE"]
# clear all rows
for r in range(1, ws_case.max_row+1):
    for c in range(1, 10):
        ws_case.cell(r, c).value = None

case_meta = [
    ["CASE FILE — TRIA (Tria)", None],
    ["Nguồn: probe _tria_probe_20260819 · verdict chỉ operator ghi · số kèm nguồn · PENDING không đoán", None],
    [None, None],
    ["Status", "TRACKING (cold-start Aug19 — un-hedge readout Aug18/19 pending operator verdict)"],
    ["Loại", "Alpha-only + Perp · hedge episode #1 ongoing (start 2026-08-04)"],
    ["Alpha ID", "ALPHA_669 · symbol=TRIA · name=Tria · chain=BSC · fullyDelisted=False"],
    ["Perp fapi", "TRIAUSDT TRADING · onboardDate=2026-02-06"],
    ["Spot api/v3", "KHÔNG có (Alpha-only, taker_spot=ABSTAIN-STRUCTURAL L-51 draft)"],
    ["Ngày phát hiện", "2026-08-19 (probe session ANALYSIS approved)"],
    ["T0 candidate", "2026-08-04 (hedge_start_px=$0.008398, episode #1 start)"],
    ["Intraday event", "2026-08-19 03:12 UTC: px +24.8%, OI +125%, funding UN-PIN + FLIP ÂM (-10.5bps)"],
    [None, None],
    ["A. EPISODE HEDGE", None],
    ["Episode #1 start", "2026-08-04 (div_avg3 vào 0.469, đi qua threshold ≤ 0.5)"],
    ["struct_n Aug18", "15 days"],
    ["min div_avg3", "0.2922 @ 2026-08-14"],
    ["Div nới bắt đầu", "2026-08-15 (0.292 → 0.309, +0.017)"],
    ["px_dist% Aug18", "+18.3% (0.008398 → 0.00975)"],
    ["px_dist% intraday Aug19", "+22.75% (0.008398 → 0.010304 @ 03:12 UTC)"],
    [None, None],
    ["B. FUNDING PROFILE", None],
    ["Pin streak Jul20-Aug18", "30 days (f_avg = +0.00005 mọi ngày, band [4e-5, 6e-5])"],
    ["Un-pin event", "2026-08-19 00:00 UTC: fr = -0.00010496 (FLIP ÂM đứt chuỗi 30-ngày)"],
    ["Regime hậu-un-pin", "PENDING operator đọc chuỗi kế"],
    [None, None],
    ["C. UN-HEDGE ANATOMY", None],
    ["pos_r đáy → Aug18", "1.223 (Aug11) → 1.395 (Aug18) = +14% slow-drip · CHƯA 🔵15%/2d threshold"],
    ["OI cover Aug17→Aug18", "$3.27M → $3.16M = -3.3% (nhẹ · tank shorts còn nguyên)"],
    ["Intraday OI Aug19", "$3.16M → $7.12M = +125% (LONG BUILD MASSIVE, KHÔNG phải cover)"],
    ["Thứ tự crowd/pos", "CROWD dẫn (gLSR +27% Aug08-14) → POS theo (pos_r +14% Aug11-18) = CROWD-CHASE"],
    [None, None],
    ["D. CHÂN HÀNG", None],
    ["Perp vol Aug18", "$25,063,774 (~10× nền T7)"],
    ["Alpha vol Aug18", "$770,626 (~85× nền T7, nền ~$7-10K/day)"],
    ["Perp/Alpha ratio", "32:1 → cú pump chạy chính trên PERP"],
    ["Băng-thông chân Alpha", "hẹp — vol ≥$100K/day có thể móc Alpha rất nhanh"],
    [None, None],
    ["E. MACHINE TAGS (Aug17-18)", None],
    ["watchlist_log Aug17", "List A + B · pos_trend=BẬT · oi_trend=PHẲNG · struct_n=14"],
    ["phase_tag Aug18", "CROWD-CHASE · stage=S2-EARLY (from phase_tag.log, ⚠ CSV chưa có)"],
    [None, None],
    ["F. FALSIFIERS / TRIGGERS TO WATCH", None],
    ["Un-hedge THẬT", "pos_r +≥15%/2d + OI ↓ + div break 0.5 (chưa có Aug18)"],
    ["Distribution", "fapi topPos Aug19=1.0613 (vs 1.395 Aug18) — nếu tin cậy: top BÁN VÀO pump"],
    ["Continuation bull", "OI tiếp leo + funding âm tiếp + Alpha vol tiếp leo"],
    [None, None],
    ["G. ON-CHAIN (chưa)", None],
    ["Contract", "BSC (cần lấy từ Alpha meta full — pending)"],
    ["Whale/holder", "PENDING OPERATOR (Nansen LOCKED)"],
    [None, None],
    ["H. NGUỒN + REPORT", None],
    ["Probe", "_probe_tria_20260819.py"],
    ["Report", "docs/reports/_tria_probe_20260819.md"],
    ["Data provenance", "fapi/v1 (perp/funding/OI/LSR) + data/export/freshwatch_daily (81 rows May26-Aug17) + bapi/defi/v1 (Alpha) + VPS watchlist_log_2026-08.csv"],
]
for r_idx, (a, b) in enumerate(case_meta, start=1):
    if a is not None: ws_case.cell(r_idx, 1).value = a
    if b is not None: ws_case.cell(r_idx, 2).value = b
print(f"  CASE meta: {len(case_meta)} rows")

# ── 7. EVENTS ────────────────────────────────────────────────────────────
ws_ev = wb["EVENTS"]
# clear all rows
for r in range(1, ws_ev.max_row+1):
    for c in range(1, 8):
        ws_ev.cell(r, c).value = None

ev_headers = ["date", "type", "description", "ref", "resolved"]
for c, h in enumerate(ev_headers, start=1):
    ws_ev.cell(1, c).value = h

events = [
    ["2026-02-06", "LISTING_PERP", "TRIAUSDT onboard fapi (perp)", "fapi exchangeInfo", "N/A"],
    ["2026-08-04", "HEDGE_EPISODE_START", "Episode #1 start (div_avg3 ≤ 0.5), hedge_start_px=$0.008398, struct_n growing", "probe watchlist v1.3", "N/A"],
    ["2026-08-08", "GLSR_CROWD_START", "gLSR bắt đầu leo mạnh (3.686 → 4.179 = +13.4%)", "freshwatch LSR", "N/A"],
    ["2026-08-11", "POS_R_TROUGH", "pos_r đáy 1.223, bắt đầu bật (Aug12 +7.4%)", "freshwatch LSR", "N/A"],
    ["2026-08-14", "DIV_AVG3_MIN", "min div_avg3 = 0.2922, gLSR peak 4.662 + acc_r 5.017 (crowd/shorts đỉnh)", "freshwatch LSR", "N/A"],
    ["2026-08-15", "DIV_NỚI_START", "div_avg3 bắt đầu nới từ min (0.292 → 0.309), un-hedge sơ khai", "freshwatch LSR", "N/A"],
    ["2026-08-18", "PUMP_D1", "Price +17.94% (0.00826 → 0.00975), vol $25M (~10× nền), OI phẳng $3.16M · Alpha vol $770K (85× nền)", "fapi klines + bapi Alpha", "N/A"],
    ["2026-08-19", "INTRADAY_LONG_BUILD", "03:12 UTC: px +24.8% (24h), OI +125% (3.16M→7.12M USD), vol $51M · UN-PIN + FLIP ÂM (fr = -10.5bps at 00:00 UTC) đứt chuỗi pin 30-ngày", "fapi ticker+OI+funding intraday", "unresolved"],
]
for r, ev in enumerate(events, start=2):
    for c, val in enumerate(ev, start=1):
        ws_ev.cell(r, c).value = val
print(f"  EVENTS: {len(events)} rows")

# ── 8. UNLOCK skeleton ───────────────────────────────────────────────────
ws_ul = wb["UNLOCK"]
for r in range(1, ws_ul.max_row+1):
    for c in range(1, 8):
        ws_ul.cell(r, c).value = None
ws_ul.cell(1,1).value = "date"
ws_ul.cell(1,2).value = "event_type"
ws_ul.cell(1,3).value = "amount_tokens"
ws_ul.cell(1,4).value = "notes"
ws_ul.cell(1,5).value = "source"
ws_ul.cell(2,1).value = "2026-08-19"
ws_ul.cell(2,2).value = "DATA-GAP"
ws_ul.cell(2,4).value = "[DATA-GAP] chưa xác định: total supply · circ supply · unlock schedule cho TRIA/Tria. Alpha BSC contract cần lấy từ full metadata. Operator: check BscScan + tracker."
ws_ul.cell(2,5).value = "task create 19/08"

# ── 9. Clear TRIGGERS / OUTCOME / MM_PROFILE (leave headers only if any) ─
for sname in ["TRIGGERS", "OUTCOME", "MM_PROFILE"]:
    if sname not in wb.sheetnames: continue
    wsx = wb[sname]
    for r in range(1, wsx.max_row+1):
        for c in range(1, 10):
            wsx.cell(r, c).value = None
    wsx.cell(1,1).value = f"{sname} (TRIA) — PENDING operator to define"
    print(f"  {sname}: cleared, placeholder")

# ── 10. Save ─────────────────────────────────────────────────────────────
wb.save(TARGET)
print(f"\nSAVED: {TARGET} ({TARGET.stat().st_size} B)")

# ── 11. Update CASE_INDEX.xlsx (add TRIA row) ───────────────────────────
INDEX = CASES / "CASE_INDEX.xlsx"
wb_idx = openpyxl.load_workbook(INDEX)
ws_idx = wb_idx["INDEX"]
# find headers row (probe found row 4)
header_row = None
token_col = state_col = None
for r in range(1, 6):
    for c in range(1, 20):
        v = ws_idx.cell(r, c).value
        if v and str(v).strip().lower() in ("token","symbol"):
            header_row = r; token_col = c
        if v and str(v).strip().lower() in ("state","status","trạng thái"):
            state_col = c
print(f"\nCASE_INDEX: header row={header_row}, token col={token_col}, state col={state_col}")

# check if TRIA already in index
existing = []
for r in range(header_row+1, ws_idx.max_row+1):
    t = ws_idx.cell(r, token_col).value
    if t: existing.append((r, str(t).strip().upper()))
print(f"  existing tokens: {[t for _,t in existing]}")

if "TRIA" not in [t for _,t in existing]:
    next_r = ws_idx.max_row + 1
    ws_idx.cell(next_r, token_col).value = "TRIA"
    if state_col:
        ws_idx.cell(next_r, state_col).value = "TRACKING (cold-start Aug19)"
    print(f"  ADDED TRIA at row {next_r}")
    wb_idx.save(INDEX)
else:
    print(f"  TRIA already exists in CASE_INDEX")

print("\n[DONE CASE_TRIA.xlsx created]")
