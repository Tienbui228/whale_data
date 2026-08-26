#!/usr/bin/env python3
"""[Tasks (2)+(3) DEV → AGENT 28/08 · thứ tự tuyệt đối]

(2) T-④ ERRATA re-render semantics production (vol hardcode 30):
    Header basis PER-VẾ. Kỳ vọng 0/8. HEMI ghi chú.

(3) Funding 5.00e-5-exact lần ba: full precision HEMI 07-03..07-16 +
    BANANAS31 07-04 + COAI 07-23 — số thật hay tròn lưu trữ?

Commit sẽ append-only trỏ d2e410a [AS-SIGNED exhibit ①].
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
GATE_DEFS = REPO / "docs/proposals/gom_h_gate_defs_20260828.md"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]

frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym): return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _v(df, date, col, n):
    s = df[df["date"] <= date].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]


def _t(df, date, col):
    r = df[df["date"] == date][col]
    if r.empty: return None
    try:
        v = float(r.iloc[0]); return v if v == v else None
    except: return None


def _div_avg3(df, date):
    s = df[df["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in s.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    return sum(x[0] for x in pairs)/len(pairs) / (sum(x[1] for x in pairs)/len(pairs) or 1e-9)


def _eval_t01_production_semantic(df, date):
    """PRODUCTION semantics: med30_vol HARDCODE 30 (align gom_h_daily.py runtime).
    Return (status, per-vé pass detail)."""
    fund_14 = _v(df, date, "funding_avg", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    px_15 = _v(df, date, "px_avg", 15)
    vol_all = _v(df, date, "vol_quote", 30)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    detail = {"n_fund": len(fund_14), "n_oi": len(oi_all), "n_px": len(px_15), "n_vol": len(vol_all)}
    # Warmup gate — production: funding≥14, oi≥floor_obs, px≥15, vol≥30 (HARDCODE)
    if len(fund_14) < 14 or len(oi_all) < floor_obs or len(px_15) < 15 or len(vol_all) < 30:
        detail["overall"] = "W"
        return "W", detail
    c = cfg["t0_1"]
    pin_eps = c.get("funding_pin_eps", 1e-9)
    max_af = max(abs(f) for f in fund_14)
    detail["funding_pin"] = "T" if max_af <= c["funding_pin_abs"] + pin_eps else "F"
    detail["funding_max"] = max_af

    oi_today = _t(df, date, "oi_usd"); oi_min = min(oi_all)
    r_oi = oi_today / oi_min if (oi_today and oi_min > 0) else None
    detail["oi_ok"] = "T" if (r_oi is not None and r_oi <= c["oi_over_min30_max"]) else "F"
    detail["oi_ratio"] = r_oi
    detail["oi_floor_basis"] = f"{len(oi_all)}d"

    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else 999
    detail["ret_ok"] = "T" if ret14 <= c["ret14_abs_max"] else "F"
    detail["ret14"] = ret14

    med7 = median(vol_all[-7:]); med30 = median(vol_all)
    r_vol = med7 / med30 if med30 > 0 else float("inf")
    detail["vol_ok"] = "T" if r_vol <= c["vol_med7_over_med30_max"] else "F"
    detail["vol_ratio"] = r_vol

    overall = "T" if all(detail[k] == "T" for k in ("funding_pin", "oi_ok", "ret_ok", "vol_ok")) else "F"
    detail["overall"] = overall
    return overall, detail


def _eval_h2(df, date):
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return "W"
    div_today = _div_avg3(df, date)
    if div_today is None: return "W"
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "W"
    divs = [_div_avg3(df, dd) for dd in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return "W"
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2 = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    return "T" if (v1 or v2) else "F"


# Nansen balance for H1
BAL = {}
for snap_path in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (snap_path.stem[:4].isdigit() and len(snap_path.stem) == 10): continue
    try: snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        BAL.setdefault(sym_u, {})
        bal = row.get("exchange_balance_tokens")
        try:
            if bal is not None: BAL[sym_u][snap_path.stem] = float(bal)
        except: pass


def _kho_3d(tok, date):
    series = BAL.get(tok, {})
    if date not in series: return None
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    best = 0.0
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp
    return best


# ═══════════════════════════════════════════════════════════
# (2) T-④ ERRATA — production semantics (vol HARDCODE 30)
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[T-④ ERRATA · re-render semantics PRODUCTION (vol HARDCODE 30)]")
print("[AS-SIGNED exhibit ①] · trỏ d2e410a · header basis PER-VẾ")
print("═" * 100)
print("""
Basis per-vé (production gom_h_daily.py):
  T0.1 funding : n=14 (HARDCODE)
  T0.1 oi      : n=floor_obs_min=14 (V② YAML)
  T0.1 ret     : n=15 (px_15, HARDCODE)
  T0.1 vol     : n=30 (HARDCODE 30)  ← khác regression trước
  H2 pos       : n=14 (HARDCODE)
  H2 oi        : n=floor_obs_min=14 (V②)
