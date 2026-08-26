#!/usr/bin/env python3
"""[AKE kho_raw table + H1-shadow eval per operator (1) 28/08]
  Per fixture Row 2 finding: AKE có 20+ ngày kho_raw=True nhưng T0.1 gate fail
  → GOM-H strict không fire. ANALYSIS xem H1-shadow (kho ∧ |ret14|≤0.15) có phủ
  AKE không (V① SHADOW report-only, ANALYSIS ký 28/08).
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

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()

frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)

TOK = "AKE"
SYM = "AKEUSDT"
df = STORE[STORE["symbol"] == SYM].sort_values("date").reset_index(drop=True)

# Load Nansen balance series
BALANCE = {}
all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                        if p.stem[:4].isdigit() and len(p.stem) == 10])
for snap_path in all_snapshots:
    ingest = snap_path.stem
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        if row.get("symbol", "").upper() == TOK:
            bal = row.get("exchange_balance_tokens")
            try:
                if bal is not None: BALANCE[ingest] = float(bal)
            except: pass


def _kho_3d(date):
    if date not in BALANCE: return None
    b_end = BALANCE[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    best = 0.0
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = BALANCE.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp
    return best if best > 0 else 0.0


def _v(date, col, n):
    s = df[df["date"] <= date].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]


def _t(date, col):
    r = df[df["date"] == date][col]
    if r.empty: return None
    try: v = float(r.iloc[0]); return v if v == v else None
    except: return None


def _ret14(date):
    px_15 = _v(date, "px_avg", 15)
    if len(px_15) < 15: return None
    return abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else None


def _fund_max14(date):
    fund_14 = _v(date, "funding_avg", 14)
    if len(fund_14) < 14: return None
    return max(abs(f) for f in fund_14)


print("═" * 100)
print(f"[AKE kho_raw=True days · H1-SHADOW eval (V①, report-only)]")
print(f"  yaml md5: {yaml_md5}")
print(f"  H1-shadow rule: kho(3d,≥10%) ∧ |ret14| ≤ 0.15 (NOT compose, chỉ visibility)")
print(f"  vs H1-strict:   kho(3d,≥10%) ∧ T0.1-compression (funding_max14≤5e-5 + oi + ret + vol)")
print("═" * 100)

# Iterate all AKE window with kho data
all_dates = sorted(BALANCE.keys())
print(f"\n  AKE adapter coverage: {all_dates[0]} → {all_dates[-1]} (n={len(all_dates)} snapshots)\n")

print(f"  {'date':>12} {'kho%':>8} {'kho_raw':>8} {'ret14':>7} {'|ret14|≤0.15':>14} {'fund_max14':>12} {'fund_pin':>9} {'H1-shadow':>10} {'H1-strict':>10}")
print(f"  {'-'*115}")

shadow_hits = 0
strict_hits = 0
n_kho_raw = 0
for d in all_dates:
    kho = _kho_3d(d)
    if kho is None or kho < 0.10: continue
    n_kho_raw += 1
    ret14 = _ret14(d)
    fund_max = _fund_max14(d)
    pin_abs = cfg["t0_1"]["funding_pin_abs"]
    pin_eps = cfg["t0_1"].get("funding_pin_eps", 1e-9)
    ret15_ok = (ret14 is not None) and (ret14 <= 0.15)
    fund_pin_ok = (fund_max is not None) and (fund_max <= pin_abs + pin_eps)

    # H1-shadow (V①)
    if ret14 is None:
        shadow = "N/A"
    else:
        shadow = "T" if ret15_ok else "F"
    if shadow == "T": shadow_hits += 1

    # H1-strict = kho ∧ T0.1 (T0.1 = all 4 vé)
    # For quick strict check just funding_pin + ret (assume others might pass)
    # Actually just use full _eval_t01
    oi_all = _v(d, "oi_usd", 30)
    px_15 = _v(d, "px_avg", 15)
    vol_30 = _v(d, "vol_quote", 30)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    if len(oi_all) < floor_obs or len(px_15) < 15 or len(vol_30) < floor_obs or fund_max is None:
        strict = "W"
    else:
        oi_today = _t(d, "oi_usd"); oi_min = min(oi_all)
        oi_ok = (oi_today is not None) and (oi_min > 0) and (oi_today / oi_min <= cfg["t0_1"]["oi_over_min30_max"])
        ret_ok = (ret14 is not None) and (ret14 <= cfg["t0_1"]["ret14_abs_max"])
        vol_7 = vol_30[-7:]
        vol_ok = median(vol_7) <= median(vol_30) * cfg["t0_1"]["vol_med7_over_med30_max"]
        strict = "T" if (fund_pin_ok and oi_ok and ret_ok and vol_ok) else "F"
    if strict == "T": strict_hits += 1

    ret14_str = f"{ret14:.4f}" if ret14 is not None else "N/A"
    fund_str = f"{fund_max:.2e}" if fund_max is not None else "N/A"
    print(f"  {d:>12} {kho*100:>7.2f}% {'True':>8} {ret14_str:>7} {'T' if ret15_ok else 'F':>14} {fund_str:>12} {'T' if fund_pin_ok else 'F':>9} {shadow:>10} {strict:>10}")

print(f"\n  ═══ AGGREGATE ═══")
print(f"  n_kho_raw_days   : {n_kho_raw}")
print(f"  H1-SHADOW hits   : {shadow_hits}  ({100*shadow_hits/n_kho_raw:.1f}% of kho_raw days)" if n_kho_raw else "  n=0")
print(f"  H1-STRICT hits   : {strict_hits}  ({100*strict_hits/n_kho_raw:.1f}% of kho_raw days)" if n_kho_raw else "")
print(f"\n  → H1-shadow phủ AKE {'CÓ' if shadow_hits > 0 else 'KHÔNG'} — ANALYSIS quyết định V① đủ signal cho case AKE?")
print("═" * 100)
