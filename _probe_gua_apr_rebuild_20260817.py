"""
_probe_gua_apr_rebuild_20260817.py
Fetch Aug10-Aug16 perp/funding/OI for GUA + APR, create updated dated CSVs,
then trigger build_case for each.
"""
import sys, io, csv, json, urllib.request, time, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

def fetch_json(url, params=None, timeout=20):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

def to_ms(d_str):
    return int(datetime.strptime(d_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

def ms_to_date(ms):
    return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")

# ── Perp klines schema (from existing gua_perp_20260810.csv) ──────────────
def get_perp_schema(path):
    with open(path, encoding="utf-8") as f:
        return csv.DictReader(f).fieldnames

def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))

def write_csv(rows, path, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ── Fetch perp klines from fapi ───────────────────────────────────────────
def fetch_perp_klines(sym, start_date, end_date):
    start_ms = to_ms(start_date)
    end_ms   = to_ms(end_date) + 86400000 - 1
    data = fetch_json("https://fapi.binance.com/fapi/v1/klines", {
        "symbol": f"{sym}USDT", "interval": "1d",
        "startTime": start_ms, "endTime": end_ms, "limit": 20,
    })
    if isinstance(data, dict) and "_error" in data:
        print(f"  fapi klines error: {data['_error']}")
        return []
    rows = []
    for k in data:
        d_str = ms_to_date(int(k[0]))
        if d_str < start_date or d_str > end_date:
            continue
        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_q = float(k[7])
        taker_q = float(k[10])
        taker_pct = round(taker_q / vol_q * 100, 4) if vol_q > 0 else 50.0
        # ret_1d computed later vs previous close
        rows.append({
            "date": d_str, "open": o, "high": h, "low": l, "close": c,
            "vol_quote_usd": round(vol_q, 2),
            "taker_buy_pct": taker_pct,
            "taker_buy_vol": round(taker_q, 2),
            "ret_1d": "",  # computed below
            "open_ms": k[0],
        })
    return rows

# ── Fetch funding from fapi ───────────────────────────────────────────────
def fetch_funding(sym, start_date, end_date, limit=200):
    start_ms = to_ms(start_date)
    end_ms   = to_ms(end_date) + 86400000
    data = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate", {
        "symbol": f"{sym}USDT", "startTime": start_ms, "endTime": end_ms, "limit": limit,
    })
    if isinstance(data, dict) and "_error" in data:
        print(f"  funding error: {data['_error']}")
        return []
    rows = []
    for item in data:
        ts = int(item.get("fundingTime", 0))
        rows.append({
            "date": ms_to_date(ts),
            "time_ms": str(ts),
            "fundingRate": item.get("fundingRate", ""),
        })
    return rows

# ── Fetch OI hist ─────────────────────────────────────────────────────────
def fetch_oi_hist(sym, days=30):
    data = fetch_json("https://fapi.binance.com/futures/data/openInterestHist", {
        "symbol": f"{sym}USDT", "period": "1d", "limit": days,
    })
    if isinstance(data, dict) and "_error" in data:
        print(f"  OI hist error: {data['_error']}")
        return []
    rows = []
    for item in data:
        ts = int(item.get("timestamp", 0))
        rows.append({
            "date": ms_to_date(ts),
            "oi_usd": item.get("sumOpenInterestValue", ""),
            "oi_token": item.get("sumOpenInterest", ""),
            "timestamp": str(ts),
        })
    return sorted(rows, key=lambda r: r["date"])

# ── Fetch LSR ─────────────────────────────────────────────────────────────
def fetch_lsr(sym, days=30):
    base_url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
    data = fetch_json(base_url, {
        "symbol": f"{sym}USDT", "period": "1d", "limit": days,
    })
    if isinstance(data, dict) and "_error" in data:
        return []
    rows = []
    for item in data:
        ts = int(item.get("timestamp", 0))
        rows.append({
            "date": ms_to_date(ts),
            "time_ms": str(ts),
            "longShortRatio": item.get("longShortRatio", ""),
            "longAccount": item.get("longAccount", ""),
            "shortAccount": item.get("shortAccount", ""),
        })
    return sorted(rows, key=lambda r: r["date"])

# ─────────────────────────────────────────────────────────────────────────────
# Main loop: GUA then APR
# ─────────────────────────────────────────────────────────────────────────────
TOKENS = {
    "GUA": {"old_tag": "20260810", "fetch_start": "2026-08-10", "end": "2026-08-16"},
    "APR": {"old_tag": "20260810", "fetch_start": "2026-08-10", "end": "2026-08-16"},
}

DATE_TAG  = "20260817"
DATE_END  = "2026-08-16"

