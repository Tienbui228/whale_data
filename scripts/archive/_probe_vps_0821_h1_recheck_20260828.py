#!/usr/bin/env python3
"""[Quick recheck (i) VPS 08-21 4 H1-fire post-H1-fix]
  E2-backlog note: "5 GOM-H fires (canonical H1 data phục hồi):
    CROSS/GWEI/TOSHI/TRIA [H1] conf=normal H3=F
    GENIUS [H2+T0.1] conf=normal H3=F"
  → CROSS/GWEI/TOSHI/TRIA fired H1 alone (không H2+T01).
  Under H1 SPEC-FIX (kho ∧ T0.1), 4 H1 fires còn không? Check T0.1 tại 08-21 4 tokens.
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

TOKENS_4_H1 = ["CROSS", "GWEI", "TOSHI", "TRIA"]  # VPS 08-21 H1-fire per e2_backlog
DATE = "2026-08-21"

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]

frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym): return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _v(df_sym, date, col, n):
    s = df_sym[df_sym["date"] <= date].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]


def _t(df_sym, date, col):
    r = df_sym[df_sym["date"] == date][col]
    if r.empty: return None
    try:
        v = float(r.iloc[0]); return v if v == v else None
    except: return None


def _eval_t01_detail(df_sym, date):
    """T0.1 with per-vế values"""
    fund_14 = _v(df_sym, date, "funding_avg", 14)
    oi_30 = _v(df_sym, date, "oi_usd", 30)
    px_15 = _v(df_sym, date, "px_avg", 15)
    vol_30 = _v(df_sym, date, "vol_quote", 30)
    d = {"fund_14_n": len(fund_14), "oi_30_n": len(oi_30), "px_15_n": len(px_15), "vol_30_n": len(vol_30)}
    if len(fund_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30:
        return "W", d
    c = cfg["t0_1"]
    max_abs_fund = max(abs(f) for f in fund_14)
    d["max_abs_fund"] = max_abs_fund
    d["funding_pin"] = max_abs_fund <= c["funding_pin_abs"]

    oi_today = _t(df_sym, date, "oi_usd")
    oi_min30 = min(oi_30) if oi_30 else None
    oi_ratio = oi_today / oi_min30 if (oi_today and oi_min30 and oi_min30 > 0) else None
    d["oi_ratio"] = oi_ratio
    d["oi_ok"] = oi_ratio is not None and oi_ratio <= c["oi_over_min30_max"]

    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    d["ret14"] = ret14
    d["ret_ok"] = ret14 <= c["ret14_abs_max"]

    vol_7 = vol_30[-7:]
    med7 = median(vol_7)
    med30 = median(vol_30)
    d["med7"] = med7; d["med30"] = med30
    d["vol_ok"] = med7 <= med30 * c["vol_med7_over_med30_max"]

    all_ok = d["funding_pin"] and d["oi_ok"] and d["ret_ok"] and d["vol_ok"]
    return "T" if all_ok else "F", d


# ─── Load Nansen snapshot for 08-21 ───
snap_path = SNAPSHOTS_DIR / f"{DATE}.json"
balance = {}
prev_days = {}
if snap_path.exists():
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    if isinstance(snap, dict):
        for r in snap.get("rows", []):
            sym = r.get("symbol", "").upper()
            if sym in TOKENS_4_H1:
                balance[sym] = r.get("exchange_balance_tokens")

# Load prev balances for kho computation
balance_series = {tok: {} for tok in TOKENS_4_H1}
all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                        if p.stem[:4].isdigit() and len(p.stem) == 10])
for snap_path in all_snapshots:
    ingest_date = snap_path.stem
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        if sym_u in balance_series:
            bal = row.get("exchange_balance_tokens")
            try:
                if bal is not None: balance_series[sym_u][ingest_date] = float(bal)
            except: pass


def _kho_check(tok, date):
    """|Δbalance|/balance ≥10% ≤3d"""
    series = balance_series.get(tok, {})
    if date not in series: return None, None, None
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    best_lb = None; best_dp = 0
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best_dp:
            best_dp = dp; best_lb = lb
    return b_end, best_dp, best_lb


print("═" * 100)
print(f"[VPS 08-21 4 H1-FIRE RECHECK · H1 SPEC-FIX (kho ∧ T0.1)]")
print(f"  Date: {DATE}")
print(f"  Tokens: {TOKENS_4_H1} (per e2_backlog VPS rerun report)")
print("═" * 100)

for tok in TOKENS_4_H1:
    sym = tok + "USDT"
    df = _df_sym(sym)
    print(f"\n  ─── {tok} ({sym}) ───")
    if df.empty:
        print(f"    STORE: EMPTY (không data)")
        continue

    # kho check
    b_end, kho, lb = _kho_check(tok, DATE)
    if b_end is None:
        print(f"    kho: balance MISSING ngày {DATE}")
    else:
        print(f"    kho: balance={b_end:.2f} · best |Δ|/b={kho*100:.2f}% ({lb}d) · gate=10% → {'PASS' if kho >= 0.10 else 'FAIL'}")

    # T0.1 check
    t01, d = _eval_t01_detail(df, DATE)
    print(f"    T0.1: {t01}")
    if "max_abs_fund" in d:
        print(f"      funding_pin (max|f|≤5e-5) : max={d['max_abs_fund']:.2e}  → {d['funding_pin']}")
        print(f"      oi_ratio (≤1.2)           : {d['oi_ratio']}  → {d['oi_ok']}")
        print(f"      ret14 (≤0.10)             : {d['ret14']:.4f}  → {d['ret_ok']}")
        print(f"      vol med7/med30 (≤1.0)     : {d['med7']:.0f}/{d['med30']:.0f}={d['med7']/d['med30']:.3f}  → {d['vol_ok']}")
    else:
        print(f"      warmup: fund_n={d.get('fund_14_n')} oi_n={d.get('oi_30_n')} px_n={d.get('px_15_n')} vol_n={d.get('vol_30_n')}")

    # H1 fixed verdict
    kho_ok = (kho is not None) and (kho >= 0.10)
    if kho_ok and t01 == "T":
        h1_fx = "T (kho ∧ T0.1 both pass)"
    elif kho_ok and t01 == "F":
        h1_fx = "F (kho fires but T0.1 fails)  ← WAS H1 fire trước fix, GIỜ KHÔNG"
    elif kho_ok and t01 == "W":
        h1_fx = "N/A (T0.1 warmup)"
    else:
        h1_fx = "F (kho fails)"
    print(f"    H1 SPEC-FIXED verdict: {h1_fx}")

print(f"\n{'═'*100}")
print(f"[VERDICT] Xem trên — bao nhiêu trong 4 tokens giữ H1=T sau fix?")
print(f"{'═'*100}")
