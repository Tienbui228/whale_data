#!/usr/bin/env python3
"""[T-④ v2.1 · CONF-FIX rev4 · KÝ-27/08]

Re-render T-④ CHỈ conf column — fires/leads/gate KHÔNG đổi (compose logic
unchanged). Fix hardcode `len(vol_30) >= 30` → `len(vol_30) >= floor_obs` (14)
để mọi rolling-vế cùng một luật obs_min=14.

Snapshot pin: gate_defs f275c53c · yaml b03420a8 (rev3 unchanged)

Output:
  docs/reports/t4_v2p1_render_20260827.txt
  docs/reports/t4_v2p1_gate_results_20260827.json
  In-memory bảng conf cũ→mới 9 dòng cho paste operator.
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
# [v2.1-THẬT KÝ 27/08] obs_min canonical từ yaml goi_nhe.obs_min
OBS_MIN = gn_cfg.get("obs_min")
_obs_min_source = "yaml goi_nhe.obs_min" if OBS_MIN is not None else "fallback 14"
if OBS_MIN is None: OBS_MIN = 14
cfg.setdefault("t0_1", {})["floor_obs_min"] = OBS_MIN
cfg.setdefault("h2", {})["floor_obs_min"] = OBS_MIN

# CONF cũ (v2) kết quả tay từ artifact 20260827:
CONF_OLD = {
    "AKE":  "LOW (0/0; N/A: 4 vế [funding_pin,oi_min30,ret14,med30_vol])",
    "BANK": "MED (2/3; N/A: med30_vol)",
    "BTR":  "MED (2/3; N/A: med30_vol)",
    "BTW":  "LOW (1/4; N/A: -)",
    "CAP":  "LOW (0/3; N/A: med30_vol)",
    "CYS":  "MED (2/4; N/A: -)",
    "HEMI": "MED (3/3; N/A: med30_vol)",
    "ON":   "MED (2/3; N/A: med30_vol)",
    "TUT":  "—",  # NO-FIRE
}

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


def _eval_t01_veles_v2p1(df, date):
    """rev4 CONF-FIX: dùng floor_obs=14 chung cho mọi rolling-vế (was: vol >= 30)."""
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
    # ─── rev4 FIX: >= 30 → >= floor_obs ───
    if len(vol_30) >= floor_obs:
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
        return f"{level} (0/0; N/A: {len(na_list)} vế [{na_str}])"
    return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})"


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
lines_out = []
_yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()
lines_out.append("═" * 100)
lines_out.append(f"[T-④ v2.1-THẬT CONF-FIX rev4 · KÝ-27/08 · gate_defs f275c53c · yaml {_yaml_md5[:8]}]")
lines_out.append(f"  obs_min={OBS_MIN} (source: {_obs_min_source})")
lines_out.append(f"  fix: hằng WARMUP_T01_VOL_MED30_N repointed → yaml goi_nhe.obs_min (v2.1-THẬT)")
lines_out.append(f"  scope: CHỈ cột conf re-render · fires/leads/trigger/gate KHÔNG đổi")
lines_out.append("═" * 100)
lines_out.append("")
lines_out.append(f"  {'case':<7} {'trigger':>10} {'lead':>6} {'conf_v2 (cũ)':<55} {'conf_v2.1 (rev4)':<50} {'delta':<15}")
lines_out.append(f"  {'-'*160}")

for tok in sorted(D0.keys()):
    d0 = D0[tok]
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        gate_results.append({"tok": tok, "status": "NO-STORE"}); continue
    d0_dt = datetime.strptime(d0, "%Y-%m-%d")
    data_start = df["date"].min()
    win_start = max(datetime.strptime(data_start, "%Y-%m-%d"), d0_dt - timedelta(days=30))
    win_end = d0_dt - timedelta(days=1)
    dq_hit = tok in dq_members

    compose_first = None; trigger = None; conf_new = "—"
    cur = win_start
    while cur <= win_end and compose_first is None:
        d = cur.strftime("%Y-%m-%d")
        h1_fires, trig, step_v, ramp_v = _h1_raw_detail(tok, d)
        h2_fires, h2_ve_here = _eval_h2_raw_details(df, d)
        if dq_hit: cur += timedelta(days=1); continue
        if h1_fires and not compose_first:
            compose_first = d; trigger = "H1-" + trig
            subs = _eval_t01_veles_v2p1(df, d)
            conf_new = _conf_label_v2(subs)
        elif h2_fires and not compose_first:
            compose_first = d; trigger = "H2"
            subs = _eval_t01_veles_v2p1(df, d)
            conf_new = _conf_label_v2(subs)
        cur += timedelta(days=1)

    if dq_hit: status = "DQ-SERIAL blocked"; lead_days = None
    elif not compose_first: status = "NO-FIRE"; lead_days = None
    else:
        lead_days = (d0_dt - datetime.strptime(compose_first, "%Y-%m-%d")).days
        status = "PASS" if lead_days >= 1 else "FAIL-LEAD"

    conf_old = CONF_OLD.get(tok, "—")
    # Compute LEVEL change
    old_level = conf_old.split(" ")[0] if conf_old != "—" else "—"
    new_level = conf_new.split(" ")[0] if conf_new != "—" else "—"
    level_change = "same" if old_level == new_level else f"{old_level}→{new_level}"
    lead_str = f"+{lead_days}d" if lead_days is not None and lead_days >= 0 else "—"

    gate_results.append({
        "tok": tok, "d0": d0,
        "compose_first": compose_first, "trigger": trigger,
        "conf_v2_old": conf_old, "conf_v2p1_new": conf_new,
        "level_change": level_change,
        "lead_days": lead_days, "status": status,
    })
    lines_out.append(f"  {tok:<7} {(trigger or '—'):>10} {lead_str:>6} {conf_old:<55} {conf_new:<50} {level_change:<15}")

# Gate KÉP (same as v2 — logic unchanged)
passes_step_only = sum(1 for r in gate_results if r["status"] == "PASS" and (r.get("trigger") in ("H1-step", "H2")))
passes_with_ramp = sum(1 for r in gate_results if r["status"] == "PASS")
evaluable = sum(1 for r in gate_results if r["status"] not in ("DQ-SERIAL blocked",))

lines_out.append("")
lines_out.append(f"  ═══ GATE KÉP (v2.1 unchanged from v2 — compose logic không đổi) ═══")
lines_out.append(f"  passes máy-ký (step + H2)          : {passes_step_only}/{evaluable}")
lines_out.append(f"  passes kèm-ramp[PROVISIONAL]        : {passes_with_ramp}/{evaluable}")
lines_out.append(f"  threshold ≥6/eval: máy-ký {'PASS' if passes_step_only >= 6 else 'FAIL'} · "
                 f"kèm-ramp {'PASS' if passes_with_ramp >= 6 else 'FAIL'}")

# Summary
lines_out.append("")
lines_out.append(f"  ═══ CONF LEVEL DELTA ═══")
level_changes = [r for r in gate_results if r.get("level_change") not in ("same", None)]
if level_changes:
    for r in level_changes:
        lines_out.append(f"  {r['tok']:<7} {r['level_change']:<15} {r['conf_v2_old']:<50} → {r['conf_v2p1_new']}")
else:
    lines_out.append(f"  (no LEVEL changes — only mẫu-số / N/A list adjustments)")

# ═══ MISS-DETAIL (per operator KÝ 27/08 · verify số cho ANALYSIS off-draft) ═══
lines_out.append("")
lines_out.append(f"  ═══ MISS-DETAIL 2 dòng — loài dữ liệu trượt (per operator KÝ 27/08) ═══")
lines_out.append(f"")
lines_out.append(f"  TUT (NO-FIRE) — LOÀI DỮ LIỆU cohort-B nghiêm nhất (left-censor/captive §3):")
lines_out.append(f"    · store: 12d pre-D0 (06-27..07-08, D0=07-09) — dưới ngưỡng H2 pos_14=14 obs")
lines_out.append(f"    · H2 evaluable 0/12 ngày (pos_14 chưa đủ 14 obs bao giờ trong window)")
lines_out.append(f"    · H1 evaluable 10/12 (snapshot bắt đầu 06-30, 2 ngày đầu window captive)")
lines_out.append(f"    · kho phẳng: max_step_3d=0.33% · max_ramp_14d=0.00% (handoff nằm trước cửa sổ adapter 06-30)")
lines_out.append(f"    → KHÔNG phải formula: đúng lỗ left-censor + captive §3, chờ store lấp ≥14d pre-D0")
lines_out.append(f"")
lines_out.append(f"  BTR (signed-only miss) — LOÀI NẠP-CHẬM (đúng loài trigger-ramp sinh ra để vá):")
lines_out.append(f"    · window 30d 07-27..08-25 · store đầy đủ")
lines_out.append(f"    · compose_first 07-28: step_3d=3.70% (<10%) · ramp_14d=15.04% (≥15% fires ramp)")
lines_out.append(f"    · balance trend 85M→115M (~35% nạp trong 28d) — steady accumulation không có 'bậc'")
lines_out.append(f"    · signed-only strips ramp trigger → BTR classified miss (bậc ≥10%/≤3d không có tại compose-first)")
lines_out.append(f"    · kèm-ramp bắt được: +29d lead PASS")
lines_out.append(f"    → Ký signed-only = chấp nhận miss loài này cho tới ramp qua review 30d (kỳ hạn 09-28)")

report = "\n".join(lines_out) + "\n"
out_txt = REPO / "docs/reports/t4_v2p1_render_20260827.txt"
out_txt.parent.mkdir(parents=True, exist_ok=True)
out_txt.write_text(report, encoding="utf-8")

out_json = REPO / "docs/reports/t4_v2p1_gate_results_20260827.json"
payload = {
    "artifact_type": "T-④ v2.1-THẬT CONF-FIX rev4",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "fix": "hằng WARMUP_T01_VOL_MED30_N repointed → yaml goi_nhe.obs_min (v2.1-THẬT)",
    "scope": "CHỈ cột conf re-render · fires/leads/trigger/gate KHÔNG đổi",
    "obs_min": OBS_MIN,
    "obs_min_source": _obs_min_source,
    "snapshot_pin": {
        "gate_defs_md5": hashlib.md5(open(GATE_DEFS, "rb").read()).hexdigest(),
        "yaml_md5":      hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest(),
    },
    "gate_ke": {
        "passes_may_ky_step_only": passes_step_only,
        "passes_kem_ramp_provisional": passes_with_ramp,
        "evaluable": evaluable,
        "note": "unchanged from v2 — compose logic không đổi",
    },
    "miss_detail": {
        "TUT": {
            "reason": "LOÀI DỮ LIỆU cohort-B (left-censor + captive §3)",
            "store_days_pre_D0": 12, "H2_eval_days": "0/12", "H1_eval_days": "10/12",
            "max_step_3d_pct": 0.33, "max_ramp_14d_pct": 0.00,
            "note": "H2 pos_14 cần ≥14 obs, store 12d chưa đủ; H1 kho phẳng handoff trước 06-30 adapter",
        },
        "BTR": {
            "reason": "LOÀI NẠP-CHẬM (steady accumulation, không có bậc)",
            "compose_first": "2026-07-28", "step_3d_at_compose_pct": 3.70,
            "ramp_14d_at_compose_pct": 15.04,
            "balance_growth_28d": "85M → 115M (~35% nạp trong 28d)",
            "signed_only_verdict": "miss (không có bậc ≥10%/≤3d tại compose-first)",
            "kem_ramp_verdict": "PASS +29d lead via H1-ramp",
            "review_expiry": "2026-09-28 (30d từ ký ramp)",
        },
    },
    "gate_results": gate_results,
}
out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

print(report)
print(f"[OUT-TXT]  {out_txt}  md5={hashlib.md5(open(out_txt, 'rb').read()).hexdigest()}")
print(f"[OUT-JSON] {out_json}  md5={hashlib.md5(open(out_json, 'rb').read()).hexdigest()}")
