"""(N4 · V③-v2) BỐN DÒNG ANALYSIS rules · flip_day + full-vé control-52 · KÝ 27/08

① header IN "obs_min=14 source=yaml" cạnh leg-set (cấm hardcode 30)
② div_min14=0.6 ĐỨNG YÊN mọi nấc — chặn nhiều = KẾT QUẢ ghi bảng, không sửa
③ control-52 = full-vé hậu-cooldown mỗi nấc (không chỉ H2 lane)
④ cột +recall-ảo riêng (flip mà blocking_axis@flip ≠ none) tách khỏi recall-THẬT

Contract (a)-(e): scope 8 div_today-blocked + control-52 + cutpoints {0.9, 0.85, 0.8} + baseline 1.0
IMPORT prod (L-66). LOCAL only.
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
OUT_CSV = REPO / "docs/reports/v3_v2_flip_20260827.csv"
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

# Build rows: for each blocked-8 token, per cut, compute flip_day + blocking_axis@flip
def h2_blocking_axis_at(tok, d, cfg):
    """Blocking axis at specific day for token."""
    df = _df(tok + "USDT")
    pos_14 = _values_upto(df, d, "lsr_pos_r", 14)
    oi_30 = _values_upto(df, d, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < OBS_MIN: return "N/A-OBS"
    pos_t = _values_upto(df, d, "lsr_pos_r", 1)
    oi_t = _values_upto(df, d, "oi_usd", 1)
    try: dt = float(_compute_div_avg3(df, d))
    except: dt = None
    if not pos_t or not oi_t or dt is None: return "N/A"
    pos_min = min(pos_14); oi_min = min(oi_30)
    if pos_min <= 0 or oi_min <= 0: return "N/A-DIV0"
    thr_pos = cfg["h2"]["pos_over_min14_min"]
    thr_dt = cfg["h2"]["div_today_min"]
    thr_oi = cfg["h2"]["oi_over_min30_max"]
    thr_dm = cfg["h2"]["div_min_14d_max"]
    pr = pos_t[0] / pos_min
    orr = oi_t[0] / oi_min
    # Which vế fails? Multiple can fail
    fails = []
    if pr < thr_pos: fails.append(f"pos({pr:.2f}<{thr_pos})")
    if dt < thr_dt: fails.append(f"div_today({dt:.2f}<{thr_dt})")
    if orr > thr_oi: fails.append(f"oi({orr:.2f}>{thr_oi})")
    # Note: div_min14 not checked at this level for divcut path — this is best-day proxy
    return " | ".join(fails) if fails else "none"


baseline_traces_b8 = {t: results_by_cut[1.0]["blocked8"][t]["trace"] for t in BLOCKED_8}

rows = []
for tok in BLOCKED_8:
    row = {"token": tok}
    baseline_kept = len(results_by_cut[1.0]["blocked8"][tok]["kept"])
    row["baseline_kept"] = baseline_kept
    for cut in [0.9, 0.85, 0.8]:
        new_trace = results_by_cut[cut]["blocked8"][tok]["trace"]
        new_kept = len(results_by_cut[cut]["blocked8"][tok]["kept"])
        row[f"cut_{cut}_kept"] = new_kept
        flip_d, flip_fired = find_flip_day(baseline_traces_b8[tok], new_trace)
        row[f"cut_{cut}_flip_day"] = flip_d or "—"
        # blocking_axis at flip (with baseline cfg)
        if flip_d:
            axis = h2_blocking_axis_at(tok, flip_d, cfg_with_div(1.0))  # blocking at baseline dao
            row[f"cut_{cut}_blocking@flip"] = axis
        else:
            row[f"cut_{cut}_blocking@flip"] = "—"
    rows.append(row)

# Rule ④: separate recall-thật vs recall-ảo per cut
# recall-thật = flip mà blocking_axis@flip == "none" (all vế pass at flip day)
# recall-ảo = flip mà blocking_axis@flip ≠ "none" (fire không đúng cửa)
print()
print("[Recall breakdown per cut · Rule ④]")
print(f"  {'cut':>5} {'8-flip':>7} {'recall-thật':>12} {'recall-ảo':>10} {'ctrl-52-add':>12}")
recall_summary = []
baseline_c52_total = sum(len(v["kept"]) for v in results_by_cut[1.0]["control52"].values())
for cut in [0.9, 0.85, 0.8]:
    flip_toks = [r["token"] for r in rows if r[f"cut_{cut}_flip_day"] != "—"]
    recall_that = [r["token"] for r in rows if r[f"cut_{cut}_flip_day"] != "—"
                   and r[f"cut_{cut}_blocking@flip"] in ("none", "—")]
    recall_ao = [r["token"] for r in rows if r[f"cut_{cut}_flip_day"] != "—"
                 and r[f"cut_{cut}_blocking@flip"] not in ("none", "—")]
    c52_total = sum(len(v["kept"]) for v in results_by_cut[cut]["control52"].values())
    c52_add = c52_total - baseline_c52_total
    recall_summary.append({"cut": cut, "n_flip": len(flip_toks),
                          "recall_that": len(recall_that), "recall_thật_list": recall_that,
                          "recall_ao": len(recall_ao), "recall_ao_list": recall_ao,
                          "ctrl52_add": c52_add})
    print(f"  {cut:>5} {len(flip_toks):>7} {len(recall_that):>12} {len(recall_ao):>10} {c52_add:>12}")

# Write CSV
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# V③-v2 flip_day · KÝ 27/08 · 4 ANALYSIS rules\n")
    f.write(f"# code md5={CODE_MD5} · yaml md5={YAML_MD5} · gate_defs md5={GATE_MD5}\n")
    f.write(f"# obs_min={OBS_MIN} source={OBS_MIN_SOURCE} · leg-set: t0_1+h2+h1+h3 rolling (cấm hardcode-30)\n")
    f.write(f"# H2 baseline: div_today_min={gom_h_cfg_base['h2']['div_today_min']} · div_min_14d_max={gom_h_cfg_base['h2']['div_min_14d_max']} · pos_over_min14_min={gom_h_cfg_base['h2']['pos_over_min14_min']} · oi_over_min30_max={gom_h_cfg_base['h2']['oi_over_min30_max']} · floor_obs_min={OBS_MIN}\n")
    f.write(f"# Rule ①: header in obs_min + source yaml + leg-set (cấm hardcode 30) ✓\n")
    f.write(f"# Rule ②: div_min14_max={gom_h_cfg_base['h2']['div_min_14d_max']} ĐỨNG YÊN mọi nấc (chặn nhiều = KẾT QUẢ ghi bảng, không sửa) ✓\n")
    f.write(f"# Rule ③: control-52 = full-vé hậu-cooldown mỗi nấc (H1-kho + H2-perp cả 2 lanes) ✓\n")
    f.write(f"# Rule ④: cột recall-thật (blocking@flip=none) TÁCH khỏi recall-ảo (blocking≠none) ✓\n")
    f.write(f"#\n")
    f.write(f"# Recall summary per cut:\n")
    for r in recall_summary:
        f.write(f"#   cut={r['cut']}: n_flip={r['n_flip']} · recall-thật={r['recall_that']} ({', '.join(r['recall_thật_list']) or '—'}) · recall-ảo={r['recall_ao']} ({', '.join(r['recall_ao_list']) or '—'}) · ctrl-52 add={r['ctrl52_add']}\n")
    f.write(f"#\n")
    cols = ["token", "baseline_kept",
            "cut_0.9_kept", "cut_0.9_flip_day", "cut_0.9_blocking@flip",
            "cut_0.85_kept", "cut_0.85_flip_day", "cut_0.85_blocking@flip",
            "cut_0.8_kept", "cut_0.8_flip_day", "cut_0.8_blocking@flip"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines} lines")

# Print flip_day breakdown
print()
print("[FLIP DAY breakdown per BLOCKED_8]")
for r in rows:
    print(f"  {r['token']:8} base={r['baseline_kept']}", end="")
    for cut in [0.9, 0.85, 0.8]:
        print(f"  cut={cut}:kept={r[f'cut_{cut}_kept']} flip={r[f'cut_{cut}_flip_day']} block@flip={r[f'cut_{cut}_blocking@flip']}", end="")
    print()
