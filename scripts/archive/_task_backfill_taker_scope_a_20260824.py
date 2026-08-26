#!/usr/bin/env python3
"""[Backfill taker Scope A — KHÔNG auto-apply, dry-run 5b-clone bảng flip]

Operator ký chat 24/08 (Backfill Scope A):
  Scope: scratch vol_k7_fresh_2026-{06,07,08}.csv (k[10] verified)
  Key: (symbol, date) upsert
  Provenance: taker_source = "k10_over_k7_scratch_backfill_20260824"
  Backup L-37: freshwatch_daily_2026-{06,07,08}.csv.bak_pre_backfill_20260824
  KHÔNG auto-apply — dry-run 5b-clone → bảng flip → chờ operator ký → apply

Steps:
  1. SSH VPS + fetch scratch/vol_k7_fresh_2026-{06,07,08}.csv (nếu chưa có local mirror)
  2. Compute per (symbol, date) canonical taker_buy_pct = taker_buy_quote / k7_quote_vol
  3. Load current freshwatch_daily_2026-{06,07,08}.csv from data/export/
  4. Dry-run consumer diff (5b-clone): absorption() flip count + delta stats
  5. Paste bảng flip + verdict → CHỜ operator ký + apply flag

Usage:
  python _task_backfill_taker_scope_a_20260824.py           # dry-run (default)
  python _task_backfill_taker_scope_a_20260824.py --apply   # sau operator ký
"""
from __future__ import annotations
import sys, io, argparse, shutil, subprocess, hashlib
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
SCRATCH_LOCAL = REPO / "data/reference/vol_k7_fresh_scratch_20260824"
BACKUP_SUFFIX = ".bak_pre_backfill_20260824"
BACKFILL_TAG = "k10_over_k7_scratch_backfill_20260824"

def _md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

