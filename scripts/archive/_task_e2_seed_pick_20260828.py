#!/usr/bin/env python3
"""[E2 seed pick — agent bốc per operator (b) 28/08]
  Roster: fw-139 minus 8 case (BANK/TUT/CYS/HEMI/ON/CAP/AKE/BTW) = 131 candidates
  Filter: |ret 26/06→22/08| < 30% từ STORE freshwatch_daily
  Pick: ≥20 (deterministic, alphabetical để reproducible)
  FP scan: GOM-H (T0.1 · H1 · H2 · H3) mỗi ngày 06-26→08-22 cho từng token seed
  Output: per-token days_fire + agg FP rate + fire dates
  Guard: H1 adapter chỉ có Nansen snapshots (fw-139 subset); token thiếu → H1=N/A
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
SYMBOLS_TXT = REPO / "data/config/freshwatch_symbols.txt"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

CASES = {"BANK", "TUT", "CYS", "HEMI", "ON", "CAP", "AKE", "BTW"}
WINDOW_START = "2026-06-26"
WINDOW_END = "2026-08-22"
RET_MAX = 0.30

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()

# ─── Load fw-139 minus 8 case = 131 candidates ───
fw_symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
# Strip USDT suffix
candidates = []
for s in fw_symbols:
    tok = s[:-4] if s.endswith("USDT") else s
    if tok not in CASES:
        candidates.append(tok)

print("═" * 100)
print(f"[E2 SEED PICK · CFG-PROVENANCE]")
print(f"  yaml: {YAML_PATH.name}  md5: {yaml_md5}")
print(f"  fw-139 total: {len(fw_symbols)}  ·  minus 8 case = {len(candidates)} candidates")
print(f"  Window: {WINDOW_START} → {WINDOW_END}")
print(f"  Filter: |ret| < {RET_MAX*100}%")
print("═" * 100)

# ─── Load STORE 05-08 ───
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym):
    return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _px_at(df, date):
    """px_avg at date, nearest ≤ date if exact missing"""
    r = df[df["date"] <= date].tail(1)
    if r.empty: return None
    v = r["px_avg"].iloc[0]
    return float(v) if pd.notna(v) else None


# ─── Compute |ret 06-26→08-22| for each candidate ───
print(f"\n[Step 1: |ret| filter — {len(candidates)} candidates]\n")
eligible = []
excluded = []
missing = []
for tok in candidates:
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        missing.append(tok)
        continue
    px0 = _px_at(df, WINDOW_START)
    px1 = _px_at(df, WINDOW_END)
    if px0 is None or px1 is None or px0 <= 0:
        missing.append(tok)
        continue
    ret = (px1 - px0) / px0
    if abs(ret) < RET_MAX:
        eligible.append((tok, ret))
    else:
        excluded.append((tok, ret))

print(f"  Eligible (|ret| < 30%): {len(eligible)}")
print(f"  Excluded (|ret| ≥ 30%): {len(excluded)}")
print(f"  Missing (no STORE data): {len(missing)}")

# ─── Pick seed (≥20 deterministic alphabetical) ───
eligible_sorted = sorted(eligible, key=lambda x: x[0])
SEED_N = max(20, min(24, len(eligible_sorted)))  # up to 24 for safety
seed = eligible_sorted[:SEED_N]

print(f"\n[Step 2: SEED PICK — first {SEED_N} alphabetical (deterministic reproducible)]\n")
print(f"  {'token':<10} {'ret 06-26→08-22':>18}")
for tok, ret in seed:
    print(f"  {tok:<10} {ret*100:>16.2f}%")

# ─── Load Nansen snapshots for H1 ───
print(f"\n[Step 3: Load Nansen snapshots for H1 replay]")
balance_series = {tok: {} for tok, _ in seed}
all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                        if p.stem[:4].isdigit() and len(p.stem) == 10])
for snap_path in all_snapshots:
    ingest_date = snap_path.stem
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        if sym_u in balance_series:
            bal = row.get("exchange_balance_tokens")
            try:
                if bal is not None: balance_series[sym_u][ingest_date] = float(bal)
            except: pass
print(f"  Loaded {len(all_snapshots)} snapshots for H1 balance series")

# ─── Eval functions ───
def _v(df_sym, date, col, n):
    s = df_sym[df_sym["date"] <= date].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]

def _t(df_sym, date, col):
    r = df_sym[df_sym["date"] == date][col]
    if r.empty: return None
    try:
        v = float(r.iloc[0]); return v if v == v else None
    except: return None

def _div_avg3(df_sym, date):
    s = df_sym[df_sym["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in s.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    avg_p = sum(x[0] for x in pairs) / len(pairs)
    avg_a = sum(x[1] for x in pairs) / len(pairs)
    return avg_p / avg_a if avg_a > 1e-9 else None

def _eval_t01(df_sym, date):
    fund_14 = _v(df_sym, date, "funding_avg", 14)
    oi_30 = _v(df_sym, date, "oi_usd", 30)
    px_15 = _v(df_sym, date, "px_avg", 15)
    vol_30 = _v(df_sym, date, "vol_quote", 30)
    if len(fund_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30: return "W"
    c = cfg["t0_1"]
    fund_ok = max(abs(f) for f in fund_14) <= c["funding_pin_abs"]
    oi_today = _t(df_sym, date, "oi_usd")
    if oi_today is None: return "W"
    oi_min30 = min(oi_30)
    if oi_min30 <= 0: return "W"
    oi_ok = (oi_today / oi_min30) <= c["oi_over_min30_max"]
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    ret_ok = ret14 <= c["ret14_abs_max"]
    vol_7 = vol_30[-7:]
    if len(vol_7) < 7: return "W"
    vol_ok = median(vol_7) <= median(vol_30) * c["vol_med7_over_med30_max"]
    return "T" if all([fund_ok, oi_ok, ret_ok, vol_ok]) else "F"

def _eval_h2(df_sym, date):
    pos_14 = _v(df_sym, date, "lsr_pos_r", 14)
    oi_30 = _v(df_sym, date, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: return "W"
    div_today = _div_avg3(df_sym, date)
    if div_today is None: return "W"
    dates = sorted(df_sym[df_sym["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "W"
    divs = [_div_avg3(df_sym, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return "W"
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df_sym, date, "lsr_pos_r"); oi_today = _t(df_sym, date, "oi_usd")
    if pos_today is None or oi_today is None: return "W"
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    if pos_min14 <= 0 or oi_min30 <= 0: return "W"
    v2 = (pos_today / pos_min14 >= c["pos_over_min14_min"]) and (oi_today / oi_min30 <= c["oi_over_min30_max"])
    return "T" if (v1 or v2) else "F"

def _eval_h3(df_sym, date):
    vol_14 = _v(df_sym, date, "vol_quote", 14)
    px_2 = _v(df_sym, date, "px_avg", 2)
    if len(vol_14) < 14: return "W"
    vol_today = _t(df_sym, date, "vol_quote")
    if vol_today is None: return "W"
    med14 = median(vol_14)
    if med14 <= 0: return "F"
    vol_ratio = vol_today / med14
    if len(px_2) < 2: return "W"
    ret_1d = abs((px_2[-1] - px_2[0]) / px_2[0]) if px_2[0] > 0 else float("inf")
    c = cfg["h3"]
    return "T" if (vol_ratio >= c["vol_mult_med14_min"] and ret_1d <= c["ret_abs_max"]) else "F"

def _eval_h1(tok, date):
    """H1 = |Δbalance|/balance ≥10% trong ≤3d window ending `date`"""
    series = balance_series.get(tok, {})
    if not series: return "N/A"
    if date not in series: return "N/A"
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    c = cfg["h1"]
    for lb in range(1, c["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        if abs(b_end - b_start) / b_start >= c["balance_delta_abs_min"]:
            return "T"
    return "F"


# ─── (4) FP scan per token ───
print(f"\n[Step 4: FP scan GOM-H each day {WINDOW_START} → {WINDOW_END}]")
print(f"  GOM-H = H1 ∨ (H2 ∧ T0.1);  H3 = confidence booster")
print(f"\n  {'token':<10} {'ret':>7} {'days':>5} {'t01':>4} {'h1':>4} {'h2':>4} {'h3':>4} {'gom-h_fires':>12} {'first_fire':>12}")

# Build date range
start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

fp_summary = []
for tok, ret in seed:
    sym = tok + "USDT"
    df = _df_sym(sym)
    t01_fires, h1_fires, h2_fires, h3_fires, gh_fires = 0, 0, 0, 0, 0
    fire_dates = []
    days_evaluated = 0
    for date in window_days:
        # Must have store row for evaluation, else skip
        if df[df["date"] == date].empty: continue
        days_evaluated += 1
        t01 = _eval_t01(df, date)
        h1 = _eval_h1(tok, date)
        h2 = _eval_h2(df, date)
        h3 = _eval_h3(df, date)
        if t01 == "T": t01_fires += 1
        if h1 == "T": h1_fires += 1
        if h2 == "T": h2_fires += 1
        if h3 == "T": h3_fires += 1
        gh = (h1 == "T") or ((h2 == "T") and (t01 == "T"))
        if gh:
            gh_fires += 1
            fire_dates.append(date)
    first_fire = fire_dates[0] if fire_dates else "-"
    fp_summary.append({
        "tok": tok, "ret": ret, "days": days_evaluated,
        "t01": t01_fires, "h1": h1_fires, "h2": h2_fires, "h3": h3_fires,
        "gh": gh_fires, "first_fire": first_fire, "all_fires": fire_dates,
    })
    print(f"  {tok:<10} {ret*100:>6.1f}% {days_evaluated:>5} {t01_fires:>4} {h1_fires:>4} {h2_fires:>4} {h3_fires:>4} {gh_fires:>12} {first_fire:>12}")

# ─── Aggregate ───
n_gh_positive = sum(1 for r in fp_summary if r["gh"] > 0)
total_gh_fires = sum(r["gh"] for r in fp_summary)
total_days = sum(r["days"] for r in fp_summary)
print(f"\n[FP AGGREGATE]")
print(f"  Seed size          : {len(seed)} tokens")
print(f"  Tokens ≥1 GOM-H fire: {n_gh_positive}/{len(seed)} ({100*n_gh_positive/len(seed):.1f}%)")
print(f"  Total GOM-H fires  : {total_gh_fires}")
print(f"  Total token-days   : {total_days}")
if total_days > 0:
    print(f"  FP rate per day    : {total_gh_fires/total_days*100:.2f}%")
print(f"\n  Per-vế fires (raw, không compose GOM-H):")
print(f"    T0.1: {sum(r['t01'] for r in fp_summary)}")
print(f"    H1  : {sum(r['h1'] for r in fp_summary)}")
print(f"    H2  : {sum(r['h2'] for r in fp_summary)}")
print(f"    H3  : {sum(r['h3'] for r in fp_summary)}")

# ─── Fire timeline detail ───
print(f"\n[Fire timeline detail — tokens có fire]")
for r in fp_summary:
    if r["gh"] > 0:
        print(f"  {r['tok']:<10}: {r['gh']} fires → {r['all_fires']}")

print(f"\n{'═'*100}")
print(f"[E2 SEED PICK DỪNG] Seed = {len(seed)} tokens (alphabetical first) ·"
      f" FP scan done · chờ operator (a)/(c) [ ] + ký GOM-H off-draft.")
print(f"{'═'*100}")
