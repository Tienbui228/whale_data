"""_task_gua_b1_fetch_20260818.py
B1: Fetch Aug17 fapi (perp klines, funding, OI, LSR) for GUAUSDT.
Writes to scratch/ with CANONICAL LSR schema (pos_r_raw/acc_r_raw/glsr_raw/taker_lsr_raw)
so build_case A-0a can consume it (Fix B from án E).
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

SYM     = "GUA"
TICKER  = "GUAUSDT"
DATE    = "2026-08-17"
NEW_TAG = "20260818"

def fetch_json(url, params=None, timeout=20):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def to_ms(d): return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# ── perp klines 1d for Aug17 ONLY ──────────────────────────────────────────
print("=== PERP klines (Aug17) ===")
start = to_ms("2026-08-17")
end   = to_ms("2026-08-17") + 86400000 - 1
d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval": "1d",
                "startTime": start, "endTime": end, "limit": 5})
time.sleep(0.3)
perp_new = []
for k in d:
    d_str = ms_to_date(int(k[0]))
    if d_str != DATE: continue
    o,h,l,c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    vol_q  = float(k[7])
    taker_q = float(k[10])
    taker_pct = round(taker_q / vol_q * 100, 4) if vol_q > 0 else 50.0
    perp_new.append({
        "date": d_str, "open": o, "high": h, "low": l, "close": c,
        "vol_quote_usd": round(vol_q, 2),
        "taker_buy_pct": taker_pct,
        "taker_buy_vol": round(taker_q, 2),
        "ret_1d": "",  # will be filled from prev close
        "open_ms": k[0],
    })
    print(f"  {d_str}: o={o} h={h} l={l} c={c} vol_usd={vol_q:.0f} taker_pct={taker_pct:.2f}%")

# ── funding for Aug17 ──────────────────────────────────────────────────────
print("\n=== FUNDING (Aug17) ===")
fund_end = to_ms("2026-08-17") + 86400000
d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
               {"symbol": TICKER, "startTime": to_ms("2026-08-17"),
                "endTime": fund_end, "limit": 20})
time.sleep(0.3)
fund_new = []
for it in d:
    ts = int(it.get("fundingTime", 0))
    dstr = ms_to_date(ts)
    if dstr != DATE: continue
    fr = it.get("fundingRate", "")
    fund_new.append({"date": dstr, "time_ms": str(ts), "fundingRate": fr})
    print(f"  {dstr} @ {ts}: fr={fr}")

# ── funding interval verify (L-41 4h vs 8h) ────────────────────────────────
if len(fund_new) >= 2:
    tss = [int(r["time_ms"]) for r in fund_new]
    intervals = [(tss[i]-tss[i-1])/3600000 for i in range(1, len(tss))]
    med = sorted(intervals)[len(intervals)//2] if intervals else None
    print(f"  fund intervals (h): {intervals} · median={med}")
    if med and abs(med-4) < 0.5:
        print(f"  → 4h interval detected, fn expected=6/day")
    elif med and abs(med-8) < 0.5:
        print(f"  → 8h interval detected, fn expected=3/day")
    else:
        print(f"  → uncertain interval — check manually")

# ── OI hist (Aug17) ────────────────────────────────────────────────────────
print("\n=== OI hist (last 30d, will filter Aug17) ===")
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period": "1d", "limit": 30})
time.sleep(0.3)
oi_all = []
for it in d:
    ts = int(it.get("timestamp", 0))
    dstr = ms_to_date(ts)
    oi_all.append({
        "date": dstr, "timestamp": str(ts),
        "oi_usd": float(it.get("sumOpenInterestValue", 0) or 0),
        "oi_token": float(it.get("sumOpenInterest", 0) or 0),
    })
# dedup-at-read (OI-dup rule): key = (date, timestamp)
seen = set(); oi_dedup = []
for r in oi_all:
    key = (r["date"], r["timestamp"])
    if key in seen: continue
    seen.add(key)
    oi_dedup.append(r)
print(f"  OI raw={len(oi_all)}, after dedup=({len(oi_dedup)})")
oi_17 = [r for r in oi_dedup if r["date"] == DATE]
for r in oi_17:
    print(f"  {r['date']}: oi_usd={r['oi_usd']:.0f} oi_token={r['oi_token']:.0f}")

# ── LSR (last 30d) — write CANONICAL schema (Fix B) ────────────────────────
print("\n=== LSR (last 30d, canonical schema) ===")
d = fetch_json("https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
               {"symbol": TICKER, "period": "1d", "limit": 30})
time.sleep(0.3)
lsr_canonical = []
for it in d:
    ts   = int(it.get("timestamp", 0))
    dstr = ms_to_date(ts)
    lsr_ratio = float(it.get("longShortRatio", 0) or 0)
    long_frac = float(it.get("longAccount", 0) or 0)
    short_frac= float(it.get("shortAccount", 0) or 0)
    # canonical mapping (per proposal Fix B, án E §5)
    # NOTE: pos_r_raw ≠ acc_r (different endpoint). Use gLSR as proxy — will be OVERRIDDEN
    # by freshwatch when available (freshwatch has true pos_r from separate endpoint)
    lsr_canonical.append({
        "date":          dstr,
        "pos_r_raw":     "",  # ABSTAIN — not available from globalLongShortAccountRatio endpoint
        "acc_r_raw":     round(lsr_ratio, 4),  # = long/short account ratio
        "glsr_raw":      round(lsr_ratio, 4),
        "taker_lsr_raw": "",  # ABSTAIN — not from this endpoint
        "_src":          "fapi_LSR_30d",
    })
print(f"  LSR rows fetched: {len(lsr_canonical)}, range: "
      f"{lsr_canonical[0]['date']}→{lsr_canonical[-1]['date']}")

# ── WRITE ──────────────────────────────────────────────────────────────────
# Write NEW scratch CSVs tagged 20260818, do NOT overwrite existing 20260817 files
perp_out = SCRATCH / f"gua_perp_aug17_only_{NEW_TAG}.csv"
fund_out = SCRATCH / f"gua_funding_aug17_only_{NEW_TAG}.csv"
oi_out   = SCRATCH / f"gua_oi_hist_{NEW_TAG}.csv"
lsr_out  = SCRATCH / f"gua_lsr_raw_{NEW_TAG}.csv"

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

if perp_new:
    write_csv(perp_out, perp_new,
              ["date","open","high","low","close","vol_quote_usd",
               "taker_buy_pct","taker_buy_vol","ret_1d","open_ms"])
    print(f"\nWritten: {perp_out.name} ({len(perp_new)} row)")
if fund_new:
    write_csv(fund_out, fund_new, ["date","time_ms","fundingRate"])
    print(f"Written: {fund_out.name} ({len(fund_new)} rows, fn={len(fund_new)})")
write_csv(oi_out, oi_dedup, ["date","timestamp","oi_usd","oi_token"])
print(f"Written: {oi_out.name} ({len(oi_dedup)} rows, after dedup)")
write_csv(lsr_out, lsr_canonical,
          ["date","pos_r_raw","acc_r_raw","glsr_raw","taker_lsr_raw","_src"])
print(f"Written: {lsr_out.name} ({len(lsr_canonical)} rows, canonical schema)")

print("\n[DONE B1 fetch]")
