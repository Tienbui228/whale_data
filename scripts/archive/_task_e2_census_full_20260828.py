#!/usr/bin/env python3
"""[E2-CENSUS FULL 52 · post H1-SPEC-FIX 28/08]
  Per operator DEV → AGENT E2-fix thứ tự cứng:
    (1) H1 fix: ∧ T0.1 tại ngày cuối cửa sổ (spec §1-H line 138)
    (2) Caveat: BANANAS31 = ⑪ control-âm (H1-mồi predicted-FP-mode) — xung đột row 14
        chờ ANALYSIS/operator, KHÔNG tự phân loại TP
    (3) FULL 52 eligible (bỏ sampling); alphabetical-24 nhãn [SEED-PROTOCOL-VIOLATED]
        Per-token per-vế fires + cột trống "TP/FP" cho ANALYSIS chấm dòng
  Header L-64 CFG-PROVENANCE. DỪNG với (1) verdict + census.
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
SYMBOLS_TXT = REPO / "data/config/freshwatch_symbols.txt"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")
SPEC_PATH = Path(r"D:/Data back test/binance-bot-signals/docs/gom_detect_spec.md")

CASES = {"BANK", "TUT", "CYS", "HEMI", "ON", "CAP", "AKE", "BTW"}
WINDOW_START = "2026-06-26"
WINDOW_END = "2026-08-22"
RET_MAX = 0.30

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()
spec_md5 = hashlib.md5(open(SPEC_PATH, "rb").read()).hexdigest() if SPEC_PATH.exists() else "N/A"

print("═" * 100)
print(f"[E2-CENSUS FULL 52 · CFG-PROVENANCE L-64]")
print(f"  yaml         : {YAML_PATH.name}  md5: {yaml_md5}")
print(f"  spec         : gom_detect_spec.md  md5: {spec_md5}")
print(f"  H1 doctrine  : |Δbalance|≥10%/≤3d ∧ T0.1-compression tại ngày cuối [FIXED per §1-H line 138]")
print(f"  GOM-H compose: H1 ∨ (H2 ∧ T0.1); H3 booster")
print(f"  Window       : {WINDOW_START} → {WINDOW_END}")
print(f"  Filter       : |ret| < {RET_MAX*100}%")
print(f"  Substrate    : STORE freshwatch_daily (per E1-v3 DEV recommendation)")
print("═" * 100)

# ─── Load fw-139 minus 8 case ───
fw_symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
candidates = [s[:-4] if s.endswith("USDT") else s for s in fw_symbols
              if (s[:-4] if s.endswith("USDT") else s) not in CASES]

# ─── Load STORE ───
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _df_sym(sym):
    return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _px_at(df, date):
    r = df[df["date"] <= date].tail(1)
    if r.empty: return None
    v = r["px_avg"].iloc[0]
    return float(v) if pd.notna(v) else None


# ─── Full 52 eligible ───
eligible = []
excluded_ret = []
missing = []
for tok in candidates:
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty:
        missing.append(tok); continue
    px0 = _px_at(df, WINDOW_START)
    px1 = _px_at(df, WINDOW_END)
    if px0 is None or px1 is None or px0 <= 0:
        missing.append(tok); continue
    ret = (px1 - px0) / px0
    if abs(ret) < RET_MAX:
        eligible.append((tok, ret))
    else:
        excluded_ret.append((tok, ret))

eligible_sorted = sorted(eligible, key=lambda x: x[0])
pilot_24 = set(t for t, _ in eligible_sorted[:24])
print(f"\n[ROSTER] fw-139 − 8 case = {len(candidates)} candidates")
print(f"  Eligible |ret|<30% : {len(eligible)} (FULL CENSUS below)")
print(f"  Excluded ≥30%     : {len(excluded_ret)}")
print(f"  Missing STORE     : {len(missing)}")
print(f"  Pilot-24 (E2-SEED-PICK ebbf790) = alphabetical first 24, nhãn [SEED-PROTOCOL-VIOLATED — agent-picked]")

# ─── Load Nansen snapshots for H1 balance series ───
balance_series = {tok: {} for tok, _ in eligible}
all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                        if p.stem[:4].isdigit() and len(p.stem) == 10])
for snap_path in all_snapshots:
    ingest_date = snap_path.stem
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        if sym_u in balance_series:
            bal = row.get("exchange_balance_tokens")
            try:
                if bal is not None: balance_series[sym_u][ingest_date] = float(bal)
            except: pass
print(f"  Nansen snapshots loaded: {len(all_snapshots)} (for H1 balance series)")


# ─── Eval functions ───
def _v(df_sym, date, col, n):
    s = df_sym[df_sym["date"] <= date].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]

def _t(df_sym, date, col):
    r = df_sym[df_sym["date"] == date][col]
    if r.empty: return None
    try:
        v = float(r.iloc[0]); return v if v == v else None
    except: return None

def _div_avg3(df_sym, date):
    s = df_sym[df_sym["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in s.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    avg_p = sum(x[0] for x in pairs) / len(pairs)
    avg_a = sum(x[1] for x in pairs) / len(pairs)
    return avg_p / avg_a if avg_a > 1e-9 else None

def _eval_t01(df_sym, date):
    fund_14 = _v(df_sym, date, "funding_avg", 14)
    oi_30 = _v(df_sym, date, "oi_usd", 30)
    px_15 = _v(df_sym, date, "px_avg", 15)
    vol_30 = _v(df_sym, date, "vol_quote", 30)
    if len(fund_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30: return "W"
    c = cfg["t0_1"]
    fund_ok = max(abs(f) for f in fund_14) <= c["funding_pin_abs"]
    oi_today = _t(df_sym, date, "oi_usd")
    if oi_today is None: return "W"
    oi_min30 = min(oi_30)
    if oi_min30 <= 0: return "W"
    oi_ok = (oi_today / oi_min30) <= c["oi_over_min30_max"]
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    ret_ok = ret14 <= c["ret14_abs_max"]
    vol_7 = vol_30[-7:]
    if len(vol_7) < 7: return "W"
    vol_ok = median(vol_7) <= median(vol_30) * c["vol_med7_over_med30_max"]
    return "T" if all([fund_ok, oi_ok, ret_ok, vol_ok]) else "F"

def _eval_h2(df_sym, date):
    pos_14 = _v(df_sym, date, "lsr_pos_r", 14)
    oi_30 = _v(df_sym, date, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: return "W"
    div_today = _div_avg3(df_sym, date)
    if div_today is None: return "W"
    dates = sorted(df_sym[df_sym["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "W"
    divs = [_div_avg3(df_sym, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return "W"
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df_sym, date, "lsr_pos_r"); oi_today = _t(df_sym, date, "oi_usd")
    if pos_today is None or oi_today is None: return "W"
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    if pos_min14 <= 0 or oi_min30 <= 0: return "W"
    v2 = (pos_today / pos_min14 >= c["pos_over_min14_min"]) and (oi_today / oi_min30 <= c["oi_over_min30_max"])
    return "T" if (v1 or v2) else "F"

def _eval_h3(df_sym, date):
    vol_14 = _v(df_sym, date, "vol_quote", 14)
    px_2 = _v(df_sym, date, "px_avg", 2)
    if len(vol_14) < 14: return "W"
    vol_today = _t(df_sym, date, "vol_quote")
    if vol_today is None: return "W"
    med14 = median(vol_14)
    if med14 <= 0: return "F"
    vol_ratio = vol_today / med14
    if len(px_2) < 2: return "W"
    ret_1d = abs((px_2[-1] - px_2[0]) / px_2[0]) if px_2[0] > 0 else float("inf")
    c = cfg["h3"]
    return "T" if (vol_ratio >= c["vol_mult_med14_min"] and ret_1d <= c["ret_abs_max"]) else "F"

def _eval_h1_kho(tok, date):
    """kho-step only: |Δbalance|/balance ≥10% ≤3d — RAW không có T0.1 gate"""
    series = balance_series.get(tok, {})
    if not series: return "N/A"
    if date not in series: return "N/A"
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    c = cfg["h1"]
    for lb in range(1, c["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        if abs(b_end - b_start) / b_start >= c["balance_delta_abs_min"]:
            return "T"
    return "F"

def _eval_h1_fixed(tok, date, t01_status):
    """H1 SPEC-FIXED: kho ∧ T0.1 tại ngày cuối"""
    kho = _eval_h1_kho(tok, date)
    if kho != "T": return kho  # F/N/A pass through
    # kho fires → need T0.1
    if t01_status == "W": return "N/A"
    if t01_status == "T": return "T"
    return "F"  # kho T, t01 F → H1 F


# ─── FULL 52 census ───
start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

print(f"\n{'═'*100}")
print(f"[E2-CENSUS FULL {len(eligible)} · FP scan GOM-H each day, H1 SPEC-FIXED]")
print(f"  Compose: GOM-H = H1 ∨ (H2 ∧ T0.1); H1 = kho ∧ T0.1  → effectively T0.1 ∧ (kho ∨ H2)")
print(f"  Empty column TP/FP for ANALYSIS/operator to fill per fire row")
print(f"{'═'*100}\n")

hdr = f"  {'token':<10} {'pilot':>5} {'ret':>7} {'days':>5} {'t01':>4} {'h1_kho':>7} {'h1_fx':>6} {'h2':>4} {'h3':>4} {'gh_fx':>6}  {'TP/FP':<8}"
print(hdr)
print(f"  {'-'*len(hdr)}")

fp_summary = []
per_fire_rows = []
for tok, ret in eligible_sorted:
    sym = tok + "USDT"
    df = _df_sym(sym)
    t01_f = h1_kho_f = h1_fx_f = h2_f = h3_f = gh_fx_f = 0
    days_evaluated = 0
    fires_dates_gh = []
    for date in window_days:
        if df[df["date"] == date].empty: continue
        days_evaluated += 1
        t01 = _eval_t01(df, date)
        h1_kho = _eval_h1_kho(tok, date)
        h1_fx = _eval_h1_fixed(tok, date, t01)
        h2 = _eval_h2(df, date)
        h3 = _eval_h3(df, date)
        if t01 == "T": t01_f += 1
        if h1_kho == "T": h1_kho_f += 1
        if h1_fx == "T": h1_fx_f += 1
        if h2 == "T": h2_f += 1
        if h3 == "T": h3_f += 1
        gh_fx = (h1_fx == "T") or ((h2 == "T") and (t01 == "T"))
        if gh_fx:
            gh_fx_f += 1
            fires_dates_gh.append(date)
            per_fire_rows.append({
                "token": tok, "date": date,
                "t01": t01, "h1_kho": h1_kho, "h1_fx": h1_fx, "h2": h2, "h3": h3,
                "active": "+".join([x for x, s in [("H1", h1_fx == "T"),
                                                    ("H2+T01", (h2 == "T") and (t01 == "T"))] if s]),
                "conf": "boosted" if h3 == "T" else "normal",
                "TP_FP": "",  # empty for ANALYSIS
            })
    fp_summary.append({
        "tok": tok, "ret": ret, "days": days_evaluated,
        "t01": t01_f, "h1_kho": h1_kho_f, "h1_fx": h1_fx_f, "h2": h2_f, "h3": h3_f,
        "gh_fx": gh_fx_f, "fires": fires_dates_gh,
        "in_pilot": tok in pilot_24,
    })
    pilot_mark = "P✓" if tok in pilot_24 else "-"
    print(f"  {tok:<10} {pilot_mark:>5} {ret*100:>6.1f}% {days_evaluated:>5} {t01_f:>4} {h1_kho_f:>7} {h1_fx_f:>6} {h2_f:>4} {h3_f:>4} {gh_fx_f:>6}  {'[  ]':<8}")

# ─── Aggregate ───
n_pos = sum(1 for r in fp_summary if r["gh_fx"] > 0)
total_gh = sum(r["gh_fx"] for r in fp_summary)
total_days = sum(r["days"] for r in fp_summary)
print(f"\n[FP AGGREGATE — H1 SPEC-FIXED]")
print(f"  Census size          : {len(fp_summary)} tokens (FULL 52 eligible)")
print(f"  Tokens ≥1 GOM-H fire : {n_pos}/{len(fp_summary)} ({100*n_pos/len(fp_summary):.1f}%)")
print(f"  Total GOM-H fires    : {total_gh}")
print(f"  Total token-days     : {total_days}")
if total_days > 0:
    print(f"  FP rate/day (upper)  : {total_gh/total_days*100:.2f}%  ← upper bound; TP hidden trong roster")
print(f"\n  Per-vế raw counts:")
print(f"    T0.1  : {sum(r['t01'] for r in fp_summary)}")
print(f"    H1_kho (raw)    : {sum(r['h1_kho'] for r in fp_summary)}")
print(f"    H1_fixed (∧T0.1): {sum(r['h1_fx'] for r in fp_summary)}   ← spec-compliant")
print(f"    H2  : {sum(r['h2'] for r in fp_summary)}")
print(f"    H3  : {sum(r['h3'] for r in fp_summary)}")

# ─── Comparison H1 before/after fix ───
kho_only = sum(r['h1_kho'] for r in fp_summary)
h1_fx = sum(r['h1_fx'] for r in fp_summary)
print(f"\n[H1 SPEC-FIX IMPACT — kho-only vs kho∧T0.1]")
print(f"  H1 kho raw    : {kho_only} fires (previous incorrect implementation)")
print(f"  H1 spec-fixed : {h1_fx} fires (∧ T0.1)  → giảm {kho_only - h1_fx} fires "
      f"({100*(kho_only-h1_fx)/max(1,kho_only):.1f}% cắt xuống)")

# ─── Per-fire dump for ANALYSIS chấm ───
print(f"\n{'═'*100}")
print(f"[PER-FIRE ROWS — ANALYSIS/operator chấm cột TP/FP dòng-per-dòng]")
print(f"{'═'*100}\n")
per_fire_hdr = f"  {'#':>4} {'token':<10} {'date':>12} {'active':>10} {'conf':>10} {'t01':>4} {'h1_fx':>6} {'h2':>4} {'h3':>4} {'TP/FP':<8}"
print(per_fire_hdr)
print(f"  {'-'*len(per_fire_hdr)}")
for i, r in enumerate(per_fire_rows, 1):
    tag = ""
    if r["token"] == "BANANAS31":
        tag = " [⑪-CONTROL-ÂM · H1-mồi predicted-FP-mode xung đột row 14 — CHỜ ANALYSIS/OPERATOR]"
    print(f"  {i:>4} {r['token']:<10} {r['date']:>12} {r['active']:>10} {r['conf']:>10} "
          f"{r['t01']:>4} {r['h1_fx']:>6} {r['h2']:>4} {r['h3']:>4} {'[  ]':<8}{tag}")

# ─── Write per-fire CSV for ANALYSIS ───
csv_out = REPO / "scratch" / "e2_census_perfire_20260828.csv"
pd.DataFrame(per_fire_rows).to_csv(csv_out, index=False)
csv_md5 = hashlib.md5(open(csv_out, "rb").read()).hexdigest()
print(f"\n[CSV OUTPUT] {csv_out.name}  md5: {csv_md5}")

# ─── Caveat fix ───
print(f"\n{'═'*100}")
print(f"[CAVEAT FIX per operator (2)]")
print(f"{'═'*100}")
print(f"""
  BANANAS31 = ⑪ CONTROL-ÂM (ANALYSIS dự báo H1-mồi, KHÔNG phải BULLA).
  Fires của BANANAS31 = predicted-FP-mode HOẶC bug(1) H1 spec-thiếu.
  Xung đột row 14: ghi thành mục riêng chờ ANALYSIS/operator chấm TP/FP.
  Agent KHÔNG tự phân loại TP cho BANANAS31 (removes E2-SEED commit's incorrect
  "known case" hint).

  BULLA (hai họ, ⑬-CLOSE canonical) KHÔNG có trong seed E2 (BULLA31 in fw-139? check).
""")

# BULLA check
bulla_in_fw = any(s.startswith("BULLA") for s in fw_symbols)
print(f"  BULLA* trong fw-139: {bulla_in_fw}")

# ─── DỪNG ───
print(f"\n{'═'*100}")
print(f"[DỪNG] (1) H1-SPEC-CHECK verdict: THIẾU → FIXED (gom_h_daily.py + census script)")
print(f"       (3) E2-census FULL {len(eligible)} eligible với H1 spec-fixed")
print(f"       Pilot-24 gắn nhãn [SEED-PROTOCOL-VIOLATED — agent-picked]")
print(f"       CSV per-fire ready cho ANALYSIS chấm TP/FP.")
print(f"       Còn nợ (i) VPS 08-21 4 H1-fire recheck · (ii) D3 day-1/2 rerun — separate")
print(f"{'═'*100}")
