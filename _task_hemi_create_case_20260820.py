"""_task_hemi_create_case_20260820.py
Create CASE_HEMI.xlsx từ template CASE_STBL (v2.1 schema).
Populate DAILY (Jul01-Aug19, 50 rows) + CASE meta + EVENTS + UNLOCK.
"""
import sys, io, shutil, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES = ROOT / "docs" / "case_files"

TEMPLATE = CASES / "CASE_STBL.xlsx"  # v2.1
TARGET = CASES / "CASE_HEMI.xlsx"

SYM = "HEMI"
TICKER = "HEMIUSDT"
ALPHA_ID = "ALPHA_343"  # UNVERIFIED
CONTRACT_BAPI = "0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b"  # BSC UNVERIFIED
START = "2026-07-01"; END = "2026-08-19"

def safe_float(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None

# 1. Copy template
assert not TARGET.exists(), "CASE_HEMI.xlsx exists — abort"
shutil.copy2(TEMPLATE, TARGET)
print(f"COPIED: {TEMPLATE.name} → {TARGET.name}")

wb = openpyxl.load_workbook(TARGET)
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
print(f"DAILY cols: {len(row2)}")

# Clear DAILY
old_last = ws.max_row
if old_last >= 3:
    ws.delete_rows(3, old_last - 2)

# 2. Load scratch
def load_csv(p):
    if not p.exists(): return []
    with open(p, encoding="utf-8") as f: return list(csv.DictReader(f))

perp = {r["date"]: r for r in load_csv(SCRATCH / "hemi_perp_20260820.csv")}
fund_all = load_csv(SCRATCH / "hemi_funding_20260820.csv")
fund_by_d = {}
for f in fund_all:
    fund_by_d.setdefault(f["date"], []).append(float(f["fundingRate"]))
oi_by_d = {r["date"]: r for r in load_csv(SCRATCH / "hemi_oi_20260820.csv")}
lsr_fw = {r["date"]: r for r in load_csv(SCRATCH / "hemi_lsr_freshwatch_20260820.csv")}
lsr_fapi = {r["date"]: r for r in load_csv(SCRATCH / "hemi_lsr_fapi_20260820.csv")}
gate_by_d = {r["date"]: r for r in load_csv(SCRATCH / "hemi_gate_20260820.csv")}
mexc_by_d = {r["date"]: r for r in load_csv(SCRATCH / "hemi_mexc_20260820.csv")}
print(f"Perp {len(perp)}, funding {len(fund_by_d)}d, OI {len(oi_by_d)}, "
      f"LSR fw {len(lsr_fw)} fapi {len(lsr_fapi)}, Gate {len(gate_by_d)}, MEXC {len(mexc_by_d)}")

# 3. Build 50 rows
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
days = []; cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)

rows = []; prev_c = None
for d_str in days:
    p = perp.get(d_str)
    if not p: continue
    o=safe_float(p["o"]); h=safe_float(p["h"]); l=safe_float(p["l"]); c=safe_float(p["c"])
    frs = fund_by_d.get(d_str, [])
    fn = len(frs); f_avg = round(sum(frs)/fn, 8) if fn else None
    oi_r = oi_by_d.get(d_str, {})
    oi_usd = safe_float(oi_r.get("oi_usd"))
    oi_tok = safe_float(oi_r.get("oi_token"))
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r=safe_float(fw["pos_r"]); acc_r=safe_float(fw["acc_r"]); gl=safe_float(fw["gLSR"])
        tk_lsr=safe_float(fw["taker_lsr"]); src="freshwatch_store"
    else:
        fa = lsr_fapi.get(d_str, {})
        pos_r=safe_float(fa.get("pos_r")); acc_r=safe_float(fa.get("acc_r")); gl=safe_float(fa.get("gLSR"))
        tk_lsr=None
        src="fapi_LSR_30d" if pos_r else "MISSING"
    ret_1d = round((c-prev_c)/prev_c*100, 4) if (c and prev_c) else None
    prev_c = c if c else prev_c
    g = gate_by_d.get(d_str)
    row = {
        "date": d_str,
        "px_avg (H+L+C)/3": round((h+l+c)/3, 8),
        "o": o, "h": h, "l": l, "c": c,
        "vol_perp_usd": safe_float(p["vol_quote_usd"]),
        "taker_buy_pct (k[10]/k[7])": safe_float(p["taker_buy_pct"]),
        "f_avg": f_avg, "f_min": min(frs) if frs else None, "f_max": max(frs) if frs else None,
        "fn (4h=6/day)": fn,
        "oi_usd": oi_usd, "oi_token": oi_tok,
        "data_ok (fn>=6)": (fn >= 6), "low_conf (fn<6)": (fn < 6),
        "ret_1d (close-to-close)": ret_1d,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl, "taker_lsr": tk_lsr,
        # Structural tags v2.1
        "vol_spot_usd": "N/A-STRUCTURAL",
        "taker_spot_pct": "ABSTAIN-STRUCTURAL",
        "vol_alpha": None,  # ALPHA_343 fullyDelisted → không có vol usable
        "taker_alpha": "N/A-DELISTED",
        "vol_spot_ext_usd": safe_float(g.get("vol_quote_usd")) if g else None,
        "spot_ext_venue": "gate",  # primary ext (Gate BSC van thông)
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr":  src,
    }
    rows.append(row)