for sym, meta in TOKENS.items():
    sym_lower = sym.lower()
    old_tag   = meta["old_tag"]
    print(f"\n{'='*60}")
    print(f"{sym} rebuild")
    print(f"{'='*60}")

    # ── 1. Perp CSV ────────────────────────────────────────────────────────
    old_perp_path = SCRATCH / f"{sym_lower}_perp_{old_tag}.csv"
    new_perp_path = SCRATCH / f"{sym_lower}_perp_{DATE_TAG}.csv"

    old_perp = read_csv(old_perp_path)
    perp_schema = get_perp_schema(old_perp_path)
    print(f"  Existing perp: {len(old_perp)} rows, last={old_perp[-1]['date']}")

    last_date  = old_perp[-1]["date"]
    last_close = float(old_perp[-1]["close"])

    # Fetch Aug10-Aug16 (or from last_date+1 day)
    fetch_start_dt = (_date.fromisoformat(last_date) + timedelta(days=1)).isoformat()
    print(f"  Fetching perp {fetch_start_dt} → {DATE_END}...")
    new_klines = fetch_perp_klines(sym, fetch_start_dt, DATE_END)
    time.sleep(0.3)

    # Compute ret_1d
    prev_close = last_close
    for r in new_klines:
        c = float(r["close"])
        r["ret_1d"] = round((c - prev_close) / prev_close * 100, 8) if prev_close else ""
        prev_close = c

    print(f"  New klines: {len(new_klines)} rows "
          f"({new_klines[0]['date']} → {new_klines[-1]['date']}" if new_klines else "  New klines: 0 rows")

    merged_perp = old_perp + new_klines
    write_csv(merged_perp, new_perp_path, perp_schema)
    print(f"  Written: {new_perp_path.name} ({len(merged_perp)} rows)")

    # ── 2. Funding CSV ─────────────────────────────────────────────────────
    old_fund_path = SCRATCH / f"{sym_lower}_funding_{old_tag}.csv"
    new_fund_path = SCRATCH / f"{sym_lower}_funding_{DATE_TAG}.csv"

    old_fund_rows = read_csv(old_fund_path)
    old_fund_schema = get_perp_schema(old_fund_path)
    print(f"  Existing funding: {len(old_fund_rows)} entries, schema={old_fund_schema}")

    last_fund_date = max(r["date"] for r in old_fund_rows)
    fetch_fund_start = last_fund_date  # re-fetch from same date to catch all 8h entries
    print(f"  Fetching funding {fetch_fund_start} → 2026-08-17...")
    new_fund = fetch_funding(sym, fetch_fund_start, "2026-08-17")
    time.sleep(0.3)

    # Dedup: use (date, fundingRate) key; keep old + append new missing
    existing_keys = {(r["date"], r["fundingRate"]) for r in old_fund_rows}
    added = 0
    append_rows = []
    for r in new_fund:
        key = (r.get("date",""), r.get("fundingRate",""))
        if key not in existing_keys:
            # Convert to old schema (date, fundingRate, markPrice if present)
            row_out = {"date": r["date"], "fundingRate": r["fundingRate"]}
            if "markPrice" in old_fund_schema:
                row_out["markPrice"] = ""
            append_rows.append(row_out)
            existing_keys.add(key)
            added += 1
    print(f"  New funding entries: {added}")

    merged_fund = old_fund_rows + append_rows
    write_csv(merged_fund, new_fund_path, old_fund_schema)
    print(f"  Written: {new_fund_path.name} ({len(merged_fund)} entries)")

    # ── 3. OI hist (fresh 30d) ─────────────────────────────────────────────
    new_oi_path = SCRATCH / f"{sym_lower}_oi_hist_{DATE_TAG}.csv"
    print(f"  Fetching OI hist (30d)...")
    oi_rows = fetch_oi_hist(sym, 30)
    time.sleep(0.3)
    print(f"  OI rows: {len(oi_rows)}, range: {oi_rows[0]['date'] if oi_rows else 'N/A'} → {oi_rows[-1]['date'] if oi_rows else 'N/A'}")
    write_csv(oi_rows, new_oi_path, ["date", "oi_usd", "oi_token", "timestamp"])
    print(f"  Written: {new_oi_path.name}")

    # ── 4. LSR (fresh 30d) ────────────────────────────────────────────────
    new_lsr_path = SCRATCH / f"{sym_lower}_lsr_raw_{DATE_TAG}.csv"
    print(f"  Fetching LSR (30d)...")
    lsr_rows = fetch_lsr(sym, 30)
    time.sleep(0.3)
    print(f"  LSR rows: {len(lsr_rows)}")
    if lsr_rows:
        write_csv(lsr_rows, new_lsr_path,
                  ["date", "time_ms", "longShortRatio", "longAccount", "shortAccount"])
        print(f"  Written: {new_lsr_path.name}")
    else:
        # Write empty with headers
        write_csv([], new_lsr_path,
                  ["date", "time_ms", "longShortRatio", "longAccount", "shortAccount"])
        print(f"  Written empty LSR (symbol may not have this data)")

print("\n" + "="*60)
print("CSVs ready. Next: build_case.py for each token")
print("="*60)

# ── Run build_case.py ─────────────────────────────────────────────────────
for sym in ["GUA", "APR"]:
    print(f"\nRunning: python build_case.py {sym} {DATE_TAG}")
    result = subprocess.run(
        ["python", "build_case.py", sym, DATE_TAG],
        cwd=str(ROOT),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120,
    )
    print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-500:]}")
        print(f"build_case FAILED for {sym} (exit={result.returncode})")
    else:
        print(f"build_case OK for {sym}")

print("\n[DONE]")
