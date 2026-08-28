"""B1-B4 SPOT-51 backfill one-shot.
- B1: Fetch full-history 1d klines Binance spot cho 51 token (S6 map has_binance_spot=YES).
      venue=binance_spot · schema hiện có · taker_abstain=False (spot k[9]/k[5] KHÔNG mirror-broken).
- B2: STALE-GUARD embedded (report N/A-STALE nếu store >2d stale).
- B3: Coverage manifest CSV per-token (first/last/n_rows/gaps + N/A-SOURCE nếu fail).
- B4: 3 sample rows TUT mới nhất.
Sanity TUT: kỳ vọng ~518+ bars, đối chiếu S3 md5 1929aa67.
"""
import sys, io, json, urllib.request, time, csv, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
STORE.mkdir(parents=True, exist_ok=True)

TOKEN_LIST_FP = SCRATCH / "s6_fw139_binance_spot_map_20260827.csv"
COVERAGE_FP = SCRATCH / "spot51_coverage_manifest_20260828.csv"

SCHEMA_VERSION = 1  # int64 to match existing binance_alpha rows in store
D_TODAY = "2026-08-28"
D_MINUS_1 = "2026-08-27"

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
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")

def fetch_full_klines(sym_pair):
    """Fetch full-history 1d klines Binance spot (paginate)."""
    all_bars = []
    start_ms = 0
    while True:
        d = fetch_json("https://api.binance.com/api/v3/klines",
                       {"symbol":sym_pair,"interval":"1d","startTime":start_ms,"limit":1000})
        time.sleep(0.15)
        if not isinstance(d, list) or not d:
            if isinstance(d, dict) and "_error" in d:
                return None, d["_error"]
            break
        all_bars.extend(d)
        last_open = int(d[-1][0])
        if len(d) < 1000: break
        # Next start = last_open + 1 day
        start_ms = last_open + 86400000
        # Guard: if we've reached today's open, stop
        if start_ms > int(datetime.now(timezone.utc).timestamp()*1000):
            break
    return all_bars, None

# ── Load 51-token list ──
tokens = []
with open(TOKEN_LIST_FP, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row.get("has_binance_spot") == "YES":
            tokens.append(row["symbol"] + "USDT")
print(f"51-token list loaded: {len(tokens)} pairs")

# ── B1 Fetch ──
print(f"\n{'='*70}\nB1 FETCH — {len(tokens)} tokens x public REST\n{'='*70}")
all_rows = []       # unified list of dicts
per_token_stats = {}
for i, pair in enumerate(tokens):
    bars, err = fetch_full_klines(pair)
    if err or not bars:
        print(f"  [{i+1}/{len(tokens)}] {pair}: FAIL ({err or 'no data'})")
        per_token_stats[pair] = {"status":"N/A-SOURCE", "n_rows":0, "first":None, "last":None, "err":err}
        continue
    # Build rows
    fetched_at = int(datetime.now(timezone.utc).timestamp()*1000)
    for k in bars:
        # klines format: [open_time, o, h, l, c, base_vol, close_time, quote_vol,
        #                 n_trades, taker_buy_base, taker_buy_quote, ignore]
        ts = int(k[0]); ds = ms_to_date(ts)
        # Skip today's open candle (incomplete)
        if ds >= D_TODAY: continue
        base_vol = float(k[5]); quote_vol = float(k[7])
        taker_buy_base = float(k[9]); taker_buy_quote = float(k[10])
        taker_pct = (taker_buy_quote / quote_vol * 100) if quote_vol > 0 else None
        all_rows.append({
            "symbol": pair, "date_str": ds,
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]), "close": float(k[4]),
            "base_vol": base_vol, "quote_vol": quote_vol,
            "n_trades": int(k[8]),
            "taker_buy_base_vol": taker_buy_base, "taker_buy_quote_vol": taker_buy_quote,
            "taker_buy_pct": taker_pct,
            "venue": "binance_spot",
            "taker_abstain": False,
            "fetched_at_ms": fetched_at,
            "schema_version": SCHEMA_VERSION,
        })
    dates = [ms_to_date(int(k[0])) for k in bars if ms_to_date(int(k[0])) < D_TODAY]
    if dates:
        per_token_stats[pair] = {"status":"OK", "n_rows":len(dates), "first":min(dates), "last":max(dates), "err":None}
        print(f"  [{i+1}/{len(tokens)}] {pair}: {len(dates)} bars ({min(dates)}→{max(dates)})")
    else:
        per_token_stats[pair] = {"status":"N/A-SOURCE", "n_rows":0, "first":None, "last":None, "err":"no dates"}

print(f"\nTotal rows fetched: {len(all_rows)}")

# ── B1 Write to partitioned parquet (per-date, merge with existing binance_alpha rows) ──
print(f"\n{'='*70}\nB1 WRITE — partitioned parquet (append binance_spot cạnh binance_alpha)\n{'='*70}")

df_all = pd.DataFrame(all_rows)
if df_all.empty:
    print("  NO ROWS — abort write")
