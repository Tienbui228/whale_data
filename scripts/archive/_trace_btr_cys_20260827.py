"""Read-only trace — DIAG U-REPLAY v1 bug. NO CODE CHANGES."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
cfg_all = yaml.safe_load(open(REPO / "screen_thresholds.yaml", encoding="utf-8"))
cfg = cfg_all["gom_h"]
gn_cfg = cfg_all.get("goi_nhe", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
cfg["t0_1"]["floor_obs_min"] = OBS_MIN
cfg["h2"]["floor_obs_min"] = OBS_MIN
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})

frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)

# Balance series
BAL = {}
for p in sorted(SNAPS.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if not r: continue
        sym_u = (r.get("symbol") or "").upper()
        if not sym_u: continue
        bal = r.get("exchange_balance_tokens")
        if bal is not None:
            try: BAL.setdefault(sym_u, {})[p.stem] = float(bal)
            except: pass


def _v(df, d_str, col, n):
    s = df[df["date"] <= d_str].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]

def _t(df, d_str, col):
    r = df[df["date"] == d_str][col]
    if r.empty: return None
    try: v = float(r.iloc[0]); return v if v == v else None
    except: return None

def _div_avg3(df, d_str):
    s = df[df["date"] <= d_str].sort_values("date").tail(3)
    pairs = []
    for _, r in s.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    return sum(x[0] for x in pairs)/len(pairs) / (sum(x[1] for x in pairs)/len(pairs) or 1e-9)


# H1 kho
def eval_h1(tok, d_str):
    ingest = (_date.fromisoformat(d_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0:
        return {"kho_data": None, "step_pct": None, "ramp_pct": None, "step_raw": False, "ramp_raw": False}
    best_step = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - _td(days=lb)).isoformat()
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if best_step is None or dp > best_step: best_step = dp
    ramp = None
    d_start_r = (_date.fromisoformat(ingest) - _td(days=14)).isoformat()
    b_start_r = series.get(d_start_r)
    if b_start_r and b_start_r > 0:
        ramp = abs(b_end - b_start_r) / b_start_r
    step_raw = best_step is not None and best_step >= 0.10
    ramp_thr = kho_ramp_cfg.get("delta_min", 0.15)
    ramp_raw = ramp is not None and ramp >= ramp_thr
    return {"kho_data": b_end, "step_pct": best_step, "ramp_pct": ramp,
            "step_raw": step_raw, "ramp_raw": ramp_raw}


# H2 raw + T0.1 pass — TWO PATHS
def eval_h2_and_t01(df, d_str):
    pos_14 = _v(df, d_str, "lsr_pos_r", 14)
    oi_all = _v(df, d_str, "oi_usd", 30)
    fund_14 = _v(df, d_str, "funding_avg", 14)
    px_15 = _v(df, d_str, "px_avg", 15)
    vol_30 = _v(df, d_str, "vol_quote", 30)
    if len(pos_14) < 14 or len(oi_all) < OBS_MIN:
        return {"h2_eval": False, "h2_raw": None, "h2_ve": None, "t01_eval": False,
                "t01_pass": None, "t01_status": "N/A-WARMUP", "t01_subs": {}}
    if len(fund_14) < 14 or len(px_15) < 15 or len(vol_30) < OBS_MIN:
        return {"h2_eval": False, "h2_raw": None, "h2_ve": None, "t01_eval": False,
                "t01_pass": None, "t01_status": "N/A-WARMUP", "t01_subs": {}}
    div_today = _div_avg3(df, d_str)
    if div_today is None:
        return {"h2_eval": False, "h2_raw": None, "h2_ve": None, "t01_eval": False,
                "t01_pass": None, "t01_status": "N/A", "t01_subs": {}}
    dates = sorted(df[df["date"] <= d_str]["date"].tolist())[-14:]
    if len(dates) < 14:
        return {"h2_eval": False, "h2_raw": None, "h2_ve": None, "t01_eval": False,
                "t01_pass": None, "t01_status": "N/A", "t01_subs": {}}
    divs = [v for v in [_div_avg3(df, d) for d in dates] if v is not None]
    if not divs:
        return {"h2_eval": False, "h2_raw": None, "h2_ve": None, "t01_eval": False,
                "t01_pass": None, "t01_status": "N/A", "t01_subs": {}}
    div_min14 = min(divs)
    c_h2 = cfg["h2"]; c_t01 = cfg["t0_1"]
    v1_divcut = (div_min14 <= c_h2["div_min_14d_max"]) and (div_today >= c_h2["div_today_min"])
    pos_today = _t(df, d_str, "lsr_pos_r"); oi_today = _t(df, d_str, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2_posratio = (r_pos is not None and r_oi is not None
                   and r_pos >= c_h2["pos_over_min14_min"]
                   and r_oi <= c_h2["oi_over_min30_max"])
    h2_raw = v1_divcut or v2_posratio
    if v1_divcut and v2_posratio: ve = "cả-hai"
    elif v1_divcut: ve = "div-cut"
    elif v2_posratio: ve = "pos-ratio"
    else: ve = None
    # T0.1 subs
    subs = {}
    max_af = max(abs(f) for f in fund_14)
    eps = c_t01.get("funding_pin_eps", 1e-9)
    subs["funding_pin"] = max_af <= c_t01["funding_pin_abs"] + eps
    subs["oi_min30"] = (oi_today is not None and oi_min > 0
                       and oi_today / oi_min <= c_t01["oi_over_min30_max"])
    ret14_val = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    subs["ret14"] = ret14_val <= c_t01["ret14_abs_max"]
    med7 = median(vol_30[-7:]) if len(vol_30) >= 7 else 0
    med30 = median(vol_30) if vol_30 else 0
    subs["med30_vol"] = med7 <= c_t01["vol_med7_over_med30_max"] * med30 if med30 > 0 else False
    n_pass = sum(1 for v in subs.values() if v)
    t01_pass_strict = all(subs.values())
    t01_status = "T" if t01_pass_strict else "F"
    return {"h2_eval": True, "h2_raw": h2_raw, "h2_ve": ve,
            "t01_eval": True, "t01_pass": t01_pass_strict, "t01_status": t01_status,
            "t01_subs": subs, "t01_n_pass": n_pass}


def trace(tok, dates):
    sym = tok + "USDT"
    df = STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)
    print(f"\n═══ {tok} ({sym}) — U3-path (probe) vs T-④-path (gói-nhẹ) ═══")
    print(f"  U3-path compose PERP: h2_raw AND t01_pass  (STRICT AND)")
    print(f"  T-④-path compose PERP: h2_raw ONLY         (gói-nhẹ OR · T0.1 = CONF label)")
    print()
    print(f"  {'date':10} | {'H1 kho':^30} | {'H2/T0.1':^40} | {'U3-perp':10} | {'T-④-perp':10} | {'DIFF':6}")
    print(f"  {'-'*10}-+-{'-'*30}-+-{'-'*40}-+-{'-'*10}-+-{'-'*10}-+-{'-'*6}")
    first_diff = None
    for d_str in dates:
        h1 = eval_h1(tok, d_str)
        h2t = eval_h2_and_t01(df, d_str)
        u3_perp_fire = h2t["h2_raw"] and h2t["t01_pass"] if h2t["h2_eval"] else False
        t4_perp_fire = h2t["h2_raw"] if h2t["h2_eval"] else False
        diff = "≠" if u3_perp_fire != t4_perp_fire else "="
        if diff == "≠" and first_diff is None:
            first_diff = d_str
        # Format H1
        if h1["kho_data"] is None:
            h1_str = "NO-KHO-DATA"
        else:
            step_v = f"{h1['step_pct']*100:.1f}%" if h1['step_pct'] is not None else "—"
            ramp_v = f"{h1['ramp_pct']*100:.1f}%" if h1['ramp_pct'] is not None else "—"
            h1_str = f"step={step_v} ramp={ramp_v} raw={h1['step_raw'] or h1['ramp_raw']}"
        # Format H2/T0.1
        if not h2t["h2_eval"]:
            h2_str = "N/A-COVERAGE"
        else:
            h2_str = f"h2_raw={h2t['h2_raw']}({h2t['h2_ve']}) t01_n_pass={h2t.get('t01_n_pass','?')}/4 t01={h2t['t01_status']}"
        print(f"  {d_str:10} | {h1_str:^30} | {h2_str:^40} | {str(u3_perp_fire):10} | {str(t4_perp_fire):10} | {diff:^6}")
    if first_diff:
        print(f"\n  → FIRST DIFF DATE: {first_diff}")
        h2t = eval_h2_and_t01(df, first_diff)
        na_subs = [k for k,v in h2t["t01_subs"].items() if not v]
        print(f"     h2_raw={h2t['h2_raw']} ({h2t['h2_ve']})")
        print(f"     t01_pass_strict={h2t['t01_pass']} (need ALL 4; fail vế: {na_subs})")
        print(f"     → U3-path câm perp (T-④ path bắt gói-nhẹ H2 raw đơn)")
    else:
        print(f"\n  → NO DIFF trong dải date này")


def trace_h1_daily(tok, dates):
    """BTR trace H1 kho path — check ramp/step values."""
    print(f"\n═══ {tok} H1-KHO trace {dates[0]}..{dates[-1]} ═══")
    print(f"  {'date':10} | {'ingest':10} | {'bal_data':>15} | {'step_pct':>10} | {'ramp_pct':>10} | {'step_raw':>10} | {'ramp_raw':>10}")
    for d_str in dates:
        h1 = eval_h1(tok, d_str)
        bal_s = f"{h1['kho_data']:,.0f}" if h1['kho_data'] else "NO-DATA"
        step_s = f"{h1['step_pct']*100:.2f}%" if h1['step_pct'] is not None else "—"
        ramp_s = f"{h1['ramp_pct']*100:.2f}%" if h1['ramp_pct'] is not None else "—"
        ingest = (_date.fromisoformat(d_str) + _td(days=1)).isoformat()
        print(f"  {d_str:10} | {ingest:10} | {bal_s:>15} | {step_s:>10} | {ramp_s:>10} | {str(h1['step_raw']):>10} | {str(h1['ramp_raw']):>10}")


def coverage(tok, win_start, win_end):
    """Full coverage h1_eval + h2_eval for probe path."""
    sym = tok + "USDT"
    df = STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)
    n_h1_eval = 0; n_h1_na = 0
    n_h2_eval = 0; n_h2_na = 0
    cur = _date.fromisoformat(win_start)
    end = _date.fromisoformat(win_end)
    while cur <= end:
        h1 = eval_h1(tok, cur.isoformat())
        if h1["kho_data"] is None: n_h1_na += 1
        else: n_h1_eval += 1
        h2t = eval_h2_and_t01(df, cur.isoformat())
        if h2t["h2_eval"]: n_h2_eval += 1
        else: n_h2_na += 1
        cur += _td(days=1)
    win_days = (end - _date.fromisoformat(win_start)).days + 1
    print(f"  {tok:10} window={win_start}..{win_end} ({win_days}d) · h1_eval={n_h1_eval} h1_na={n_h1_na} · h2_eval={n_h2_eval} h2_na={n_h2_na}")


# ─── Executions ───
print("═" * 100)
print("[TRACE U3-path vs T-④-path — DIAG U-REPLAY v1 bug]")
print("═" * 100)

# 1c CYS 07-10..07-14 (mũi tách)
trace("CYS", ["2026-07-10","2026-07-11","2026-07-12","2026-07-13","2026-07-14"])

# 1b BTR 07-25..07-30
trace("BTR", ["2026-07-25","2026-07-26","2026-07-27","2026-07-28","2026-07-29","2026-07-30"])
trace_h1_daily("BTR", ["2026-07-25","2026-07-26","2026-07-27","2026-07-28","2026-07-29","2026-07-30"])

# 1d full coverage BTR CYS APR TAG
print("\n" + "═" * 100)
print("[COVERAGE ĐẦY ĐỦ SỐ — BTR · CYS · APR · TAG]")
print("═" * 100)
for tok, win_s, win_e in [
    ("BTR", "2026-07-27", "2026-08-22"),  # per-token window
    ("CYS", "2026-06-26", "2026-08-22"),
    ("APR", "2026-06-26", "2026-08-22"),
    ("TAG", "2026-06-26", "2026-08-22"),
]:
    coverage(tok, win_s, win_e)
