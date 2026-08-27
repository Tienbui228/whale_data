#!/usr/bin/env python3
"""[U-REPLAY v3 ANNEX · NEAR-MISS cho 19 SÓT-vs-cross · KÝ 27/08 · L-66]

Per token trong 19 SÓT-vs-cross (từ u_replay_v3), đo KHOẢNG-CÁCH-TỚI-DAO trong
cửa sổ [per_token_start..D_cross]:
  - max(pos_r/min14)      [dao 1.25]
  - min(div_min14)        [dao 0.6]  (thấp hơn = gần dao hơn)
  - max(div_today)        [dao 1.0]
  - max(kho_step_3d)      [dao 10%]
  - max(kho_ramp_14d)     [dao 15%]
  - n_days_evaluable per trục
NEAR-MISS nếu bất kỳ trục ≥80% dao · in trục + giá trị + ngày.

6 LATE-VS-ANCHOR: first_fire_date + gap = first_fire − D_cross
  · trễ-sát (≤3d) vs trễ-cấu-trúc

Rule-shadowing note: FORMULA-MISS không thể gán dưới OR-compose bằng eval-count
  — thay bằng cột NEAR-MISS annex (không xóa nhãn cũ).

IMPORT prod hàm thật (L-66) — _values_upto, _compute_div_avg3, _eval_t01, _eval_h2.
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv
from pathlib import Path
from datetime import date as _date, timedelta as _td
from statistics import median
import pandas as pd

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

from gom_h_daily import (
    _md5, _load_cfg, _load_universe,
    _values_upto, _compute_div_avg3, _compute_div_avg3_min14,
    _eval_t01, _eval_h2, _eval_h1,
)
from adapter_h1_nansen import read_adapter_daily

SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")
V3_CSV = REPO / "docs/reports/u_replay_v3_fw139_20260827.csv"
OUT_CSV = REPO / "docs/reports/u_replay_v3_annex_nearmiss_20260827.csv"

WINDOW_START = _date(2026, 6, 26)
NEAR_MISS_PCT = 0.80  # ≥ 80% of dao

cfg_all = _load_cfg()
gom_h_cfg = cfg_all["gom_h"]
gn_cfg = cfg_all.get("goi_nhe", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
gom_h_cfg["t0_1"]["floor_obs_min"] = OBS_MIN
gom_h_cfg["h2"]["floor_obs_min"] = OBS_MIN
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})

_cfg_h2 = gom_h_cfg["h2"]
_cfg_h1 = gom_h_cfg["h1"]
THR_POS_RATIO   = _cfg_h2["pos_over_min14_min"]         # 1.25
THR_DIV_MIN14   = _cfg_h2["div_min_14d_max"]            # 0.6
THR_DIV_TODAY   = _cfg_h2["div_today_min"]              # 1.0
THR_KHO_STEP    = _cfg_h1["balance_delta_abs_min"]      # 0.10 = 10%
THR_KHO_RAMP    = kho_ramp_cfg.get("delta_min", 0.15)   # 0.15 = 15%

# ─── Read SÓT-VS-CROSS list from v3 CSV ───
sot_data = {}  # {token: {D_cross, cause}}
with open(V3_CSV, encoding="utf-8") as f:
    lines = f.readlines()
# Parse SÓT-VS-CROSS block from comment header
in_sot = False
for line in lines:
    if "SÓT-VS-CROSS đích danh" in line: in_sot = True; continue
    if in_sot and line.startswith("# SÓT-VS-RUN"): break
    if in_sot and line.startswith("#   ") and "D_run=" in line:
        # Format: "#   TOKEN     D_run=YYYY-MM-DD D_cross=YYYY-MM-DD ret_max_30d=X.XX% · cause=..."
        parts = line.strip("# ").strip().split()
        tok = parts[0]
        d_cross = next((p.split("=")[1] for p in parts if p.startswith("D_cross=")), None)
        d_run = next((p.split("=")[1] for p in parts if p.startswith("D_run=")), None)
        cause = "—"
        if "cause=" in line:
            cause = line.split("cause=")[1].strip()
        sot_data[tok] = {"D_run": d_run, "D_cross": d_cross, "cause": cause}

print(f"[ANNEX] loaded {len(sot_data)} SÓT-VS-CROSS tokens from v3 CSV")


# ─── Load STORE (freshwatch_daily) ───
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym):
    return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


# ─── Balance series ───
BAL = {}
for p in sorted(SNAPSHOTS_DIR.glob("*.json")):
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


def kho_step_3d(tok, target_date_str):
    ingest = (_date.fromisoformat(target_date_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0: return None
    best = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - _td(days=lb)).isoformat()
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if best is None or dp > best: best = dp
    return best


def kho_ramp_14d(tok, target_date_str):
    ingest = (_date.fromisoformat(target_date_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0: return None
    win = kho_ramp_cfg.get("window_days", 14)
    d_start = (_date.fromisoformat(ingest) - _td(days=win)).isoformat()
    b_start = series.get(d_start)
    if b_start is None or b_start <= 0: return None
    return abs(b_end - b_start) / b_start


# ─── Near-miss compute per token ───
def annex_token(tok, D_cross_str):
    """Return per-axis max/min + n_evaluable + near-miss flag."""
    sym = tok + "USDT"
    df = _df_sym(sym)
    per_token_start = WINDOW_START
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)
    end_date = _date.fromisoformat(D_cross_str) if D_cross_str else per_token_start
    result = {
        "max_pos_ratio": None,      "max_pos_ratio_date": None,      "n_eval_pos": 0,
        "min_div_min14": None,      "min_div_min14_date": None,      "n_eval_div_min14": 0,
        "max_div_today": None,      "max_div_today_date": None,      "n_eval_div_today": 0,
        "max_kho_step":  None,      "max_kho_step_date":  None,      "n_eval_kho_step":  0,
        "max_kho_ramp":  None,      "max_kho_ramp_date":  None,      "n_eval_kho_ramp":  0,
    }
    cur = per_token_start
    while cur <= end_date:
        d_str = cur.isoformat()
        # pos_ratio = pos_today / min(pos_14)
        pos_14 = _values_upto(df, d_str, "lsr_pos_r", 14)
        if len(pos_14) >= 14:
            pos_today = _values_upto(df, d_str, "lsr_pos_r", 1)
            if pos_today and pos_today[0] > 0 and min(pos_14) > 0:
                pr = pos_today[0] / min(pos_14)
                result["n_eval_pos"] += 1
                if result["max_pos_ratio"] is None or pr > result["max_pos_ratio"]:
                    result["max_pos_ratio"] = pr; result["max_pos_ratio_date"] = d_str
        # div_min14 (min across 14d rolling)
        div_min14 = _compute_div_avg3_min14(df, d_str)
        if div_min14 == div_min14 and not (div_min14 != div_min14):  # not NaN
            try:
                vv = float(div_min14)
                if vv != float("inf") and vv == vv:
                    result["n_eval_div_min14"] += 1
                    if result["min_div_min14"] is None or vv < result["min_div_min14"]:
                        result["min_div_min14"] = vv; result["min_div_min14_date"] = d_str
            except: pass
        # div_today
        div_today = _compute_div_avg3(df, d_str)
        try:
            vv = float(div_today)
            if vv == vv and vv != float("inf"):
                result["n_eval_div_today"] += 1
                if result["max_div_today"] is None or vv > result["max_div_today"]:
                    result["max_div_today"] = vv; result["max_div_today_date"] = d_str
        except: pass
        # kho step
        step = kho_step_3d(tok, d_str)
        if step is not None:
            result["n_eval_kho_step"] += 1
            if result["max_kho_step"] is None or step > result["max_kho_step"]:
                result["max_kho_step"] = step; result["max_kho_step_date"] = d_str
        # kho ramp
        ramp = kho_ramp_14d(tok, d_str)
        if ramp is not None:
            result["n_eval_kho_ramp"] += 1
            if result["max_kho_ramp"] is None or ramp > result["max_kho_ramp"]:
                result["max_kho_ramp"] = ramp; result["max_kho_ramp_date"] = d_str
        cur += _td(days=1)

    # Near-miss check: ≥ 80% of dao per axis
    nm_hits = []
    # Higher is closer for max_pos_ratio (dao 1.25)
    if result["max_pos_ratio"] and result["max_pos_ratio"] >= THR_POS_RATIO * NEAR_MISS_PCT:
        nm_hits.append(f"pos_ratio={result['max_pos_ratio']:.2f}@{result['max_pos_ratio_date']}")
    # LOWER is closer for min_div_min14 (dao 0.6 max, so ≤ 0.6+0.2*(1-0.8)=0.72 near-miss if we want ≥80% "close")
    # Interpretation: min_div_min14 ≤ 0.6 = pass. NEAR-MISS if 0.6 < value ≤ 0.6 / 0.8 = 0.75
    # Or simpler: percentage relative = threshold / value; if value <= 1.25 * threshold → near
    if result["min_div_min14"] is not None and result["min_div_min14"] <= THR_DIV_MIN14 / NEAR_MISS_PCT:
        nm_hits.append(f"div_min14={result['min_div_min14']:.3f}@{result['min_div_min14_date']}")
    # Higher is closer for max_div_today (dao 1.0)
    if result["max_div_today"] and result["max_div_today"] >= THR_DIV_TODAY * NEAR_MISS_PCT:
        nm_hits.append(f"div_today={result['max_div_today']:.3f}@{result['max_div_today_date']}")
    # Higher is closer for max_kho_step (dao 10%)
    if result["max_kho_step"] and result["max_kho_step"] >= THR_KHO_STEP * NEAR_MISS_PCT:
        nm_hits.append(f"kho_step={result['max_kho_step']*100:.2f}%@{result['max_kho_step_date']}")
    # Higher is closer for max_kho_ramp (dao 15%)
    if result["max_kho_ramp"] and result["max_kho_ramp"] >= THR_KHO_RAMP * NEAR_MISS_PCT:
        nm_hits.append(f"kho_ramp={result['max_kho_ramp']*100:.2f}%@{result['max_kho_ramp_date']}")

    result["near_miss"] = "Y" if nm_hits else "N"
    result["near_miss_axes"] = " | ".join(nm_hits) if nm_hits else "—"
    result["per_token_start"] = per_token_start.isoformat()
    return result


# ─── LATE-VS-ANCHOR gap analysis · reuse v3 compose_replay (import) ───
sys.path.insert(0, str(REPO / "scripts/archive"))
# v3 script is standalone (top-level exec), can't import compose_replay directly.
# Replicate its exact compose (with in-memory cooldown + prod _eval_h1 adapter path).
_ADAPTER_CACHE = {}
def _get_adapter(ingest_str):
    if ingest_str not in _ADAPTER_CACHE:
        try: _ADAPTER_CACHE[ingest_str] = read_adapter_daily(ingest_str)
        except: _ADAPTER_CACHE[ingest_str] = pd.DataFrame()
    return _ADAPTER_CACHE[ingest_str]

def first_kept_fire(tok):
    """v3-equivalent kept-fire finder: prod _eval_h1 (adapter) + cooldown state.
    Return first kept fire post per_token_start (all fires, sorted by date)."""
    sym = tok + "USDT"
    df = _df_sym(sym)
    if tok in dq_members_all: return None
    per_token_start = WINDOW_START
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)
    cd_days = gom_h_cfg.get("gom_h_cooldown_days", 14)
    cn_days = gom_h_cfg.get("gom_h_cooldown_clean_days", 3)
    lane_state = {"kho": {"last_fire": None, "clean_streak": 0},
                  "perp": {"last_fire": None, "clean_streak": 0}}
    kept = []
    end = _date(2026, 8, 31)  # look 30d past window
    cur = per_token_start
    while cur <= end:
        d_str = cur.isoformat()
        adapter_df = _get_adapter((_date.fromisoformat(d_str) + _td(days=1)).isoformat())
        h2_status, _ = _eval_h2(df, d_str, gom_h_cfg["h2"])
        t01_status, _ = _eval_t01(df, d_str, gom_h_cfg["t0_1"])
        _, h1_detail = _eval_h1(sym, d_str, adapter_df, gom_h_cfg["h1"], t01_status=t01_status)
        h1_kho_raw = h1_detail.get("kho_raw", "N/A")
        h1_step_raw = (h1_kho_raw == "True")
        ramp = kho_ramp_14d(tok, d_str)
        h1_ramp_raw = ramp is not None and ramp >= THR_KHO_RAMP
        h1_raw_gn = h1_step_raw or h1_ramp_raw
        h2_raw_gn = (h2_status == "T")
        for lane, raw_fires in [("kho", h1_raw_gn), ("perp", h2_raw_gn)]:
            state = lane_state[lane]
            if raw_fires:
                if state["last_fire"] is None:
                    can_fire = True
                else:
                    days_since = (cur - _date.fromisoformat(state["last_fire"])).days
                    can_fire = (days_since >= cd_days and state["clean_streak"] >= cn_days)
                if can_fire:
                    trig = "H1-step" if (lane == "kho" and h1_step_raw) else \
                           ("H1-ramp" if lane == "kho" else "H2")
                    kept.append({"date": d_str, "lane": lane, "trigger": trig})
                    state["last_fire"] = d_str
                    state["clean_streak"] = 0
            else:
                is_ev_false = ((lane == "kho" and (h1_kho_raw == "False" or ramp is not None))
                               or (lane == "perp" and h2_status == "F"))
                if is_ev_false: state["clean_streak"] += 1
        cur += _td(days=1)
    return min(kept, key=lambda f: f["date"]) if kept else None

dq_members_all = set(cfg_all.get("dq_serial", {}).get("members", []))


# ─── Assemble ANNEX rows ───
print(f"[ANNEX] Computing NEAR-MISS + LATE gap for {len(sot_data)} tokens...")
rows = []
for i, (tok, meta) in enumerate(sot_data.items()):
    if i % 5 == 0: print(f"  {i}/{len(sot_data)}...")
    r = annex_token(tok, meta["D_cross"])
    r["token"] = tok
    r["cause_v3"] = meta["cause"]
    r["D_run"] = meta["D_run"]
    r["D_cross"] = meta["D_cross"]

    # For LATE-VS-ANCHOR: find first kept fire (v3-equivalent compose + cooldown)
    if meta["cause"] == "LATE-VS-ANCHOR":
        ff = first_kept_fire(tok)
        if ff:
            r["first_fire_date"] = ff["date"]
            r["first_fire_trigger"] = ff["trigger"]
            gap = (_date.fromisoformat(ff["date"]) - _date.fromisoformat(meta["D_cross"])).days
            r["gap_days"] = gap
            # trễ-sát: 0 < gap ≤ 3 (fire post-cross but soon after)
            # trễ-cấu-trúc: gap > 3
            # if gap ≤ 0: fire pre-cross (should have been hit_cross=Y) — outlier
            if gap <= 0:
                r["late_type"] = "outlier-pre-cross"
            elif gap <= 3:
                r["late_type"] = "trễ-sát"
            else:
                r["late_type"] = "trễ-cấu-trúc"
        else:
            r["first_fire_date"] = ""
            r["first_fire_trigger"] = ""
            r["gap_days"] = ""
            r["late_type"] = "no-fire"
    else:
        r["first_fire_date"] = ""
        r["first_fire_trigger"] = ""
        r["gap_days"] = ""
        r["late_type"] = ""
    rows.append(r)


# ─── Write CSV ───
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
CODE_MD5 = _md5(REPO / "scripts/gom_h_daily.py")
YAML_MD5 = _md5(REPO / "screen_thresholds.yaml")
GATE_MD5 = _md5(REPO / "docs/proposals/gom_h_gate_defs_20260828.md")

with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# U-REPLAY v3 ANNEX · NEAR-MISS cho 19 SÓT-vs-cross · KÝ 27/08 · L-66\n")
    f.write(f"# code md5={CODE_MD5} · yaml md5={YAML_MD5} · gate_defs md5={GATE_MD5}\n")
    f.write(f"# Thresholds: pos_ratio={THR_POS_RATIO} · div_min14≤{THR_DIV_MIN14} · div_today≥{THR_DIV_TODAY} · kho_step≥{THR_KHO_STEP*100}% · kho_ramp≥{THR_KHO_RAMP*100}%\n")
    f.write(f"# NEAR-MISS = bất kỳ trục ≥{NEAR_MISS_PCT*100:.0f}% dao\n")
    f.write(f"#   · max_pos_ratio ≥ {THR_POS_RATIO*NEAR_MISS_PCT:.3f}\n")
    f.write(f"#   · min_div_min14 ≤ {THR_DIV_MIN14/NEAR_MISS_PCT:.3f}\n")
    f.write(f"#   · max_div_today ≥ {THR_DIV_TODAY*NEAR_MISS_PCT:.3f}\n")
    f.write(f"#   · max_kho_step  ≥ {THR_KHO_STEP*NEAR_MISS_PCT*100:.2f}%\n")
    f.write(f"#   · max_kho_ramp  ≥ {THR_KHO_RAMP*NEAR_MISS_PCT*100:.2f}%\n")
    f.write(f"#\n")
    f.write(f"# RULE-SHADOWING NOTE (khai tường minh, không xóa nhãn cũ):\n")
    f.write(f"#   FORMULA-MISS taxonomy (u_replay_v3) không thể gán dưới OR-compose bằng eval-count\n")
    f.write(f"#   — thay bằng cột NEAR-MISS annex (per-axis distance to dao). Nhãn FORMULA-MISS\n")
    f.write(f"#   trong v3 giữ nguyên cho backward compat; annex mới là ground-truth phân giải.\n")
    f.write(f"#\n")
    f.write(f"# LATE-VS-ANCHOR gap: first_fire − D_cross · trễ-sát ≤3d · trễ-cấu-trúc >3d\n")
    f.write(f"#\n")
    if rows:
        cols = ["token", "cause_v3", "D_run", "D_cross", "per_token_start",
                "max_pos_ratio", "max_pos_ratio_date", "n_eval_pos",
                "min_div_min14", "min_div_min14_date", "n_eval_div_min14",
                "max_div_today", "max_div_today_date", "n_eval_div_today",
                "max_kho_step",  "max_kho_step_date",  "n_eval_kho_step",
                "max_kho_ramp",  "max_kho_ramp_date",  "n_eval_kho_ramp",
                "near_miss", "near_miss_axes",
                "first_fire_date", "first_fire_trigger", "gap_days", "late_type"]
        # Format numeric fields as pct/decimals
        for r in rows:
            for k in ["max_pos_ratio","min_div_min14","max_div_today"]:
                if r.get(k) is not None: r[k] = f"{r[k]:.3f}"
                else: r[k] = ""
            for k in ["max_kho_step","max_kho_ramp"]:
                if r.get(k) is not None: r[k] = f"{r[k]*100:.2f}%"
                else: r[k] = ""
            for k in ["max_pos_ratio_date","min_div_min14_date","max_div_today_date",
                      "max_kho_step_date","max_kho_ramp_date"]:
                if r.get(k) is None: r[k] = ""
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV}")
print(f"[MD5] {md5_out}")
print(f"[WC]  {n_lines} lines")

# Summary
nm_yes = [r for r in rows if r["near_miss"] == "Y"]
nm_no  = [r for r in rows if r["near_miss"] == "N"]
late_rows = [r for r in rows if r["cause_v3"] == "LATE-VS-ANCHOR"]
late_sat = [r for r in late_rows if r.get("late_type") == "trễ-sát"]
late_cauTruc = [r for r in late_rows if r.get("late_type") == "trễ-cấu-trúc"]

print(f"\n[SUMMARY]")
print(f"  NEAR-MISS=Y : {len(nm_yes)}/{len(rows)}")
for r in nm_yes:
    print(f"    {r['token']:10} cause_v3={r['cause_v3']:16} axes: {r['near_miss_axes']}")
print(f"  NEAR-MISS=N : {len(nm_no)}/{len(rows)}")
for r in nm_no: print(f"    {r['token']:10} cause_v3={r['cause_v3']}")

print(f"\n[LATE-VS-ANCHOR breakdown] {len(late_rows)} tokens")
print(f"  trễ-sát  (≤3d): {len(late_sat)}")
for r in late_sat:
    print(f"    {r['token']:10} first_fire={r['first_fire_date']} trig={r['first_fire_trigger']} gap={r['gap_days']}d")
print(f"  trễ-cấu-trúc (>3d): {len(late_cauTruc)}")
for r in late_cauTruc:
    print(f"    {r['token']:10} first_fire={r['first_fire_date']} trig={r['first_fire_trigger']} gap={r['gap_days']}d")