# derived
pos_arr = [r["pos_r"] for r in rows]
acc_arr = [r["acc_r"] for r in rows]
gl_arr = [r["gLSR"] for r in rows]
for i, r in enumerate(rows):
    p, a, g = pos_arr[i], acc_arr[i], gl_arr[i]
    r["div_raw (pos_r/acc_r)"] = round(p/a,4) if (p and a) else None
    if i >= 2:
        p3=[v for v in pos_arr[i-2:i+1] if v]; a3=[v for v in acc_arr[i-2:i+1] if v]
        if len(p3)==3 and len(a3)==3:
            aa=sum(a3)/3
            r["div_avg3 (avg3p/avg3a)"] = round((sum(p3)/3)/aa,4) if aa else None
    if i >= 5 and gl_arr[i-5]:
        r["glsr_slope_5d (ratio t/t-5)"] = round(g/gl_arr[i-5],4) if g else None
    if i >= 3:
        pp,ap=pos_arr[i-3],acc_arr[i-3]
        r["d_pos_3d (%chg)"] = round((p-pp)/pp*100,4) if (p and pp) else None
        r["d_acc_3d (%chg)"] = round((a-ap)/ap*100,4) if (a and ap) else None

# Write DAILY
for ridx, r in enumerate(rows, start=3):
    for name, cix in ci.items():
        v = r.get(name)
        if v is not None:
            ws.cell(ridx, cix).value = v
print(f"Wrote {len(rows)} DAILY rows")

# CASE meta
ws_case = wb["CASE"]
for r in range(1, ws_case.max_row+1):
    for c in range(1, 10):
        ws_case.cell(r, c).value = None

