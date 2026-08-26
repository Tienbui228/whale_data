#!/usr/bin/env python3
"""[T-④ REGRESSION per §4 D0-table + §2 window · TREO chờ operator ký]

Reads D0 canonical from docs/proposals/gom_h_gate_defs_20260828.md (§4 markdown table).
KHÔNG hardcode D0 values.

Per operator relay (4) 28/08: "T-④ REGRESSION TREO thêm một nhịp: chạy trên §4 D0-table
+ §2 window CHỈ SAU khi operator ký dòng xung đột D0. Chuẩn bị sẵn script đọc D0 từ
file, không hardcode."

Usage (post-ký):
  python scripts/archive/_task_t4_regression_from_gate_defs_20260828.py
"""
from __future__ import annotations
import sys, io, json, hashlib, re
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

# Guard TREO
if not GATE_DEFS.exists():
    print(f"[TREO] gate_defs file MISSING: {GATE_DEFS}")
    sys.exit(0)

# Optional CLI flag to unlock TREO (operator ký D0 conflict)
if "--operator-signed-d0" not in sys.argv:
    print("═" * 80)
    print("[TREO] T-④ regression WAITING operator ký dòng xung đột D0 canonical.")
    print(f"       gate_defs md5 : {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
    print(f"       Run với --operator-signed-d0 để unlock (after chat KÝ).")
    print("═" * 80)
    # Still parse + print D0 table for visibility
    txt = GATE_DEFS.read_text(encoding="utf-8")
    m = re.search(r"## §4\..*?\n(\|.*?\n)(?=\n##|\Z)", txt, re.DOTALL)
    if m:
        print("\nD0 canonical table §4 (parsed từ file):\n")
        print(m.group(0)[:1200])
    sys.exit(0)

# ─── Parse D0 from §4 markdown table ───
def _parse_d0_table(path: Path) -> dict:
    """Extract D0 dates from §4 markdown table (line-based, robust)."""
    txt = path.read_text(encoding="utf-8")
    lines = txt.split("\n")
    out = {}
    in_section = False
    for line in lines:
        if line.startswith("## §4."):
            in_section = True; continue
        if in_section and line.startswith("## §"):
            break  # next section
        if not in_section: continue
        if not line.startswith("|"): continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 2: continue
        token = cells[0]; d0 = cells[1]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d0):
            out[token] = d0
    return out

d0_table = _parse_d0_table(GATE_DEFS)
print("═" * 100)
print(f"[T-④ REGRESSION · post-KÝ · §4 D0-table + §2 window]")
print(f"  gate_defs md5: {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
print(f"  D0 canonical ({len(d0_table)} tokens): {d0_table}")
print("═" * 100)

# ─── Standard T-④ regression logic below (post-ký) ───
# ... (identical semantic to _task_v_verdict_tables_20260828.py T-④ block,
#      but với D0 từ file, evaluation window = [max(data_start, D0-30) .. D0-1])
# TODO: chạy sau operator ký + kết hợp CSV bản mới V④-RT backfill.

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]

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