else:
    dates_written = 0
    dates_group = df_all.groupby("date_str")
    for ds, g in dates_group:
        p = STORE / f"date={ds}" / "part-0.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            existing = pd.read_parquet(p)
            # Dedup: keep existing rows unless overlapping (symbol, venue) — for binance_spot new, keep new
            # Remove any existing rows with venue=binance_spot for these symbols (to avoid dupes on rerun)
            mask = ~((existing["venue"] == "binance_spot") & (existing["symbol"].isin(g["symbol"])))
            merged = pd.concat([existing[mask], g], ignore_index=True)
        else:
            merged = g
        table = pa.Table.from_pandas(merged, preserve_index=False)
        pq.write_table(table, p, compression="snappy")
        dates_written += 1
    print(f"  dates written: {dates_written} partition files (merge preserved existing binance_alpha)")

# ── B3 Coverage manifest ──
print(f"\n{'='*70}\nB3 COVERAGE MANIFEST\n{'='*70}")
gap_check = {}
for pair, s in per_token_stats.items():
    if s["status"] != "OK":
        gap_check[pair] = {"gaps": [], "gap_count": 0}
        continue
    # Fetch all dates for this symbol from all_rows
    dates = sorted(r["date_str"] for r in all_rows if r["symbol"] == pair)
    date_set = set(dates)
    d_first = _date.fromisoformat(dates[0])
    d_last = _date.fromisoformat(dates[-1])
    all_days = set()
    d_cur = d_first
    while d_cur <= d_last:
        all_days.add(d_cur.isoformat())
        d_cur += timedelta(days=1)
    gaps = sorted(all_days - date_set)
    gap_check[pair] = {"gaps": gaps, "gap_count": len(gaps)}

with open(COVERAGE_FP, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["symbol","status","n_rows","first_date","last_date","gap_count","gap_dates_sample","err"])
    for pair in tokens:
        s = per_token_stats.get(pair, {"status":"N/A-SOURCE","n_rows":0,"first":None,"last":None,"err":"not_fetched"})
        g = gap_check.get(pair, {"gap_count":0, "gaps":[]})
        sample = ";".join(g["gaps"][:5]) + (" ..." if g["gap_count"]>5 else "")
        w.writerow([pair, s["status"], s["n_rows"], s.get("first") or "",
                    s.get("last") or "", g["gap_count"], sample, s.get("err") or ""])

md5_manifest = hashlib.md5(COVERAGE_FP.read_bytes()).hexdigest()
n_manifest = sum(1 for _ in open(COVERAGE_FP, encoding="utf-8"))
print(f"  Manifest: {COVERAGE_FP.name} · wc-l={n_manifest} · md5={md5_manifest}")

n_ok = sum(1 for s in per_token_stats.values() if s["status"]=="OK")
n_fail = sum(1 for s in per_token_stats.values() if s["status"]=="N/A-SOURCE")
print(f"  OK: {n_ok}/{len(tokens)} · N/A-SOURCE: {n_fail}")

# ── B2 STALE-GUARD design + cron ──
print(f"\n{'='*70}\nB2 STALE-GUARD + CRON WIRE\n{'='*70}")
print(f"""
Cron design (Windows Task Scheduler):
  Trigger: DAILY 01:05 UTC (sau nến 1d đóng 00:00 UTC + 5min guard)
  Action:  cd D:\\Data back test\\whale_data ^&^& python scripts\\collect_spot_daily.py

STALE-GUARD embedded (in consumers, không chặn collect):
  before render nhãn spot_cvd/ma_shadow:
    last_partition_date = max(dates in data/raw/spot_klines_1d/date=*)
    days_stale = (today_utc - last_partition_date).days
    if days_stale > 2:
      render N/A-STALE (last={last_partition_date}, {days_stale}d stale)
      DO NOT compute imb/pos_days trên data cũ

Cron line (Windows schtasks):
  schtasks /Create /SC DAILY /TN "SpotCollect51Daily" /TR ^
    "cd /D \\"D:\\Data back test\\whale_data\\" && python scripts\\collect_spot_daily.py" ^
    /ST 01:05 /RL LIMITED
""")

# ── B4 3 sample TUT rows ──
print(f"\n{'='*70}\nB4 3 SAMPLE TUT ROWS (mới nhất)\n{'='*70}")
tut_rows = sorted([r for r in all_rows if r["symbol"]=="TUTUSDT"], key=lambda x: x["date_str"], reverse=True)[:3]
for r in tut_rows:
    print(f"  {r['date_str']}: o={r['open']:.6g} h={r['high']:.6g} l={r['low']:.6g} c={r['close']:.6g} · "
          f"quote_vol=${r['quote_vol']:,.0f} · taker_pct={r['taker_buy_pct']:.2f}% · venue={r['venue']}")

# TUT total bars for sanity check vs S3 md5 1929aa67 (S3 had 518 bars 2025-03-27→2026-08-26)
tut_all = [r for r in all_rows if r["symbol"]=="TUTUSDT"]
print(f"\nTUT total bars: {len(tut_all)} (S3 previous: 518 bars 2025-03-27→2026-08-26)")
if tut_all:
    dates = sorted(r["date_str"] for r in tut_all)
    print(f"TUT range: {dates[0]} → {dates[-1]}")

# STALE check on new store
latest_partition = max([p.name.replace("date=","") for p in STORE.iterdir() if p.name.startswith("date=")])
days_stale = (_date.fromisoformat(D_TODAY) - _date.fromisoformat(latest_partition)).days
print(f"\nStore latest partition: {latest_partition} · today={D_TODAY} · days_stale={days_stale} " +
      ("✓ FRESH" if days_stale <= 2 else "⚠ STALE"))

print(f"\n[DONE B1-B4]")
