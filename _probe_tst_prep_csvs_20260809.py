"""
_probe_tst_prep_csvs_20260809.py
Convert raw klines/funding/OI to the format build_case.py expects.
Schema:
  perp/spot CSV: date, o, h, l, c, vol_quote_usd, taker_pct, ret_1d
  funding CSV:   date, fundingRate  (one row per funding event)
  oi CSV:        date, oi_usd, oi_token
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260809"

def log(s=""): print(s)

log("=" * 70)
log("TST CSV PREP  |  convert raw → build_case schema")
log("=" * 70)


def klines_to_csv(raw_csv_in, out_path):
    """Convert raw klines (open_time,open,high,low,close,...) to build_case format."""
    with open(raw_csv_in, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    log(f"  Input: {raw_csv_in.name} ({len(rows)} rows)")

    # Convert
    converted = []
    prev_c = None
    for r in rows:
        ts = int(r["open_time"])
        d  = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        o  = float(r["open"])
        h  = float(r["high"])
        l  = float(r["low"])
        c  = float(r["close"])
        vol = float(r.get("volume", 0) or 0)            # base vol (tokens)
        q_vol = float(r.get("quote_vol", 0) or 0)       # quote vol (USDT)
        taker_buy_vol   = float(r.get("taker_buy_vol", 0) or 0)   # base
        taker_buy_q_vol = float(r.get("taker_buy_quote_vol", 0) or 0)  # quote
        # taker_pct: taker buy base vol / total base vol * 100
        taker_pct = round(taker_buy_vol / vol * 100, 4) if vol > 0 else None
        # ret_1d: (c - prev_c) / prev_c * 100
        ret_1d = round((c - prev_c) / prev_c * 100, 4) if prev_c and prev_c > 0 else None
        # vol_quote_usd: prefer quote vol, else base * close
        vol_quote_usd = q_vol if q_vol > 0 else round(vol * c, 2)
        converted.append({
            "date": d, "o": o, "h": h, "l": l, "c": c,
            "vol_quote_usd": vol_quote_usd,
            "taker_pct": taker_pct,
            "ret_1d": ret_1d,
        })
        prev_c = c

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","o","h","l","c","vol_quote_usd","taker_pct","ret_1d"])
        w.writeheader()
        w.writerows(converted)
    log(f"  Output: {out_path.name} ({len(converted)} rows)")
    if converted:
        log(f"    First: {converted[0]}")
        log(f"    Last:  {converted[-1]}")
    return converted


def funding_json_to_csv(json_path, out_path):
    """Convert funding JSON to CSV with date + fundingRate columns."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    log(f"  Input: {Path(json_path).name} ({len(data)} records)")

    rows = []
    for entry in data:
        ts   = int(entry.get("fundingTime", 0))
        rate = entry.get("fundingRate", "")
        if ts:
            d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            rows.append({"date": d, "fundingRate": rate,
                         "fundingTime_utc": datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")})

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","fundingRate","fundingTime_utc"])
        w.writeheader()
        w.writerows(rows)
    log(f"  Output: {out_path.name} ({len(rows)} rows)")
    if rows:
        log(f"    Oldest: {rows[0]}")
        log(f"    Newest: {rows[-1]}")

    # Summary by day: count and avg
    day_rates = {}
    for r in rows:
        day_rates.setdefault(r["date"], []).append(float(r["fundingRate"]))
    log(f"  Days with funding data: {len(day_rates)}")
    # Last 5 days
    log(f"  Last 5 days summary:")
    for d in sorted(day_rates.keys())[-5:]:
        rates = day_rates[d]
        log(f"    {d}: fn={len(rates)} avg={sum(rates)/len(rates):.6f} min={min(rates):.6f} max={max(rates):.6f}")
    return rows


def oi_json_to_csv(json_path, out_path):
    """Convert OI hist JSON to CSV with date + oi_usd + oi_token columns."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    log(f"  Input: {Path(json_path).name} ({len(data)} records)")

    rows = []
    for entry in data:
        ts  = int(entry.get("timestamp", 0))
        oi_token = entry.get("sumOpenInterest", "")
        oi_usd   = entry.get("sumOpenInterestValue", "")
        if ts:
            d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            rows.append({"date": d, "oi_usd": oi_usd, "oi_token": oi_token})

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","oi_usd","oi_token"])
        w.writeheader()
        w.writerows(rows)
    log(f"  Output: {out_path.name} ({len(rows)} rows)")
    if rows:
        log(f"    Oldest: {rows[0]}")
        log(f"    Newest: {rows[-1]}")
    return rows


# ── Convert perp ─────────────────────────────────────────────────────────────
log("\n--- Perp klines ---")
klines_to_csv(
    SCRATCH / f"tst_perp_{DATE_TAG}.csv",
    SCRATCH / f"tst_perp_conv_{DATE_TAG}.csv"
)

# ── Convert spot ─────────────────────────────────────────────────────────────
log("\n--- Spot klines ---")
klines_to_csv(
    SCRATCH / f"tst_spot_{DATE_TAG}.csv",
    SCRATCH / f"tst_spot_conv_{DATE_TAG}.csv"
)

# ── Convert funding ───────────────────────────────────────────────────────────
log("\n--- Funding ---")
funding_json_to_csv(
    SCRATCH / f"tst_funding_{DATE_TAG}.json",
    SCRATCH / f"tst_funding_conv_{DATE_TAG}.csv"
)

# ── Convert OI ───────────────────────────────────────────────────────────────
log("\n--- OI hist ---")
oi_json_to_csv(
    SCRATCH / f"tst_oi_hist_{DATE_TAG}.json",
    SCRATCH / f"tst_oi_hist_conv_{DATE_TAG}.csv"
)

# ── Rename/copy to final names expected by build_case.py ──────────────────────
log("\n--- Rename to build_case.py expected names ---")
# build_case.py reads: tst_perp_20260809.csv, tst_spot_20260809.csv,
#                      tst_lsr_raw_20260809.csv, tst_funding_20260809.csv, tst_oi_hist_20260809.csv
import shutil
pairs = [
    (f"tst_perp_conv_{DATE_TAG}.csv",      f"tst_perp_{DATE_TAG}.csv"),
    (f"tst_spot_conv_{DATE_TAG}.csv",      f"tst_spot_{DATE_TAG}.csv"),
    (f"tst_funding_conv_{DATE_TAG}.csv",   f"tst_funding_{DATE_TAG}.csv"),
    (f"tst_oi_hist_conv_{DATE_TAG}.json",  None),  # skip — already JSON
]
for src_name, dst_name in pairs:
    src = SCRATCH / src_name
    if dst_name and src.exists():
        dst = SCRATCH / dst_name
        shutil.copy2(src, dst)
        log(f"  Copied {src_name} → {dst_name}")

# funding and OI: rename the converted files
shutil.copy2(SCRATCH / f"tst_funding_conv_{DATE_TAG}.csv",
             SCRATCH / f"tst_funding_{DATE_TAG}.csv")
shutil.copy2(SCRATCH / f"tst_oi_hist_conv_{DATE_TAG}.csv",
             SCRATCH / f"tst_oi_hist_{DATE_TAG}.csv")
log(f"  tst_funding_{DATE_TAG}.csv overwritten with converted CSV")
log(f"  tst_oi_hist_{DATE_TAG}.csv created from JSON")

log(f"\n[PREP DONE] — files ready for build_case.py:")
log(f"  tst_perp_20260809.csv       → perp klines (build_case schema)")
log(f"  tst_spot_20260809.csv       → spot klines (build_case schema)")
log(f"  tst_lsr_raw_20260809.csv    → LSR (already correct)")
log(f"  tst_funding_20260809.csv    → funding (date+fundingRate per event)")
log(f"  tst_oi_hist_20260809.csv    → OI (date+oi_usd+oi_token)")
