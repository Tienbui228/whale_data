"""_task_pumpbtc_create_case_20260820.py
Create CASE_PUMPBTC.xlsx từ template CASE_HEMI.xlsx (v2.1 schema 52 cols).
Fetch MEXC klines 60d cho vol_spot_ext_usd chuỗi.
Populate DAILY + CASE meta + EVENTS + UNLOCK.
"""
import sys, io, shutil, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
EXPORT = ROOT / "data" / "export"
CASES = ROOT / "docs" / "case_files"
TEMPLATE = CASES / "CASE_HEMI.xlsx"
TARGET = CASES / "CASE_PUMPBTC.xlsx"

SYM = "PUMPBTC"
TICKER = "PUMPBTCUSDT"
ALPHA_ID = "ALPHA_131"
CONTRACT = "0xB7C0007ab75350c582d5eAb1862b872B5cF53F0C"  # VERIFIED 20/08
START = "2026-06-20"; END = "2026-08-19"

def safe_float(v):
    if v in (None, "", "None"): return None
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
def to_ms(d): return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# 1. Copy template
assert not TARGET.exists(), "CASE_PUMPBTC.xlsx exists — abort"
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

# 2. Load perp scratch + fetch missing
perp = {}
perp_csv = SCRATCH / "pumpbtc_perp_20260820.csv"
if perp_csv.exists():
    with open(perp_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            perp[r["date"]] = r
print(f"Perp scratch: {len(perp)} rows")

# 3. Fetch funding + OI + LSR fresh
s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1
fund_all = []; cur = s_ms
while cur <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol":TICKER,"startTime":cur,"endTime":e_ms,"limit":1000})
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
print(f"Funding: {len(fund_by_d)}d")

d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol":TICKER,"period":"1d","limit":30})
time.sleep(0.3)
oi_by_d = {}
for it in d if isinstance(d, list) else []:
    ts = int(it["timestamp"]); d_str = ms_to_date(ts)
    oi_by_d[d_str] = {"oi_usd": float(it["sumOpenInterestValue"] or 0),
                     "oi_token": float(it["sumOpenInterest"] or 0)}
print(f"OI: {len(oi_by_d)}d")

# LSR
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
                "gLSR": safe_float(row.get("lsr_global_r")),
                "taker_lsr": safe_float(row.get("taker_ratio")),
            }
print(f"LSR fw: {len(lsr_fw)}d")

