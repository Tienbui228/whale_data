#!/usr/bin/env python3
"""[T-④ re-render v2 + Census CSV v3-input · post operator (2)(3) 29/08]

(2) T-④ re-render CÙNG SNAPSHOT (gate_defs f275c53c) — 2 fixes:
  (a) col trigger per fire {step | ramp | H2-vế} + gate KÉP máy-ký vs kèm-ramp
  (b) conf display fix: mẫu số evaluable thật, N/A liệt kê ĐỦ, bỏ "conf=conf="
  AKE 0/0 explain: 4 vế N/A tại 07-05 → "(0/0; N/A: 4 vế)"

(3) Census v3-input CSV cho ANALYSIS: 85 kept + conf + trigger + tuổi + TP_FP trống
    Append-only khuôn v2. Breakdown DQ-58 per-lane per-day. HIGH-9 fires liệt kê.
"""
from __future__ import annotations
import sys, io, json, hashlib, csv
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
    """FIX v2: mẫu số = n_eval thật, N/A liệt kê ĐỦ vế thiếu, KHÔNG double 'conf=' prefix."""
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
    """H2 raw + which vế bắt {pos-ratio | div-cut | cả hai | không}"""
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


# ─── Nansen balance ───
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
    """Return (fires, trigger: 'step'|'ramp'|None, step_val, ramp_val)"""
    step = _kho_step_3d(tok, date)
    ramp = _kho_ramp_14d(tok, date)
    step_fire = step is not None and step >= 0.10
    ramp_fire = ramp is not None and ramp >= kho_ramp_cfg.get("delta_min", 0.15)
    if step_fire: return True, "step", step, ramp
    elif ramp_fire: return True, "ramp", step, ramp
    return False, None, step, ramp