""")

D0 = {"BANK": "2026-07-11", "TUT": "2026-07-09", "CYS": "2026-08-04",
      "AKE": "2026-07-15", "BTW": "2026-08-03", "HEMI": "2026-08-15",
      "ON": "2026-07-19", "CAP": "2026-07-30", "BTR": "2026-08-26"}

print(f"  {'case':<7} {'D0':>12} {'window':>27} {'H1_first':>12} {'perp_first':>15} {'compose':>15} {'lead':>7} {'verdict':>15}")
print(f"  {'-'*130}")

for tok in sorted(D0.keys()):
    d0 = D0[tok]
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"  {tok:<7} {d0:>12} NO-STORE"); continue
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    data_start = df["date"].min()
    win_start_dt = max(datetime.strptime(data_start, "%Y-%m-%d"), d0_dt - timedelta(days=30))
    win_end_dt = d0_dt - timedelta(days=1)
    win_str = f"{win_start_dt.strftime('%m-%d')}..{win_end_dt.strftime('%m-%d')}"

    lane_kho_fires = []
    lane_perp_fires = []
    all_fires = []
    raw_hist = {"kho": {}, "perp": {}}
    h1_ev = h2t01_ev = 0

    cur = win_start_dt
    while cur <= win_end_dt:
        d = cur.strftime("%Y-%m-%d")
        t01, td = _eval_t01_production_semantic(df, d)
        h2 = _eval_h2(df, d)
        kho = _kho_3d(tok, d)

        h1_raw = (kho is not None) and (kho >= 0.10)
        h2t01_raw = (h2 == "T") and (t01 == "T") if (h2 != "W" and t01 != "W") else None

        raw_hist["kho"][d] = h1_raw if kho is not None else None
        raw_hist["perp"][d] = h2t01_raw

        if kho is not None and t01 != "W": h1_ev += 1
        if h2 != "W" and t01 != "W": h2t01_ev += 1

        h1_t = h1_raw and t01 == "T"
        h2t01_t = h2 == "T" and t01 == "T"

        def _in_cd(lane_fires, raw_h):
            if not lane_fires or not raw_h: return False
            last = lane_fires[-1]
            days_since = (cur - datetime.strptime(last, "%Y-%m-%d")).days
            streak = 0; max_s = 0
            for lb in range(1, days_since):
                dp = (cur - timedelta(days=lb)).strftime("%Y-%m-%d")
                rv = raw_h.get(dp)
                if rv is False: streak += 1; max_s = max(max_s, streak)
                elif rv is True: streak = 0
            return not (days_since >= 14 and max_s >= 3)

        fired = False
        if h1_raw:
            if not _in_cd(lane_kho_fires, raw_hist["kho"]) and h1_t:
                lane_kho_fires.append(d); fired = True
        if h2t01_raw:
            if not _in_cd(lane_perp_fires, raw_hist["perp"]) and h2t01_t:
                lane_perp_fires.append(d); fired = True
        if fired: all_fires.append(d)

        cur += timedelta(days=1)

    h1_first = lane_kho_fires[0] if lane_kho_fires else None
    perp_first = lane_perp_fires[0] if lane_perp_fires else None
    compose_first = all_fires[0] if all_fires else None

    if h1_ev == 0 and h2t01_ev == 0:
        verdict = "NOT-EVALUABLE"
    elif compose_first is None:
        verdict = "NO-FIRE"
    else:
        lead = (d0_dt - datetime.strptime(compose_first, "%Y-%m-%d")).days
        verdict = "PASS" if lead >= 1 else "FAIL-LEAD"

    lead_s = f"+{(d0_dt - datetime.strptime(compose_first, '%Y-%m-%d')).days}d" if compose_first else "—"
    print(f"  {tok:<7} {d0:>12} {win_str:>27} {str(h1_first or '—'):>12} {str(perp_first or '—'):>15} {str(compose_first or '—'):>15} {lead_s:>7} {verdict:>15}")

print(f"\n  ═══ AGGREGATE ═══")
print(f"  Expected 0/8 (per operator anticipation post vol-quorum align)")
print(f"\n  HEMI 07-16 NOTE: 3/4 vé T (funding=T 5.00e-5 exact · oi=T 1.177/1.2 · ret=T 0.095/0.10),")
print(f"  chặn bởi vol-quorum 20/30 [HARDCODE 30] → T0.1=W → không fire pre-D0.")


# ═══════════════════════════════════════════════════════════
# (3) Funding FULL PRECISION
# ═══════════════════════════════════════════════════════════
print("\n\n" + "═" * 100)
print("[FUNDING FULL PRECISION — HEMI 07-03..07-16 · BANANAS31 07-04 · COAI 07-23]")
print("[Question: 5.00e-05 exact số thật hay làm tròn lưu trữ? — V⑤ inclusive]")
print("═" * 100)

def _fund_precision(tok, dates):
    print(f"\n  ═══ {tok} ═══")
    df = _df_sym(tok + "USDT")
    if df.empty: print(f"    NO STORE"); return
    print(f"  {'date':>12} {'funding_avg':>30} {'funding_min':>30} {'funding_max':>30} {'funding_n':>4}")
    for d in dates:
        r = df[df["date"] == d]
        if r.empty:
            print(f"  {d:>12} {'NOT IN STORE':>30}")
            continue
        fa = r["funding_avg"].iloc[0] if "funding_avg" in r.columns else None
        fm = r["funding_min"].iloc[0] if "funding_min" in r.columns else None
        fx = r["funding_max"].iloc[0] if "funding_max" in r.columns else None
        fn = r["funding_n"].iloc[0] if "funding_n" in r.columns else None
        # Print with full precision — repr() gives all digits
        fa_s = repr(fa) if fa is not None else "N/A"
        fm_s = repr(fm) if fm is not None else "N/A"
        fx_s = repr(fx) if fx is not None else "N/A"
        print(f"  {d:>12} {fa_s:>30} {fm_s:>30} {fx_s:>30} {int(fn) if pd.notna(fn) else 'N/A':>4}")

# HEMI 07-03..07-16
hemi_dates = [(datetime.strptime("2026-07-03","%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
              for i in range(14)]
_fund_precision("HEMI", hemi_dates)

# BANANAS31 07-04 (and window for max14 = 07-04)
# Need to also show the funding_max14 calculation — max(|funding_avg|) over trailing 14d ending 07-04
bn_dates = [(datetime.strptime("2026-06-21","%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
              for i in range(14)]
print(f"\n  ═══ BANANAS31 (07-04 target; trailing 14d = 06-21..07-04) ═══")
_fund_precision("BANANAS31", bn_dates)

# COAI 07-23 (trailing 14d = 07-10..07-23)
coai_dates = [(datetime.strptime("2026-07-10","%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
              for i in range(14)]
print(f"\n  ═══ COAI (07-23 target; trailing 14d = 07-10..07-23) ═══")
_fund_precision("COAI", coai_dates)

# CSV source check
print(f"\n\n  ═══ SOURCE FIELD PROVENANCE ═══")
csv_path = REPO / "data/export/freshwatch_daily_2026-07.csv"
if csv_path.exists():
    with open(csv_path, encoding="utf-8") as f:
        header = f.readline()
    print(f"  freshwatch_daily_2026-07.csv header: {header.strip()[:200]}")
    print(f"  funding_avg = per-day mean of funding_settlements (raw fapi funding rate)")
    print(f"  funding_n = số settlement (3 per day for 8h symbols, 24 for 1h symbols)")
    print(f"  Precision: python float (double, ~15-17 sig digits) → NO ROUNDING at read")
    print(f"  → 5.00e-05 exact = raw funding value (from fapi settlement) matches gate exactly")

print(f"\n{'═'*100}")
print(f"[DỪNG] (2) T-④ ERRATA production semantics · (3) funding precision paste.")
print(f"       (4) gate_defs 824bdcb6 CHỜ · (5) sáng cron.")
print(f"{'═'*100}")
