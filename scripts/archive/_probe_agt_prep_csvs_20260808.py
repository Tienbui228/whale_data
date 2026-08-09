"""
_probe_agt_prep_csvs_20260808.py
Convert raw klines/JSON → build_case.py schema CSVs.
Perp: klines → date,o,h,l,c,vol_quote_usd,taker_pct,ret_1d
Funding: JSON → date,fundingRate,fundingTime_utc CSV
OI: JSON → date,oi_usd,oi_token CSV
L-21: trim 2026-08-08 partial candle.
Spot: NO PAIR — write empty CSV với note.
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260808"
TRIM_DATE = "2026-08-08"  # L-21: candle not closed at collect time (08:38 UTC)

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"AGT CSV PREP  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── Perp klines ─────────────────────────────────────────────────────────────
log("\n--- Perp klines ---")
with open(SCRATCH / f"agt_perp_raw_{DATE_TAG}.csv", encoding="utf-8") as f:
    raw_perp = list(csv.DictReader(f))
log(f"  Raw rows: {len(raw_perp)}")

converted = []
prev_c = None
for r in raw_perp:
    ts  = int(r["open_time"])
    d   = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    o   = float(r["open"])
    h   = float(r["high"])
    l   = float(r["low"])
    c   = float(r["close"])
    vol = float(r["volume"] or 0)
    q_vol = float(r["quote_vol"] or 0)
    tbv = float(r["taker_buy_vol"] or 0)
    taker_pct = round(tbv/vol*100, 4) if vol > 0 else None
    ret_1d = round((c-prev_c)/prev_c*100, 4) if prev_c and prev_c > 0 else None
    vol_quote_usd = q_vol if q_vol > 0 else round(vol*c, 2)
    converted.append({"date":d,"o":o,"h":h,"l":l,"c":c,
                       "vol_quote_usd":vol_quote_usd,"taker_pct":taker_pct,"ret_1d":ret_1d})
    prev_c = c

# L-21 trim
before = len(converted)
converted = [r for r in converted if r["date"] != TRIM_DATE]
log(f"  After L-21 trim: {len(converted)} (removed {before-len(converted)} rows = {TRIM_DATE})")
if converted:
    log(f"  Range: {converted[0]['date']} → {converted[-1]['date']}")
    log(f"  Last: {converted[-1]}")

perp_out = SCRATCH / f"agt_perp_{DATE_TAG}.csv"
with open(perp_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","vol_quote_usd","taker_pct","ret_1d"])
    w.writeheader()
    w.writerows(converted)
log(f"  Saved: {perp_out.name}")

# ── Spot: NO PAIR — write empty CSV ─────────────────────────────────────────
log("\n--- Spot klines ---")
log(f"  AGTUSDT spot pair does NOT exist on Binance (HTTP 400)")
log(f"  → vol_spot_usd = MISSING (no spot pair)")
spot_out = SCRATCH / f"agt_spot_{DATE_TAG}.csv"
with open(spot_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","vol_quote_usd","taker_pct","ret_1d"])
    w.writeheader()  # empty — 0 data rows
log(f"  Saved empty: {spot_out.name} (0 rows, reason: no spot pair)")

# ── Funding JSON → CSV ────────────────────────────────────────────────────────
log("\n--- Funding ---")
fund_raw = json.loads((SCRATCH / f"agt_funding_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  Raw records: {len(fund_raw)}")

fund_rows = []
for entry in fund_raw:
    ts   = int(entry.get("fundingTime", 0))
    rate = entry.get("fundingRate", "")
    if ts:
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        utc_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        fund_rows.append({"date": d, "fundingRate": rate, "fundingTime_utc": utc_str})

fund_out = SCRATCH / f"agt_funding_{DATE_TAG}.csv"
with open(fund_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","fundingRate","fundingTime_utc"])
    w.writeheader()
    w.writerows(fund_rows)
log(f"  CSV rows: {len(fund_rows)}")
if fund_rows:
    log(f"  Range: {fund_rows[0]['date']} → {fund_rows[-1]['date']}")
# Day summary last 5
day_rates = {}
for r in fund_rows:
    day_rates.setdefault(r["date"], []).append(float(r["fundingRate"]))
log(f"  Days with funding: {len(day_rates)}")
log(f"  Last 5 days:")
for d in sorted(day_rates.keys())[-5:]:
    rates = day_rates[d]
    log(f"    {d}: fn={len(rates)} f_avg={sum(rates)/len(rates):.6f} f_min={min(rates):.6f} f_max={max(rates):.6f}")
log(f"  Saved: {fund_out.name}")

# ── OI JSON → CSV ─────────────────────────────────────────────────────────────
log("\n--- OI hist ---")
oi_raw = json.loads((SCRATCH / f"agt_oi_hist_{DATE_TAG}.json").read_text(encoding="utf-8"))
log(f"  Raw records: {len(oi_raw)}")

oi_rows = []
for entry in oi_raw:
    ts       = int(entry.get("timestamp", 0))
    oi_token = entry.get("sumOpenInterest","")
    oi_usd   = entry.get("sumOpenInterestValue","")
    if ts:
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_rows.append({"date":d,"oi_usd":oi_usd,"oi_token":oi_token})

oi_out = SCRATCH / f"agt_oi_hist_{DATE_TAG}.csv"
with open(oi_out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
    w.writeheader()
    w.writerows(oi_rows)
log(f"  CSV rows: {len(oi_rows)}")
if oi_rows:
    log(f"  Range: {oi_rows[0]['date']} → {oi_rows[-1]['date']}")
    log(f"  Last: {oi_rows[-1]}")
log(f"  Saved: {oi_out.name}")

# ── Final check ───────────────────────────────────────────────────────────────
log("\n--- Final file list ---")
for label, name, expected_rows in [
    ("Perp CSV", f"agt_perp_{DATE_TAG}.csv", len(converted)),
    ("Spot CSV", f"agt_spot_{DATE_TAG}.csv", 0),
    ("Funding CSV", f"agt_funding_{DATE_TAG}.csv", len(fund_rows)),
    ("OI CSV", f"agt_oi_hist_{DATE_TAG}.csv", len(oi_rows)),
    ("LSR CSV", f"agt_lsr_raw_{DATE_TAG}.csv", 31),
]:
    p = SCRATCH / name
    log(f"  {label}: {name} — {'EXISTS' if p.exists() else 'MISSING'} (expected ~{expected_rows} rows)")

log(f"\n[CSV PREP DONE]")
log(f"  Build call: python build_case.py AGTUSDT {DATE_TAG} '<CASE_QUESTION>'")
