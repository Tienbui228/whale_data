"""
_probe_spot_klines_20260817.py
S-4: Fetch klines Jul01-Aug16 for AIN, GUA, APR
  - AIN/GUA: Alpha store (→ Aug03) + Alpha bapi top-up (Aug04-Aug16)
  - APR: KuCoin full range
Output: scratch/spot_klines_{SYM}_20260817.csv
"""
import sys, io, json, csv, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
STORE   = ROOT / "data" / "raw" / "spot_klines_1d"
SCRATCH = ROOT / "scratch"

DATE_START = "2026-07-01"
DATE_END   = "2026-08-16"

ALPHA_KLINES_URL = "https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines"

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

KLINE_FIELDS = ["date","open","high","low","close","quote_vol","base_vol","taker_abstain","venue","note"]

# ─────────────────────────────────────────────────────────────────────────────
# Alpha bapi klines fetch
# ─────────────────────────────────────────────────────────────────────────────
def fetch_alpha_klines(alpha_id, start_date, end_date):
    """Returns list of dicts with date, open, high, low, close, quote_vol.
    symbol must be {alpha_id}USDT per collect_alpha_daily.py L207.
    """
    start_ms = to_ms(start_date)
    end_ms   = to_ms(end_date) + 86400000  # inclusive end
    ticker = f"{alpha_id}USDT"
    data = fetch_json(ALPHA_KLINES_URL, {
        "symbol":    ticker,
        "interval":  "1d",
        "startTime": start_ms,
        "endTime":   end_ms,
        "limit":     100,
    })
    if isinstance(data, dict):
        if "_error" in data:
            print(f"  Alpha bapi error: {data['_error']}")
            return []
        # Might be {data: [...]} or {code: ..., data: [...]}
        data = data.get("data", [])
    if not isinstance(data, list):
        print(f"  Alpha bapi unexpected response type: {type(data)}")
        return []
    rows = []
    for k in data:
        if not isinstance(k, list) or len(k) < 8:
            continue
        d_str = ms_to_date(int(k[0]))
        if d_str < start_date or d_str > end_date:
            continue
        base_vol  = float(k[5] or 0)
        quote_vol = float(k[7] or 0)
        close     = float(k[4])
        # GUARD: taker_buy_base == base_vol always on Alpha — ABSTAIN
        rows.append({
            "date":          d_str,
            "open":          k[1],
            "high":          k[2],
            "low":           k[3],
            "close":         str(quote_vol / base_vol if base_vol > 0 else close),  # avg_px
            "quote_vol":     str(quote_vol),
            "base_vol":      str(base_vol),
            "taker_abstain": "True",
            "venue":         "binance_alpha",
            "note":          "",
        })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# Read from local Alpha store
# ─────────────────────────────────────────────────────────────────────────────
def read_alpha_store(sym_name, start_date, end_date):
    """Read rows from parquet store for date range."""
    import pandas as pd
    rows = []
    if not STORE.exists():
        print(f"  Store not found: {STORE}")
        return rows

    date_dirs = sorted([d for d in STORE.iterdir()
                        if d.is_dir() and d.name.startswith("date=")])

    for dd in date_dirs:
        d_str = dd.name.replace("date=", "")
        if d_str < start_date or d_str > end_date:
            continue
        pq = dd / "part-0.parquet"
        if not pq.exists():
            continue
        df = pd.read_parquet(pq)
        sub = df[df["symbol"].isin([f"{sym_name}USDT", sym_name])]
        for _, r in sub.iterrows():
            rows.append({
                "date":          d_str,
                "open":          str(r.get("open", "")),
                "high":          str(r.get("high", "")),
                "low":           str(r.get("low", "")),
                "close":         str(r.get("close", "")),
                "quote_vol":     str(r.get("quote_vol", "")),
                "base_vol":      str(r.get("base_vol", "")),
                "taker_abstain": str(r.get("taker_abstain", True)),
                "venue":         str(r.get("venue", "binance_alpha")),
                "note":          "from_store",
            })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# KuCoin klines
