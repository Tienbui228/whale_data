"""(V③-v3) blocking-check REBUILD v1-only (α semantics) · KÝ 27/08 LOCAL

Fix từ V③-v2 (h2_blocking_axis_at tự dựng RETIRED per operator errata "artifact probe
tự dựng"):
  · v1-only blocking: check {div_min14 > 0.6 · div_today < 1.0-baseline} · dao sweep
    tác động chỉ v1 · blocking_axis@flip = which v1 leg fails at baseline dao
  · IMPORT prod _eval_h2 (L-66) — không rebuild leg logic
  · Cột mới: lead_vs_cross@flip · D_cross từ v3-FINAL
  · Nhãn RETIRED "recall-ảo" · MỚI: THẬT (lead≥1d) · LATE (lead<1)
  · 4 rules v2 giữ (①-④ · rule④ nhãn đổi)

Guard annex: 4 FORMULA-NEAR đã pre-cross-verified ✓ (ENSO 07-12 · FF 07-20 ·
  MUBARAK 07-28 · SQD 07-04 đều trước cross · captive labels chỉ làm chúng
  trông GẦN hơn — vẫn xa dao).
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
OUT_CSV = REPO / "docs/reports/v3_v3_flip_20260827.csv"
WINDOW_START = _date(2026, 6, 26); WINDOW_END = _date(2026, 8, 22)

cfg_all = _load_cfg()
gom_h_cfg_base = cfg_all["gom_h"]
gn_cfg = cfg_all.get("goi_nhe", {})
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
OBS_MIN_SOURCE = "yaml goi_nhe.obs_min" if gn_cfg.get("obs_min") is not None else "fallback 14"
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
        if s:
            bal = r.get("exchange_balance_tokens")
            if bal is not None:
                try: BAL.setdefault(s, {})[p.stem] = float(bal)
                except: pass

def _df(sym): return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)

def kho_step_3d(tok, target):
    ingest = (_date.fromisoformat(target) + _td(days=1)).isoformat()
    s = BAL.get(tok, {})
    b = s.get(ingest)
    if b is None or b <= 0: return None
    best = None
    for lb in range(1, 4):
        p = s.get((_date.fromisoformat(ingest) - _td(days=lb)).isoformat())
        if p is None or p <= 0: continue
        dp = abs(b - p) / p
        if best is None or dp > best: best = dp
    return best

def kho_ramp_14d(tok, target):
    ingest = (_date.fromisoformat(target) + _td(days=1)).isoformat()
    s = BAL.get(tok, {})
    b = s.get(ingest)
    if b is None or b <= 0: return None
    win = kho_ramp_cfg.get("window_days", 14)
    p = s.get((_date.fromisoformat(ingest) - _td(days=win)).isoformat())
    if p is None or p <= 0: return None
    return abs(b - p) / p

_ADAPTER = {}
def _get_adapter(ing):
    if ing not in _ADAPTER:
        try: _ADAPTER[ing] = read_adapter_daily(ing)
        except: _ADAPTER[ing] = pd.DataFrame()
    return _ADAPTER[ing]


def compose_replay(tok, cfg):
    """Full compose gói-nhẹ + cooldown 14d/3d re-arm. Return kept fires + per-day trace."""
    sym = tok + "USDT"
    df = _df(sym)
    if tok in dq_members: return [], []
    pts = WINDOW_START
    if not df.empty:
        fs = _date.fromisoformat(df["date"].min())
        pts = max(WINDOW_START, fs)
    cd = cfg.get("gom_h_cooldown_days", 14)
    cn = cfg.get("gom_h_cooldown_clean_days", 3)
    lane_state = {"kho":{"last":None,"clean":0}, "perp":{"last":None,"clean":0}}
    kept = []; trace = []
    cur = pts
    while cur <= WINDOW_END:
        d = cur.isoformat()
        adapter_df = _get_adapter((_date.fromisoformat(d) + _td(days=1)).isoformat())
        h2_status, h2_detail = _eval_h2(df, d, cfg["h2"])
        t01_status, _ = _eval_t01(df, d, cfg["t0_1"])
        _, h1_det = _eval_h1(sym, d, adapter_df, cfg["h1"], t01_status=t01_status)
        h1_step = (h1_det.get("kho_raw", "N/A") == "True")
        ramp = kho_ramp_14d(tok, d)
        h1_ramp = ramp is not None and ramp >= kho_ramp_cfg.get("delta_min", 0.15)
        h1_raw = h1_step or h1_ramp
        h2_raw = (h2_status == "T")
        day_fired = []
        for lane, raw in [("kho", h1_raw), ("perp", h2_raw)]:
            st = lane_state[lane]
            if raw:
                if st["last"] is None: can = True
                else:
                    since = (cur - _date.fromisoformat(st["last"])).days
                    can = since >= cd and st["clean"] >= cn
                if can:
                    trig = "H1-step" if (lane=="kho" and h1_step) else ("H1-ramp" if lane=="kho" else "H2")
                    kept.append({"date": d, "lane": lane, "trigger": trig})
                    day_fired.append(lane)
                    st["last"] = d; st["clean"] = 0
            else:
                st["clean"] += 1
        trace.append({"date": d, "h2_status": h2_status, "h1_step": h1_step, "h1_ramp": h1_ramp,
                      "fired": day_fired})
        cur += _td(days=1)
    return kept, trace


# ─── HEADER L-64 ĐỦ per Rule ① ───
YAML_MD5 = _md5(REPO / "screen_thresholds.yaml")
CODE_MD5 = _md5(REPO / "scripts/gom_h_daily.py")
GATE_MD5 = _md5(REPO / "docs/proposals/gom_h_gate_defs_20260828.md")

print("═" * 100)
print(f"[V③-v2 flip_day · 4 ANALYSIS rules · KÝ 27/08 · LOCAL]")
print(f"  obs_min=14 source={OBS_MIN_SOURCE}  · leg-set: t0_1 + h2 + h1 + h3 (all rolling read yaml, cấm hardcode-30)")
print(f"  code md5={CODE_MD5[:12]} · yaml md5={YAML_MD5[:12]} · gate_defs md5={GATE_MD5[:12]}")
print(f"  H2 baseline: div_today={gom_h_cfg_base['h2']['div_today_min']} · div_min14≤{gom_h_cfg_base['h2']['div_min_14d_max']} · pos≥{gom_h_cfg_base['h2']['pos_over_min14_min']} · floor_obs={OBS_MIN}")
print(f"  Rule ②: div_min14={gom_h_cfg_base['h2']['div_min_14d_max']} ĐỨNG YÊN mọi nấc — không sửa")
print("═" * 100)

# Universe control-52
symbols = _load_universe()
tokens_all = [s[:-4] if s.endswith("USDT") else s for s in symbols]
control_52 = [t for t in tokens_all if t not in D0_9CASE and t not in dq_members
              and t not in BLOCKED_8][:52]

# Baseline (dao = 1.0)
def cfg_with_div(dao):
    c = copy.deepcopy(gom_h_cfg_base)
    c["t0_1"]["floor_obs_min"] = OBS_MIN
    c["h2"]["floor_obs_min"] = OBS_MIN
    c["h2"]["div_today_min"] = dao
    # Rule ②: div_min_14d_max UNCHANGED
    return c

def run_full(tokens_list, cfg):
    """Full compose (all lanes, all vế) hậu-cooldown · Rule ③."""
    per_token = {}
    for tok in tokens_list:
        kept, trace = compose_replay(tok, cfg)
        per_token[tok] = {"kept": kept, "trace": trace}
    return per_token

def find_flip_day(baseline_trace, new_trace):
    """flip_day = ngày đầu tiên new fires nhưng baseline không (per token)."""
    b_days = {t["date"]: t["fired"] for t in baseline_trace}
    for entry in new_trace:
        if entry["fired"] and not b_days.get(entry["date"]):
            return entry["date"], entry["fired"]
    return None, None


# Run baseline + 3 cutpoints
CUTS = [1.0, 0.9, 0.85, 0.8]
results_by_cut = {}
print("[Running compose_replay for BLOCKED_8 + control_52 across 4 cuts...]")
for cut in CUTS:
    cfg = cfg_with_div(cut)
    b8 = run_full(BLOCKED_8, cfg)
    c52 = run_full(control_52, cfg)
    results_by_cut[cut] = {"blocked8": b8, "control52": c52}
    total_b8 = sum(len(v["kept"]) for v in b8.values())
    total_c52 = sum(len(v["kept"]) for v in c52.values())
    print(f"  cut={cut}: blocked8_kept={total_b8} · control52_kept={total_c52}")

# V③-v3 rebuild: blocking-check v1-ONLY (α semantics · IMPORT prod _eval_h2, không tự dựng)
# ERRATA: h2_blocking_axis_at (v2) tự dựng check-all-3-axes → RETIRED per operator ky
#   "artifact probe tự dựng" (checked v2 axes indiscriminately, mis-labeled recall-ảo)
# NEW semantic: blocking@flip = which v1 leg fails under BASELINE dao=1.0
#   dao sweep only affects v1 (div_today) → blocking = "div_today" typical, rare "div_min14"
def v1_blocking_axis_at(tok, d):
    """v1-only blocking under baseline dao=1.0. Uses prod detail via _eval_h2."""
    df = _df(tok + "USDT")
    cfg_baseline = copy.deepcopy(gom_h_cfg_base)
    cfg_baseline["h2"]["floor_obs_min"] = OBS_MIN
    _, detail = _eval_h2(df, d, cfg_baseline["h2"])  # baseline dao=1.0
    dm14 = detail.get("div_min14")
    dt = detail.get("div_today")
    if dm14 is None or dt is None: return "N/A"
    thr_dm = cfg_baseline["h2"]["div_min_14d_max"]
    thr_dt_baseline = cfg_baseline["h2"]["div_today_min"]
    fails = []
    if dm14 > thr_dm: fails.append(f"div_min14({dm14:.3f}>{thr_dm})")
    if dt < thr_dt_baseline: fails.append(f"div_today({dt:.3f}<{thr_dt_baseline})")
    return " | ".join(fails) if fails else "none"

# D_cross per BLOCKED_8 from v3-FINAL
D_CROSS = {
    "ACU":     "2026-08-13",
    "ARIA":    "2026-08-10",
    "BULLA":   "2026-07-17",
    "FHE":     "2026-08-06",
    "LIGHT":   "2026-08-08",
    "SQD":     "2026-08-10",
    "TRADOOR": "2026-08-06",
    "XNY":     "2026-07-24",
}


baseline_traces_b8 = {t: results_by_cut[1.0]["blocked8"][t]["trace"] for t in BLOCKED_8}

rows = []
for tok in BLOCKED_8:
    row = {"token": tok, "D_cross": D_CROSS.get(tok, "—")}
    baseline_kept = len(results_by_cut[1.0]["blocked8"][tok]["kept"])
    row["baseline_kept"] = baseline_kept
    for cut in [0.9, 0.85, 0.8]:
        new_trace = results_by_cut[cut]["blocked8"][tok]["trace"]
        new_kept = len(results_by_cut[cut]["blocked8"][tok]["kept"])
        row[f"cut_{cut}_kept"] = new_kept
        flip_d, flip_fired = find_flip_day(baseline_traces_b8[tok], new_trace)
        row[f"cut_{cut}_flip_day"] = flip_d or "—"
        # V③-v3: v1-only blocking under baseline
        if flip_d:
            axis = v1_blocking_axis_at(tok, flip_d)  # v1-only, baseline dao
            row[f"cut_{cut}_blocking@flip_v1"] = axis
            # lead_vs_cross = D_cross - flip_day
            dc = D_CROSS.get(tok)
            if dc:
                lead = (_date.fromisoformat(dc) - _date.fromisoformat(flip_d)).days
                row[f"cut_{cut}_lead_vs_cross"] = lead
                row[f"cut_{cut}_label"] = "THẬT" if lead >= 1 else "LATE"
            else:
                row[f"cut_{cut}_lead_vs_cross"] = ""
                row[f"cut_{cut}_label"] = "no-D_cross"
        else:
            row[f"cut_{cut}_blocking@flip_v1"] = "—"
            row[f"cut_{cut}_lead_vs_cross"] = ""
            row[f"cut_{cut}_label"] = "no-flip"
    rows.append(row)

# Rule ④ v3: THẬT (lead≥1d pre-cross) vs LATE (lead<1)
# "recall-ảo" RETIRED — errata "artifact probe tự dựng" per operator ky 27/08
print()
print("[Recall breakdown per cut · Rule ④ v3 (THẬT vs LATE)]")
print(f"  {'cut':>5} {'8-flip':>7} {'recall-thật':>12} {'recall-ảo':>10} {'ctrl-52-add':>12}")
recall_summary = []
baseline_c52_total = sum(len(v["kept"]) for v in results_by_cut[1.0]["control52"].values())
for cut in [0.9, 0.85, 0.8]:
    flip_toks = [r["token"] for r in rows if r[f"cut_{cut}_flip_day"] != "—"]
    # V③-v3: THẬT (lead≥1d) · LATE (lead<1)
    that_list = [r["token"] for r in rows if r.get(f"cut_{cut}_label") == "THẬT"]
    late_list = [r["token"] for r in rows if r.get(f"cut_{cut}_label") == "LATE"]
    c52_total = sum(len(v["kept"]) for v in results_by_cut[cut]["control52"].values())
    c52_add = c52_total - baseline_c52_total
    recall_summary.append({"cut": cut, "n_flip": len(flip_toks),
                          "n_that": len(that_list), "that_list": that_list,
                          "n_late": len(late_list), "late_list": late_list,
                          "ctrl52_add": c52_add})
    print(f"  cut={cut:.2f} n_flip={len(flip_toks)} · THẬT={len(that_list)} ({', '.join(that_list) or '—'}) · LATE={len(late_list)} ({', '.join(late_list) or '—'}) · ctrl-52 add={c52_add}")

# Write CSV
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# V③-v3 flip_day · rebuild v1-only blocking + lead_vs_cross + THẬT/LATE · KÝ 27/08\n")
    f.write(f"# ERRATA: h2_blocking_axis_at (v2) RETIRED — artifact probe tự dựng (v2 axes indiscriminate check)\n")
    f.write(f"# V③-v3: blocking@flip_v1 = which v1 leg fails under BASELINE dao=1.0 (dao sweep ảnh hưởng chỉ v1)\n")
    f.write(f"# code md5={CODE_MD5} · yaml md5={YAML_MD5} · gate_defs md5={GATE_MD5}\n")
    f.write(f"# obs_min={OBS_MIN} source={OBS_MIN_SOURCE} · leg-set: t0_1+h2+h1+h3 rolling (cấm hardcode-30)\n")
    f.write(f"# H2 baseline: div_today_min={gom_h_cfg_base['h2']['div_today_min']} · div_min_14d_max={gom_h_cfg_base['h2']['div_min_14d_max']} · pos_over_min14_min={gom_h_cfg_base['h2']['pos_over_min14_min']} · oi_over_min30_max={gom_h_cfg_base['h2']['oi_over_min30_max']} · floor_obs_min={OBS_MIN}\n")
    f.write(f"# Rules v3: ①header ✓ · ②div_min14 ĐỨNG YÊN ✓ · ③control-52 full-vé ✓ · ④ v3 THẬT (lead≥1d) vs LATE (lead<1) — recall-ảo RETIRED\n")
    f.write(f"# GUARD ANNEX: 4 FORMULA-NEAR pre-cross-verified ✓\n")
    f.write(f"#   ENSO 07-12 pre D_cross=08-06 (lead 25d) · FF 07-20 pre 08-24 (lead 35d)\n")
    f.write(f"#   MUBARAK 07-28 pre 08-08 (lead 11d)   · SQD 07-04 pre 08-10 (lead 37d)\n")
    f.write(f"#   Captive labels chỉ làm best-day trông GẦN hơn thực — vẫn xa dao.\n")
    f.write(f"# IMPORT prod (L-66): _eval_h2 IMPORT · v1_blocking_axis_at dùng detail từ prod\n")
    f.write(f"#\n")
    f.write(f"# Recall summary per cut (V③-v3):\n")
    for r in recall_summary:
        f.write(f"#   cut={r['cut']}: n_flip={r['n_flip']} · THẬT={r['n_that']} ({', '.join(r['that_list']) or '—'}) · LATE={r['n_late']} ({', '.join(r['late_list']) or '—'}) · ctrl-52 add={r['ctrl52_add']}\n")
    f.write(f"#\n")
    cols = ["token", "D_cross", "baseline_kept",
            "cut_0.9_kept", "cut_0.9_flip_day", "cut_0.9_blocking@flip_v1", "cut_0.9_lead_vs_cross", "cut_0.9_label",
            "cut_0.85_kept", "cut_0.85_flip_day", "cut_0.85_blocking@flip_v1", "cut_0.85_lead_vs_cross", "cut_0.85_label",
            "cut_0.8_kept", "cut_0.8_flip_day", "cut_0.8_blocking@flip_v1", "cut_0.8_lead_vs_cross", "cut_0.8_label"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines} lines")

# Print flip_day breakdown v3
print()
print("[FLIP DAY breakdown per BLOCKED_8 · V③-v3]")
for r in rows:
    print(f"  {r['token']:8} D_cross={r['D_cross']} base={r['baseline_kept']}")
    for cut in [0.9, 0.85, 0.8]:
        print(f"    cut={cut} kept={r[f'cut_{cut}_kept']} flip={r[f'cut_{cut}_flip_day']} v1-block={r[f'cut_{cut}_blocking@flip_v1']} lead={r[f'cut_{cut}_lead_vs_cross']}d label={r[f'cut_{cut}_label']}")
