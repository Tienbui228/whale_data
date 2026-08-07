#!/usr/bin/env python3
"""Task 3b: fapi backfill funding 24-26/07 × 139 syms + fix oi_usd column + re-regen CSV.

Steps:
  1. On VPS: fetch /fapi/v1/fundingRate for each freshwatch symbol × 3 dates → JSON
  2. On VPS: re-run regen aggregation with correct oi column + funding live
  3. SCP result back → inject into fw137_test July CSV (replace existing 24-26/07 rows)
"""
import sys, subprocess, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd

REPO      = Path(__file__).resolve().parent
FW137_DIR = REPO / "scratch" / "fw137_test"
VPS       = "root@5.223.67.21"
BASE      = "/root/Data_back_test/whale_data"
FW_SYM    = REPO / "scratch" / "freshwatch_symbols.txt"

def ssh(cmd, timeout=180):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# ── VPS script: fapi fetch + regen with corrected columns ────────────────────
VPS_SCRIPT = r'''#!/usr/bin/env python3
"""VPS: fetch fapi funding 24-26/07 + regen daily rows with oi_usd fix."""
import sys, glob, json, math, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
import numpy as np
import urllib.request

BASE  = "/root/Data_back_test/whale_data"
DATES = ["2026-07-24", "2026-07-25", "2026-07-26"]
FW_SYM_PATH = BASE + "/data/config/freshwatch_symbols.txt"
FAPI = "https://fapi.binance.com"

with open(FW_SYM_PATH, encoding="utf-8") as f:
    fw_syms = sorted(set(l.strip() for l in f if l.strip()))
print(f"universe: {len(fw_syms)} symbols")

def load_store_date(store, date):
    path = f"{BASE}/data/raw/{store}/date={date}/*.parquet"
    files = glob.glob(path)
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_parquet(f))
        except Exception as e:
            print(f"  WARN: {f}: {e}", file=sys.stderr)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def fapi_get(url, params="", retries=3):
    full = url + ("?" + params if params else "")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(2 * (attempt + 1))
    return None

# ── Step 1: Fetch fapi funding rates for 24-26/07 ──────────────────────────
print("\n=== Fetching fapi funding rates 24-26/07 ===")

# Date boundaries in ms
def date_to_ms(d):
    from datetime import datetime, timezone
    return int(datetime(*(int(x) for x in d.split("-")), tzinfo=timezone.utc).timestamp() * 1000)

funding_rows = []
for sym in fw_syms:
    for date in DATES:
        start_ms = date_to_ms(date)
        end_ms   = start_ms + 86400_000  # +24h
        data = fapi_get(
            f"{FAPI}/fapi/v1/fundingRate",
            f"symbol={sym}&startTime={start_ms}&endTime={end_ms}&limit=100"
        )
        if data and isinstance(data, list):
            for row in data:
                funding_rows.append({
                    "symbol": sym,
                    "date": date,
                    "fundingRate": float(row.get("fundingRate", float("nan"))),
                    "fundingTime": row.get("fundingTime", 0),
                })

df_fn = pd.DataFrame(funding_rows) if funding_rows else pd.DataFrame()
print(f"Fetched {len(df_fn)} funding rows, {df_fn['symbol'].nunique() if not df_fn.empty else 0} syms")
if not df_fn.empty:
    print(df_fn.groupby("date")["symbol"].count())

# ── Step 2: Regen with corrected column mappings ────────────────────────────
print("\n=== Regen daily rows ===")

all_rows = []
for date in DATES:
    print(f"\n--- {date} ---")

    kl = load_store_date("klines_1h", date)
    if not kl.empty and "symbol" in kl.columns:
        kl = kl[kl["symbol"].isin(fw_syms)]
    print(f"  klines_1h: {len(kl)} rows, {kl['symbol'].nunique() if not kl.empty else 0} syms")

    pos = load_store_date("top_pos_1h", date)
    if not pos.empty and "symbol" in pos.columns:
        pos = pos[pos["symbol"].isin(fw_syms)]

    # oi_hist_1h — correct column: sum_open_interest_value
    oi = load_store_date("oi_hist_1h", date)
    if not oi.empty and "symbol" in oi.columns:
        oi = oi[oi["symbol"].isin(fw_syms)]
    if not oi.empty:
        # Detect correct OI column
        oi_col_candidates = ["sum_open_interest_value", "sumOpenInterestValue", "oi_usd", "openInterestUsd"]
        oi_col = next((c for c in oi_col_candidates if c in oi.columns), None)
        print(f"  oi_hist_1h: {len(oi)} rows | oi_col={oi_col} | cols: {list(oi.columns)[:8]}")
    else:
        oi_col = None
        print("  oi_hist_1h: EMPTY")

    ta = load_store_date("top_acct_1h", date)
    if not ta.empty and "symbol" in ta.columns:
        ta = ta[ta["symbol"].isin(fw_syms)]

    if kl.empty:
        print(f"  SKIP {date}: no klines_1h")
        continue

    fn_date = df_fn[df_fn["date"] == date] if not df_fn.empty else pd.DataFrame()

    for sym in kl["symbol"].unique():
        kl_s = kl[kl["symbol"] == sym]

        # VWAP
        qv  = kl_s["quote_volume"].fillna(0) if "quote_volume" in kl_s.columns else pd.Series([0]*len(kl_s))
        cl  = kl_s["close"].fillna(float("nan")) if "close" in kl_s.columns else pd.Series([float("nan")]*len(kl_s))
        px_avg = float((cl * qv).sum() / qv.sum()) if qv.sum() > 0 else float("nan")
        vol_quote = float(qv.sum())

        # taker_buy_pct
        taker_buy_pct = float("nan")
        if "taker_buy_base_volume" in kl_s.columns and "base_volume" in kl_s.columns:
            tb = kl_s["taker_buy_base_volume"].fillna(0).sum()
            bv = kl_s["base_volume"].fillna(0).sum()
            taker_buy_pct = float(tb / bv * 100) if bv > 0 else float("nan")
        elif "taker_buy_quote_volume" in kl_s.columns and qv.sum() > 0:
            tb = kl_s["taker_buy_quote_volume"].fillna(0).sum()
            taker_buy_pct = float(tb / qv.sum() * 100)

        # lsr_global_r from top_pos_1h
        lsr_global_r = float("nan")
        if not pos.empty:
            pos_s = pos[pos["symbol"] == sym]
            if not pos_s.empty:
                for c in ["long_short_ratio", "longShortRatio"]:
                    if c in pos_s.columns:
                        lsr_global_r = float(pos_s[c].mean())
                        break

        # lsr_pos_r from top_acct_1h
        lsr_pos_r = float("nan")
        if not ta.empty:
            ta_s = ta[ta["symbol"] == sym]
            if not ta_s.empty:
                for la_c, sa_c in [("longAccount", "shortAccount"), ("long_account", "short_account")]:
                    if la_c in ta_s.columns and sa_c in ta_s.columns:
                        la = ta_s[la_c].mean()
                        sa = ta_s[sa_c].mean()
                        lsr_pos_r = float(la / sa) if sa > 0 else float("nan")
                        break

        # funding from fapi fetch
        funding_avg = float("nan")
        funding_min = float("nan")
        funding_max = float("nan")
        funding_n   = float("nan")
        if not fn_date.empty:
            fn_s = fn_date[fn_date["symbol"] == sym]
            if not fn_s.empty:
                rates = fn_s["fundingRate"].dropna()
                if len(rates) > 0:
                    funding_avg = float(rates.mean())
                    funding_min = float(rates.min())
                    funding_max = float(rates.max())
                    funding_n   = float(len(rates))

        # OI from oi_hist_1h — CORRECTED: use sum_open_interest_value
        oi_usd = float("nan")
        if not oi.empty and oi_col:
            oi_s = oi[oi["symbol"] == sym]
            if not oi_s.empty:
                oi_usd = float(oi_s[oi_col].iloc[-1])

        row = {
            "date":          date,
            "symbol":        sym,
            "px_avg":        px_avg,
            "vol_quote":     vol_quote,
            "taker_buy_pct": taker_buy_pct,
            "funding_avg":   funding_avg,
            "funding_min":   funding_min,
            "funding_max":   funding_max,
            "funding_n":     funding_n,
            "oi_usd":        oi_usd,
            "lsr_pos_r":     lsr_pos_r,
            "lsr_acc_r":     float("nan"),
            "lsr_global_r":  lsr_global_r,
            "taker_ratio":   float("nan"),
            "low_conf":      0,
            "src_ratio":     "regen_1h_stores_v2",
            "data_ok":       1 if not math.isnan(lsr_global_r) else 0,
        }
        all_rows.append(row)

if all_rows:
    df_out = pd.DataFrame(all_rows)
    df_out.to_csv("/tmp/regen_24_26jul_v2.csv", index=False)
    print(f"\nWrote /tmp/regen_24_26jul_v2.csv: {len(df_out)} rows, {df_out['symbol'].nunique()} syms")
    print(df_out.groupby("date")["symbol"].count())
    # Sample: OI and funding check
    sample = df_out[(df_out["oi_usd"].notna()) & (df_out["oi_usd"] > 0)].head(3)
    if not sample.empty:
        print("Sample oi_usd non-null:")
        print(sample[["date", "symbol", "oi_usd", "funding_avg", "funding_n"]].to_string())
    oi_null = (df_out["oi_usd"].isna() | (df_out["oi_usd"] == 0)).sum()
    fn_null = df_out["funding_n"].isna().sum()
    print(f"oi_usd null/zero: {oi_null}/{len(df_out)}")
    print(f"funding_n null: {fn_null}/{len(df_out)}")
else:
    print("No rows generated")
'''

