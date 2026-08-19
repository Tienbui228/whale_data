"""_probe_tria_venue_20260819.py — PHẦN A + B + PHẦN D recon.
Read-only fetch (no case file writes here — separate write task after guard).
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"

ALPHA_ID = "ALPHA_669"
TICKER_PERP = "TRIAUSDT"
START = "2026-07-20"; END = "2026-08-18"

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

# ═══════════════════════════════════════════════════════════════════════
# PHẦN A — TRIA ALPHA vol per-day Jul20-Aug18
# ═══════════════════════════════════════════════════════════════════════
print("="*70)
print("[PHẦN A] TRIA Alpha vol per-day (bapi alpha-trade/klines, ALPHA_669)")
print("="*70)

# Alpha klines endpoint: bapi/defi/v1/public/alpha-trade/klines
# Bapi limit likely 30 or 50, try 40
s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines",
               {"symbol": f"{ALPHA_ID}USDT", "interval": "1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 40})
time.sleep(0.3)

alpha_by_d = {}
if isinstance(d, dict) and "data" in d:
    data = d["data"] or []
elif isinstance(d, list):
    data = d
else:
    data = []
    print(f"  ERROR: {d}")

# alpha klines schema (12 fields, standard-like)
for k in data:
    ts = int(k[0]); d_str = ms_to_date(ts)
    if d_str < START or d_str > END: continue
    alpha_by_d[d_str] = {
        "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
        "base_vol": float(k[5]),
        "quote_vol_usd": float(k[7]),  # k[7] = quote asset vol
        "trades": int(k[8]),
    }

print(f"  Alpha rows: {len(alpha_by_d)}")
print(f"\n  date       o          c          quote_vol_usd  trades")
for d_str in sorted(alpha_by_d):
    r = alpha_by_d[d_str]
    print(f"  {d_str}  {r['o']:.6f}  {r['c']:.6f}  {r['quote_vol_usd']:>13.2f}  {r['trades']}")

# Nền T7 recompute — median Jul20-Jul31
from statistics import median
nen_dates = [d for d in alpha_by_d if "2026-07-20" <= d <= "2026-07-31"]
nen_vols  = [alpha_by_d[d]["quote_vol_usd"] for d in nen_dates]
print(f"\n  Nền T7 window (20-31/07): {len(nen_vols)} days")
if nen_vols:
    med = median(nen_vols); mn = min(nen_vols); mx = max(nen_vols)
    print(f"    median = ${med:,.2f}")
    print(f"    range  = ${mn:,.2f} .. ${mx:,.2f}")
    print(f"\n  → CLAIM in probe 19/08: '~$7-10K/day nền T7'")
    print(f"  → ACTUAL:  median ${med:,.0f} · range ${mn:,.0f}..${mx:,.0f}")
    correction_needed = not (7000 <= med <= 10000)
    print(f"  → CORRECTION NEEDED: {correction_needed}")

# ═══════════════════════════════════════════════════════════════════════
# PHẦN B — TRIA SPOT-EXT (BYBIT)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("[PHẦN B] Bybit spot verify + backfill TRIA/USDT")
print("="*70)

# 1. instruments-info
print("\n  [B.1] Bybit /v5/market/instruments-info?category=spot&symbol=TRIAUSDT")
d = fetch_json("https://api.bybit.com/v5/market/instruments-info",
               {"category":"spot", "symbol":"TRIAUSDT"})
time.sleep(0.3)
print(f"  raw response: {json.dumps(d)[:800]}")

instr_ok = False
if isinstance(d, dict) and d.get("retCode") == 0:
    lst = d.get("result", {}).get("list", [])
    if lst:
        instr_ok = True
        rec = lst[0]
        print(f"\n  RECORD:")
        for k in ["symbol","baseCoin","quoteCoin","status","innovation","launchTime"]:
            print(f"    {k}: {rec.get(k)}")
    else:
        print("  → LIST EMPTY: TRIAUSDT not on Bybit spot")
elif isinstance(d, dict) and d.get("retCode") != 0:
    print(f"  retCode={d.get('retCode')} retMsg={d.get('retMsg')}")

# 2. klines fetch (only if instr exists)
bybit_by_d = {}
identity_pairs = []  # for anti-mirror check
if instr_ok:
    print(f"\n  [B.2] Bybit /v5/market/kline?symbol=TRIAUSDT&interval=D")
    # Bybit v5 klines: from/to in ms
    s_ms_bybit = to_ms(START)
    e_ms_bybit = to_ms(END) + 86400000 - 1
    d = fetch_json("https://api.bybit.com/v5/market/kline",
                   {"category":"spot", "symbol":"TRIAUSDT", "interval":"D",
                    "start": s_ms_bybit, "end": e_ms_bybit, "limit": 200})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        rows = d.get("result", {}).get("list", []) or []
        print(f"  raw rows: {len(rows)}")
        if rows:
            print(f"  first raw: {rows[0]}")
            print(f"  last raw:  {rows[-1]}")
            # Bybit v5 klines fields (per docs):
            # [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
            for k in rows:
                ts = int(k[0]); d_str = ms_to_date(ts)
                if d_str < START or d_str > END: continue
                bybit_by_d[d_str] = {
                    "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
                    "base_vol": float(k[5]),   # base coin volume (TRIA)
                    "turnover_usd": float(k[6]),  # quote turnover (USD)
                }
            print(f"\n  in-window: {len(bybit_by_d)} days")
    else:
        print(f"  Bybit klines error: {d}")

# 3. IDENTITY-CHECK anti-mirror (L-51 draft)
if bybit_by_d:
    print(f"\n  [B.3] IDENTITY-CHECK anti-mirror (bit-level compare volume vs turnover)")
    print(f"  Sample 3 days:")
    days = sorted(bybit_by_d.keys())[:3]
    for d_str in days:
        r = bybit_by_d[d_str]
        # base_vol (TRIA token count) vs turnover_usd (USD)
        # If base_vol == turnover_usd (bit exact), that's mirror bug like Alpha k[9]/k[10]
        bv = r["base_vol"]; tv = r["turnover_usd"]
        # implicit avg price
        implied_avg = tv / bv if bv > 0 else None
        actual_c = r["c"]
        print(f"    {d_str}:")
        print(f"      base_vol      = {bv:.8f}")
        print(f"      turnover_usd  = {tv:.8f}")
        print(f"      bit-equal?    = {bv == tv}")
        print(f"      implied_avg   = {implied_avg}  (close={actual_c})")

# 4. Bybit taker/side check
if instr_ok:
    print(f"\n  [B.4] Bybit taker/side check — attempt public tick endpoints")
    # v5/market/recent-trade returns side field
    d = fetch_json("https://api.bybit.com/v5/market/recent-trade",
                   {"category":"spot","symbol":"TRIAUSDT","limit":5})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        trades = d.get("result",{}).get("list",[]) or []
        if trades:
            print(f"    recent-trade sample: {trades[0]}")
            # side present?
            print(f"    has 'side' field: {'side' in trades[0]}")
    else:
        print(f"    recent-trade error: {d}")

# ═══════════════════════════════════════════════════════════════════════
# PHẦN D — Quick recon Bybit/OKX/Gate cho BTW/GUA/APR/CLO
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("[PHẦN D] Quick recon: BTW / GUA / APR / CLO on Bybit / OKX / Gate")
print("="*70)

def bybit_check(sym):
    d = fetch_json("https://api.bybit.com/v5/market/instruments-info",
                   {"category":"spot","symbol":f"{sym}USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("retCode") == 0:
        lst = d.get("result",{}).get("list",[])
        if lst:
            r = lst[0]
            return f"OK · status={r.get('status')} · launch={r.get('launchTime')}"
        return "empty list"
    return f"err retCode={d.get('retCode') if isinstance(d,dict) else '?'}"

def okx_check(sym):
    d = fetch_json("https://www.okx.com/api/v5/public/instruments",
                   {"instType":"SPOT","instId":f"{sym}-USDT"})
    time.sleep(0.3)
    if isinstance(d, dict) and str(d.get("code")) == "0":
        lst = d.get("data",[])
        if lst:
            r = lst[0]
            return f"OK · state={r.get('state')} · listTime={r.get('listTime')}"
        return "empty data"
    return f"err code={d.get('code') if isinstance(d,dict) else '?'} msg={d.get('msg') if isinstance(d,dict) else ''}"

def gate_check(sym):
    d = fetch_json(f"https://api.gateio.ws/api/v4/spot/currency_pairs/{sym}_USDT")
    time.sleep(0.3)
    if isinstance(d, dict) and d.get("id"):
        return f"OK · status={d.get('trade_status')} · id={d.get('id')}"
    return f"err {d}"

for tok in ["BTW", "GUA", "APR", "CLO", "TRIA"]:
    print(f"\n  {tok}:")
    print(f"    Bybit: {bybit_check(tok)}")
    print(f"    OKX:   {okx_check(tok)}")
    print(f"    Gate:  {gate_check(tok)}")

# ═══════════════════════════════════════════════════════════════════════
# SAVE DATA TO SCRATCH FOR WRITE TASK
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("[SAVE scratch CSVs for write task]")
print("="*70)

alpha_csv = SCRATCH / "tria_alpha_vol_20260819.csv"
with open(alpha_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","base_vol","quote_vol_usd","trades"])
    w.writeheader()
    for d_str in sorted(alpha_by_d):
        w.writerow({"date": d_str, **alpha_by_d[d_str]})
print(f"  Written: {alpha_csv.name} ({len(alpha_by_d)} rows)")

if bybit_by_d:
    bybit_csv = SCRATCH / "tria_bybit_spot_20260819.csv"
    with open(bybit_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","base_vol","turnover_usd"])
        w.writeheader()
        for d_str in sorted(bybit_by_d):
            w.writerow({"date": d_str, **bybit_by_d[d_str]})
    print(f"  Written: {bybit_csv.name} ({len(bybit_by_d)} rows)")

print("\n[DONE probe A+B+D recon]")
