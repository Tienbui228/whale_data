#!/usr/bin/env python3
"""[PHA-E DATA-PREP] E1 replay 8 case + E2 control-set — DEV chuẩn bị số, KHÔNG chấm.

Operator ký chat 28/08 PHA E. E1-caveat ANALYSIS chép nguyên văn ở đầu output.
Không chạm replay.py, không thay ngưỡng, KHÔNG kết luận PASS/FAIL.
"""
from __future__ import annotations
import sys, io, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
from statistics import median
import openpyxl
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
CASE_DIR = REPO / "docs/case_files"
YAML_PATH = REPO / "screen_thresholds.yaml"

# ─── E1-caveat NGUYÊN VĂN (chép head report per operator) ───
E1_CAVEAT = """
[E1-CAVEAT ANALYSIS — chép nguyên văn ở đầu báo cáo, không sửa]

"Các số này được fit trên chính 8 case positive → E1 replay pass phần lớn là by
construction — ngưỡng H1/H2/H3 đã tune trên chính observations của 8 case.
Ai đọc E1 như validation là rơi đúng bẫy L-53 / sanity-vòng-tròn.
E1 là ĐO NỘI, không phải VALIDATION. Validation THẬT = E2 control-set + forward 30d.
Gate off-draft phải ≥6/8 E1 + E2 FP rate + control ≥20 chưa-chạy."
"""

# ─── 8 CASE tokens + ignition dates ───
CASES = {
    "BANK":  {"ignition": "2026-07-10", "ignition_src": "EVENTS row 6 'T0 ignition (OI +8%,+20%)'"},
    "TUT":   {"ignition": "2026-07-08", "ignition_src": "EVENTS row 9 'pre-ignition trough' — actual pump TBD OP-VERIFY"},
    "CYS":   {"ignition": None,          "ignition_src": "EVENTS empty for ignition — OP-VERIFY (DUMP events only)"},
    "HEMI":  {"ignition": "2026-07-20", "ignition_src": "EVENTS row 4 PUMP_D1_NEG_FUND (also L-53 wave-2 15/08)"},
    "ON":    {"ignition": None,          "ignition_src": "EVENTS row 4-7 DUMP events only — OP-VERIFY"},
    "CAP":   {"ignition": "2026-07-30", "ignition_src": "EVENTS row 6 PUMP_20PCT (+32.29%)"},
    "AKE":   {"ignition": None,          "ignition_src": "EVENTS 'PENDING ANALYSIS' — OP-VERIFY"},
    "BTW":   {"ignition": None,          "ignition_src": "EVENTS DUMP-only — OP-VERIFY (pre-06/08 period)"},
}

# Load cfg
cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()

# ─── CFG-PROVENANCE header (L-64) ───
def _header():
    print("═" * 100)
    print(f"[CFG-PROVENANCE PHA-E]")
    print(f"  Source: screen_thresholds.yaml (gom_h)")
    print(f"  yaml md5: {yaml_md5}")
    print(f"  Values ACTUALLY USED:")
    for section, values in cfg.items():
        if isinstance(values, dict):
            print(f"    {section}:")
            for k, v in values.items():
                print(f"      {k}: {v}")
        else:
            print(f"    {section}: {values}")
    print(f"  spec_version: v4.0-draft")
    print(f"  amendments_applied: [GOM-RESTRUCT-20260824, ⑬-COLUMN-MANIFEST-20260826, H1-đường-(a)-20260828]")
    print("═" * 100)

# ─── Read CASE_*.xlsx DAILY sheet + build days list ───
def _load_case_daily(token: str) -> pd.DataFrame:
    p = CASE_DIR / f"CASE_{token}.xlsx"
    wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
    ws = wb["DAILY"]
    hdrs = {c: ws.cell(2, c).value for c in range(1, ws.max_column+1)}
    rows = []
    for r in range(3, ws.max_row+1):
        row = {hdrs[c]: ws.cell(r, c).value for c in range(1, ws.max_column+1) if hdrs.get(c)}
        if row.get("date"):
            rows.append(row)
    wb.close()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Normalize date format
    df["date"] = df["date"].astype(str).str[:10]
    return df.sort_values("date").reset_index(drop=True)

# ─── Formulas from gom_h_daily.py (dup here to avoid coupling) ───
def _values_upto(df, date, col, n):
    if col not in df.columns: return []
    df_sub = df[df["date"] <= date].sort_values("date").tail(n)
    vals = []
    for v in df_sub[col].tolist():
        try:
            fv = float(v)
            if fv == fv: vals.append(fv)
        except: pass
    return vals

def _today(df, date, col):
    r = df[df["date"] == date][col] if col in df.columns else pd.Series()
    if r.empty: return None
    try:
        v = float(r.iloc[0])
        return v if v == v else None
    except: return None