regen_path = REPO / "_task_regen_vps_v2.py"
regen_path.write_text(VPS_SCRIPT, encoding="utf-8")

print("=== SCPing v2 regen script to VPS ===")
r_scp = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no",
     str(regen_path), f"{VPS}:/tmp/_task_regen_vps_v2.py"],
    capture_output=True, encoding="utf-8", timeout=30,
)
print(f"SCP rc={r_scp.returncode}", r_scp.stderr[:80] if r_scp.stderr else "")

print("\n=== Running v2 regen on VPS ===")
out, err = ssh("python3 /tmp/_task_regen_vps_v2.py 2>&1", timeout=300)
print(out[:5000])
if err:
    print("STDERR:", err[:300])

print("\n=== SCPing v2 result back ===")
r_get = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no",
     f"{VPS}:/tmp/regen_24_26jul_v2.csv",
     str(REPO / "scratch" / "regen_24_26jul_v2.csv")],
    capture_output=True, encoding="utf-8", timeout=60,
)
print(f"SCP result rc={r_get.returncode}", r_get.stderr[:80] if r_get.stderr else "")

regen_csv = REPO / "scratch" / "regen_24_26jul_v2.csv"
if regen_csv.exists():
    df_regen = pd.read_csv(regen_csv)
    print(f"\nRegen v2 CSV: {len(df_regen)} rows")
    print(df_regen.groupby("date")["symbol"].count().to_string())

    fw_list = [l.strip() for l in FW_SYM.read_text(encoding="utf-8").splitlines() if l.strip()]
    df_regen = df_regen[df_regen["symbol"].isin(fw_list)]
    print(f"After freshwatch filter: {len(df_regen)} rows")

    # Quality check
    oi_ok = ((df_regen["oi_usd"] > 0) & df_regen["oi_usd"].notna()).sum()
    fn_ok = (df_regen["funding_n"] > 0).sum()
    print(f"oi_usd > 0: {oi_ok}/{len(df_regen)}")
    print(f"funding_n > 0: {fn_ok}/{len(df_regen)}")

    # Inject into fw137_test July CSV (replace prior v1 rows)
    jul_csv = FW137_DIR / "freshwatch_daily_2026-07.csv"
    df_jul  = pd.read_csv(jul_csv)
    print(f"\nJuly CSV before inject: {len(df_jul)} rows")

    df_jul = df_jul[~df_jul["date"].isin(["2026-07-24", "2026-07-25", "2026-07-26"])]
    cols = df_jul.columns.tolist()
    for c in cols:
        if c not in df_regen.columns:
            df_regen[c] = float("nan")

    df_inject = df_regen[cols]
    df_out = pd.concat([df_jul, df_inject], ignore_index=True).sort_values(["date", "symbol"])
    df_out.to_csv(jul_csv, index=False)
    print(f"July CSV after inject: {len(df_out)} rows")
    dates_check = df_out[df_out["date"].isin(["2026-07-24", "2026-07-25", "2026-07-26"])]
    print(f"Rows per date (24-26/07): {dates_check.groupby('date')['symbol'].count().to_string()}")
    print(f"oi_usd>0 in injected rows: {(dates_check['oi_usd'] > 0).sum()}")
    print(f"funding_n>0 in injected rows: {(dates_check['funding_n'] > 0).sum()}")
else:
    print("regen_24_26jul_v2.csv not found — regen failed")

print("\n=== DỪNG — duyệt quality trước khi chạy 4.2-v3 ===")
