"""(V③-REOPEN DATA TABLE) 8 div_today-blocked tokens + control-52
Cutpoints {0.8, 0.85, 0.9, 1.0-baseline} · import prod (L-66).

For each cutpoint: mutate cfg["h2"]["div_today_min"] · replay compose gói-nhẹ
per token · count kept fires post-cooldown · in delta vs baseline.

Blocked 8: ACU · ARIA · BULLA · FHE · LIGHT · SQD · TRADOOR · XNY
Control-52: eligible tokens from census (52 outside 9-case) — reuse T-④ eligibility.
"""
from __future__ import annotations
import sys, io, json, hashlib, csv, copy
from pathlib import Path
from datetime import date as _date, timedelta as _td

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

from gom_h_daily import (
    _md5, _load_cfg, _load_universe,
    _eval_t01, _eval_h2, _eval_h1, _values_upto, _compute_div_avg3,
)
from adapter_h1_nansen import read_adapter_daily
import pandas as pd

SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
OUT_CSV = REPO / "docs/reports/v3_reopen_div_today_20260827.csv"

WINDOW_START = _date(2026, 6, 26)
WINDOW_END = _date(2026, 8, 22)

cfg_all = _load_cfg()
gom_h_cfg_baseline = cfg_all["gom_h"]
gn_cfg = cfg_all.get("goi_nhe", {})
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
dq_members = set(cfg_all.get("dq_serial", {}).get("members", []))

BLOCKED_8 = ["ACU", "ARIA", "BULLA", "FHE", "LIGHT", "SQD", "TRADOOR", "XNY"]
D0_9CASE = {"BANK","TUT","CYS","AKE","BTW","HEMI","ON","CAP","BTR"}

# Store + BAL
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)

