"""Retry 2 failed tokens (EDENUSDT · ZKPUSDT) + comprehensive verify."""
import sys, io, json, urllib.request, time, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
D_TODAY = "2026-08-28"
SCHEMA_VERSION = 1

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
    all_bars = []; start_ms = 0
    while True:
        d = fetch_json("https://api.binance.com/api/v3/klines",
                       {"symbol":sym_pair,"interval":"1d","startTime":start_ms,"limit":1000})
        time.sleep(0.3)
        if not isinstance(d, list) or not d:
            if isinstance(d, dict) and "_error" in d: return None, d["_error"]
            break
        all_bars.extend(d)
        last_open = int(d[-1][0])
        if len(d) < 1000: break
        start_ms = last_open + 86400000
        if start_ms > int(datetime.now(timezone.utc).timestamp()*1000): break
    return all_bars, None

# ── Retry 2 tokens with backoff ──
RETRY_PAIRS = ["EDENUSDT", "ZKPUSDT"]
print(f"[RETRY] {len(RETRY_PAIRS)} tokens")
retry_rows = []; retry_stats = {}
for pair in RETRY_PAIRS:
    for attempt in range(3):
        bars, err = fetch_full_klines(pair)
        if bars: break
        print(f"  {pair} attempt {attempt+1}/3 fail: {err}")
        time.sleep(2 ** attempt)
    if not bars:
        retry_stats[pair] = "N/A-FETCH"; continue
    fetched_at = int(datetime.now(timezone.utc).timestamp()*1000)
    for k in bars:
        ts = int(k[0]); ds = ms_to_date(ts)
        if ds >= D_TODAY: continue
        base_vol = float(k[5]); quote_vol = float(k[7])
        tb_base = float(k[9]); tb_quote = float(k[10])
        taker_pct = (tb_quote/quote_vol*100) if quote_vol > 0 else None
        retry_rows.append({
            "symbol": pair, "date_str": ds,
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]), "close": float(k[4]),
            "base_vol": base_vol, "quote_vol": quote_vol, "n_trades": int(k[8]),
            "taker_buy_base_vol": tb_base, "taker_buy_quote_vol": tb_quote,
            "taker_buy_pct": taker_pct,
            "venue": "binance_spot", "taker_abstain": False,
            "fetched_at_ms": fetched_at, "schema_version": SCHEMA_VERSION,
        })
    dates = [r["date_str"] for r in retry_rows if r["symbol"]==pair]
    retry_stats[pair] = f"OK n={len(dates)} {min(dates)}→{max(dates)}"
    print(f"  {pair}: {retry_stats[pair]}")

if retry_rows:
    df_retry = pd.DataFrame(retry_rows)
    for ds, g in df_retry.groupby("date_str"):
        p = STORE / f"date={ds}" / "part-0.parquet"
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            existing = pd.read_parquet(p)
            mask = ~((existing["venue"]=="binance_spot") & (existing["symbol"].isin(g["symbol"])))
            merged = pd.concat([existing[mask], g], ignore_index=True)
        else:
            merged = g
        pq.write_table(pa.Table.from_pandas(merged, preserve_index=False), p, compression="snappy")
    print(f"  Written retry rows to {len(df_retry.groupby('date_str'))} partitions")

# ── B4-COMPREHENSIVE VERIFY ──
print(f"\n{'='*70}\nB4 COMPREHENSIVE VERIFY\n{'='*70}")

files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
print(f"Store partitions: {len(files)}")

# Aggregate per-symbol stats for binance_spot venue
per_sym = {}
for f in files:
    df = pd.read_parquet(f, columns=["symbol","venue","date_str","taker_buy_pct"])
    df_spot = df[df["venue"]=="binance_spot"]
    for sym in df_spot["symbol"].unique():
        rows = df_spot[df_spot["symbol"]==sym]
        if sym not in per_sym: per_sym[sym] = {"dates":[], "taker_nonan":0, "taker_total":0}
        per_sym[sym]["dates"].extend(rows["date_str"].tolist())
        per_sym[sym]["taker_nonan"] += rows["taker_buy_pct"].notna().sum()
        per_sym[sym]["taker_total"] += len(rows)

# Print verify table
print(f"\n{'token':<14} {'n_rows':>7} {'first_date':<12} {'last_date':<12} {'taker_nonNaN%':>14}")
print('-'*62)
rows_sorted = sorted(per_sym.items())
n_ok = 0; sum_rows = 0
for sym, s in rows_sorted:
    dates = sorted(set(s["dates"]))
    first = dates[0] if dates else "—"; last = dates[-1] if dates else "—"
    pct = (s["taker_nonan"]/s["taker_total"]*100) if s["taker_total"] else 0.0
    print(f"{sym:<14} {len(dates):>7} {first:<12} {last:<12} {pct:>13.1f}%")
    n_ok += 1; sum_rows += len(dates)
print('-'*62)
print(f"TOTAL: {n_ok} tokens · {sum_rows} rows")

# Sample partition md5s
print(f"\nSample partition md5s:")
for pn in ["date=2025-04-10", "date=2026-01-01", "date=2026-08-27"]:
    p = STORE / pn / "part-0.parquet"
    if p.exists():
        m = hashlib.md5(p.read_bytes()).hexdigest()
        df = pd.read_parquet(p)
        vc = df["venue"].value_counts().to_dict()
        print(f"  {pn}: md5={m} · rows={len(df)} · venues={vc}")

# TUT verify (positive-pin D4 candidate)
print(f"\nTUT positive-pin verify:")
tut_dates = sorted(set(per_sym.get("TUTUSDT", {}).get("dates", [])))
print(f"  TUT range: {tut_dates[0] if tut_dates else 'N/A'} → {tut_dates[-1] if tut_dates else 'N/A'} · n={len(tut_dates)}")
print(f"  TUT taker non-NaN: {per_sym.get('TUTUSDT',{}).get('taker_nonan',0)}/{per_sym.get('TUTUSDT',{}).get('taker_total',0)}")
