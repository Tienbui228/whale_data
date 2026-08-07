#!/usr/bin/env python3
"""Probe+Task: Regen freshwatch daily rows for 2026-07-24/25/26 from VPS 1h stores.

Sources available on VPS:
  klines_1h    → px_avg (VWAP), vol_quote, taker_buy_pct
  top_pos_1h   → lsr_global_r (long_short_ratio avg)
  funding_8h   → funding_avg/min/max/n
  oi_hist_1h   → oi_usd (end-of-day snapshot)
  taker_ratio_1h → lsr_pos_r, lsr_acc_r, taker_ratio

Script SCPs the aggregation to VPS, runs it, SCPs result back → injects into fw137_test/.
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

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# ── Write VPS aggregation script ──────────────────────────────────────────────
VPS_SCRIPT = r'''#!/usr/bin/env python3
"""Run on VPS: aggregate 1h stores → daily CSV rows for 2026-07-24/25/26."""
import sys, glob, json, math
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
import numpy as np

BASE  = "/root/Data_back_test/whale_data"
DATES = ["2026-07-24", "2026-07-25", "2026-07-26"]
FW_SYM_PATH = BASE + "/data/config/freshwatch_symbols.txt"

with open(FW_SYM_PATH, encoding="utf-8") as f:
    fw_syms = set(l.strip() for l in f if l.strip())

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

def safe_div(a, b):
    return a / b if b and not math.isnan(b) and b > 0 else float("nan")

all_rows = []

for date in DATES:
    print(f"\n--- {date} ---")

    # klines_1h: px_avg, vol_quote, taker_buy_pct
    kl = load_store_date("klines_1h", date)
    if not kl.empty and "symbol" in kl.columns:
        kl = kl[kl["symbol"].isin(fw_syms)]
    print(f"  klines_1h: {len(kl)} rows, {kl['symbol'].nunique() if not kl.empty else 0} syms")

    # top_pos_1h: lsr_global_r
    pos = load_store_date("top_pos_1h", date)
    if not pos.empty and "symbol" in pos.columns:
        pos = pos[pos["symbol"].isin(fw_syms)]
    print(f"  top_pos_1h: {len(pos)} rows, {pos['symbol'].nunique() if not pos.empty else 0} syms")

    # funding_8h: funding_avg/min/max/n
    fn = load_store_date("funding_8h", date)
    if not fn.empty and "symbol" in fn.columns:
        fn = fn[fn["symbol"].isin(fw_syms)]
    print(f"  funding_8h: {len(fn)} rows, {fn['symbol'].nunique() if not fn.empty else 0} syms")
    if not fn.empty:
        print(f"    funding_8h columns: {list(fn.columns)}")

    # oi_hist_1h: oi_usd
    oi = load_store_date("oi_hist_1h", date)
    if not oi.empty and "symbol" in oi.columns:
        oi = oi[oi["symbol"].isin(fw_syms)]
    print(f"  oi_hist_1h: {len(oi)} rows, {oi['symbol'].nunique() if not oi.empty else 0} syms")
    if not oi.empty:
        print(f"    oi_hist_1h columns: {list(oi.columns)}")

    # taker_ratio_1h: lsr_pos_r, lsr_acc_r, taker_ratio
    tr = load_store_date("taker_ratio_1h", date)
    if not tr.empty and "symbol" in tr.columns:
        tr = tr[tr["symbol"].isin(fw_syms)]
    print(f"  taker_ratio_1h: {len(tr)} rows, {tr['symbol'].nunique() if not tr.empty else 0} syms")
    if not tr.empty:
        print(f"    taker_ratio_1h columns: {list(tr.columns)}")

    # top_acct_1h: lsr_pos_r, lsr_acc_r
    ta = load_store_date("top_acct_1h", date)
    if not ta.empty and "symbol" in ta.columns:
        ta = ta[ta["symbol"].isin(fw_syms)]
    print(f"  top_acct_1h: {len(ta)} rows, {ta['symbol'].nunique() if not ta.empty else 0} syms")
    if not ta.empty:
        print(f"    top_acct_1h columns: {list(ta.columns)}")

    # retail_global_1h: global LSR alternative
    rg = load_store_date("retail_global_1h", date)
    if not rg.empty:
        print(f"  retail_global_1h: {len(rg)} rows | cols: {list(rg.columns)[:6]}")

    # ── Aggregate klines_1h → daily ──
    if kl.empty:
        print(f"  SKIP {date}: no klines_1h data")
        continue

    syms = kl["symbol"].unique()
    for sym in syms:
        kl_s = kl[kl["symbol"] == sym]

        # VWAP
        qv = kl_s["quote_volume"].fillna(0)
        cl = kl_s["close"].fillna(float("nan"))
        px_avg = float((cl * qv).sum() / qv.sum()) if qv.sum() > 0 else float("nan")

        vol_quote = float(qv.sum())

        # taker_buy_pct
        taker_buy_pct = float("nan")
        if "taker_buy_base_volume" in kl_s.columns and "base_volume" in kl_s.columns:
            tb = kl_s["taker_buy_base_volume"].fillna(0).sum()
            bv = kl_s["base_volume"].fillna(0).sum()
            taker_buy_pct = float(tb / bv * 100) if bv > 0 else float("nan")
        elif "taker_buy_quote_volume" in kl_s.columns:
            tb = kl_s["taker_buy_quote_volume"].fillna(0).sum()
            taker_buy_pct = float(tb / qv.sum() * 100) if qv.sum() > 0 else float("nan")

        # lsr_global_r from top_pos_1h
        lsr_global_r = float("nan")
        if not pos.empty:
            pos_s = pos[pos["symbol"] == sym]
            if not pos_s.empty and "long_short_ratio" in pos_s.columns:
                lsr_global_r = float(pos_s["long_short_ratio"].mean())

        # lsr_pos_r, lsr_acc_r from top_acct_1h or taker_ratio_1h
        lsr_pos_r = float("nan")
        lsr_acc_r = float("nan")
        taker_ratio_val = float("nan")
        if not ta.empty:
            ta_s = ta[ta["symbol"] == sym]
            if not ta_s.empty:
                # check available columns
                if "longAccount" in ta_s.columns and "shortAccount" in ta_s.columns:
                    la = ta_s["longAccount"].mean()
                    sa = ta_s["shortAccount"].mean()
                    lsr_pos_r = la / sa if sa > 0 else float("nan")
                elif "long_account" in ta_s.columns and "short_account" in ta_s.columns:
                    la = ta_s["long_account"].mean()
                    sa = ta_s["short_account"].mean()
                    lsr_pos_r = la / sa if sa > 0 else float("nan")
        if not tr.empty:
            tr_s = tr[tr["symbol"] == sym]
            if not tr_s.empty:
                cols = tr_s.columns.tolist()
                for c in ["taker_ratio", "takerBuyRatio", "taker_buy_ratio"]:
                    if c in cols:
                        taker_ratio_val = float(tr_s[c].mean())
                        break

        # funding from funding_8h
        funding_avg = float("nan")
        funding_min = float("nan")
        funding_max = float("nan")
        funding_n   = float("nan")
        if not fn.empty:
            fn_s = fn[fn["symbol"] == sym]
            if not fn_s.empty:
                fr_col = next((c for c in ["fundingRate","funding_rate","rate"] if c in fn_s.columns), None)
                if fr_col:
                    rates = fn_s[fr_col].dropna()
                    if len(rates) > 0:
                        funding_avg = float(rates.mean())
                        funding_min = float(rates.min())
                        funding_max = float(rates.max())
                        funding_n   = float(len(rates))

        # OI from oi_hist_1h (use last snapshot of day)
        oi_usd = float("nan")
        if not oi.empty:
            oi_s = oi[oi["symbol"] == sym]
            if not oi_s.empty:
                oi_col = next((c for c in ["sumOpenInterestValue","oi_usd","openInterestUsd"] if c in oi_s.columns), None)
                if oi_col:
                    oi_usd = float(oi_s[oi_col].iloc[-1])

        row = {
            "date":         date,
            "symbol":       sym,
            "px_avg":       px_avg,
            "vol_quote":    vol_quote,
            "taker_buy_pct": taker_buy_pct,
            "funding_avg":  funding_avg,
            "funding_min":  funding_min,
            "funding_max":  funding_max,
            "funding_n":    funding_n,
            "oi_usd":       oi_usd,
            "lsr_pos_r":    lsr_pos_r,
            "lsr_acc_r":    lsr_acc_r,
            "lsr_global_r": lsr_global_r,
            "taker_ratio":  taker_ratio_val,
            "low_conf":     0,
            "src_ratio":    "regen_1h_stores",
            "data_ok":      1 if not math.isnan(lsr_global_r) else 0,
        }
        all_rows.append(row)

if all_rows:
    df_out = pd.DataFrame(all_rows)
    df_out.to_csv("/tmp/regen_24_26jul.csv", index=False)
    print(f"\nWrote /tmp/regen_24_26jul.csv: {len(df_out)} rows, {df_out['symbol'].nunique()} syms")
    print(df_out.groupby("date")["symbol"].count())
    print(df_out[["date","symbol","px_avg","lsr_global_r","funding_avg","oi_usd"]].head(6).to_string())
else:
    print("No rows generated")
'''

regen_path = REPO / "_task_regen_vps.py"
regen_path.write_text(VPS_SCRIPT, encoding="utf-8")

print("=== SCPing regen script to VPS ===")
r_scp = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no",
     str(regen_path), f"{VPS}:/tmp/_task_regen_vps.py"],
    capture_output=True, encoding="utf-8", timeout=30,
)
print(f"SCP rc={r_scp.returncode}")

print("\n=== Running regen aggregation on VPS ===")
out, err = ssh("python3 /tmp/_task_regen_vps.py 2>&1", timeout=300)
print(out[:3000])
if err:
    print("STDERR:", err[:300])

print("\n=== SCPing result back ===")
r_get = subprocess.run(
    ["scp", "-o", "StrictHostKeyChecking=no",
     f"{VPS}:/tmp/regen_24_26jul.csv",
     str(REPO / "scratch" / "regen_24_26jul.csv")],
    capture_output=True, encoding="utf-8", timeout=60,
)
print(f"SCP result rc={r_get.returncode}", r_get.stderr[:80] if r_get.stderr else "")

regen_csv = REPO / "scratch" / "regen_24_26jul.csv"
if regen_csv.exists():
    df_regen = pd.read_csv(regen_csv)
    print(f"Regen CSV: {len(df_regen)} rows")
    print(df_regen.groupby("date")["symbol"].count().to_string())

    # Load freshwatch list to filter
    fw_list = [l.strip() for l in FW_SYM.read_text(encoding="utf-8").splitlines() if l.strip()]
    df_regen = df_regen[df_regen["symbol"].isin(fw_list)]
    print(f"After freshwatch filter: {len(df_regen)} rows")

    # Inject into fw137_test July CSV
    jul_csv = FW137_DIR / "freshwatch_daily_2026-07.csv"
    df_jul  = pd.read_csv(jul_csv)
    print(f"\nJuly CSV before inject: {len(df_jul)} rows")

    # Remove any existing rows for those dates (should be none, but be safe)
    df_jul = df_jul[~df_jul["date"].isin(["2026-07-24", "2026-07-25", "2026-07-26"])]

    # Align columns
    cols = df_jul.columns.tolist()
    for c in cols:
        if c not in df_regen.columns:
            df_regen[c] = float("nan")

    df_inject = df_regen[cols]
    df_out = pd.concat([df_jul, df_inject], ignore_index=True).sort_values(["date", "symbol"])
    df_out.to_csv(jul_csv, index=False)
    print(f"July CSV after inject: {len(df_out)} rows")
    print(f"Rows per date (24-26/07): {df_out[df_out['date'].isin(['2026-07-24','2026-07-25','2026-07-26'])].groupby('date')['symbol'].count().to_string()}")
else:
    print("regen_24_26jul.csv not found — regen failed")

print("\n=== DỪNG — duyệt inject trước khi re-run --daily ===")