# ─────────────────────────────────────────────────────────────────────────────
def fetch_kucoin_klines(sym, start_date, end_date):
    """
    KuCoin /api/v1/market/candles
    Response: data = [[ts_seconds, open, close, high, low, base_vol, quote_vol], ...]
    Descending order (newest first).
    """
    start_s = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    end_s   = int(datetime.strptime(end_date,   "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 86400

    data = fetch_json("https://api.kucoin.com/api/v1/market/candles", {
        "type":      "1day",
        "symbol":    f"{sym}-USDT",
        "startAt":   start_s,
        "endAt":     end_s,
    })
    if "_error" in data:
        print(f"  KuCoin error: {data['_error']}")
        return []
    if data.get("code") != "200000":
        print(f"  KuCoin code={data.get('code')} msg={data.get('msg')}")
        return []

    rows = []
    for k in data.get("data", []):
        # [ts_sec, open, close, high, low, base_vol, quote_vol]
        d_str = datetime.fromtimestamp(int(k[0]), tz=timezone.utc).strftime("%Y-%m-%d")
        if d_str < start_date or d_str > end_date:
            continue
        rows.append({
            "date":          d_str,
            "open":          k[1],
            "high":          k[3],
            "low":           k[4],
            "close":         k[2],
            "quote_vol":     k[6],   # quote_vol = USDT vol
            "base_vol":      k[5],
            "taker_abstain": "True", # KuCoin no taker
            "venue":         "kucoin",
            "note":          "wash_suspect_flag=True ratio=98.4",
        })
    # Sort ascending by date
    rows.sort(key=lambda r: r["date"])
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# Write CSV
# ─────────────────────────────────────────────────────────────────────────────
def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KLINE_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  Written: {path.name} ({len(rows)} rows)")

# ─────────────────────────────────────────────────────────────────────────────
# AIN — Alpha store + bapi top-up
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("AIN klines (ALPHA_260)")
print("=" * 60)
STORE_LAST = "2026-08-03"

print(f"  Reading Alpha store {DATE_START} → {STORE_LAST}...")
ain_store = read_alpha_store("AIN", DATE_START, STORE_LAST)
print(f"  Store rows: {len(ain_store)}")
if ain_store:
    print(f"  Store range: {ain_store[0]['date']} → {ain_store[-1]['date']}")

# Fetch Aug04-Aug16 from bapi
topup_start = "2026-08-04"
print(f"  Fetching Alpha bapi {topup_start} → {DATE_END}...")
ain_bapi = fetch_alpha_klines("ALPHA_260", topup_start, DATE_END)
print(f"  bapi rows: {len(ain_bapi)}")
if ain_bapi:
    print(f"  bapi range: {ain_bapi[0]['date']} → {ain_bapi[-1]['date']}")
time.sleep(0.5)

# Merge (store first, then bapi, dedup by date)
ain_all = {r["date"]: r for r in ain_store}
for r in ain_bapi:
    ain_all[r["date"]] = r  # bapi overrides store for same date
ain_rows = sorted(ain_all.values(), key=lambda r: r["date"])
ain_rows = [r for r in ain_rows if DATE_START <= r["date"] <= DATE_END]
print(f"  Final: {len(ain_rows)} rows {ain_rows[0]['date'] if ain_rows else 'N/A'} → {ain_rows[-1]['date'] if ain_rows else 'N/A'}")

write_csv(ain_rows, SCRATCH / "spot_klines_AIN_20260817.csv")

# ─────────────────────────────────────────────────────────────────────────────
# GUA — Alpha store + bapi top-up
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("GUA klines (ALPHA_483)")
print("=" * 60)

print(f"  Reading Alpha store {DATE_START} → {STORE_LAST}...")
gua_store = read_alpha_store("GUA", DATE_START, STORE_LAST)
print(f"  Store rows: {len(gua_store)}")
if gua_store:
    print(f"  Store range: {gua_store[0]['date']} → {gua_store[-1]['date']}")

print(f"  Fetching Alpha bapi {topup_start} → {DATE_END}...")
gua_bapi = fetch_alpha_klines("ALPHA_483", topup_start, DATE_END)
print(f"  bapi rows: {len(gua_bapi)}")
if gua_bapi:
    print(f"  bapi range: {gua_bapi[0]['date']} → {gua_bapi[-1]['date']}")
time.sleep(0.5)

gua_all = {r["date"]: r for r in gua_store}
for r in gua_bapi:
    gua_all[r["date"]] = r
gua_rows = sorted(gua_all.values(), key=lambda r: r["date"])
gua_rows = [r for r in gua_rows if DATE_START <= r["date"] <= DATE_END]
print(f"  Final: {len(gua_rows)} rows {gua_rows[0]['date'] if gua_rows else 'N/A'} → {gua_rows[-1]['date'] if gua_rows else 'N/A'}")

write_csv(gua_rows, SCRATCH / "spot_klines_GUA_20260817.csv")

# ─────────────────────────────────────────────────────────────────────────────
# APR — KuCoin full range
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("APR klines (KuCoin — wash_suspect_flag=True)")
print("=" * 60)

print(f"  Fetching KuCoin {DATE_START} → {DATE_END}...")
apr_rows = fetch_kucoin_klines("APR", DATE_START, DATE_END)
print(f"  KuCoin rows: {len(apr_rows)}")
if apr_rows:
    print(f"  Range: {apr_rows[0]['date']} → {apr_rows[-1]['date']}")

write_csv(apr_rows, SCRATCH / "spot_klines_APR_20260817.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Quick spot-check
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SPOT-CHECK: last 3 rows per token")
print("=" * 60)

for sym, rows in [("AIN", ain_rows), ("GUA", gua_rows), ("APR", apr_rows)]:
    print(f"\n  {sym}:")
    for r in rows[-3:]:
        qv = float(r["quote_vol"]) if r["quote_vol"] else 0
        print(f"    {r['date']} close={r['close']} quote_vol={qv:,.0f} venue={r['venue']}")

print("\n[DONE S-4]")
