#!/usr/bin/env python3
"""[T-④ v2 JSON artifact · L-59 file-canonical]

Emit gate_results structured JSON + snapshot-pin metadata for ANALYSIS
machine-consumption. Companion to scratch/t4_v2_render_20260827.txt.

Reruns compose logic on same snapshot as _task_t4_rerender_v2_census_v3_20260829.py
để đảm bảo consistency (single-source-of-truth).
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
    try: v = float(r.iloc[0]); return v if v == v else None
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


def _conf_label_v2(subs):
    na_list = [k for k, v in subs.items() if v is None]
    n_pass = sum(1 for v in subs.values() if v is True)
    n_eval = sum(1 for v in subs.values() if v is not None)
    if n_pass >= 4: level = "HIGH"
    elif n_pass >= 2: level = "MED"
    else: level = "LOW"
    na_str = ",".join(na_list) if na_list else "-"
    if n_eval == 0:
        return f"{level} (0/0; N/A: {len(na_list)} vế [{na_str}])", level, n_pass, n_eval, na_list
    return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})", level, n_pass, n_eval, na_list


def _eval_h2_raw_details(df, date):
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return None, None
    div_today = _div_avg3(df, date)
    if div_today is None: return None, None
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return None, None
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return None, None
    div_min14 = min(divs)
    c = cfg["h2"]
    v1_divcut = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2_posratio = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    if v1_divcut and v2_posratio: ve = "cả-hai"
    elif v1_divcut: ve = "div-cut"
    elif v2_posratio: ve = "pos-ratio"
    else: ve = None
    return (v1_divcut or v2_posratio), ve


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
    ingest = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    series = BAL.get(tok, {})
    if ingest not in series: return None
    b_end = series[ingest]
    d_end_ing = datetime.strptime(ingest, "%Y-%m-%d")
    best = 0.0
    for lb in range(1, 4):
        d_start_ing = (d_end_ing - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start_ing)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp
    return best if best > 0 else 0.0


def _kho_ramp_14d(tok, date):
    ingest = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    series = BAL.get(tok, {})
    if ingest not in series: return None
    b_end = series[ingest]
    d_start_ing = (datetime.strptime(ingest, "%Y-%m-%d") - timedelta(days=14)).strftime("%Y-%m-%d")
    b_start = series.get(d_start_ing)
    if b_start is None or b_start <= 0: return None
    return abs(b_end - b_start) / b_start


def _h1_raw_detail(tok, date):
    step = _kho_step_3d(tok, date)
    ramp = _kho_ramp_14d(tok, date)
    step_fire = step is not None and step >= 0.10
    ramp_fire = ramp is not None and ramp >= kho_ramp_cfg.get("delta_min", 0.15)
    if step_fire: return True, "step", step, ramp
    elif ramp_fire: return True, "ramp", step, ramp
    return False, None, step, ramp


gate_results = []
for tok in sorted(D0.keys()):
    d0 = D0[tok]
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        gate_results.append({"tok": tok, "d0": d0, "status": "NO-STORE"}); continue
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    data_start = df["date"].min()
    win_start = max(datetime.strptime(data_start, "%Y-%m-%d"), d0_dt - timedelta(days=30))
    win_end = d0_dt - timedelta(days=1)
    win_str = f"{win_start.strftime('%m-%d')}..{win_end.strftime('%m-%d')}"
    dq_hit = tok in dq_members

    compose_first = None; trigger = None; h2_ve = None
    conf_str = "—"; conf_level = None; conf_pass = None; conf_eval = None; conf_na = []
    step_val = None; ramp_val = None
    cur = win_start
    while cur <= win_end and compose_first is None:
        d = cur.strftime("%Y-%m-%d")
        h1_fires, trig, step_v, ramp_v = _h1_raw_detail(tok, d)
        h2_fires, h2_ve_here = _eval_h2_raw_details(df, d)
        if dq_hit:
            cur += timedelta(days=1); continue
        if h1_fires and not compose_first:
            compose_first = d; trigger = "H1-" + trig
            step_val = step_v; ramp_val = ramp_v
            subs = _eval_t01_veles(df, d)
            conf_str, conf_level, conf_pass, conf_eval, conf_na = _conf_label_v2(subs)
        elif h2_fires and not compose_first:
            compose_first = d; trigger = "H2"; h2_ve = h2_ve_here
            step_val = step_v; ramp_val = ramp_v
            subs = _eval_t01_veles(df, d)
            conf_str, conf_level, conf_pass, conf_eval, conf_na = _conf_label_v2(subs)
        cur += timedelta(days=1)

    if dq_hit: status = "DQ-SERIAL blocked"; lead_days = None
    elif not compose_first: status = "NO-FIRE"; lead_days = None
    else:
        lead_days = (d0_dt - datetime.strptime(compose_first, "%Y-%m-%d")).days
        status = "PASS" if lead_days >= 1 else "FAIL-LEAD"

    gate_results.append({
        "tok": tok, "d0": d0, "window": win_str,
        "compose_first": compose_first, "trigger": trigger,
        "h2_ve": h2_ve, "conf_str": conf_str, "conf_level": conf_level,
        "conf_pass": conf_pass, "conf_eval": conf_eval, "conf_na": conf_na,
        "kho_step_pct": (step_val * 100 if step_val is not None else None),
        "kho_ramp_pct": (ramp_val * 100 if ramp_val is not None else None),
        "lead_days": lead_days, "status": status,
    })

passes_step_only = sum(1 for r in gate_results if r["status"] == "PASS" and (r["trigger"] == "H1-step" or r["trigger"] == "H2"))
passes_with_ramp = sum(1 for r in gate_results if r["status"] == "PASS")
evaluable = sum(1 for r in gate_results if r["status"] not in ("DQ-SERIAL blocked",))

out = {
    "artifact_type": "T-④ v2 gate_results",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "snapshot_pin": {
        "gate_defs_md5": hashlib.md5(open(GATE_DEFS, "rb").read()).hexdigest(),
        "yaml_md5": hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest(),
        "amendments": ["GOI-NHE-20260829", "V④-RT-2CHỐT-ANALYSIS-20260828",
                       "⑬-COLUMN-MANIFEST-20260826", "GOM-RESTRUCT-20260824"],
    },
    "gate_ke": {
        "passes_may_ky_step_only": passes_step_only,
        "passes_kem_ramp_provisional": passes_with_ramp,
        "evaluable": evaluable,
        "threshold_rule": "≥6/evaluable per operator (a)",
        "may_ky_verdict": "PASS" if passes_step_only >= 6 else "FAIL",
        "kem_ramp_verdict": "PASS" if passes_with_ramp >= 6 else "FAIL",
    },
    "gate_results": gate_results,
}
out_path = REPO / "scratch/t4_v2_gate_results_20260827.json"
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[OUT] {out_path}")
print(f"[MD5] {hashlib.md5(open(out_path, 'rb').read()).hexdigest()}")
print(f"[GATE-KÉP] máy-ký={passes_step_only}/{evaluable} · kèm-ramp={passes_with_ramp}/{evaluable} · threshold ≥6/eval")