def _eval_t01(df, date):
    fund_14 = _v(df, date, "funding_avg", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    px_15 = _v(df, date, "px_avg", 15)
    vol_30 = _v(df, date, "vol_quote", 30)
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    if len(fund_14) < 14 or len(oi_all) < floor_obs or len(px_15) < 15 or len(vol_30) < floor_obs:
        return "W"
    c = cfg["t0_1"]
    pin_eps = c.get("funding_pin_eps", 1e-9)
    if not (max(abs(f) for f in fund_14) <= c["funding_pin_abs"] + pin_eps): return "F"
    oi_today = _t(df, date, "oi_usd"); oi_min = min(oi_all)
    if oi_today is None or oi_min <= 0 or (oi_today / oi_min) > c["oi_over_min30_max"]: return "F"
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else 999
    if ret14 > c["ret14_abs_max"]: return "F"
    vol_7 = vol_30[-7:]
    if median(vol_7) > median(vol_30) * c["vol_med7_over_med30_max"]: return "F"
    return "T"


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


# Load Nansen balance series for all D0 tokens
BAL_SERIES = {tok: {} for tok in d0_table.keys()}
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


def _kho_3d(tok, date):
    series = BAL_SERIES.get(tok, {})
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
    return best if best > 0 else 0.0


# ─── Regression body ───
print("\n" + "═" * 100)
print("[T-④ REGRESSION BODY · substrate STORE · V④-RT two-lane cooldown]")
print("═" * 100)

# For each token, per §2 window = [max(data_start, D0-30) .. D0-1]
print(f"\n  {'case':<7} {'D0':>12} {'window':>27} {'H1_first':>12} {'H2+T01_first':>15} {'compose_first':>15} {'lead':>7} {'verdict':>15}   reason")
print(f"  {'-'*135}")

gate_results = []
for tok, d0 in sorted(d0_table.items()):
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        gate_results.append({"tok": tok, "verdict": "NOT-EVALUABLE", "reason": "NO STORE data"})
        print(f"  {tok:<7} {d0:>12} {'—':>27} {'—':>12} {'—':>15} {'—':>15} {'—':>7} {'NOT-EVALUABLE':>15}   no store data")
        continue

    # §2 window: [max(data_start, D0-30) .. D0-1]
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    data_start = df["date"].min()
    win_start_dt = max(datetime.strptime(data_start, "%Y-%m-%d"), d0_dt - timedelta(days=30))
    win_end_dt = d0_dt - timedelta(days=1)
    if win_start_dt > win_end_dt:
        gate_results.append({"tok": tok, "verdict": "NOT-EVALUABLE", "reason": "window empty"})
        print(f"  {tok:<7} {d0:>12} EMPTY-WINDOW {'—':>12} {'—':>15} {'—':>15} {'—':>7} {'NOT-EVALUABLE':>15}   window empty")
        continue

    win_str = f"{win_start_dt.strftime('%m-%d')}..{win_end_dt.strftime('%m-%d')}"

    # Track fires per lane with V④-RT cooldown
    lane_kho_fires = []  # dates lane_kho fires (compose fire, not raw)
    lane_perp_fires = []
    all_compose_fires = []
    h1_evaluable_days = 0
    h2t01_evaluable_days = 0

    raw_hist = {"kho": {}, "perp": {}}

    cur = win_start_dt
    while cur <= win_end_dt:
        d = cur.strftime("%Y-%m-%d")
        t01 = _eval_t01(df, d)
        h2 = _eval_h2(df, d)
        kho = _kho_3d(tok, d)

        # H1 raw: kho ≥10% (regardless of T01)
        h1_raw = None
        if kho is not None:
            h1_raw = kho >= 0.10

        # H2∧T01 raw
        if h2 == "W" or t01 == "W":
            perp_raw = None
        else:
            perp_raw = (h2 == "T") and (t01 == "T")

        raw_hist["kho"][d] = h1_raw
        raw_hist["perp"][d] = perp_raw

        # Evaluability
        h1_eval = (kho is not None) and (t01 != "W")
        h2t01_eval = (h2 != "W") and (t01 != "W")
        if h1_eval: h1_evaluable_days += 1
        if h2t01_eval: h2t01_evaluable_days += 1

        # Compose fire eligibility
        h1_t = (kho is not None) and (kho >= 0.10) and (t01 == "T")
        h2t01_t = (h2 == "T") and (t01 == "T")

        # V④-RT cooldown per lane
        def _in_cd(lane_fires, raw_h):
            if not lane_fires or not raw_h: return False
            last = lane_fires[-1]
            days_since = (cur - datetime.strptime(last, "%Y-%m-%d")).days
            # count clean streak
            streak = 0
            max_s = 0
            for lb in range(1, days_since):
                dp = (cur - timedelta(days=lb)).strftime("%Y-%m-%d")
                rv = raw_h.get(dp)
                if rv is False:
                    streak += 1; max_s = max(max_s, streak)
                elif rv is True:
                    streak = 0
                # None hold
            return not (days_since >= 14 and max_s >= 3)

        # Apply cooldown, record fires
        fired_this_day = False
        if h1_raw is True:
            if not _in_cd(lane_kho_fires, raw_hist["kho"]):
                if h1_t:
                    lane_kho_fires.append(d)
                    fired_this_day = True
        if perp_raw is True:
            if not _in_cd(lane_perp_fires, raw_hist["perp"]):
                if h2t01_t:
                    lane_perp_fires.append(d)
                    fired_this_day = True
        if fired_this_day:
            all_compose_fires.append(d)

        cur += timedelta(days=1)

    # Determine first fire in each lane + compose first
    h1_first = lane_kho_fires[0] if lane_kho_fires else None
    perp_first = lane_perp_fires[0] if lane_perp_fires else None
    compose_first = all_compose_fires[0] if all_compose_fires else None

    # Evaluability
    all_h_na = (h1_evaluable_days == 0) and (h2t01_evaluable_days == 0)
    if all_h_na:
        gate_results.append({"tok": tok, "verdict": "NOT-EVALUABLE",
                              "reason": f"H all N/A trong window ({win_str})"})
        print(f"  {tok:<7} {d0:>12} {win_str:>27} {'—':>12} {'—':>15} {'—':>15} {'—':>7} {'NOT-EVALUABLE':>15}   mọi H không-evaluable")
        continue

    if compose_first is None:
        gate_results.append({"tok": tok, "verdict": "NO-FIRE",
                              "reason": f"h1_eval={h1_evaluable_days}d h2t01_eval={h2t01_evaluable_days}d"})
        print(f"  {tok:<7} {d0:>12} {win_str:>27} {'—':>12} {'—':>15} {'—':>15} {'—':>7} {'NO-FIRE':>15}   h1_eval={h1_evaluable_days}d perp_eval={h2t01_evaluable_days}d")
        continue

    d_first = datetime.strptime(compose_first, "%Y-%m-%d")
    lead = (d0_dt - d_first).days
    verdict = "PASS" if lead >= 1 else "FAIL-LEAD"
    gate_results.append({"tok": tok, "verdict": verdict, "compose_first": compose_first, "lead": lead})
    print(f"  {tok:<7} {d0:>12} {win_str:>27} {str(h1_first or '—'):>12} {str(perp_first or '—'):>15} {compose_first:>15} {f'+{lead}d':>7} {verdict:>15}   h1={h1_evaluable_days}d perp={h2t01_evaluable_days}d")

# Aggregate
evaluable = [r for r in gate_results if r["verdict"] != "NOT-EVALUABLE"]
passes = [r for r in evaluable if r["verdict"] == "PASS"]
print(f"\n  ═══ T-④ GATE VERDICT (post-D0-KÝ, §2 window, V④-RT cooldown) ═══")
print(f"  passes / evaluable : {len(passes)} / {len(evaluable)}  ({100*len(passes)/max(1,len(evaluable)):.1f}%)")
print(f"  Rút mẫu số NOT-EVALUABLE : {sum(1 for r in gate_results if r['verdict'] == 'NOT-EVALUABLE')}")
print(f"  Gate threshold §3 E1 = 6/8 (số [ ] chờ operator xác nhận)")
if len(evaluable) > 0:
    if len(passes) >= 6:
        print(f"  → E1 condition ĐẠT nếu threshold 6/8 (chờ ANALYSIS-op ký)")
    else:
        print(f"  → E1 condition CHƯA đạt threshold 6/8 (passes={len(passes)})")

print(f"\n[JSON dump]")
import json as _j
output_json = REPO / "scratch" / "t4_regression_post_d0_20260828.json"
output_json.write_text(_j.dumps({
    "spec_sha": "c8cf65b0",
    "code_sha": "166085f",
    "gate_defs_md5": hashlib.md5(open(GATE_DEFS,"rb").read()).hexdigest(),
    "d0_table": d0_table,
    "gate_results": gate_results,
    "passes_over_evaluable": f"{len(passes)}/{len(evaluable)}",
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  {output_json.name}  md5: {hashlib.md5(open(output_json,'rb').read()).hexdigest()}")
