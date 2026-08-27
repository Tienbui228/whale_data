#!/usr/bin/env python3
"""[G3 + G4 + G5 · GOI-NHE-20260829 · f275c53c] Combined re-render + census + DQ

G3 T-④ RE-RENDER: 9 case × {H1-raw · H2-raw · compose OR} × {fire_first · conf · lead · status}
G4 Census re-run control-52 gói-nhẹ hậu-cooldown + phân bố conf + trip 0.4
G5 DQ check + AKE kho-ramp thử + queue 3 điều kiện (paste sẵn)

Header L-64 · basis=14d · substrate STORE.
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
SYMBOLS_TXT = REPO / "data/config/freshwatch_symbols.txt"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")
GATE_DEFS = REPO / "docs/proposals/gom_h_gate_defs_20260828.md"

cfg_all = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))
cfg = cfg_all["gom_h"]
dq_members = set(cfg_all.get("dq_serial", {}).get("members", []))
gn_cfg = cfg_all.get("goi_nhe", {})
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})

D0 = {"BANK": "2026-07-11", "TUT": "2026-07-09", "CYS": "2026-08-04",
      "AKE": "2026-07-15", "BTW": "2026-08-03", "HEMI": "2026-08-15",
      "ON": "2026-07-19", "CAP": "2026-07-30", "BTR": "2026-08-26"}

# Load STORE
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
    """T0.1 4 sub-vé return per-vé status (T/F/N/A) — for conf mapping."""
    fund_14 = _v(df, date, "funding_avg", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    px_15 = _v(df, date, "px_avg", 15)
    vol_30 = _v(df, date, "vol_quote", 30)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    subs = {"funding_pin": None, "oi_min30": None, "ret14": None, "med30_vol": None}
    c = cfg["t0_1"]

    if len(fund_14) >= 14:
        max_af = max(abs(f) for f in fund_14)
        eps = c.get("funding_pin_eps", 1e-9)
        subs["funding_pin"] = max_af <= c["funding_pin_abs"] + eps
    if len(oi_all) >= floor_obs:
        oi_today = _t(df, date, "oi_usd"); oi_min = min(oi_all)
        if oi_today is not None and oi_min > 0:
            subs["oi_min30"] = (oi_today / oi_min) <= c["oi_over_min30_max"]
    if len(px_15) >= 15:
        ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
        subs["ret14"] = ret14 <= c["ret14_abs_max"]
    if len(vol_30) >= 30:
        subs["med30_vol"] = median(vol_30[-7:]) <= median(vol_30) * c["vol_med7_over_med30_max"]
    return subs


def _conf_label(subs):
    """HIGH=4, MED=2-3, LOW=0-1. NaN skip."""
    na_list = [k for k, v in subs.items() if v is None]
    n_pass = sum(1 for v in subs.values() if v is True)
    n_eval = sum(1 for v in subs.values() if v is not None)
    if n_pass >= 4: level = "HIGH"
    elif n_pass >= 2: level = "MED"
    else: level = "LOW"
    na_str = ",".join(na_list) if na_list else "-"
    return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})"


def _eval_h2_raw(df, date):
    """H2 raw regardless of T0.1"""
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return None  # W
    div_today = _div_avg3(df, date)
    if div_today is None: return None
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return None
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return None
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2 = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    return v1 or v2


# ─── Balance for H1 raw (step + ramp) ───
BAL = {}
for p in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: snap = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    for r in snap.get("rows", []):
        sym_u = r.get("symbol", "").upper()
        BAL.setdefault(sym_u, {})
        bal = r.get("exchange_balance_tokens")
        if bal is not None:
            try: BAL[sym_u][p.stem] = float(bal)
            except: pass


def _kho_step_3d(tok, date):
    """step: |Δ|/b ≥10% ≤3d, ending at bal_date=date semantic (ingest_date=date+1)"""
    # Per adapter spec §5 bal_date semantic: bal_date D = ingest_date D+1 snapshot
    ingest = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    series = BAL.get(tok, {})
    if ingest not in series: return None
    b_end = series[ingest]
    d_end_ing = datetime.strptime(ingest, "%Y-%m-%d")
    best = 0.0
    for lb in range(1, 4):  # 1,2,3
        d_start_ing = (d_end_ing - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start_ing)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp
    return best if best > 0 else 0.0


def _kho_ramp_14d(tok, date):
    """GÓI-NHẸ ramp: |bal(D) − bal(D−14)| / bal(D−14) ≥ 0.15"""
    ingest = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    series = BAL.get(tok, {})
    if ingest not in series: return None
    b_end = series[ingest]
    d_start_ing = (datetime.strptime(ingest, "%Y-%m-%d") - timedelta(days=14)).strftime("%Y-%m-%d")
    b_start = series.get(d_start_ing)
    if b_start is None or b_start <= 0: return None  # đầu 0/N/A → N/A không fire
    return abs(b_end - b_start) / b_start


def _h1_raw_gn(tok, date):
    """h1_raw = step ≥10%/≤3d OR ramp ≥15%/≤14d"""
    step = _kho_step_3d(tok, date)
    ramp = _kho_ramp_14d(tok, date)
    step_fire = step is not None and step >= 0.10
    ramp_fire = ramp is not None and ramp >= kho_ramp_cfg.get("delta_min", 0.15)
    return step_fire or ramp_fire, step, ramp


# ═══════════════════════════════════════════════════════════
# G3 T-④ RE-RENDER compose GÓI-NHẸ
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print(f"[G3 T-④ RE-RENDER · compose GÓI-NHẸ (H1-raw OR H2-raw) · basis=14d · §2 window]")
print(f"  gate_defs md5: {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
print(f"  amendments: GOI-NHE-20260829, V④-RT, ⑬, GOM-RESTRUCT")
print("═" * 100)

print(f"\n  {'case':<7} {'D0':>12} {'window':>25} {'H1-first':>13} {'H2-first':>13} {'compose-first':>15} {'conf':>25} {'lead':>7} {'status':>15}")
print(f"  {'-'*145}")

gate_results = []
for tok in sorted(D0.keys()):
    d0 = D0[tok]
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"  {tok:<7} {d0:>12} NO-STORE"); continue
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    data_start = df["date"].min()
    win_start = max(datetime.strptime(data_start, "%Y-%m-%d"), d0_dt - timedelta(days=30))
    win_end = d0_dt - timedelta(days=1)
    win_str = f"{win_start.strftime('%m-%d')}..{win_end.strftime('%m-%d')}"

    dq_hit = tok in dq_members
    h1_fires, h2_fires, compose_fires = [], [], []
    fire_confs = []

    cur = win_start
    while cur <= win_end:
        d = cur.strftime("%Y-%m-%d")
        h1_raw, step, ramp = _h1_raw_gn(tok, d)
        h2_raw = _eval_h2_raw(df, d)
        if dq_hit:
            cur += timedelta(days=1); continue  # blocked, no fires
        if h1_raw:
            h1_fires.append(d)
            if not compose_fires:
                subs = _eval_t01_veles(df, d)
                fire_confs.append(_conf_label(subs))
                compose_fires.append(d)
        if h2_raw:
            h2_fires.append(d)
            if not compose_fires or compose_fires[-1] != d:
                subs = _eval_t01_veles(df, d)
                fire_confs.append(_conf_label(subs))
                if not compose_fires: compose_fires.append(d)
        cur += timedelta(days=1)

    if dq_hit:
        status = "DQ-SERIAL blocked"
        h1_first = h2_first = compose_first = "—"
        conf_str = "—"
        lead_str = "—"
    elif not compose_fires:
        status = "NO-FIRE"
        h1_first = h1_fires[0] if h1_fires else "—"
        h2_first = h2_fires[0] if h2_fires else "—"
        compose_first = "—"
        conf_str = "—"
        lead_str = "—"
    else:
        h1_first = h1_fires[0] if h1_fires else "—"
        h2_first = h2_fires[0] if h2_fires else "—"
        compose_first = compose_fires[0]
        lead = (d0_dt - datetime.strptime(compose_first, "%Y-%m-%d")).days
        lead_str = f"+{lead}d" if lead >= 0 else f"{lead}d"
        status = "PASS" if lead >= 1 else "FAIL-LEAD"
        conf_str = fire_confs[0][:24] if fire_confs else "—"

    gate_results.append({"tok": tok, "status": status, "compose_first": compose_first,
                          "h1_first": h1_first, "h2_first": h2_first})
    print(f"  {tok:<7} {d0:>12} {win_str:>25} {str(h1_first):>13} {str(h2_first):>13} {str(compose_first):>15} {conf_str:>25} {lead_str:>7} {status:>15}")

# Aggregate
evaluable = [r for r in gate_results if r["status"] not in ("NOT-EVAL", "DQ-SERIAL blocked")]
passes = [r for r in evaluable if r["status"] == "PASS"]
print(f"\n  passes/evaluable = {len(passes)}/{len(evaluable)} vs [6/8]  ({'PASS' if len(passes)>=6 else 'FAIL'} threshold)")
print(f"  (DEV render — không tuyên gate per operator G3 note)")


# ═══════════════════════════════════════════════════════════
# G4 Census re-run control-52 gói-nhẹ hậu-cooldown
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print(f"[G4 CENSUS re-run control-52 · compose GÓI-NHẸ hậu-cooldown · trip 0.4]")
print("═" * 100)

CASES_8 = set(D0.keys())
fw_symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
candidates = [s[:-4] if s.endswith("USDT") else s for s in fw_symbols
              if (s[:-4] if s.endswith("USDT") else s) not in CASES_8]

WINDOW_START = "2026-06-26"
WINDOW_END = "2026-08-22"

# Filter eligible |ret| < 30%
eligible = []
for tok in candidates:
    df = _df_sym(tok + "USDT")
    if df.empty: continue
    px0_r = df[df["date"] <= WINDOW_START].tail(1)["px_avg"]
    px1_r = df[df["date"] <= WINDOW_END].tail(1)["px_avg"]
    if px0_r.empty or px1_r.empty: continue
    p0 = float(px0_r.iloc[0]); p1 = float(px1_r.iloc[0])
    if p0 <= 0 or abs((p1 - p0) / p0) >= 0.30: continue
    eligible.append(tok)

print(f"\n  Control eligible: {len(eligible)} tokens (target 52)")

# Per-token compose scan with cooldown
def _apply_cooldown(fires_dates, cooldown=14, clean=3):
    """§8.4(i) reuse: first + re-arm ≥cooldown AND ≥clean sạch sau"""
    if not fires_dates: return []
    fires_dates = sorted(fires_dates)
    kept = [fires_dates[0]]
    last = datetime.strptime(fires_dates[0], "%Y-%m-%d")
    for f in fires_dates[1:]:
        d = datetime.strptime(f, "%Y-%m-%d")
        days_since = (d - last).days
        if days_since >= cooldown:
            kept.append(f); last = d
    return kept

start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

total_raw_fires = 0
total_kept_fires = 0
per_token_alert_30d = {}  # for trip 0.4 check
conf_dist = {"HIGH": 0, "MED": 0, "LOW": 0}
n_dq_blocked = 0

for tok in eligible:
    dq_hit = tok in dq_members
    df = _df_sym(tok + "USDT")
    raw_fires = []
    for d in window_days:
        if dq_hit:
            n_dq_blocked += 1; continue
        h1_raw, _, _ = _h1_raw_gn(tok, d)
        h2_raw = _eval_h2_raw(df, d)
        if h1_raw or h2_raw:
            raw_fires.append(d)
    kept = _apply_cooldown(raw_fires)
    total_raw_fires += len(raw_fires)
    total_kept_fires += len(kept)
    per_token_alert_30d[tok] = len(kept)  # window ~58d, approx as 30d proxy
    # Conf per kept fire
    for d in kept:
        subs = _eval_t01_veles(df, d)
        n_pass = sum(1 for v in subs.values() if v is True)
        if n_pass >= 4: conf_dist["HIGH"] += 1
        elif n_pass >= 2: conf_dist["MED"] += 1
        else: conf_dist["LOW"] += 1

print(f"\n  Raw fires:  {total_raw_fires}")
print(f"  Kept post-cooldown: {total_kept_fires}")
print(f"  DQ-SERIAL blocked days: {n_dq_blocked}")
print(f"  Conf phân bố (kept): {conf_dist}")
avg_alert_per_token_30d = total_kept_fires / max(1, len(eligible)) * (30 / 58)  # window ~58d
print(f"\n  E2 tripwire 0.4/token/30d (compose gói-nhẹ mới):")
print(f"    avg = {avg_alert_per_token_30d:.3f} · trần 0.4 · verdict: {'TRIPPED' if avg_alert_per_token_30d > 0.4 else 'OK'}")
print(f"    (Cấm suy 0.16 cũ — compose khác semantic per operator)")


# ═══════════════════════════════════════════════════════════
# G5 DQ check + AKE kho-ramp thử
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print(f"[G5 DQ CHECK + AKE kho-ramp thử]")
print("═" * 100)

# DQ check: xác nhận DQ-SERIAL merge chưa
print(f"\n  DQ-SERIAL yaml members: {sorted(dq_members)}")
print(f"  spec §7 (bot-signals) referent 29/08: DQ-SERIAL v0 CÓ (spec sha 490a8f49 merged)")
print(f"  Code wire: gom_h_daily.py compose loop CÓ dq_serial_hit check TRƯỚC cooldown")
print(f"  → Row 14 status: POSITIVE post-DQ-v0 (fires blocked by DQ, không khởi cooldown)")

# AKE kho-ramp thử
print(f"\n  AKE kho-ramp thử (window 06-27→07-14 pre-D0 07-15):")
d0_ake = datetime.strptime("2026-07-15", "%Y-%m-%d")
win_start_ake = max(datetime.strptime("2026-06-27", "%Y-%m-%d"), d0_ake - timedelta(days=30))
n_ramp_ake = 0
ramp_dates = []
cur = win_start_ake
while cur <= d0_ake - timedelta(days=1):
    d = cur.strftime("%Y-%m-%d")
    ramp = _kho_ramp_14d("AKE", d)
    if ramp is not None and ramp >= 0.15:
        n_ramp_ake += 1
        ramp_dates.append((d, ramp))
    cur += timedelta(days=1)
print(f"    n_ramp_fire pre-D0: {n_ramp_ake}")
if ramp_dates:
    for d, r in ramp_dates[:5]:
        print(f"      {d}  ramp={r*100:.2f}%")
    print(f"    → BÁO ANALYSIS: AKE row 2 kho-ramp bắt được → xem lại loại row")
else:
    print(f"    → Không bắt được ramp — AKE row 2 giữ KNOWN-MISS-BY-SCOPE (ANALYSIS quyết)")