meta = [
    ["CASE FILE — HEMI", None],
    ["Nguồn: probe _probe_hemi_h0_h1_20260820 + _probe_hemi_h2_h4_20260820 · verdict operator ký · PENDING không đoán", None],
    [None, None],
    ["Status", "TRACKING (cold-start 20/08 — active campaign Aug15+ · contract UNVERIFIED §H6)"],
    ["Loại", "Perp fapi + Gate + MEXC spot · Alpha DELISTED · 3-wave pump pattern (Jul20 · Aug15 · Aug19)"],
    ["Perp fapi", "HEMIUSDT TRADING · onboardDate=2025-08-29 (12 tháng history)"],
    ["Contract (BAPI symbol-match, ⚠ UNVERIFIED F1)", f"{CONTRACT_BAPI} on BSC (chờ operator confirm — bài F1 GUA/SUPERFORTUNE)"],
    ["Alpha ID (⚠ DELISTED)", f"{ALPHA_ID} · name=Hemi · fullyDelisted=True · offline=True · KHÔNG dùng cho vol_alpha"],
    ["Spot venues thông (van OPEN)", "Gate HEMI_USDT (BSC dep+wd OPEN ✓) · MEXC HEMIUSDT (Trading, flags chưa fetch)"],
    ["Spot venues KHÔNG dùng", "Binance HEMIBNB (status=BREAK) · Bybit/OKX/KuCoin/Bitget: KHÔNG có pair"],
    ["Ngày phát hiện", "2026-08-20 (probe ANALYSIS approved)"],
    ["Watchlist_log", "KHÔNG có HEMI row nào trong Aug 2026 watchlist_log — machine miss hoàn toàn"],
    [None, None],
    ["A. GOM-MISS AUTOPSY (Jul01-Aug13, 44 days baseline)", None],
    ["GOM-A A1 (div_avg3 ≥ 1.5 AND gLSR ≤ 1.1)", "MISS ALL 44 DAYS · nearest miss Jul23: div3=0.932 (thiếu 0.568) + gLSR=1.186 (vượt 0.086) · max div3 window=1.115 Aug01"],
    ["GOM-B B1 (div_avg3 ≤ 0.5 struct_n≥3 pin)", "HIT Jul05-09 (5 ngày liên tục, đúng khuôn hedge deep). B1 kích nhưng không có A1 follow-through → HEMI đã ở B1 nhưng chưa unwind hedge lên A1"],
    ["Phân loại miss", "(b) NEAR-MISS-CONFIG: cả 2 vế A1 fail simultaneously — div không đủ + gLSR không đủ. Không phải (a) data-gap, không phải (c) verdict-fail"],
    ["oi_cycle_pos series (Aug từ khi có data)", "Aug01=0.16 · Aug04-05=0 (đáy) · Aug10=0.31 · Aug13=0.03 (giữ đáy trước pump)"],
    [None, None],
    ["B. CAMPAIGN 14-19/08 READOUT", None],
    ["Aug14 pre-pump", "c=$0.00487 consolidation, pos_r 3.466, gLSR 2.932, OI $3.28M"],
    ["Aug15 PUMP D1", "+43.62% ret1d, vol $171,755,407 (**~48× nền T7 perp**), OI $3.36M (chưa build), pos_r 3.836 (peak window), gLSR 2.769"],
    ["Aug16 FLUSH_WITH_OI_BUILD", "-10.56% ret1d, vol $420,748,704 (**~118× nền T7, biggest day**), **OI $9,665,377 (+187% từ $3.36M)** ← short-cover CRUSHED (pos_r 3.83→1.76 = -54%, acc_r 3.74→1.17 = -69%) + long BUILD massive"],
    ["Aug17 REBOUND", "+11.60%, vol $85.4M, OI $8.25M, pos_r 1.644, acc_r 1.361, gLSR 1.252, div 1.208"],
    ["Aug18 TEST + PHASE-TAG=S3-HARVEST", "+1.85%, vol $48.4M, OI $9.19M, pos_r 1.972 · TEST-BAIT candidate (chờ 21/08 chấm HELD/REJECTED)"],
    ["Aug19 PUMP D3", "+22.72%, vol $277,788,044 (**~78× nền T7**), OI $9,785,223 (peak window), pos_r 2.344, gLSR 1.208, **div 1.671** (fully un-hedged/long-committed)"],
    [None, None],
    ["C. HARVEST DETAIL", None],
    ["pos_r peak", "3.836 @ Aug15"],
    ["pos_r đáy sau HARVEST", "1.644 @ Aug17"],
    ["pos-break %", "-57.14% (3.836→1.644) — VƯỢT ngưỡng 25-30% xa, đây là HARVEST clean"],
    ["Ngày sập", "Aug16 (crashed từ Aug15 pump)"],
    ["gLSR flip Aug15→Aug17", "2.769 → 1.118 → 1.252 = crowd flip mạnh (from bull 2.77 → mid 1.12 sau flush, không sụp xuyên 1.0)"],
    [None, None],
    ["D. GLSR/ACC CHUỖI + SQUEEZE-FUEL", None],
    ["Aug10-14 pre-pump", "gLSR 3.06→2.93 (crowd bull dày), acc_r 3.80→3.95 (short-heavy)"],
    ["Aug15 pump D1", "gLSR 2.77 (bull giảm nhẹ), acc_r 3.74"],
    ["Aug16 crash", "gLSR 1.118 (crowd flip → bear), acc_r 1.171 (short cover triệt để)"],
    ["Aug17-19", "gLSR 1.25→1.21 (bull chậm build lại), acc_r 1.36→1.40 (short không tái vào)"],
    ["SQUEEZE-FUEL kết luận", "Short = CỦI (Aug16 short cover cạn), Long = ĐANG BUILD LẠI (Aug17-19 pos_r 1.64→2.34)"],
    [None, None],
    ["E. FUNDING REGIME", None],
    ["Baseline Jul01-Aug14", "PIN 100% (f_avg=+0.00005 mỗi ngày, band [4e-5, 6e-5])"],
    ["Jul20 pump D1 exception", "**f_avg=-0.000136 NEGATIVE** (chỉ ngày này âm trong window) — pump ăn theo short-side short cover"],
    ["Aug15 pump D2", "f_avg=+0.000047 (near-pin)"],
    ["Aug16 crash", "f_avg=+0.000021 (thấp bất thường, ~2× thấp hơn pin)"],
    ["Aug19 pump D3", "f_avg=+0.00005 (quay lại pin)"],
    [None, None],
    ["F. CHÂN HÀNG (multi-venue, price-band + identity CHECK)", None],
    ["Price-band check vs perp", "Gate 0.02-0.04% dev · MEXC 0.00-0.04% dev → ✓ PASS (no wash)"],
    ["Identity-check L-51 3 mẫu", "Gate bit-eq=False · MEXC bit-eq=False → ✓ PASS (real 2-field)"],
    ["Nền T7 perp (Jul01-Aug13)", "median $3,578,625/day · range $1M-$103M"],
    ["Nền T7 Gate", "median $49,158/day · range $12K-$497K"],
    ["Nền T7 MEXC", "median $91,146/day · range $59K-$1.45M"],
    ["Nền T7 spot tổng", "$140K/day (Gate + MEXC)"],
    ["Peak day Aug16 spot", "TBD from Gate/MEXC (perp $420M day)"],
    [None, None],
    ["G. DOCTRINE #10 — kho 590M ≈ $5.1M ÷ băng thông", None],
    ["Kho hiện tại (operator feed 20/08)", "590M HEMI tokens ≈ $5.1M @ price $0.00873 (Aug19 close)"],
    ["Deposit event 14-19/08", "+100M tokens (490M → 590M = +22.6%) TRONG giá +90% = deposit-in-pump khuôn APR"],
    ["Kịch bản 10% MM spot only", "$5.1M ÷ (10% × $140K/day) = ~365 days"],
    ["Kịch bản 30% MM spot only", "$5.1M ÷ (30% × $140K/day) = ~121 days"],
    ["Peak-day capacity", "Aug16 spot vol TBD ~ (perp $420M ngày đó, spot lớn hơn nền nhiều) — xả nhanh khi crowd tham gia"],
    [None, None],
    ["H. §H6 CẦN OPERATOR (mọi nhãn treo [OWNERSHIP-UNVERIFIED])", None],
    ["Contract 0x + chain", "PENDING (Alpha bapi trả 0x5ffd... BSC nhưng DELISTED — cần confirm identity)"],
    ["Kho lên sàn nào (Binance hot vs khác?)", "PENDING BscScan trace ví đích"],
    ["Ví nguồn deposit chạm cụm GUA/TRIA/AIN?", "PENDING — mắt operator on-chain"],
    ["Unlock schedule + supply", "PENDING (BscScan totalSupply, vesting)"],
    [None, None],
    ["I. NGUỒN + REPORT", None],
    ["Probe H0/H1", "_probe_hemi_h0_h1_20260820.py"],
    ["Probe H2/H4", "_probe_hemi_h2_h4_20260820.py"],
    ["Report", "docs/reports/_hemi_build_20260820.md"],
    ["Data provenance", "fapi/v1 + freshwatch_daily (fw-139) + bapi/defi/v1 (Alpha DELISTED) + Gate + MEXC + operator on-chain 20/08"],
]
for r_idx, (a, b) in enumerate(meta, start=1):
    if a is not None: ws_case.cell(r_idx, 1).value = a
    if b is not None: ws_case.cell(r_idx, 2).value = b
