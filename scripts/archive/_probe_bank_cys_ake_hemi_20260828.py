#!/usr/bin/env python3
"""[(2) BANK/CYS/AKE per-day H2-raw=T × T0.1 4 sub-vé — 2 cột tách bạch]
[(3) HEMI 07-16 4 sub-vé]

Tách 2 cột NGUYÊN THUỶ:
  giá trị    — số đo được nếu vé eligible
  chưa-eligible — n_obs actual vs floor threshold (nếu chưa đủ warmup)
"""
from __future__ import annotations
import sys, io, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
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


def _h2_raw(df, date):
    """H2 raw = compose T2 kết luận, không kể T0.1"""
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return None, "W"
    div_today = _div_avg3(df, date)
    if div_today is None: return None, "W"
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return None, "W"
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return None, "W"
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2 = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    return (v1 or v2), ("T" if (v1 or v2) else "F")


def _t01_subv(df, date):
    """T0.1 4 sub-vế tách 2 cột: giá trị vs chưa-eligible."""
    out = {}
    # funding14
    fund_14 = _v(df, date, "funding_avg", 14)
    if len(fund_14) < 14:
        out["funding_pin"] = {"value": None, "not_elig": f"n_fund={len(fund_14)}/14"}
    else:
        max_af = max(abs(f) for f in fund_14)
        pin = cfg["t0_1"]["funding_pin_abs"]
        eps = cfg["t0_1"].get("funding_pin_eps", 1e-9)
        out["funding_pin"] = {"value": max_af, "threshold": pin,
                               "pass": max_af <= pin + eps, "not_elig": None}
    # oi-floor (V②)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    if len(oi_all) < floor_obs:
        out["oi_floor"] = {"value": None, "not_elig": f"n_oi={len(oi_all)}/{floor_obs}"}
    else:
        oi_today = _t(df, date, "oi_usd")
        oi_min = min(oi_all)
        r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
        thr = cfg["t0_1"]["oi_over_min30_max"]
        out["oi_floor"] = {"value": r_oi, "threshold": thr, "floor_basis": f"{len(oi_all)}d",
                            "pass": (r_oi is not None) and (r_oi <= thr), "not_elig": None}
    # ret14 (px_15)
    px_15 = _v(df, date, "px_avg", 15)
    if len(px_15) < 15:
        out["ret14"] = {"value": None, "not_elig": f"n_px={len(px_15)}/15"}
    else:
        ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
        thr = cfg["t0_1"]["ret14_abs_max"]
        out["ret14"] = {"value": ret14, "threshold": thr, "pass": ret14 <= thr, "not_elig": None}
    # med30-vol (HARDCODE 30 per code)
    vol_30 = _v(df, date, "vol_quote", 30)
    if len(vol_30) < 30:
        out["med30_vol"] = {"value": None, "not_elig": f"n_vol={len(vol_30)}/30 [HARDCODE 30]"}
    else:
        med7 = median(vol_30[-7:]); med30 = median(vol_30)
        r = med7 / med30 if med30 > 0 else float("inf")
        thr = cfg["t0_1"]["vol_med7_over_med30_max"]
        out["med30_vol"] = {"value": r, "threshold": thr, "pass": r <= thr, "not_elig": None}
    return out


def _print_row(date, h2_val, subv):
    def _fmt(v, k):
        d = v.get(k, {})
        if d.get("not_elig"):
            return "—", d["not_elig"]
        if d.get("value") is None:
            return "—", "—"
        val = d["value"]
        thr = d.get("threshold", "")
        p = "T" if d.get("pass") else "F"
        if k == "funding_pin":
            return f"{val:.2e} ≤ {thr} → {p}", ""
        elif k == "oi_floor":
            return f"{val:.3f} ≤ {thr} → {p} [{d.get('floor_basis','')}]", ""
        elif k == "ret14":
            return f"{val:.4f} ≤ {thr} → {p}", ""
        elif k == "med30_vol":
            return f"{val:.3f} ≤ {thr} → {p}", ""
        return str(val), ""

    print(f"  ─── {date} · H2_raw={h2_val} ───")
    for k in ["funding_pin", "oi_floor", "ret14", "med30_vol"]:
        v, ne = _fmt(subv, k)
        label = {"funding_pin": "funding_pin  ", "oi_floor": "oi_floor     ",
                 "ret14": "ret14        ", "med30_vol": "med30_vol    "}[k]
        if ne:
            print(f"    {label} : chưa-eligible: {ne}")
        else:
            print(f"    {label} : {v}")


