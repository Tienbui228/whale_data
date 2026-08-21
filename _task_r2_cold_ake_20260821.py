"""_task_r2_cold_ake_20260821.py — COLD_START CASE_AKE.xlsx pack C-0→C-8.
DAILY 2026-05-01 → 2026-08-20 · pre-2026-06-27 OI/LSR = N/A-RETENTION.
Template: CASE_HEMI.xlsx (v2 schema no cols 51-52 — cols 51-52 append separate task R4).
Actually use CASE_PUMPBTC (v2.1 with cols 51-52) as template for consistency going forward.
"""
import sys, io, pickle, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date as _date, timedelta
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES = ROOT / "docs" / "case_files"

TEMPLATE = CASES / "CASE_PUMPBTC.xlsx"  # v2.1 schema (has cols 51-52)
TARGET = CASES / "CASE_AKE.xlsx"

# Guard: no clobber
assert not TARGET.exists(), "CASE_AKE.xlsx already exists — abort"
assert TEMPLATE.exists()
shutil.copy2(TEMPLATE, TARGET)
print(f"COPIED template: {TEMPLATE.name} → {TARGET.name}")

with open(SCRATCH / "r_nhip1_fetch_20260821.pkl", "rb") as f:
    ALL = pickle.load(f)
d = ALL["AKE"]

def safe_float(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None

wb = openpyxl.load_workbook(TARGET)
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
print(f"DAILY cols: {len(row2)}")

# Clear existing data rows
if ws.max_row >= 3:
    ws.delete_rows(3, ws.max_row - 2)

# Build all dates 2026-05-01 → 2026-08-20
d0 = _date(2026,5,1); d1 = _date(2026,8,20)
days = []
cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)

CUTOFF_LSR = "2026-06-27"  # OI/LSR available từ 2026-06-27

def col(name):
    return ci.get(name)

prev_c = None
for i, d_str in enumerate(days):
    r = i + 3
    ws.cell(r, col("date")).value = d_str
    klines = d["klines"].get(d_str)
    if klines:
        ws.cell(r, col("o")).value = klines["o"]
        ws.cell(r, col("h")).value = klines["h"]
        ws.cell(r, col("l")).value = klines["l"]
        ws.cell(r, col("c")).value = klines["c"]
        ws.cell(r, col("px_avg (H+L+C)/3")).value = round((klines["h"]+klines["l"]+klines["c"])/3, 8)
        ws.cell(r, col("vol_perp_usd")).value = klines["vol_quote_usd"]
        tk_c = col("taker_buy_pct (k[10]/k[7])")
        if tk_c: ws.cell(r, tk_c).value = klines["taker_buy_pct"]
        c = klines["c"]
        if prev_c:
            rc = col("ret_1d (close-to-close)")
            if rc: ws.cell(r, rc).value = round((c-prev_c)/prev_c*100, 4)
        prev_c = c
    frs = d["fund_by_d"].get(d_str, [])
    if frs:
        ws.cell(r, col("f_avg")).value = round(sum(frs)/len(frs), 8)
        ws.cell(r, col("f_min")).value = min(frs)
        ws.cell(r, col("f_max")).value = max(frs)
        ws.cell(r, col("fn (4h=6/day)")).value = len(frs)
        ws.cell(r, col("data_ok (fn>=6)")).value = len(frs) >= 6
        ws.cell(r, col("low_conf (fn<6)")).value = len(frs) < 6
    # OI
    oi_c = col("oi_usd"); oi_t_c = col("oi_token")
    oi_data = d["oi"].get(d_str)
    if oi_data:
        ws.cell(r, oi_c).value = oi_data["oi_usd"]
        if oi_t_c: ws.cell(r, oi_t_c).value = oi_data["oi_token"]
    else:
        # N/A-RETENTION for pre-cutoff and pre-fapi-window
        ws.cell(r, oi_c).value = "N/A-RETENTION" if d_str < CUTOFF_LSR else None
    # LSR
    lsr = d["lsr"].get(d_str)
    pos_c = col("pos_r"); acc_c = col("acc_r"); gl_c = col("gLSR"); tk_c2 = col("taker_lsr")
    src_c = col("data_source_lsr")
    if lsr:
        ws.cell(r, pos_c).value = lsr.get("pos_r")
        ws.cell(r, acc_c).value = lsr.get("acc_r")
        ws.cell(r, gl_c).value = lsr.get("gLSR")
        if tk_c2: ws.cell(r, tk_c2).value = lsr.get("taker_lsr")
        if src_c: ws.cell(r, src_c).value = lsr.get("src", "")
    else:
        if d_str < CUTOFF_LSR:
            ws.cell(r, pos_c).value = "N/A-RETENTION"
            ws.cell(r, acc_c).value = "N/A-RETENTION"
            ws.cell(r, gl_c).value = "N/A-RETENTION"
    # Structural tags (Alpha-only universe likely — verify later, tag ABSTAIN for now)
    vs_c = col("vol_spot_usd"); tk_sp_c = col("taker_spot_pct")
    ta_c = col("taker_alpha"); va_c = col("vol_alpha")
    if vs_c: ws.cell(r, vs_c).value = "N/A-STRUCTURAL"
    if tk_sp_c: ws.cell(r, tk_sp_c).value = "ABSTAIN-STRUCTURAL"
    if ta_c: ws.cell(r, ta_c).value = "ABSTAIN-STRUCTURAL"
    # vol_alpha + spot_ext_venue: CHƯA-TRA (chờ nhịp 2)
    if va_c: ws.cell(r, va_c).value = "CHƯA-TRA"
    ve_c = col("vol_spot_ext_usd"); vv_c = col("spot_ext_venue")
    if ve_c: ws.cell(r, ve_c).value = "CHƯA-TRA"
    if vv_c: ws.cell(r, vv_c).value = "CHƯA-TRA"
    # data_source_perp
    dsp_c = col("data_source_perp")
    if dsp_c and klines: ws.cell(r, dsp_c).value = "fapi_klines_1d"