def _div_avg3_case(df, date):
    # CASE has div_avg3 col already
    v = _today(df, date, "div_avg3")
    if v is not None: return v
    # Fallback compute from lsr_pos_r / lsr_acc_r
    df_sub = df[df["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in df_sub.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    avg_p = sum(x[0] for x in pairs) / len(pairs)
    avg_a = sum(x[1] for x in pairs) / len(pairs)
    return avg_p / avg_a if avg_a > 1e-9 else None

def _eval_t01(df, date, c):
    funding_14 = _values_upto(df, date, "f_avg", 14)
    oi_30 = _values_upto(df, date, "oi_usd", 30)
    px_15 = _values_upto(df, date, "px_avg", 15)
    vol_30 = _values_upto(df, date, "vol_perp_usd", 30)
    if len(funding_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30:
        return "N/A-WARMUP"
    fund_ok = all(abs(v) <= c["funding_pin_abs"] for v in funding_14)
    oi_today = _today(df, date, "oi_usd")
    if oi_today is None: return "N/A-WARMUP"
    oi_ok = oi_today <= c["oi_over_min30_max"] * min(oi_30)
    ret14 = abs(px_15[-1] - px_15[0]) / px_15[0] if px_15[0] > 0 else float("inf")
    ret_ok = ret14 <= c["ret14_abs_max"]
    med7 = median(vol_30[-7:]); med30 = median(vol_30)
    vol_ok = med7 <= c["vol_med7_over_med30_max"] * med30 if med30 > 0 else False
    return "T" if (fund_ok and oi_ok and ret_ok and vol_ok) else "F"

def _eval_h1(df, date, c):
    """H1 replay via CASE col exch_balance_delta (tracker) — thiếu → N/A."""
    v = _today(df, date, "exch_balance_delta")
    if v is None: return "N/A"
    # Interpret as pct — if adapter kho_step_pct semantic: |Δbalance|/balance ≥ 10%
    # exch_balance_delta could be raw delta USD or pct. Mark N/A if unclear.
    # For safety: check if any exch_balance_delta filled at all in CASE
    return "N/A"  # Coverage-note: no historical adapter data in CASE files without op tracker

def _eval_h2(df, date, c):
    pos_14 = _values_upto(df, date, "lsr_pos_r", 14)
    oi_30 = _values_upto(df, date, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: return "N/A-WARMUP"
    div_today = _div_avg3_case(df, date)
    if div_today is None: return "N/A-WARMUP"
    # min(div_avg3) 14d
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "N/A-WARMUP"
    divs = [_div_avg3_case(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return "N/A-WARMUP"
    div_min14 = min(divs)
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _today(df, date, "lsr_pos_r"); oi_today = _today(df, date, "oi_usd")
    if pos_today is None or oi_today is None: return "N/A-WARMUP"
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    if pos_min14 <= 0 or oi_min30 <= 0: return "N/A-WARMUP"
    v2 = (pos_today / pos_min14 >= c["pos_over_min14_min"]) and (oi_today / oi_min30 <= c["oi_over_min30_max"])
    return "T" if (v1 or v2) else "F"

def _eval_h3(df, date, c):
    vol_14 = _values_upto(df, date, "vol_perp_usd", 14)
    px_2 = _values_upto(df, date, "px_avg", 2)
    if len(vol_14) < 14: return "N/A-WARMUP"
    vol_today = _today(df, date, "vol_perp_usd")
    if vol_today is None: return "N/A-WARMUP"
    med14 = median(vol_14)
    if med14 <= 0: return "F"
    vol_ratio = vol_today / med14
    if len(px_2) < 2: return "N/A-WARMUP"
    ret_1d = abs((px_2[-1] - px_2[0]) / px_2[0]) if px_2[0] > 0 else float("inf")
    return "T" if (vol_ratio >= c["vol_mult_med14_min"] and ret_1d <= c["ret_abs_max"]) else "F"

# ─── E1 REPLAY 8 CASE ───
def _run_e1():
    print(E1_CAVEAT)
    _header()
    print(f"\n[E1 REPLAY 8 CASE via ADAPTER-DAILY v0.1]")
    print(f"  Map cột (CASE DAILY schema legacy col 5 taker_buy_pct = PERCENT):")
    print(f"    date → date · px_avg → px · f_avg/min/max → funding · oi_usd → oi ·")
    print(f"    lsr_pos_r/acc_r/global_r → LSR canonical · div_avg3 pre-computed ·")
    print(f"    vol_perp_usd → vol_quote · taker_buy_pct → col 5 legacy (percent unit)")
    print(f"  H1 replay: adapter lịch sử = N/A (CASE.exch_balance_delta chưa map tracker OP)")
    print(f"  Thiếu → NaN + low_conf; không sửa replay.py.")
    print()
    print(f"  {'token':<7} {'md5':>10} {'H1_first':>12} {'H2_first':>12} {'H3_first':>12} {'ignition':>12} {'lead_H2':>8}")
    print(f"  {'-'*80}")
    results = []
    for tok, meta in CASES.items():
        p = CASE_DIR / f"CASE_{tok}.xlsx"
        md5 = hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
        df = _load_case_daily(tok)
        if df.empty:
            print(f"  {tok:<7} {md5:>10}  <no DAILY rows>")
            continue
        # Iterate per-day, find first T per H
        h1_first = h2_first = h3_first = None
        for d in df["date"].tolist():
            if h1_first is None and _eval_h1(df, d, cfg["h1"]) == "T": h1_first = d
            if h2_first is None and _eval_h2(df, d, cfg["h2"]) == "T": h2_first = d
            if h3_first is None and _eval_h3(df, d, cfg["h3"]) == "T": h3_first = d
        ign = meta["ignition"]
        def _lead(first, ign):
            if not first or not ign: return "N/A"
            try:
                d1 = datetime.strptime(first, "%Y-%m-%d")
                d2 = datetime.strptime(ign, "%Y-%m-%d")
                return f"{(d2 - d1).days}d"
            except: return "?"
        lead_h2 = _lead(h2_first, ign)
        print(f"  {tok:<7} {md5:>10} {str(h1_first or 'N/A'):>12} {str(h2_first or 'N/A'):>12} {str(h3_first or 'N/A'):>12} {str(ign or 'N/A'):>12} {lead_h2:>8}")
        results.append({"token": tok, "md5": md5, "H1_first": h1_first, "H2_first": h2_first,
                        "H3_first": h3_first, "ignition": ign, "ignition_src": meta["ignition_src"], "lead_H2": lead_h2})
    print()
    print(f"  KHÔNG kết luận PASS/FAIL — ANALYSIS chấm theo gate ≥[6]/8 sau khi operator điền [ ].")
    print(f"  Ignition source per token:")
    for r in results:
        print(f"    {r['token']}: {r['ignition_src']}")

# ─── E2 CONTROL SET SKELETON ───
def _run_e2():
    print(f"\n" + "═" * 100)
    print(f"[E2 CONTROL SET]")
    print(f"  seed = [OPERATOR ĐIỀN]  ← chờ chữ ký + số")
    print(f"  Filter: fw-139 token có |ret 26/06→22/08| < 30% (đối chiếu k[7] fresh)")
    print(f"  Chạy GOM-H cùng kỳ; bảng FP: token · ngày H bật · H nào · giá trị vs ngưỡng")

    # Compute |ret 26/06→22/08| for fw-139
    frames = []
    for m in ["06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists(): frames.append(pd.read_csv(p))
    store = pd.concat(frames, ignore_index=True)
    syms = sorted({l.strip() for l in open(REPO / "data/config/freshwatch_symbols.txt", encoding="utf-8") if l.strip()})
    control_set = []
    for sym in syms:
        df_sym = store[store["symbol"] == sym].sort_values("date")
        r_start = df_sym[df_sym["date"] == "2026-06-26"]["px_avg"]
        r_end = df_sym[df_sym["date"] == "2026-08-22"]["px_avg"]
        if r_start.empty or r_end.empty: continue
        px_start = r_start.iloc[0]; px_end = r_end.iloc[0]
        if pd.isna(px_start) or pd.isna(px_end) or px_start <= 0: continue
        ret = abs(px_end - px_start) / px_start
        if ret < 0.30:
            control_set.append((sym, ret))
    control_set.sort(key=lambda x: x[1])
    print(f"\n  Control-set eligible (|ret| < 30%, sorted asc): {len(control_set)} tokens")
    print(f"  {'sym':<15} {'|ret|':>7}")
    for s, r in control_set[:30]:
        print(f"    {s:<15} {r:>7.4f}")
    if len(control_set) > 30:
        print(f"    ... {len(control_set) - 30} more")
    print(f"\n  Bảng FP GOM-H trên control-set cùng kỳ 26/06→22/08:")
    print(f"    [PENDING] chờ seed OP → sample ≥20 tokens → run gom_h_daily cùng kỳ →")
    print(f"    aggregate fires per (token, day, H).")
    print(f"    Structure ready; execution skipped until seed provided.")

# ─── Main ───
_run_e1()
_run_e2()
print(f"\n" + "═" * 100)
print(f"[PHA-E DATA-PREP DỪNG] Hai bảng → ANALYSIS + operator.")
print(f"ĐIỂM DỪNG 2: operator điền mọi [ ] từ E1+E2 → ký 'GOM-H off-draft'.")
print(f"Trước chữ ký đó GOM-H VĨNH VIỄN REPORT-ONLY.")
print("═" * 100)