# ═══════════════════════════════════════════════════════════
# (2) BANK/CYS/AKE per-day H2-raw=T × T0.1 4 sub-vế
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[(2) BANK/CYS/AKE per-day H2-raw=T × T0.1 4 sub-vé (giá trị vs chưa-eligible tách bạch)]")
print("═" * 100)

WINDOW_START = "2026-06-01"
WINDOW_END = "2026-08-22"

for tok in ["BANK", "CYS", "AKE"]:
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"\n  {tok}: NO STORE data")
        continue
    print(f"\n\n═══ {tok} ({sym}) ═══")
    # Find all days where H2_raw = T
    start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
    end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
    h2_days = []
    for i in range((end_dt - start_dt).days + 1):
        d = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
        raw, status = _h2_raw(df, d)
        if raw is True: h2_days.append(d)
    print(f"  H2-raw=T days: {len(h2_days)} — {h2_days[:12]}{'... (+more)' if len(h2_days)>12 else ''}")
    if not h2_days:
        print(f"  ⚠ {tok}: KHÔNG có ngày H2-raw=T trong window")
        continue
    print(f"\n  T0.1 4 sub-vé từng ngày H2-raw=T:")
    for d in h2_days[:15]:
        subv = _t01_subv(df, d)
        _print_row(d, "T", subv)
    if len(h2_days) > 15:
        print(f"\n  ... ({len(h2_days) - 15} ngày còn lại omitted, xem file)")


# ═══════════════════════════════════════════════════════════
# (3) HEMI 07-16 4 sub-vế
# ═══════════════════════════════════════════════════════════
print("\n\n" + "═" * 100)
print("[(3) HEMI 07-16 4 sub-vé — kiểm boundary artifact PASS T-④]")
print("═" * 100)

df_hemi = _df_sym("HEMIUSDT")
if df_hemi.empty:
    print("  HEMI NO STORE data")
else:
    d = "2026-07-16"
    raw, status = _h2_raw(df_hemi, d)
    subv = _t01_subv(df_hemi, d)
    print(f"\n  HEMI store_start: {df_hemi['date'].min()}")
    print(f"  Target date {d}, days since store_start = {(datetime.strptime(d, '%Y-%m-%d') - datetime.strptime(df_hemi['date'].min(), '%Y-%m-%d')).days}")
    _print_row(d, status, subv)
    # Full H2 detail
    pos_14 = _v(df_hemi, d, "lsr_pos_r", 14)
    oi_all = _v(df_hemi, d, "oi_usd", 30)
    div_today = _div_avg3(df_hemi, d)
    dates = sorted(df_hemi[df_hemi["date"] <= d]["date"].tolist())[-14:]
    divs = [_div_avg3(df_hemi, dd) for dd in dates]
    divs = [v for v in divs if v is not None]
    div_min14 = min(divs) if divs else None
    pos_today = _t(df_hemi, d, "lsr_pos_r"); oi_today = _t(df_hemi, d, "oi_usd")
    pos_min14 = min(pos_14) if pos_14 else None
    oi_min = min(oi_all) if oi_all else None
    r_pos = pos_today/pos_min14 if (pos_today and pos_min14 and pos_min14 > 0) else None
    r_oi = oi_today/oi_min if (oi_today and oi_min and oi_min > 0) else None
    div_today_s = f"{div_today:.4f}" if div_today is not None else "None"
    div_min14_s = f"{div_min14:.4f}" if div_min14 is not None else "None"
    r_pos_s = f"{r_pos:.4f}" if r_pos is not None else "None"
    r_oi_s = f"{r_oi:.4f}" if r_oi is not None else "None"
    print(f"\n  H2 detail 07-16:")
    print(f"    n_pos_14={len(pos_14)} · n_oi_avail={len(oi_all)} (floor_obs_min={cfg['h2'].get('floor_obs_min',14)})")
    print(f"    div_today={div_today_s} · div_min14={div_min14_s}")
    print(f"    r_pos={r_pos_s} (≥1.25?) · r_oi={r_oi_s} (≤1.2?)")
    print(f"    → H2 raw = {status}")

print(f"\n{'═'*100}\n[DỪNG] Task (0)(1)(2)(3) done. (4) chờ 824bdcb6. (5) sáng cron.\n{'═'*100}")