print(f"Wrote {len(days)} DAILY rows (row 3-{len(days)+2})")

# CASE meta (pack C-0→C-8 outline)
ws_case = wb["CASE"]
for r in range(1, ws_case.max_row+1):
    for c in range(1, 10):
        ws_case.cell(r, c).value = None

meta = [
    ["CASE FILE — AKE", None],
    ["Cold-start 21/08/2026 · nguồn probe/task R2 nhịp 1 · verdict operator ký", None],
    [None, None],
    ["Status", "COLD_START — DAILY populated May01-Aug20, contract UNVERIFIED (nhịp 2 pending)"],
    ["Loại", "PENDING (chờ ANALYSIS đọc)"],
    ["Perp fapi", "AKEUSDT TRADING · onboardDate=2025-09-26"],
    ["Ngày phát hiện", "2026-08-21 (R2 cold-start)"],
    ["contract_canonical", "[UNVERIFIED — chờ operator paste nhịp 2 R0]"],
    ["Alpha ID (⚠ symbol-string, chưa verify)", "[CHƯA-TRA — nhịp 2]"],
    ["Venue spot-ext (col 51-52)", "[CHƯA-TRA — nhịp 2 R5]"],
    [None, None],
    ["LAYER COVERAGE (R7)", None],
    ["first_nn LSR", "2026-06-27 (freshwatch store)"],
    ["first_nn OI", "2026-07-22 (fapi 30d limit, tính từ run 21/08)"],
    ["N/A-RETENTION dates (LSR/OI pre-2026-06-27)", "2026-05-01 → 2026-06-26 (57 days) — không tự collect thêm"],
    ["N/A-GAP dates (freshwatch gap 24-26/07)", "2026-07-24, 07-25, 07-26 (họ TUT + BTW)"],
    [None, None],
    ["CORRECTIONS (R8)", None],
    ["Gap 24-26/07 nguồn store", "3 ngày freshwatch drop toàn universe — không sửa lịch sử"],
    ["OI pre-Jul22", "N/A-RETENTION (fapi 30d limit, chỉ trả 29 rows Jul22-Aug20 tại run 21/08)"],
    [None, None],
    ["Nguồn + Ref", None],
    ["Fetch task", "_task_r_nhip1_fetch_20260821.py + _task_r2_cold_ake_20260821.py"],
    ["Data window", "klines/funding May01-Aug20 (112d) · OI Jul22-Aug20 (29d) · LSR Jun27-Aug17 (freshwatch)"],
]
for r_idx, (a, b) in enumerate(meta, start=1):
    if a is not None: ws_case.cell(r_idx, 1).value = a
    if b is not None: ws_case.cell(r_idx, 2).value = b