# fapi fallback LSR
def fetch_ep(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol":TICKER,"period":"1d","limit":30})
    time.sleep(0.3)
    by_d = {}
    for it in d if isinstance(d, list) else []:
        ts = int(it["timestamp"]); by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d
lsr_pos = fetch_ep("topLongShortPositionRatio")
lsr_acc = fetch_ep("topLongShortAccountRatio")
lsr_glo = fetch_ep("globalLongShortAccountRatio")

# 4. FETCH MEXC klines 60d
print("\n=== Fetching MEXC klines 60d for vol_spot_ext_usd chuỗi ===")
d = fetch_json("https://api.mexc.com/api/v3/klines",
               {"symbol":f"{SYM}USDT","interval":"1d","startTime":s_ms,"endTime":e_ms,"limit":100})
time.sleep(0.3)
mexc_by_d = {}
if isinstance(d, list):
    # MEXC schema: [openTime, o, h, l, c, base_vol, closeTime, quote_vol]
    for k in d:
        ts = int(k[0]); d_str = ms_to_date(ts)
        if d_str < START or d_str > END: continue
        mexc_by_d[d_str] = {
            "c": float(k[4]),
            "base_vol": float(k[5]),
            "quote_vol_usd": float(k[7]),
        }
print(f"MEXC daily: {len(mexc_by_d)}d")
# Identity check
sample_dates = sorted(mexc_by_d.keys())[:3]
print("  Identity-check 3 mẫu (bit-eq):")
for d_str in sample_dates:
    r = mexc_by_d[d_str]
    bit_eq = r["base_vol"] == r["quote_vol_usd"]
    print(f"    {d_str}: base_vol={r['base_vol']} quote_vol={r['quote_vol_usd']} bit-eq={bit_eq}")

# 5. Build 61 rows
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
days = []; cur = d0
while cur <= d1:
    days.append(cur.isoformat()); cur += timedelta(days=1)

rows = []; prev_c = None
for d_str in days:
    p = perp.get(d_str)
    if not p: continue
    o = safe_float(p["o"]); h = safe_float(p["h"]); l = safe_float(p["l"]); c = safe_float(p["c"])
    frs = fund_by_d.get(d_str, [])
    fn = len(frs); f_avg = round(sum(frs)/fn, 8) if fn else None
    oi_r = oi_by_d.get(d_str, {})
    fw = lsr_fw.get(d_str)
    if fw:
        pos_r, acc_r, gl, tk_lsr, src = fw["pos_r"], fw["acc_r"], fw["gLSR"], fw["taker_lsr"], "freshwatch_store"
    else:
        pos_r = lsr_pos.get(d_str); acc_r = lsr_acc.get(d_str); gl = lsr_glo.get(d_str)
        tk_lsr = None
        src = "fapi_LSR_30d" if pos_r else "MISSING"
    ret_1d = round((c-prev_c)/prev_c*100, 4) if (c and prev_c) else None
    prev_c = c if c else prev_c
    m = mexc_by_d.get(d_str)
    row = {
        "date": d_str,
        "px_avg (H+L+C)/3": round((h+l+c)/3, 8),
        "o": o, "h": h, "l": l, "c": c,
        "vol_perp_usd": safe_float(p["vol_quote_usd"]),
        "taker_buy_pct (k[10]/k[7])": safe_float(p["taker_buy_pct"]),
        "f_avg": f_avg, "f_min": min(frs) if frs else None, "f_max": max(frs) if frs else None,
        "fn (4h=6/day)": fn,
        "oi_usd": oi_r.get("oi_usd"), "oi_token": oi_r.get("oi_token"),
        "data_ok (fn>=6)": (fn >= 6), "low_conf (fn<6)": (fn < 6),
        "ret_1d (close-to-close)": ret_1d,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl, "taker_lsr": tk_lsr,
        # Structural
        "vol_spot_usd": "N/A-STRUCTURAL",  # no Binance spot pair
        "taker_spot_pct": "ABSTAIN-STRUCTURAL",
        "vol_alpha": None,  # Alpha ALPHA_131 alive but mirror-broken taker; keep vol_alpha empty (per L-52 discussion) or write value?
        "taker_alpha": "ABSTAIN-STRUCTURAL(L-48_mirror_confirmed)",
        # SPOT-EXT (v2.1): MEXC = venue lớn nhất (verified across Gate/MEXC/Bitget)
        "vol_spot_ext_usd": safe_float(m.get("quote_vol_usd")) if m else None,
        "spot_ext_venue": "mexc",
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr":  src,
    }
    rows.append(row)

# derived cols
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
print(f"\nWrote {len(rows)} DAILY rows")

# CASE meta
ws_case = wb["CASE"]
for r in range(1, ws_case.max_row+1):
    for c in range(1, 10):
        ws_case.cell(r, c).value = None

meta = [
    ["CASE FILE — PUMPBTC (pumpBTC Governance Token)", None],
    ["Nguồn: probe _probe_pumpbtc_20260820 + venues_vol supp · verdict operator ký · PENDING không đoán", None],
    [None, None],
    ["Status", "TRACKING (cold-start 20/08 — hedge episode dài 51+d từ 2026-06-27, contract VERIFIED)"],
    ["Loại", "Perp fapi + Alpha (mirror-broken) + 3 spot venues (MEXC · Bitget · Gate ETH-only) · captive-hedged deep"],
    ["Perp fapi", "PUMPBTCUSDT TRADING · onboardDate=2025-06-13 (14 tháng history)"],
    ["Anti-collision", "PUMP-family: PUMPBTCUSDT (target) ≠ PUMPUSDT (Pump.fun Solana, khác token). Cả 2 alive fapi."],
    ["Contract (VERIFIED 20/08 ✓)", f"{CONTRACT} on BSC · operator relay 20/08 bit-eq với bapi ALPHA_131 (lowercase identical)"],
    ["Alpha ID", f"{ALPHA_131 if False else ALPHA_ID} · name='pumpBTC Governance Token' · chain=BSC · fullyDelisted=False · offline=False"],
    ["Alpha taker", "MIRROR L-48 confirmed 3/3 bit-eq → taker_alpha = ABSTAIN-STRUCTURAL"],
    ["Spot venues (ranked 24h vol)", "MEXC $53,561 (LỚN NHẤT ✓) · Bitget $38,841 · Gate $14,605 (⚠ BSC LOCKED, ETH only)"],
    ["Venues KHÔNG có", "Binance spot / Bybit / OKX / KuCoin = ∅"],
    ["Gate chain flags (⚠ bài SUPERFORTUNE)", "ETH: dep=0 wd=0 VAN THÔNG ✓ · BSC: dep=1 wd=1 VAN GIẤY (ISOLATED, không đếm)"],
    ["Price-band vs perp (±20%)", "MEXC 0.18% · Bitget 0.37% · Gate 0.43% — ALL ✓ PASS"],
    ["Ngày phát hiện", "2026-08-20"],
    [None, None],
    ["A. HEDGE EPISODE (watchlist_log Aug11-19)", None],
    ["hedge_start", "2026-06-27 (episode dài ~7 tuần, ongoing)"],
    ["struct_n Aug19", "51 days (chưa break, chưa vào unhedge_registry)"],
    ["div_raw range window", "0.18-0.30 SUỐT (deep hedge, xa threshold 0.5)"],
    ["div_avg3 hiện tại", "0.270 (Aug19)"],
    ["List membership", "A + B (Aug11-Aug19), 51 rows in watchlist_log"],
    ["oi_trend (Aug15-19)", "GIẢM → 'short cover thật (OI rút)' per watchlist_log v1.4"],
    [None, None],
    ["B. LSR PROFILE", None],
    ["pos_r range 30d", "1.21 - 1.42 (moderate, không extreme)"],
    ["acc_r range 30d", "4.66 - 7.13 (short-heavy tank)"],
    ["gLSR range 30d", "4.95 - 7.92 (crowd LONG dày, short tank cũng dày)"],
    ["Loài đọc", "Committed-long hedged captive · khuôn TRIA-lite (không extreme pos như STBL/HEMI)"],
    [None, None],
    ["C. FUNDING REGIME", None],
    ["Pin days last30", "3-4/30 · KHÔNG pin đóng đinh (khác TRIA/STBL/HEMI)"],
    ["f_avg range", "5e-5 (pin) → 7.1e-4 (Aug10 spike)"],
    ["Pin quay lại Aug17-19", "3d liên tiếp cuối window — setup mới đang đặt?"],
    ["Burst check ≥15bps", "KHÔNG (max ~7bps Aug10)"],
    [None, None],
    ["D. OI CYCLE + PHASE-TAG", None],
    ["OI 30d min/max/cur", "$1,247,789 → $1,914,833 · current $1,679,346"],
    ["oi_cycle_pos", "0.6470 (middle-high, không peak)"],
    ["PHASE-TAG Aug18 (CSV live)", "PUMPBTC,UNKNOWN,LOW,False — machine không classified (thiếu signal S3)"],
    ["Đọc tay 14d", "S2-EARLY suốt (hedge stable, pump attempts Aug16 rejected Aug17-18, Aug19 retry)"],
    [None, None],
    ["E. STATIC-SEAT CHECK (L-53 calib)", None],
    ["avg14(pos_r) vs cần ≥2.5", "1.335 ❌ FAIL (xa)"],
    ["min14(pos_r)", "1.208 ❌ FAIL"],
    ["avg14(OI) vs cần ≤$5M", "$1.8M ✓ PASS"],
    ["pin days 14d vs cần ≥10", "3/14 ❌ FAIL"],
    ["Verdict STATIC-SEAT", "❌ KHÔNG phải candidate (khác HEMI n=1 pattern)"],
    [None, None],
    ["F. CHÂN HÀNG (multi-venue)", None],
    ["Venue primary (col 51/52)", "MEXC (vol 24h $53,561 = lớn nhất trong 3 venues)"],
    ["Alt venues (metadata only)", "Bitget $38,841 · Gate ETH-only $14,605 (BSC LOCKED)"],
    ["Alpha vol", "ALPHA_131 alive · mirror broken · vol usable nhưng label PROVISIONAL"],
    ["Nền T7 chân spot", "Chưa compute chi tiết — MEXC klines vừa fetch cho DAILY"],
    ["Taker luật", "MEXC klines no native taker → ABSTAIN · Gate no taker → ABSTAIN · Alpha mirror → ABSTAIN"],
    [None, None],
    ["G. DOCTRINE #10 mẫu số", None],
    ["Băng thông spot 24h (3 venues thông)", "MEXC + Bitget + Gate-ETH = $107,006/day (van thông confirmed)"],
    ["Kho on-chain", "PENDING §P4 (operator feed)"],
    [None, None],
    ["H. §P4 CẦN OPERATOR (tag [PENDING §P4.2-5])", None],
    ["Contract 0x + chain", "✓ DONE 20/08 (bit-eq identical với bapi ALPHA_131)"],
    ["Exchange balance trend 30d", "PENDING"],
    ["Whale + top100 concentration", "PENDING"],
    ["Unlock/circ supply + FDV vs MC tracker", "PENDING"],
    ["Ảnh tracker on-chain", "PENDING"],
    [None, None],
    ["I. NGUỒN + REPORT", None],
    ["Probe main", "_probe_pumpbtc_20260820.py"],
    ["Probe venues vol supp", "_probe_pumpbtc_venues_vol_20260820.py"],
    ["Report", "docs/reports/_pumpbtc_probe_20260820.md"],
    ["Data provenance", "fapi/v1 + freshwatch (fw-139) + bapi ALPHA_131 + MEXC + Bitget + Gate + operator contract 20/08"],
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
    ["2025-06-13","LISTING_PERP","PUMPBTCUSDT onboard fapi","fapi exchangeInfo","N/A"],
    ["2026-06-27","HEDGE_EPISODE_START","div_avg3 ≤ 0.5 first day (per watchlist_log v1.4). hedge_start_px~$0.008785","watchlist_log","N/A"],
    ["2026-07-23","F_PIN_FIRST","First pin day in window (f_avg=5.8e-5)","fapi funding","N/A"],
    ["2026-08-10","F_SPIKE","f_avg=7.1e-4 (~7bps, gần 15bps burst threshold)","fapi funding","N/A"],
    ["2026-08-16","RALLY_ATTEMPT","+5.18% ret1d (biggest window), vol $704K (~1.1× nền)","fapi klines","N/A"],
    ["2026-08-17","REJECTED","-4.84% ret1d — pump Aug16 rejected","fapi klines","N/A"],
    ["2026-08-18","CONTINUE_DOWN","-3.45%, pin returned","fapi","N/A"],
    ["2026-08-19","PIN_RETURN_D3 + RETRY","+4.47%, pin 3d liên tiếp (Aug17-19), watchlist struct_n=51","fapi + watchlist_log","unresolved"],
    ["2026-08-20","CONTRACT_VERIFIED","0xB7C0007ab75350c582d5eAb1862b872B5cF53F0C on BSC — operator relay, bit-eq bapi ALPHA_131","operator relay 20/08","N/A"],
]
for r, ev in enumerate(events, start=2):
    for c, val in enumerate(ev, start=1):
        ws_ev.cell(r, c).value = val
print(f"EVENTS: {len(events)} rows")

# UNLOCK
ws_ul = wb["UNLOCK"]
for r in range(1, ws_ul.max_row+1):
    for c in range(1, 8): ws_ul.cell(r, c).value = None
ws_ul.cell(1,1).value = "date"; ws_ul.cell(1,2).value = "event_type"
ws_ul.cell(1,3).value = "amount_tokens"; ws_ul.cell(1,4).value = "notes"; ws_ul.cell(1,5).value = "source"
ws_ul.cell(2,1).value = "2026-08-20"; ws_ul.cell(2,2).value = "DATA-GAP"
ws_ul.cell(2,4).value = ("[DATA-GAP §P4.2-5] Contract identity DONE (0xB7C0007ab75350c582d5eAb1862b872B5cF53F0C BSC). "
                          "PENDING: exchange balance trend 30d · whale + top100 concentration · unlock/circ supply · MC tracker source. "
                          "Cần BscScan trace + tracker snapshot.")
ws_ul.cell(2,5).value = "task create 20/08"

# TRIGGERS/OUTCOME/MM_PROFILE
for sname in ["TRIGGERS","OUTCOME","MM_PROFILE"]:
    if sname not in wb.sheetnames: continue
    wsx = wb[sname]
    for r in range(1, wsx.max_row+1):
        for c in range(1, 10): wsx.cell(r, c).value = None
    wsx.cell(1,1).value = f"{sname} (PUMPBTC) — PENDING operator to define"

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
if "PUMPBTC" not in existing:
    next_r = ws_idx.max_row + 1
    ws_idx.cell(next_r, token_col).value = "PUMPBTC"
    if state_col:
        ws_idx.cell(next_r, state_col).value = "TRACKING (cold-start Aug20, hedge episode 51d ongoing, contract VERIFIED)"
    wb_idx.save(INDEX)
    print(f"CASE_INDEX: ADDED PUMPBTC at row {next_r}")

print("\n[DONE CASE_PUMPBTC]")
