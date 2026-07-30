#!/usr/bin/env python3
"""So sánh native_1d vs derived_1h (00:00 UTC) vs keep-last (23:00 UTC)
cho 5 symbol × 07-24→07-29 để xác định boundary của Binance native_1d.
Cũng probe OI boundary."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import subprocess, tempfile, os

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

probe = r'''
import pandas as pd
from pathlib import Path
import datetime

DATA = Path("/root/Data_back_test/whale_data/data/raw")
SYMBOLS = ["BULLAUSDT", "TAGUSDT", "BANKUSDT", "BASEDUSDT", "POWERUSDT"]
DATES = ["2026-07-24","2026-07-25","2026-07-26","2026-07-27","2026-07-28","2026-07-29"]

def ts_to_utc(ms: int) -> str:
    return datetime.datetime.utcfromtimestamp(ms/1000).strftime("%m-%d %H:%M")

def midnight_ms(date_str: str) -> int:
    """00:00 UTC of date_str."""
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    return int(d.timestamp() * 1000)

# Cache parquets
tp1h_cache: dict[str,pd.DataFrame] = {}
tp1d_cache: dict[str,pd.DataFrame] = {}

def load_1h(date_str: str) -> pd.DataFrame:
    if date_str not in tp1h_cache:
        p = DATA / "top_pos_1h" / f"date={date_str}" / "part-0.parquet"
        tp1h_cache[date_str] = pd.read_parquet(p) if p.exists() else pd.DataFrame()
    return tp1h_cache[date_str]

def load_1d(date_str: str) -> pd.DataFrame:
    if date_str not in tp1d_cache:
        p = DATA / "top_pos_1d" / f"date={date_str}" / "part-0.parquet"
        tp1d_cache[date_str] = pd.read_parquet(p) if p.exists() else pd.DataFrame()
    return tp1d_cache[date_str]

print("=== PART 1: native_1d vs derived_1h (00:00 UTC) vs keep-last (23:xx UTC) ===\n")
print(f"{'Symbol':<14} {'Date':<12} {'native_1d':>10} {'00:00-UTC':>10} {'keep-last':>10} {'ts_native':>14} {'d(n-0h)%':>9} {'d(n-kl)%':>9}")
print("-" * 100)

rows_out = []
for sym in SYMBOLS:
    for date_str in DATES:
        df1d = load_1d(date_str)
        df1h = load_1h(date_str)

        # native_1d value
        native_val = None
        native_ts = None
        if not df1d.empty:
            row = df1d[df1d["symbol"] == sym]
            if not row.empty:
                native_val = float(row.iloc[0]["long_short_ratio"])
                if "as_of_ts_ms" in row.columns:
                    native_ts = int(row.iloc[0]["as_of_ts_ms"])

        # derived_1h = snapshot at 00:00 UTC of date_str
        mid_ms = midnight_ms(date_str)
        h00_val = None
        if not df1h.empty:
            snap = df1h[(df1h["symbol"] == sym) & (df1h["as_of_ts_ms"] == mid_ms)]
            if not snap.empty:
                h00_val = float(snap.iloc[0]["long_short_ratio"])

        # keep-last = max as_of_ts_ms of date_str
        kl_val = None
        kl_ts_str = None
        if not df1h.empty:
            sym_rows = df1h[df1h["symbol"] == sym].sort_values("as_of_ts_ms")
            if not sym_rows.empty:
                last = sym_rows.iloc[-1]
                kl_val = float(last["long_short_ratio"])
                kl_ts_str = ts_to_utc(int(last["as_of_ts_ms"]))

        # Diffs
        def pct(a, b):
            if a is None or b is None: return None
            return 100*(a-b)/b if b != 0 else None

        d_n_h00 = pct(native_val, h00_val)
        d_n_kl  = pct(native_val, kl_val)

        n_str   = f"{native_val:.4f}" if native_val is not None else "N/A"
        h_str   = f"{h00_val:.4f}"   if h00_val   is not None else "N/A"
        kl_str  = f"{kl_val:.4f}"    if kl_val    is not None else "N/A"
        ts_str  = ts_to_utc(native_ts) if native_ts else "N/A"
        dh_str  = f"{d_n_h00:+.2f}%" if d_n_h00 is not None else "N/A"
        dk_str  = f"{d_n_kl:+.2f}%"  if d_n_kl  is not None else "N/A"

        print(f"{sym:<14} {date_str:<12} {n_str:>10} {h_str:>10} {kl_str:>10} {ts_str:>14} {dh_str:>9} {dk_str:>9}")
        rows_out.append({
            "sym": sym, "date": date_str,
            "native": native_val, "h00": h00_val, "kl": kl_val,
            "native_ts_ms": native_ts,
            "d_n_h00": d_n_h00, "d_n_kl": d_n_kl,
        })

# Summary: avg abs diff
valid_h00 = [r for r in rows_out if r["d_n_h00"] is not None]
valid_kl  = [r for r in rows_out if r["d_n_kl"]  is not None]
if valid_h00:
    avg_h00 = sum(abs(r["d_n_h00"]) for r in valid_h00) / len(valid_h00)
    print(f"\n>> Avg |native - 00:00 UTC| = {avg_h00:.3f}% (n={len(valid_h00)})")
if valid_kl:
    avg_kl = sum(abs(r["d_n_kl"]) for r in valid_kl) / len(valid_kl)
    print(f">> Avg |native - keep-last| = {avg_kl:.3f}% (n={len(valid_kl)})")

# native_ts analysis
native_timestamps = [(r["sym"], r["date"], r["native_ts_ms"]) for r in rows_out if r["native_ts_ms"]]
if native_timestamps:
    print("\n=== native_1d as_of_ts_ms values ===")
    seen_ts = set()
    for sym, date_str, ts_ms in native_timestamps[:15]:
        ts_str = ts_to_utc(ts_ms)
        if ts_ms not in seen_ts:
            seen_ts.add(ts_ms)
            print(f"  {sym} {date_str}: as_of_ts_ms={ts_ms} => {ts_str} UTC")

print("\n=== PART 2: OI boundary check ===")
# Check oi_hist_1d for OI native_1d value and timestamp
oi1d_dir = DATA / "oi_hist_1d"
if oi1d_dir.exists():
    dates_oi = sorted([d.name for d in oi1d_dir.iterdir() if d.is_dir()])
    print(f"oi_hist_1d available dates: {dates_oi}")
    for date_str in ["2026-07-24","2026-07-25"]:
        p = oi1d_dir / f"date={date_str}" / "part-0.parquet"
        if p.exists():
            df_oi = pd.read_parquet(p)
            for sym in ["BULLAUSDT","TAGUSDT"]:
                row = df_oi[df_oi["symbol"] == sym]
                if not row.empty:
                    ts_ms = int(row.iloc[0].get("as_of_ts_ms", 0))
                    oi_v  = row.iloc[0].get("sum_open_interest_value", "N/A")
                    print(f"  oi_hist_1d {date_str} {sym}: OI={oi_v:.0f}, as_of_ts_ms={ts_ms} ({ts_to_utc(ts_ms) if ts_ms else 'N/A'} UTC)")
else:
    print("oi_hist_1d: directory not found")

# Check oi_hist_1h boundary for comparison
oi1h_dir = DATA / "oi_hist_1h"
for date_str in ["2026-07-24"]:
    p = oi1h_dir / f"date={date_str}" / "part-0.parquet"
    if p.exists():
        df_oi1h = pd.read_parquet(p)
        mid_ms = midnight_ms(date_str)
        for sym in ["BULLAUSDT"]:
            # midnight snapshot
            snap = df_oi1h[(df_oi1h["symbol"]==sym) & (df_oi1h["as_of_ts_ms"]==mid_ms)]
            kl   = df_oi1h[df_oi1h["symbol"]==sym].sort_values("as_of_ts_ms").tail(1)
            if not snap.empty:
                print(f"  oi_hist_1h {date_str} {sym} 00:00 UTC: OI={snap.iloc[0].get('sum_open_interest_value','N/A'):.0f}")
            if not kl.empty:
                kl_ts = int(kl.iloc[0]["as_of_ts_ms"])
                print(f"  oi_hist_1h {date_str} {sym} keep-last ({ts_to_utc(kl_ts)} UTC): OI={kl.iloc[0].get('sum_open_interest_value','N/A'):.0f}")
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(probe)
    tmp = f.name

r = subprocess.run(
    ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", tmp,
     "root@5.223.67.21:/tmp/probe_ratio_boundary.py"],
    capture_output=True
)
os.unlink(tmp)
print(f"SCP: {'OK' if r.returncode == 0 else r.stderr.decode()}")

result = subprocess.run(
    ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST,
     "cd /root/Data_back_test/whale_data && python3 /tmp/probe_ratio_boundary.py 2>&1"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])