BAL = {}
for p in sorted(SNAPS.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if not r: continue
        s = (r.get("symbol") or "").upper()
        if not s: continue
        bal = r.get("exchange_balance_tokens")
        if bal is not None:
            try: BAL.setdefault(s, {})[p.stem] = float(bal)
            except: pass


def _df_sym(sym): return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def kho_step_3d(tok, target_str):
    ingest = (_date.fromisoformat(target_str) + _td(days=1)).isoformat()
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


def kho_ramp_14d(tok, target_str):
    ingest = (_date.fromisoformat(target_str) + _td(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0: return None
    win = kho_ramp_cfg.get("window_days", 14)
    d_start = (_date.fromisoformat(ingest) - _td(days=win)).isoformat()
    b_start = series.get(d_start)
    if b_start is None or b_start <= 0: return None
    return abs(b_end - b_start) / b_start


_ADAPTER_CACHE = {}
def _get_adapter(ing):
    if ing not in _ADAPTER_CACHE:
        try: _ADAPTER_CACHE[ing] = read_adapter_daily(ing)
        except: _ADAPTER_CACHE[ing] = pd.DataFrame()
    return _ADAPTER_CACHE[ing]


def compose_replay_with_cfg(tok, gom_h_cfg):
    """Replay compose gói-nhẹ with given cfg (allowing div_today_min override)."""
    sym = tok + "USDT"
    df = _df_sym(sym)
    if tok in dq_members: return []
    per_token_start = WINDOW_START
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)
    cd_days = gom_h_cfg.get("gom_h_cooldown_days", 14)
    cn_days = gom_h_cfg.get("gom_h_cooldown_clean_days", 3)
    lane_state = {"kho": {"last_fire": None, "clean_streak": 0},
                  "perp": {"last_fire": None, "clean_streak": 0}}
    kept = []
    cur = per_token_start
    while cur <= WINDOW_END:
        d_str = cur.isoformat()
        adapter_df = _get_adapter((_date.fromisoformat(d_str) + _td(days=1)).isoformat())
        h2_status, _ = _eval_h2(df, d_str, gom_h_cfg["h2"])
        t01_status, _ = _eval_t01(df, d_str, gom_h_cfg["t0_1"])
        _, h1_detail = _eval_h1(sym, d_str, adapter_df, gom_h_cfg["h1"], t01_status=t01_status)
        h1_step_raw = (h1_detail.get("kho_raw", "N/A") == "True")
        ramp = kho_ramp_14d(tok, d_str)
        h1_ramp_raw = ramp is not None and ramp >= kho_ramp_cfg.get("delta_min", 0.15)
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
                state["clean_streak"] += 1  # simple: false OR unknown → streak
        cur += _td(days=1)
    return kept


# Print div_today at best-day for 8 tokens (baseline reference)
print("═" * 100)
print("[V③-REOPEN DATA TABLE] 8 div_today-blocked tokens")
print("═" * 100)
print(f"code md5={_md5(REPO / 'scripts/gom_h_daily.py')}  yaml md5={_md5(REPO / 'screen_thresholds.yaml')}")
print(f"Baseline H2 dao: div_today_min={gom_h_cfg_baseline['h2']['div_today_min']} · div_min14_max={gom_h_cfg_baseline['h2']['div_min_14d_max']} · pos={gom_h_cfg_baseline['h2']['pos_over_min14_min']}")
print()

# For each blocked token: find max div_today across window (best-day)
print("[div_today per token · best-day baseline]")
print(f"  {'tok':10} {'best_day':12} {'div_today':>10} {'pos_ratio':>10} {'div_min14':>10}")
best_days = {}
for tok in BLOCKED_8:
    df = _df_sym(tok + "USDT")
    if df.empty:
        print(f"  {tok:10} NO STORE")
        continue
    max_dt = None; max_day = None; max_pos = None; max_dm14 = None
    cur = WINDOW_START
    while cur <= WINDOW_END:
        d = cur.isoformat()
        try:
            dt = float(_compute_div_avg3(df, d))
        except: dt = None
        pos_14 = _values_upto(df, d, "lsr_pos_r", 14)
        pos_today = _values_upto(df, d, "lsr_pos_r", 1)
        if dt is not None and dt == dt and pos_today and pos_14:
            pos_min = min(pos_14) if pos_14 else 0
            pr = pos_today[0] / pos_min if pos_min > 0 else None
            if max_dt is None or dt > max_dt:
                max_dt = dt; max_day = d; max_pos = pr
        cur += _td(days=1)
    best_days[tok] = (max_day, max_dt, max_pos)
    pos_str = f"{max_pos:.3f}" if max_pos is not None else "N/A"
    if max_dt is not None:
        print(f"  {tok:10} {max_day or '—':12} {max_dt:>10.3f} {pos_str:>10}")
    else:
        print(f"  {tok:10} N/A")

# ─── Cutpoint sweep ───
print()
print("[CUTPOINT SWEEP · div_today thresholds {0.8, 0.85, 0.9} vs baseline 1.0]")
print("  Cột: 'blocked-8 lật' = số con trong 8 flip to have any kept fire post-cooldown")
print("        'ctrl-52 add'   = số fires MỚI trên 52 control (52 - 9-case = eligible outside 9)")
print()

# Eligible 52 = fw-139 - 9-case - DQ (loose approx from T-④ census)
symbols = _load_universe()
tokens_all = [s[:-4] if s.endswith("USDT") else s for s in symbols]
control_52 = [t for t in tokens_all if t not in D0_9CASE and t not in dq_members
              and t not in BLOCKED_8]
# Baseline: current dao 1.0
def count_fires(tokens_list, cfg_override):
    total = 0
    per_tok = {}
    for tok in tokens_list:
        kept = compose_replay_with_cfg(tok, cfg_override)
        per_tok[tok] = len(kept)
        total += len(kept)
    return total, per_tok

# Baseline dao 1.0
cfg_base = copy.deepcopy(gom_h_cfg_baseline)
cfg_base["t0_1"]["floor_obs_min"] = OBS_MIN
cfg_base["h2"]["floor_obs_min"] = OBS_MIN
baseline_8_total, baseline_8_per = count_fires(BLOCKED_8, cfg_base)
baseline_52_total, baseline_52_per = count_fires(control_52[:52], cfg_base)  # cap 52

results = []
cutpoints = [0.9, 0.85, 0.8]
for cut in cutpoints:
    cfg_cut = copy.deepcopy(gom_h_cfg_baseline)
    cfg_cut["t0_1"]["floor_obs_min"] = OBS_MIN
    cfg_cut["h2"]["floor_obs_min"] = OBS_MIN
    cfg_cut["h2"]["div_today_min"] = cut
    tot_8, per_8 = count_fires(BLOCKED_8, cfg_cut)
    tot_52, per_52 = count_fires(control_52[:52], cfg_cut)
    # Flip count for 8: tokens with 0 baseline fires but >0 in cut
    flipped_8 = [t for t in BLOCKED_8 if baseline_8_per.get(t, 0) == 0 and per_8.get(t, 0) > 0]
    # Control 52 added: sum of (cut - baseline) per token (only positive)
    ctrl_add = sum(max(0, per_52.get(t, 0) - baseline_52_per.get(t, 0)) for t in control_52[:52])
    results.append({
        "cutpoint": cut,
        "blocked8_baseline_total": baseline_8_total,
        "blocked8_at_cut_total": tot_8,
        "blocked8_flipped_count": len(flipped_8),
        "blocked8_flipped_list": ", ".join(flipped_8) if flipped_8 else "—",
        "ctrl52_baseline_total": baseline_52_total,
        "ctrl52_at_cut_total": tot_52,
        "ctrl52_added_fires": ctrl_add,
    })

print(f"  Baseline (dao=1.0): blocked-8 total kept fires = {baseline_8_total} · control-52 = {baseline_52_total}")
print()
print(f"  {'cut':>5} {'8-tot':>7} {'8-flip':>8} {'flipped':<40} {'52-tot':>7} {'52-add':>7}")
for r in results:
    print(f"  {r['cutpoint']:>5} {r['blocked8_at_cut_total']:>7} {r['blocked8_flipped_count']:>8} {r['blocked8_flipped_list']:<40} {r['ctrl52_at_cut_total']:>7} {r['ctrl52_added_fires']:>7}")

# Write CSV
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# V③-REOPEN DATA TABLE · KÝ 27/08 · 8 div_today-blocked + control-52 cutpoint sweep\n")
    f.write(f"# code md5={_md5(REPO / 'scripts/gom_h_daily.py')} · yaml md5={_md5(REPO / 'screen_thresholds.yaml')}\n")
    f.write(f"# Baseline H2 dao: div_today_min={gom_h_cfg_baseline['h2']['div_today_min']} · div_min14≤{gom_h_cfg_baseline['h2']['div_min_14d_max']} · pos≥{gom_h_cfg_baseline['h2']['pos_over_min14_min']}\n")
    f.write(f"# Import máy prod (L-66) · compose gói-nhẹ + cooldown 14d + re-arm 3d\n")
    f.write(f"# Cột: blocked-8 flipped = số con lật thành có kept fire post-cooldown\n")
    f.write(f"#       ctrl-52 added = số fires MỚI trên 52 control tokens (fw-139 - 9-case - DQ - BLOCKED_8)\n")
    f.write(f"#\n")
    f.write(f"# BEST-DAY per BLOCKED_8 (baseline):\n")
    for tok in BLOCKED_8:
        bd = best_days.get(tok)
        if bd and bd[1] is not None:
            pos_v = f"{bd[2]:.3f}" if bd[2] is not None else "N/A"
            f.write(f"#   {tok:10} best_day={bd[0]} div_today={bd[1]:.3f} pos_ratio={pos_v}\n")
    f.write(f"#\n")
    f.write(f"# BASELINE (dao=1.0): blocked-8 kept={baseline_8_total} · ctrl-52 kept={baseline_52_total}\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader()
    for r in results: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.name}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines} lines")