print(f"CASE meta: {len(meta)} rows")

# EVENTS
ws_ev = wb["EVENTS"]
for r in range(1, ws_ev.max_row+1):
    for c in range(1, 8): ws_ev.cell(r, c).value = None
for c, h in enumerate(["date","type","description","ref","resolved"], start=1):
    ws_ev.cell(1, c).value = h

events = [
    ["2025-08-29","LISTING_PERP","HEMIUSDT onboard fapi (perp)","fapi exchangeInfo","N/A"],
    ["2026-07-05","GOM_B1_HIT_5D","B1 conditions met (div_avg3≤0.5 struct_n=5 + pin) Jul05-09 — nhưng không có A1 follow-through","probe H2 autopsy","N/A"],
    ["2026-07-20","PUMP_D1_NEG_FUND","+51.50% ret1d, vol $103.7M · **f_avg=-0.000136 (âm duy nhất window)** — short-side ignite","fapi klines+funding","N/A"],
    ["2026-07-21","CRASH_D1","-21.61%, vol $84.5M · pos_r 2.11→1.27 (-40%), gLSR 3.35→1.84 flip","fapi + LSR","N/A"],
    ["2026-08-15","PUMP_D2","+43.62%, vol $171.8M (~48× nền), OI $3.36M chưa build, pos_r 3.836 peak window","fapi klines+OI+LSR","N/A"],
    ["2026-08-16","FLUSH_WITH_OI_BUILD","-10.56% ret + vol $420.7M (biggest day, ~118× nền) + **OI $9.67M (+187%)** ← short-cover CRUSHED (pos_r -54%, acc_r -69%) + long BUILD massive","fapi + LSR","N/A"],
    ["2026-08-17","REBOUND","+11.60%, vol $85.4M, OI $8.25M, div_raw 1.208","fapi + LSR","N/A"],
    ["2026-08-18","S3-HARVEST_PHASE_TAG + TEST_BAIT","PHASE-TAG chấm S3-HARVEST; +1.85% chop, vol $48.4M, OI $9.19M, pos_r 1.972 · TEST result HELD/REJECTED chấm 21/08","phase_tag.log + fapi","unresolved"],
    ["2026-08-19","PUMP_D3","+22.72%, vol $277.8M (~78× nền), OI $9.79M peak window, div_raw 1.671 (fully un-hedged)","fapi + LSR","N/A"],
    ["2026-08-19","DEPOSIT_IN_PUMP","+100M tokens (490M → 590M = +22.6%) TRONG giá +90% (14-19/08) — khuôn APR deposit-in-pump","operator tracker 20/08","unresolved"],
]
for r, ev in enumerate(events, start=2):
    for c, val in enumerate(ev, start=1):
        ws_ev.cell(r, c).value = val
