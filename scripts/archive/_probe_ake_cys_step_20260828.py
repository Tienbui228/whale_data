#!/usr/bin/env python3
"""[Task (2)+(3) per operator relay 28/08]
  (2) T-① AKE step: 06/07 · 08/07 in đủ 4 sub-vế T0.1 tại ngày cuối cửa sổ step
  (3) CYS hai-lane verify:
      (i) mọi ngày H2-fire CYS trong census/store full window
      (ii) H1 raw + T0.1 4 sub-vế từng ngày 03-05/08
      Điều kiện row: gap perp-fire→kho ≤14d ∧ H1 fire thật.
      Cảnh báo: T-① CYS 08-06 T0.1 hard-F funding 1.3e-3 → trượt → báo ANALYSIS.
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


def _eval_t01_veles(df, date):
    """T0.1 with per-vế values"""
    fund_14 = _v(df, date, "funding_avg", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    px_15 = _v(df, date, "px_avg", 15)
    vol_30 = _v(df, date, "vol_quote", 30)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    d = {"floor_basis": f"{len(oi_all)}d"}
    if len(fund_14) < 14 or len(oi_all) < floor_obs or len(px_15) < 15 or len(vol_30) < floor_obs:
        return "W", d
    c = cfg["t0_1"]
    pin_eps = c.get("funding_pin_eps", 1e-9)
    max_af = max(abs(f) for f in fund_14)
    d["max_abs_fund"] = max_af
    d["funding_pin"] = "T" if max_af <= c["funding_pin_abs"] + pin_eps else "F"
    oi_today = _t(df, date, "oi_usd"); oi_min = min(oi_all)
    r_oi = oi_today / oi_min if (oi_today and oi_min > 0) else None
    d["oi_ratio"] = r_oi
    d["oi_ok"] = "T" if (r_oi is not None and r_oi <= c["oi_over_min30_max"]) else "F"
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    d["ret14"] = ret14
    d["ret_ok"] = "T" if ret14 <= c["ret14_abs_max"] else "F"
    vol_7 = vol_30[-7:]
    med7 = median(vol_7); med30 = median(vol_30)
    d["med7"] = med7; d["med30"] = med30
    d["vol_ok"] = "T" if med7 <= med30 * c["vol_med7_over_med30_max"] else "F"
    d["overall"] = "T" if all(d[k] == "T" for k in ("funding_pin", "oi_ok", "ret_ok", "vol_ok")) else "F"
    return d["overall"], d


def _eval_h2(df, date):
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return "W"
    div_today = _div_avg3(df, date)
    if div_today is None: return "W"
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "W"
    divs = [_div_avg3(df, d) for d in dates]
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


# ─── Load Nansen balance ───
BAL_SERIES = {"AKE": {}, "CYS": {}}
for snap_path in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (snap_path.stem[:4].isdigit() and len(snap_path.stem) == 10): continue
    try: snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    ingest = snap_path.stem
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        if sym_u in BAL_SERIES:
            bal = row.get("exchange_balance_tokens")
            try:
                if bal is not None: BAL_SERIES[sym_u][ingest] = float(bal)
            except: pass


def _kho_3d_at(tok, ingest_date):
    """Return best kho over ≤3d window ending at ingest_date."""
    series = BAL_SERIES.get(tok, {})
    if ingest_date not in series: return None
    b_end = series[ingest_date]
    d_end = datetime.strptime(ingest_date, "%Y-%m-%d")
    best = 0.0; best_lb = None
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp; best_lb = lb
    return {"b_end": b_end, "best_kho": best, "best_lb": best_lb}


# ═══════════════════════════════════════════════════════════
# (2) T-① AKE step: 06/07 · 08/07 in đủ 4 sub-vế T0.1 tại ngày cuối cửa sổ step
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print(f"[(2) T-① AKE STEP — 2 ngày cuối cửa sổ step: 06/07 · 08/07]")
print(f"  yaml md5: {yaml_md5}")
print(f"  Semantic: 'ngày cuối cửa sổ step' = target date. Kho ≤3d window ending target.")
print("═" * 100)

df_ake = _df_sym("AKEUSDT")
for step_end in ["2026-07-06", "2026-07-08"]:
    print(f"\n  ─── AKE step-end = {step_end} ───")
    kho = _kho_3d_at("AKE", step_end)
    if kho and kho["best_lb"]:
        print(f"    Kho 3d: b_end={kho['b_end']:.0f} · best |Δ|/b={kho['best_kho']*100:.2f}% ({kho['best_lb']}d)")
    else:
        print(f"    Kho: MISSING balance for {step_end}")
    t01, v = _eval_t01_veles(df_ake, step_end)
    print(f"    T0.1 overall: {t01}  ·  floor_basis={v.get('floor_basis')}")
    if "max_abs_fund" in v:
        pin_abs = cfg["t0_1"]["funding_pin_abs"]
        print(f"      funding_max14 : {v['max_abs_fund']:.2e} ≤ {pin_abs} → {v['funding_pin']}")
        print(f"      oi_ratio      : {v['oi_ratio']:.4f} ≤ 1.2 → {v['oi_ok']}")
        print(f"      |ret14|       : {v['ret14']:.4f} ≤ 0.10 → {v['ret_ok']}")
        print(f"      med7/med30    : {v['med7']:.0f}/{v['med30']:.0f}={v['med7']/v['med30']:.3f} ≤ 1.0 → {v['vol_ok']}")
    else:
        print(f"      WARMUP: floor_basis {v.get('floor_basis')}")


# ═══════════════════════════════════════════════════════════
# (3) CYS hai-lane verify
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print(f"[(3) CYS HAI-LANE VERIFY]")
print(f"  Window: 2026-06-26 → 2026-08-22 census")
print(f"  Condition row: gap perp-fire → kho ≤14d ∧ H1 fire thật")
print("═" * 100)

df_cys = _df_sym("CYSUSDT")
if df_cys.empty:
    print("  CYS NO STORE data — skip")
    sys.exit(0)

# (i) H2-fires CYS trong window
print(f"\n  ═══ (i) CYS H2-fires full window ═══")
start_dt = datetime.strptime("2026-06-26", "%Y-%m-%d")
end_dt = datetime.strptime("2026-08-22", "%Y-%m-%d")
h2_fires_cys = []
h2t01_fires_cys = []
for i in range((end_dt - start_dt).days + 1):
    d = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
    h2 = _eval_h2(df_cys, d)
    t01, _ = _eval_t01_veles(df_cys, d)
    if h2 == "T":
        h2_fires_cys.append(d)
    if h2 == "T" and t01 == "T":
        h2t01_fires_cys.append(d)

print(f"  H2=T ngày: {len(h2_fires_cys)} — {h2_fires_cys[:10]}{'... (+more)' if len(h2_fires_cys)>10 else ''}")
print(f"  H2 ∧ T0.1 = perp-fire ngày: {len(h2t01_fires_cys)} — {h2t01_fires_cys}")

# (ii) H1 raw + T0.1 4 sub-vế 03-05/08
print(f"\n  ═══ (ii) CYS H1 raw + T0.1 4 sub-vế ngày 03-05/08 ═══")
for d in ["2026-08-03", "2026-08-04", "2026-08-05"]:
    print(f"\n  ─── CYS @ {d} ───")
    kho = _kho_3d_at("CYS", d)
    if kho:
        kho_raw = "T" if kho["best_kho"] >= 0.10 else "F"
        print(f"    Kho 3d: b_end={kho['b_end']:.0f} · |Δ|/b={kho['best_kho']*100:.2f}% ({kho['best_lb']}d) → kho_raw={kho_raw}")
    else:
        print(f"    Kho: MISSING balance for {d}")
    t01, v = _eval_t01_veles(df_cys, d)
    print(f"    T0.1: {t01}")
    if "max_abs_fund" in v:
        pin_abs = cfg["t0_1"]["funding_pin_abs"]
        print(f"      funding_max14 : {v['max_abs_fund']:.2e} ≤ {pin_abs} → {v['funding_pin']}")
        print(f"      oi_ratio      : {v['oi_ratio']:.4f} ≤ 1.2 → {v['oi_ok']}")
        print(f"      |ret14|       : {v['ret14']:.4f} ≤ 0.10 → {v['ret_ok']}")
        print(f"      med7/med30    : {v['med7']:.0f}/{v['med30']:.0f}={v['med7']/v['med30']:.3f} ≤ 1.0 → {v['vol_ok']}")

# Condition check: gap perp-fire → kho ≤14d ∧ H1 fire thật
print(f"\n  ═══ (iii) ROW CONDITION CHECK ═══")
if not h2t01_fires_cys:
    print(f"  ⚠ CYS không có perp-fire (H2 ∧ T0.1) nào trong window — condition FAIL")
    print(f"    → row không hợp lệ cho CYS. Báo ANALYSIS tìm ứng viên khác (per cảnh báo).")
else:
    latest_perp = max(h2t01_fires_cys)
    print(f"  Latest perp-fire CYS: {latest_perp}")
    # Check kho fires within 14d after latest_perp
    latest_perp_dt = datetime.strptime(latest_perp, "%Y-%m-%d")
    kho_fires_within = []
    for lb in range(1, 15):
        d = (latest_perp_dt + timedelta(days=lb)).strftime("%Y-%m-%d")
        kho = _kho_3d_at("CYS", d)
        if kho and kho["best_kho"] >= 0.10:
            # Need also T0.1=T for H1 fire thật
            t01, _ = _eval_t01_veles(df_cys, d)
            if t01 == "T":
                kho_fires_within.append((d, kho["best_kho"], "H1=T"))
            else:
                kho_fires_within.append((d, kho["best_kho"], f"H1=F (T0.1={t01})"))
    if kho_fires_within:
        real_h1 = [x for x in kho_fires_within if x[2] == "H1=T"]
        if real_h1:
            print(f"  ✅ Row condition PASS: {len(real_h1)} H1-fire thật trong 14d sau perp-fire {latest_perp}")
            for d, k, s in real_h1:
                gap = (datetime.strptime(d, "%Y-%m-%d") - latest_perp_dt).days
                print(f"     {d} kho={k*100:.2f}% gap={gap}d {s}")
        else:
            print(f"  ⚠ kho fires ({len(kho_fires_within)}) trong 14d nhưng KHÔNG có H1 fire thật (T0.1 fail hết)")
            for d, k, s in kho_fires_within:
                print(f"     {d} kho={k*100:.2f}% {s}")
    else:
        print(f"  ⚠ Không có kho step ≥10% trong 14d sau perp-fire {latest_perp}")

# Cảnh báo 08-06 pre-check
print(f"\n  ═══ CẢNH BÁO PRE-CHECK: CYS 08-06 T0.1 funding ═══")
t01_806, v_806 = _eval_t01_veles(df_cys, "2026-08-06")
if "max_abs_fund" in v_806:
    print(f"    CYS 08-06 funding_max14 = {v_806['max_abs_fund']:.2e}  (threshold ≤ 5e-5)")
    print(f"    funding_pin verdict = {v_806['funding_pin']}")
    if v_806['funding_pin'] == "F" and v_806['max_abs_fund'] > 1e-4:
        print(f"    ⚠ hard-F funding — per cảnh báo operator: trượt → báo ANALYSIS tìm ứng viên khác, KHÔNG ép")

print(f"\n{'═'*100}")
print(f"[DỪNG] (2)(3) done. (0)(1)(4) blocked pending gate_defs file + operator sign.")
print(f"       (5) morning nợ cũ.")
print(f"{'═'*100}")