print(f"CASE meta: {len(meta)} rows")

# Empty EVENTS + UNLOCK + others (per rule: KHÔNG điền EVENTS/OUTCOME/verdict/state)
for sname in ["EVENTS", "TRIGGERS", "OUTCOME", "MM_PROFILE"]:
    if sname in wb.sheetnames:
        wsx = wb[sname]
        for r in range(1, wsx.max_row+1):
            for c in range(1, 10):
                wsx.cell(r, c).value = None
        wsx.cell(1, 1).value = f"{sname} (AKE) — EMPTY, PENDING ANALYSIS"

# UNLOCK skeleton
ws_ul = wb["UNLOCK"]
for r in range(1, ws_ul.max_row+1):
    for c in range(1, 8): ws_ul.cell(r, c).value = None
ws_ul.cell(1,1).value = "date"; ws_ul.cell(1,2).value = "event_type"
ws_ul.cell(1,3).value = "amount_tokens"; ws_ul.cell(1,4).value = "notes"; ws_ul.cell(1,5).value = "source"
ws_ul.cell(2,1).value = "2026-08-21"; ws_ul.cell(2,2).value = "DATA-GAP"
ws_ul.cell(2,4).value = "PENDING nhịp 2 R0 contract + R5 venue verify"
ws_ul.cell(2,5).value = "R2 cold-start"

wb.save(TARGET)
print(f"\nSAVED: {TARGET} ({TARGET.stat().st_size} B)")

# Update CASE_INDEX
INDEX = CASES / "CASE_INDEX.xlsx"
wb_idx = openpyxl.load_workbook(INDEX)
ws_idx = wb_idx["INDEX"]
header_row = None; token_col = state_col = None
for r in range(1, 6):
    for c in range(1, 20):
        v = ws_idx.cell(r,c).value
        if v and str(v).strip().lower() in ("token","symbol"):
            header_row=r; token_col=c
        if v and str(v).strip().lower() in ("state","status","trạng thái"):
            state_col=c
existing = [str(ws_idx.cell(r,token_col).value).strip().upper() for r in range(header_row+1, ws_idx.max_row+1) if ws_idx.cell(r,token_col).value]
if "AKE" not in existing:
    next_r = ws_idx.max_row + 1
    ws_idx.cell(next_r, token_col).value = "AKE"
    if state_col:
        ws_idx.cell(next_r, state_col).value = "COLD_START 21/08 (R2 nhịp 1) — DAILY populated, contract UNVERIFIED (nhịp 2)"
    wb_idx.save(INDEX)
    print(f"CASE_INDEX: ADDED AKE at row {next_r}")

# Sample 3 rows around 14/07 (per operator evidence request)
print("\n=== SAMPLE 3 dòng quanh AKE 14/07 ===")
wb2 = openpyxl.load_workbook(TARGET, data_only=True)
ws2 = wb2["DAILY"]
row2b = [c.value for c in ws2[2]]
ci2 = {str(n).strip(): i+1 for i, n in enumerate(row2b) if n}
for r in range(3, ws2.max_row+1):
    d = str(ws2.cell(r, 1).value)[:10] if ws2.cell(r, 1).value else ""
    if d in ("2026-07-13", "2026-07-14", "2026-07-15"):
        vals = {k: ws2.cell(r, ci2[k]).value for k in ["date","c","vol_perp_usd","oi_usd","pos_r","f_avg"] if k in ci2}
        print(f"  row{r}: {vals}")

print("\n[DONE R2]")