def _fetch_scratch_from_vps():
    """SCP vol_k7_fresh_2026-{06,07,08}.csv from VPS to local reference dir."""
    SCRATCH_LOCAL.mkdir(parents=True, exist_ok=True)
    files = []
    for m in ["06", "07", "08"]:
        remote = f"root@5.223.67.21:/root/Data_back_test/whale_data/scratch/vol_k7_fresh_2026-{m}.csv"
        local = SCRATCH_LOCAL / f"vol_k7_fresh_2026-{m}.csv"
        if not local.exists():
            print(f"  SCP {remote} → {local}")
            r = subprocess.run(["scp", remote, str(local)], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  ERR: {r.stderr[:200]}")
                continue
        files.append(local)
        n_rows = sum(1 for _ in open(local, encoding="utf-8", errors="replace")) - 1
        print(f"  {local.name}: {_md5(local)}  rows={n_rows}")
    return files

def _load_scratch(files):
    """Load and compute canonical k[10]/k[7] taker_buy_pct."""
    frames = []
    for f in files:
        df = pd.read_csv(f)
        # Compute canonical
        df["taker_buy_pct_canonical"] = df["taker_buy_quote"] / df["k7_quote_vol"]
        # Guard: k7=0 or nan → nan
        df.loc[df["k7_quote_vol"] <= 0, "taker_buy_pct_canonical"] = float("nan")
        frames.append(df[["symbol", "date", "taker_buy_pct_canonical"]])
    return pd.concat(frames, ignore_index=True)

def _load_current_store():
    """Load current freshwatch_daily 06/07/08 with taker_buy_pct."""
    frames = []
    for m in ["06", "07", "08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["_source_file"] = p.name
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def _consumer_diff_5b_clone(scratch_df, store_df):
    """Dry-run consumer diff: absorption() flip count + delta stats."""
    # Merge
    m = store_df.merge(
        scratch_df.rename(columns={"taker_buy_pct_canonical": "taker_buy_pct_backfill"}),
        on=["symbol", "date"], how="left"
    )
    m["taker_legacy"] = m["taker_buy_pct"]  # existing r/(1+r)
    m["taker_canonical"] = m["taker_buy_pct_backfill"]
    m["has_canonical"] = m["taker_canonical"].notna()
    m["delta_frac"] = m["taker_canonical"] - m["taker_legacy"]
    m["delta_abs"] = m["delta_frac"].abs()

    n_covered = m["has_canonical"].sum()
    covered = m[m["has_canonical"]].copy()
    stats = {
        "n_total": len(m),
        "n_covered": int(n_covered),
        "mean": covered["delta_frac"].mean(),
        "median": covered["delta_frac"].median(),
        "p90_abs": covered["delta_abs"].quantile(0.90),
        "max_abs": covered["delta_abs"].max(),
    }

    # Absorption flip count per (symbol, day): 7d window [0.44, 0.505]%
    tbp_lo, tbp_hi = 0.44, 0.505
    flip_rows = []
    for sym, g in covered.sort_values(["symbol","date"]).groupby("symbol"):
        g = g.reset_index(drop=True)
        for i in range(6, len(g)):
            window = g.iloc[i-6:i+1]
            leg_vals = window["taker_legacy"].values
            can_vals = window["taker_canonical"].values
            if any(pd.isna(v) for v in leg_vals) or any(pd.isna(v) for v in can_vals):
                continue
            leg_pass = all(tbp_lo <= v <= tbp_hi for v in leg_vals)
            can_pass = all(tbp_lo <= v <= tbp_hi for v in can_vals)
            if leg_pass != can_pass:
                flip_rows.append({
                    "symbol": sym, "date": g.iloc[i]["date"],
                    "leg_pass": leg_pass, "can_pass": can_pass,
                    "leg_last": leg_vals[-1], "can_last": can_vals[-1],
                })
    return stats, flip_rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply backfill to store (SAU operator ký)")
    args = ap.parse_args()

    print("═" * 90)
    print(" [Backfill taker Scope A] Dry-run 5b-clone (KHÔNG apply mặc định)")
    print("═" * 90)

    print(f"\n[1] Fetch scratch vol_k7_fresh from VPS:")
    files = _fetch_scratch_from_vps()
    if not files:
        sys.exit("ERR: no scratch files fetched")

    print(f"\n[2] Load scratch + compute canonical k[10]/k[7]:")
    scratch_df = _load_scratch(files)
    print(f"  scratch rows: {len(scratch_df)}")
    print(f"  unique (sym, date): {scratch_df[['symbol','date']].drop_duplicates().shape[0]}")

    print(f"\n[3] Load current store:")
    store_df = _load_current_store()
    print(f"  store rows: {len(store_df)}")

    print(f"\n[4] Dry-run consumer diff (5b-clone):")
    stats, flip_rows = _consumer_diff_5b_clone(scratch_df, store_df)
    print(f"  n_total store rows: {stats['n_total']}")
    print(f"  n_covered by scratch backfill: {stats['n_covered']}")
    print(f"  Delta stats (canonical - legacy):")
    print(f"    mean:    {stats['mean']:.4f}")
    print(f"    median:  {stats['median']:.4f}")
    print(f"    p90 |Δ|: {stats['p90_abs']:.4f}")
    print(f"    max |Δ|: {stats['max_abs']:.4f}")
    print(f"\n  Absorption flip count (7d window [44,50.5]%): {len(flip_rows)}")
    if flip_rows:
        print(f"  Top 20:")
        print(f"  {'sym':<15} {'date':>12}  {'leg':>4} {'can':>4}  {'leg_last':>10} {'can_last':>10}  {'|Δ|':>7}")
        for f in sorted(flip_rows, key=lambda x: abs(x['can_last']-x['leg_last']), reverse=True)[:20]:
            delta = abs(f['can_last'] - f['leg_last'])
            print(f"  {f['symbol']:<15} {f['date']:>12}  {str(f['leg_pass'])[:4]:>4} {str(f['can_pass'])[:4]:>4}  "
                  f"{f['leg_last']:>10.4f} {f['can_last']:>10.4f}  {delta:>7.4f}")
        if len(flip_rows) > 20:
            print(f"  ... {len(flip_rows) - 20} more")

    print(f"\n[5] Verdict:")
    baseline_5b_flips = 11  # from _probe_5b_consumer_diff_20260824.py
    if len(flip_rows) > 3 * baseline_5b_flips:
        print(f"  ✗ flips = {len(flip_rows)} > 3× baseline (5b=11) → CHỜ SIGNOFF PHASE 2")
    else:
        print(f"  ✓ flips = {len(flip_rows)} ≤ 3× baseline (5b=11) → safe to apply với operator ký")

    if not args.apply:
        print(f"\n[DRY-RUN] KHÔNG apply. Bảng flip + delta stats trên → về operator ký.")
        print(f"  Sau ký: rerun với --apply → backup L-37 + write store + verify.")
        return

    # --- APPLY MODE (sau operator ký) ---
    print(f"\n[APPLY] Backfill Scope A — backup L-37 + write store")
    for m in ["06", "07", "08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if not p.exists(): continue
        bak = p.with_suffix(p.suffix + BACKUP_SUFFIX)
        if not bak.exists():
            shutil.copy2(p, bak)
            print(f"  backup: {bak.name}  md5={_md5(bak)}")
    print(f"  [APPLY not yet implemented — chờ operator ký + relay để enable]")

if __name__ == "__main__":
    main()
