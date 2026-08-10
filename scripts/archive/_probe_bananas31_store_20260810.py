"""Item (4): BANANAS31 data store verify — prep for GATE 15/08.

Check all required data series exist and are complete:
- freshwatch_daily_*.csv: px_avg / oi_usd / lsr_* / taker_ratio / funding_avg
- data/raw/spot_klines_1d: BANANAS31 alpha klines
- Date coverage from earliest available → 2026-08-09

data-source: VPS canonical store + local alpha klines
machine: VPS via SSH + local
date-range: earliest → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, csv, subprocess, json, os
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
ROOT = Path(r"D:\Data back test\whale_data")
SYM_PERP  = "BANANAS31USDT"
SYM_BASE  = "BANANAS31"
SYM_LOWER = "bananas31"
CHECK_COLS = ["px_avg", "vol_quote", "taker_buy_pct", "funding_avg",
              "oi_usd", "lsr_pos_r", "lsr_acc_r", "lsr_global_r", "taker_ratio"]

def is_null(v):
    return v is None or str(v).strip() in ("", "nan", "None", "N/A")

def ssh_cat(remote_path: str) -> list[str] | None:
    r = subprocess.run(["ssh", VPS, f"cat {remote_path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None
    return r.stdout.splitlines()

print(f"=== BANANAS31 STORE VERIFY — gate prep 15/08 ===\n")

# ── 1. Freshwatch CSV coverage ────────────────────────────────────────────────
print("=== [1] FRESHWATCH CSV — VPS canonical ===")
months = ["2026-06", "2026-07", "2026-08"]
all_fw_rows: list[dict] = []
for mo in months:
    path = f"/root/Data_back_test/whale_data/data/export/freshwatch_daily_{mo}.csv"
    lines = ssh_cat(path)
    if lines is None:
        print(f"  {mo}: NOT FOUND on VPS")
        continue
    rows = [r for r in csv.DictReader(lines) if r.get("symbol") == SYM_PERP]
    dates = sorted(set(r["date"] for r in rows))
    print(f"  {mo}: {len(rows)} BANANAS31 rows | dates: {dates[0] if dates else '?'} → {dates[-1] if dates else '?'}")
    all_fw_rows.extend(rows)

if all_fw_rows:
    all_fw_rows.sort(key=lambda r: r.get("date",""))
    print(f"\n  Total: {len(all_fw_rows)} rows | {all_fw_rows[0]['date']} → {all_fw_rows[-1]['date']}")

    # Null check per column
    n = len(all_fw_rows)
    print(f"\n  NULL% per column ({n} rows):")
    any_issue = False
    for c in CHECK_COLS:
        nulls = sum(1 for r in all_fw_rows if is_null(r.get(c)))
        pct = nulls/n*100
        flag = " ⚠" if pct > 50 else (" !" if pct > 0 else " ✓")
        if pct > 0:
            any_issue = True
        print(f"    {c:<18}: {nulls:>5}/{n} = {pct:.0f}%{flag}")

    # Gap check
    all_dates = sorted(set(r["date"] for r in all_fw_rows))
    if all_dates:
        gaps = []
        cur = datetime.strptime(all_dates[0], "%Y-%m-%d")
        for d in all_dates[1:]:
            nxt = datetime.strptime(d, "%Y-%m-%d")
            diff = (nxt - cur).days
            if diff > 1:
                gaps.append((cur.strftime("%Y-%m-%d"), d, diff))
            cur = nxt
        if gaps:
            print(f"\n  GAPS ({len(gaps)}):")
            for g_from, g_to, g_days in gaps:
                print(f"    {g_from} → {g_to}: {g_days} days gap")
        else:
            print(f"\n  Gaps: NONE ✓")
else:
    print("  NO BANANAS31 rows found in freshwatch CSVs")

# ── 2. Alpha klines store (local) ─────────────────────────────────────────────
print(f"\n=== [2] ALPHA KLINES STORE — local spot_klines_1d ===")
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
if not alpha_store.exists():
    print(f"  Store dir NOT FOUND: {alpha_store}")
else:
    # Alpha uses base-USDT partition by date
    # Find parquet files for BANANAS31
    import glob as _glob
    # Check common partition patterns
    patterns = [
        f"**/*BANANAS31*.parquet",
        f"**/*bananas31*.parquet",
        f"**/venue=binance_alpha/**/*.parquet",
    ]
    alpha_files = []
    for pat in patterns[:2]:  # only specific BANANAS31 patterns first
        found = list(alpha_store.glob(pat))
        alpha_files.extend(found)
    alpha_files = list(set(alpha_files))

    if not alpha_files:
        # Try reading a parquet to see structure
        all_parquets = list(alpha_store.glob("**/*.parquet"))
        print(f"  No BANANAS31-specific parquet found. Store has {len(all_parquets)} total parquet files")
        if all_parquets:
            # Show first few
            sample = sorted(str(f) for f in all_parquets[:3])
            for s in sample:
                print(f"    {s}")
    else:
        print(f"  Found {len(alpha_files)} BANANAS31 parquet files")
        for f in sorted(alpha_files)[:5]:
            print(f"    {f} ({f.stat().st_size:,} bytes)")

    # Try to read via pandas if available
    try:
        import pandas as pd
        # Find all parquet files for alpha venue
        all_parquets = list(alpha_store.glob("venue=binance_alpha/**/*.parquet"))
        if all_parquets:
            # Read a sample to find BANANAS31
            frames = []
            for pq in all_parquets:
                try:
                    df = pd.read_parquet(pq)
                    if "symbol" in df.columns:
                        sub = df[df["symbol"].str.contains("BANANAS31", na=False)]
                    else:
                        # May be partitioned, symbol in path
                        sub = df
                    if not sub.empty:
                        frames.append(sub)
                except Exception:
                    pass
            if frames:
                df_b = pd.concat(frames, ignore_index=True)
                if "date" in df_b.columns or "open_time" in df_b.columns:
                    dt_col = "date" if "date" in df_b.columns else "open_time"
                    df_b[dt_col] = pd.to_datetime(df_b[dt_col])
                    df_b = df_b.sort_values(dt_col)
                    print(f"\n  BANANAS31 alpha klines: {len(df_b)} candles")
                    print(f"  Range: {df_b[dt_col].min().date()} → {df_b[dt_col].max().date()}")
                    print(f"  Cols: {list(df_b.columns)[:10]}")
            else:
                print(f"  No BANANAS31 rows found across {len(all_parquets)} parquet files in binance_alpha venue")
    except ImportError:
        print("  pandas not available for parquet read")
    except Exception as e:
        print(f"  parquet read error: {e}")

# ── 3. VPS alpha klines store ─────────────────────────────────────────────────
print(f"\n=== [3] VPS ALPHA KLINES — spot_klines_1d ===")
r = subprocess.run(
    ["ssh", VPS,
     f"find /root/Data_back_test/whale_data/data/raw/spot_klines_1d -name '*.parquet' | xargs grep -l 'BANANAS31' 2>/dev/null | head -5; "
     f"ls /root/Data_back_test/whale_data/data/raw/spot_klines_1d/ 2>/dev/null | head -10"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(f"  VPS store listing:\n{r.stdout[:800]}")

# ── 4. GOM state — BANANAS31 ─────────────────────────────────────────────────
print(f"\n=== [4] GOM STATE — BANANAS31 ===")
r2 = subprocess.run(
    ["ssh", VPS,
     f"python3 -c \"import json; s=json.load(open('/root/Data_back_test/whale_data/data/gom_state.json')); b=s.get('BANANAS31',{{}}); print(json.dumps({{k:v for k,v in b.items() if k!='days'}}, indent=2, default=str))\""],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if r2.stdout.strip():
    print(r2.stdout[:1000])
else:
    print(f"  BANANAS31 not in gom_state (or error): {r2.stderr[:200]}")

# ── 5. Summary ────────────────────────────────────────────────────────────────
print(f"\n=== VERDICT ===")
print(f"Check the above. GATE 15/08 requires:")
print(f"  [A] freshwatch: all lsr/oi/taker cols non-null for BANANAS31 throughout history")
print(f"  [B] gap check PASS (no multi-day gaps in date range)")
print(f"  [C] gom_state: close_date present (BANANAS31 had a GOM chain that closed)")
print(f"  [D] TASKS.md PASS-definition frozen — verify line-by-line")