# ═══════════════════════════════════════════════════════════
# (2) T-④ RE-RENDER v2 with trigger col + gate KÉP + conf fix
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print(f"[T-④ RE-RENDER v2 · GOI-NHE-20260829 · gate_defs f275c53c · L-59 file-canonical]")
print(f"  gate_defs md5: {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
print(f"  amendments: GOI-NHE-20260829 · V④-RT · ⑬ · GOM-RESTRUCT")
print(f"  fixes: (a) col trigger + gate KÉP máy-ký vs kèm-ramp")
print(f"         (b) conf display: mẫu số evaluable thật · N/A liệt kê đủ · bỏ conf=conf=")
print("═" * 100)

print(f"\n  {'case':<7} {'D0':>12} {'window':>25} {'compose-first':>15} {'trigger':>10} {'H2-vế':>10} {'conf':>35} {'lead':>7} {'status':>15}")
print(f"  {'-'*155}")

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

    compose_first = None
    trigger = None
    h2_ve = None
    conf_str = "—"
    cur = win_start
    while cur <= win_end and compose_first is None:
        d = cur.strftime("%Y-%m-%d")
        h1_fires, trig, step_v, ramp_v = _h1_raw_detail(tok, d)
        h2_fires, h2_ve_here = _eval_h2_raw_details(df, d)
        if dq_hit:
            cur += timedelta(days=1); continue
        if h1_fires and not compose_first:
            compose_first = d; trigger = "H1-" + trig
            subs = _eval_t01_veles(df, d)
            conf_str = _conf_label_v2(subs)
        elif h2_fires and not compose_first:
            compose_first = d; trigger = "H2"; h2_ve = h2_ve_here
            subs = _eval_t01_veles(df, d)
            conf_str = _conf_label_v2(subs)
        cur += timedelta(days=1)

    if dq_hit:
        status = "DQ-SERIAL blocked"; lead_str = "—"
    elif not compose_first:
        status = "NO-FIRE"; lead_str = "—"
    else:
        lead = (d0_dt - datetime.strptime(compose_first, "%Y-%m-%d")).days
        lead_str = f"+{lead}d" if lead >= 0 else f"{lead}d"
        status = "PASS" if lead >= 1 else "FAIL-LEAD"

    gate_results.append({
        "tok": tok, "d0": d0, "window": win_str,
        "compose_first": compose_first or "—", "trigger": trigger or "—",
        "h2_ve": h2_ve or "—", "conf": conf_str, "lead": lead_str, "status": status,
    })
    print(f"  {tok:<7} {d0:>12} {win_str:>25} {str(compose_first or '—'):>15} "
          f"{str(trigger or '—'):>10} {str(h2_ve or '—'):>10} {conf_str:>35} {lead_str:>7} {status:>15}")

# Gate KÉP: passes máy-ký (step only) vs passes kèm-ramp (step OR ramp)
# Compute alternative: nếu strip ramp triggers
passes_step_only = sum(1 for r in gate_results if r["status"] == "PASS" and (r["trigger"] == "H1-step" or r["trigger"] == "H2"))
passes_with_ramp = sum(1 for r in gate_results if r["status"] == "PASS")
evaluable = sum(1 for r in gate_results if r["status"] not in ("DQ-SERIAL blocked",))

print(f"\n  ═══ GATE KÉP ═══")
print(f"  passes máy-ký (step-only trigger) : {passes_step_only}/{evaluable}")
print(f"  passes kèm-ramp[PROVISIONAL]      : {passes_with_ramp}/{evaluable}")
print(f"  threshold [6/8] · máy-ký {'PASS' if passes_step_only >= 6 else 'FAIL'} · "
      f"kèm-ramp {'PASS' if passes_with_ramp >= 6 else 'FAIL'}")

# AKE 0/0 explain
print(f"\n  AKE 0/0 explain (07-05):")
df_ake = _df_sym("AKEUSDT")
subs_ake = _eval_t01_veles(df_ake, "2026-07-05")
print(f"    subs: {subs_ake}")
na_veles = [k for k, v in subs_ake.items() if v is None]
print(f"    → {len(na_veles)}/4 vế N/A: {na_veles}")
print(f"    → conf label: {_conf_label_v2(subs_ake)}")


# ═══════════════════════════════════════════════════════════
# (3) CENSUS v3-input CSV for ANALYSIS
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print(f"[CENSUS v3-input · 85 kept gói-nhẹ + conf/trigger/tuổi/TP_FP · append-only khuôn v2]")
print("═" * 100)

CASES_8 = set(D0.keys())
fw_symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
candidates = [s[:-4] if s.endswith("USDT") else s for s in fw_symbols
              if (s[:-4] if s.endswith("USDT") else s) not in CASES_8]

WINDOW_START = "2026-06-26"
WINDOW_END = "2026-08-22"
TODAY = datetime.now(timezone.utc).date()

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

def _apply_cooldown(fires_dates, cooldown=14):
    if not fires_dates: return []
    fires_dates = sorted(fires_dates)
    kept = [fires_dates[0]]
    last = datetime.strptime(fires_dates[0], "%Y-%m-%d")
    for f in fires_dates[1:]:
        d = datetime.strptime(f, "%Y-%m-%d")
        if (d - last).days >= cooldown:
            kept.append(f); last = d
    return kept

start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

# Per-token scan
census_rows = []  # kept fires with details
dq_breakdown = {"BANANAS31": {"lane_kho_days": 0, "lane_perp_days": 0}}
high_9_fires = []
conf_totals = {"HIGH": 0, "MED": 0, "LOW": 0}

for tok in eligible:
    dq_hit = tok in dq_members
    df = _df_sym(tok + "USDT")
    raw_fires = []  # {date, trigger, h2_ve, kho_val, ramp_val, subs}
    for d in window_days:
        if dq_hit:
            # count DQ per lane per day
            h1_fires, _, _, _ = _h1_raw_detail(tok, d)
            h2_fires, _ = _eval_h2_raw_details(df, d)
            if h1_fires: dq_breakdown[tok]["lane_kho_days"] += 1
            if h2_fires: dq_breakdown[tok]["lane_perp_days"] += 1
            continue
        h1_fires, trig, step_v, ramp_v = _h1_raw_detail(tok, d)
        h2_fires, h2_ve = _eval_h2_raw_details(df, d)
        if h1_fires:
            raw_fires.append({"date": d, "trigger": "H1-" + trig, "h2_ve": None,
                              "step_val": step_v, "ramp_val": ramp_v})
        elif h2_fires:
            raw_fires.append({"date": d, "trigger": "H2", "h2_ve": h2_ve,
                              "step_val": step_v, "ramp_val": ramp_v})
    kept = _apply_cooldown([r["date"] for r in raw_fires])
    for r in raw_fires:
        if r["date"] not in kept: continue
        subs = _eval_t01_veles(df, r["date"])
        conf = _conf_label_v2(subs)
        n_pass = sum(1 for v in subs.values() if v is True)
        if n_pass >= 4: conf_totals["HIGH"] += 1; high_9_fires.append((tok, r["date"], conf, r["trigger"]))
        elif n_pass >= 2: conf_totals["MED"] += 1
        else: conf_totals["LOW"] += 1
        fire_dt = datetime.strptime(r["date"], "%Y-%m-%d").date()
        age = (TODAY - fire_dt).days
        census_rows.append({
            "token": tok, "date": r["date"],
            "trigger": r["trigger"],
            "h2_ve": r["h2_ve"] or "-",
            "conf": conf,
            "step_pct": f"{r['step_val']*100:.2f}" if r["step_val"] else "N/A",
            "ramp_pct": f"{r['ramp_val']*100:.2f}" if r["ramp_val"] else "N/A",
            "age_days": age,
            "TP_FP": "",
        })

print(f"\n  Eligible: {len(eligible)} · Kept fires (gói-nhẹ hậu-cooldown): {len(census_rows)}")
print(f"  Conf phân bố: HIGH={conf_totals['HIGH']} · MED={conf_totals['MED']} · LOW={conf_totals['LOW']}")

# DQ-58 breakdown
print(f"\n  ═══ DQ-58 breakdown per-lane per-day ═══")
for tok, cnt in dq_breakdown.items():
    total = cnt["lane_kho_days"] + cnt["lane_perp_days"]
    print(f"    {tok}: lane_kho={cnt['lane_kho_days']}d · lane_perp={cnt['lane_perp_days']}d · total={total} (KHÔNG khởi cooldown)")

# HIGH-9 fires list
print(f"\n  ═══ HIGH-{conf_totals['HIGH']} fires (ưu tiên ANALYSIS chấm) ═══")
for tok, d, conf, trig in high_9_fires:
    print(f"    {tok:<10} {d}  trigger={trig:>8}  {conf}")

# Write CSV
out_csv = REPO / "scratch/census_63_grades_v3_input_20260829.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    f.write("# CENSUS v3-input · gói-nhẹ compose OR · kept post-cooldown · TP_FP trống chờ ANALYSIS\n")
    f.write("# TP = ≥+50% close D0..D+30 hoặc trong campaign niêm; tuổi<30d = PENDING\n")
    f.write("# fire_age_days = today (2026-08-27) − date\n")
    f.write("# trigger ∈ {H1-step, H1-ramp, H2} · h2_ve ∈ {pos-ratio, div-cut, cả-hai, -}\n")
    f.write("# conf = LEVEL (n_pass/n_eval; N/A: <list vế N/A>)\n")
    f.write(f"# generated_at: {datetime.now(timezone.utc).isoformat()}\n")
    f.write("#\n")
    w = csv.DictWriter(f, fieldnames=["token","date","trigger","h2_ve","conf","step_pct","ramp_pct","age_days","TP_FP"])
    w.writeheader()
    for r in census_rows: w.writerow(r)
md5 = hashlib.md5(open(out_csv, "rb").read()).hexdigest()
print(f"\n  Output: {out_csv.name}  md5: {md5}")


# ═══════════════════════════════════════════════════════════
# (4) Kho-ramp prod wire status
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print(f"[KHO-RAMP PROD WIRE STATUS]")
print("═" * 100)
print("""
gom_h_daily.py:475 → h1_ramp_raw = False  ← HARDCODE STUB
                     TODO: wire ramp check via balance_series[D-14]

Verdict: kho-ramp = PROBE-ONLY (this script + G3 probe)
         PROD (cron gom_h_daily.py) chỉ dùng step ≥10%/≤3d, KHÔNG ramp

Impact:
  - Cron đêm nay 27/08 01:45 UTC compose = step-only (NO ramp)
  - AKE 07-13/07-14 ramp fires KHÔNG kích compose prod → cron sẽ MISS ramp signal
  - T-④ 8/9 PASS con số trong G3 → dùng probe (có ramp) — nếu prod KHÔNG ramp,
    T-④ prod passes có thể thấp hơn (AKE mất H1-ramp pathway)

Go-live ≠ verify — khai rõ trong G6 report:
  "ramp: probe-only, prod wire chờ commit X" (X = TBD sau operator ký merge)

Next commit sẽ wire ramp vào prod _kho_ramp_14d + integration vào compose loop.
""")

print(f"\n{'═'*100}\n[DỪNG] T-④ v2 + Census v3 + kho-ramp status ready.\n{'═'*100}")
