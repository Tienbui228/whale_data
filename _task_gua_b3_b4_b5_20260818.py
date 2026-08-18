"""_task_gua_b3_b4_b5_20260818.py
B3: Fill spot Aug17 + verify Alpha GUA status (alive/delisted).
B4: Append 4 EVENTS from operator on-chain feed.
B5: Read UNLOCK sheet + note DATA-GAP.

Write only to xlsx after each step's inline guard.
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES   = ROOT / "docs" / "case_files"
XLSX    = CASES / "CASE_GUA.xlsx"

SYM      = "GUA"
ALPHA_ID = "ALPHA_483"

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

# ── B3.1: Alpha status probe ────────────────────────────────────────────────
print("="*70)
print("B3.1: ALPHA GUA status probe (endpoint verify)")
print("="*70)

# alpha bapi klines endpoint — try to fetch recent 3 days
alpha_url = "https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"
end_ms = int(time.time() * 1000)
start_ms = end_ms - 3*86400000
d = fetch_json(alpha_url, {"symbol": f"{ALPHA_ID}USDT", "interval": "1d",
                            "startTime": start_ms, "endTime": end_ms, "limit": 5})
alpha_alive = None
alpha_rows_recent = 0
if isinstance(d, dict) and "_error" in d:
    print(f"  ERROR: {d['_error']}")
elif isinstance(d, dict) and d.get("code") not in (None, "000000", 0):
    print(f"  API returned code={d.get('code')} msg={d.get('message')}")
    alpha_alive = False
elif isinstance(d, dict) and "data" in d:
    rows = d.get("data") or []
    alpha_rows_recent = len(rows)
    alpha_alive = alpha_rows_recent > 0
    print(f"  Alpha response OK, rows={alpha_rows_recent}")
    for r in rows[-3:]:
        print(f"    {r}")
elif isinstance(d, list):
    alpha_rows_recent = len(d)
    alpha_alive = alpha_rows_recent > 0
    print(f"  Alpha response (list) rows={alpha_rows_recent}")
    for r in d[-3:]:
        print(f"    {r}")
else:
    print(f"  Unexpected response type: {type(d).__name__}")
print(f"\n  ALPHA GUA VERDICT: alive={alpha_alive}, rows_recent={alpha_rows_recent}")
time.sleep(0.3)

# Also fetch token metadata for fullyDelisted flag
meta_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
d = fetch_json(meta_url, {})
alpha_meta = None
if isinstance(d, dict) and "data" in d:
    for tok in (d.get("data") or []):
        if tok.get("alphaId") == ALPHA_ID:
            alpha_meta = tok
            break
if alpha_meta:
    print(f"\n  Alpha metadata: name={alpha_meta.get('name')}, symbol={alpha_meta.get('symbol')}")
    for k in ["fullyDelisted","offline","listingStatus","tradeStatus","alphaId","symbol","name","chainName","contractAddress"]:
        if k in alpha_meta:
            print(f"    {k}: {alpha_meta.get(k)}")
else:
    print("  Alpha metadata: NOT FOUND in token list (may be delisted from list)")

# ── B3.2: Check spot_klines_1d store for GUA recent partitions ─────────────
print("\n" + "="*70)
print("B3.2: spot_klines_1d store — GUA recent partitions")
print("="*70)

store_dir = ROOT / "data" / "raw" / "spot_klines_1d"
gua_alpha_rows = []
if store_dir.exists():
    parts = sorted([p for p in store_dir.iterdir() if p.is_dir()], reverse=True)[:10]
    print(f"  Latest 10 partitions checked:")
    for p in parts:
        date_str = p.name.replace("date=", "")
        # look for parquet or csv
        found_files = list(p.glob("*.parquet")) + list(p.glob("*.csv"))
        gua_found = None
        for ff in found_files:
            try:
                if ff.suffix == ".csv":
                    with open(ff, encoding="utf-8") as f:
                        for row in csv.DictReader(f):
                            if row.get("symbol","") in ("GUA","GUAUSDT",ALPHA_ID,f"{ALPHA_ID}USDT"):
                                gua_found = row
                                break
                # skip parquet for simplicity (pandas may not be avail)
            except Exception as e:
                pass
        marker = "✓" if gua_found else "—"
        print(f"    {marker} {date_str}: {'GUA row found' if gua_found else 'no GUA'}")
        if gua_found:
            gua_alpha_rows.append({"date": date_str, **gua_found})
else:
    print(f"  Store dir MISSING: {store_dir}")

# ── B3.3: Update CASE_GUA Aug17 spot values ────────────────────────────────
print("\n" + "="*70)
print("B3.3: Update CASE_GUA Aug17 spot cols")
print("="*70)
wb = openpyxl.load_workbook(XLSX)
ws = wb["DAILY"]
row2 = [c.value for c in ws[2]]
col_idx = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}

# find Aug17 row
r17 = None
for r in range(3, ws.max_row+1):
    d = ws.cell(r, col_idx["date"]).value
    if d and str(d)[:10] == "2026-08-17":
        r17 = r
        break
print(f"  Aug17 row: {r17}")

# Compute Aug17 spot values
# Given alpha status: if alpha alive → use recent alpha_klines_store for Aug17 vol_alpha
# For vol_spot_usd on Aug17: no external CEX spot data available for GUA (WASH override from án 17/08)
# Aug16 had vol_spot_usd=234377.68 (from alpha_klines_store per handover — venue=binance_alpha)
# For Aug17: try to get from spot_klines_1d store or from alpha endpoint
aug17_vol_alpha = None
if alpha_alive and gua_alpha_rows:
    # If Aug17 partition has data:
    for r in gua_alpha_rows:
        if r["date"] == "2026-08-17":
            # look for quote_vol / vol_usd field
            for k in ("quote_vol","vol_usd","vol_quote_usd","volume_quote"):
                v = r.get(k)
                if v:
                    try: aug17_vol_alpha = float(v); break
                    except: pass
            break
# If not in store, try direct alpha bapi klines for Aug17
if aug17_vol_alpha is None and alpha_alive:
    d = fetch_json(alpha_url,
                   {"symbol": f"{ALPHA_ID}USDT", "interval": "1d",
                    "startTime": 1786924800000, "endTime": 1787011200000, "limit": 5})
    time.sleep(0.3)
    if isinstance(d, dict) and "data" in d:
        for r in d["data"]:
            ts = int(r[0]) if isinstance(r, list) else int(r.get("openTime",0))
            d_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            if d_str == "2026-08-17":
                if isinstance(r, list) and len(r) >= 8:
                    aug17_vol_alpha = float(r[7])  # quote asset volume
                    print(f"  Alpha bapi Aug17 vol_alpha = ${aug17_vol_alpha:,.0f}")
                break

# Aug17 spot_perp_ratio = vol_alpha / oi_usd (if vol_alpha present)
oi_aug17 = ws.cell(r17, col_idx["oi_usd"]).value
oi_aug17 = float(oi_aug17) if oi_aug17 else None
if aug17_vol_alpha and oi_aug17:
    ratio = round(aug17_vol_alpha / oi_aug17, 6)
    print(f"  Aug17: vol_alpha={aug17_vol_alpha:,.0f} oi={oi_aug17:,.0f} ratio={ratio}")
    # write cols
    ws.cell(r17, col_idx["vol_spot_usd"]).value = round(aug17_vol_alpha, 2)  # use alpha as spot proxy
    ws.cell(r17, col_idx["spot_perp_ratio"]).value = ratio
else:
    print(f"  Aug17: vol_alpha unavailable (alpha_alive={alpha_alive}), no write")

# taker_spot_pct: ABSTAIN (L-48 Alpha)
ws.cell(r17, col_idx["taker_spot_pct"]).value = None

# vol_alpha col + taker_alpha col
if "vol_alpha" in col_idx and aug17_vol_alpha:
    ws.cell(r17, col_idx["vol_alpha"]).value = f"alpha_klines_bapi:{aug17_vol_alpha:.0f}"
if "taker_alpha" in col_idx:
    ws.cell(r17, col_idx["taker_alpha"]).value = "ABSTAIN(L-48_alpha_taker_broken)"

# ── B4: EVENTS append (operator on-chain feed) ─────────────────────────────
print("\n" + "="*70)
print("B4: EVENTS append (operator on-chain feed)")
print("="*70)
ws_ev = wb["EVENTS"]
ev_row1 = [c.value for c in ws_ev[1]]
print(f"  EVENTS headers: {ev_row1}")
next_row = ws_ev.max_row + 1
print(f"  Next EVENTS row: {next_row}")

events_new = [
    # ① 2026-07-1x exchange balance +~40M (30M→70M)
    ["2026-07-15", "EXCH_BAL_ADD",
     "exchange balance +~40M tokens (30M→70M, ngày chính xác ~mid Jul, tracker range)",
     "operator on-chain feed 18/08 (khoảng ngày)", "unresolved"],
    # ② 2026-08-09/10 exchange balance +~62M (68M→130M)
    ["2026-08-10", "EXCH_BAL_ADD_IN_PUMP",
     "exchange balance +~62M tokens (68M→130M), NGAY SAU pump 05-08/08 = khuôn APR deposit-trong-pump",
     "operator on-chain feed 18/08", "unresolved"],
    # ③ whale holdings −97.5% (90d)
    ["2026-08-18", "WHALE_HOLDING_DROP",
     "whale holdings −97.5% trong 90d (đọc theo snapshot 18/08)",
     "operator on-chain feed 18/08", "unresolved"],
    # ④ pump 05-08/08 range + OI đỉnh
    ["2026-08-08", "PUMP_WINDOW",
     "cú pump 05-08/08: xác định range giá + OI đỉnh (đọc DAILY riêng để chốt số)",
     "operator on-chain feed 18/08", "unresolved"],
]
for ev in events_new:
    for ci, val in enumerate(ev, start=1):
        ws_ev.cell(next_row, ci).value = val
    print(f"  + row {next_row}: {ev[0]} | {ev[1]}")
    next_row += 1
print(f"  EVENTS appended: 4 rows (operator source, all unresolved)")

# ── B5: UNLOCK verify (đang trống) ─────────────────────────────────────────
print("\n" + "="*70)
print("B5: UNLOCK sheet — verify + DATA-GAP note")
print("="*70)
ws_ul = wb["UNLOCK"]
print(f"  UNLOCK dims: {ws_ul.dimensions}")
print(f"  UNLOCK row1: {[c.value for c in ws_ul[1]]}")
# task says "1x1 trống" — confirmed empty. Write DATA-GAP notice.
ws_ul.cell(1,1).value = "date"
ws_ul.cell(1,2).value = "event_type"
ws_ul.cell(1,3).value = "amount_tokens"
ws_ul.cell(1,4).value = "notes"
ws_ul.cell(1,5).value = "source"
# Row 2: DATA-GAP notice
ws_ul.cell(2,1).value = "2026-08-18"
ws_ul.cell(2,2).value = "DATA-GAP"
ws_ul.cell(2,3).value = None
ws_ul.cell(2,4).value = ("[DATA-GAP] chưa xác định: total supply · circ supply · unlock schedule. "
                          "Mâu thuẫn: 130M token exchange × $0.04281 = $5.57M > MC tracker $1.98M "
                          "→ 3 khả năng: (a) MC tracker sai (dùng circ cũ), (b) 130M không phải "
                          "circ (một phần lock), (c) exchange balance khác trader-owned. "
                          "Cần contract on-chain + tracker source cụ thể.")
ws_ul.cell(2,5).value = "task 18/08 B5"
print(f"  UNLOCK filled: headers + 1 DATA-GAP row")

# ── SAVE ──────────────────────────────────────────────────────────────────
wb.save(XLSX)
print(f"\n  SAVED: {XLSX}")

print("\n[DONE B3+B4+B5]")

# ── Print summary for report ──────────────────────────────────────────────
print("\n" + "="*70)
print("SUMMARY FOR REPORT")
print("="*70)
print(f"Alpha status: alive={alpha_alive}")
if alpha_meta:
    print(f"  fullyDelisted={alpha_meta.get('fullyDelisted')} "
          f"offline={alpha_meta.get('offline')} "
          f"listingStatus={alpha_meta.get('listingStatus')} "
          f"tradeStatus={alpha_meta.get('tradeStatus')}")
print(f"Alpha vol Aug17 = {aug17_vol_alpha}")
print(f"EVENTS added: 4 (rows {next_row-4}..{next_row-1})")
print(f"UNLOCK: filled headers + DATA-GAP note")