print(f"EVENTS: {len(events)} rows")

# UNLOCK skeleton
ws_ul = wb["UNLOCK"]
for r in range(1, ws_ul.max_row+1):
    for c in range(1, 8): ws_ul.cell(r, c).value = None
ws_ul.cell(1,1).value = "date"; ws_ul.cell(1,2).value = "event_type"
ws_ul.cell(1,3).value = "amount_tokens"; ws_ul.cell(1,4).value = "notes"; ws_ul.cell(1,5).value = "source"
ws_ul.cell(2,1).value = "2026-08-20"; ws_ul.cell(2,2).value = "DATA-GAP"
ws_ul.cell(2,4).value = ("[DATA-GAP] chưa xác định (§H6 pending operator): contract 0x confirmed (bapi trả "
                          "0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b BSC nhưng ALPHA_343 DELISTED — cần confirm), "
                          "total/circ supply, unlock schedule, kho lên sàn nào (Binance hot vs khác), "
                          "ví nguồn deposit chạm cụm GUA/TRIA/AIN?, MC tracker.")
ws_ul.cell(2,5).value = "task create 20/08"

# TRIGGERS/OUTCOME/MM_PROFILE
for sname in ["TRIGGERS","OUTCOME","MM_PROFILE"]:
    if sname not in wb.sheetnames: continue
    wsx = wb[sname]
    for r in range(1, wsx.max_row+1):
        for c in range(1, 10): wsx.cell(r, c).value = None
    wsx.cell(1,1).value = f"{sname} (HEMI) — PENDING operator to define"

wb.save(TARGET)
print(f"\nSAVED: {TARGET} ({TARGET.stat().st_size} B)")

# CASE_INDEX
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
if "HEMI" not in existing:
    next_r = ws_idx.max_row + 1
    ws_idx.cell(next_r, token_col).value = "HEMI"
    if state_col:
        ws_idx.cell(next_r, state_col).value = "TRACKING (cold-start Aug20, active campaign, contract UNVERIFIED)"
    wb_idx.save(INDEX)
    print(f"CASE_INDEX: ADDED HEMI at row {next_r}")

print("\n[DONE CASE_HEMI]")
