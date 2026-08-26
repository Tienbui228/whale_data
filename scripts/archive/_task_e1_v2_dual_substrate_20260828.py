#!/usr/bin/env python3
"""[E1-v2 DUAL-SUBSTRATE] fix E1 per operator 28/08:
  (1) H1 replay adapter historical (66 snapshots) fw-8 window 06-30→08-22
  (2) Warmup-boundary per H on CASE substrate (chứng minh vùng mù)
  (3) DUAL-SUBSTRATE: E1 STORE 06-01→08-24 cạnh CASE; lệch cột riêng
  (4) Giữ caveat + KHÔNG chấm
"""
from __future__ import annotations
import sys, io, hashlib, json
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import openpyxl
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
CASE_DIR = REPO / "docs/case_files"
YAML_PATH = REPO / "screen_thresholds.yaml"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

E1_CAVEAT = """
[E1-CAVEAT ANALYSIS — chép nguyên văn ở đầu báo cáo, không sửa]

"Các số này được fit trên chính 8 case positive → E1 replay pass phần lớn là by
construction — ngưỡng H1/H2/H3 đã tune trên chính observations của 8 case.
Ai đọc E1 như validation là rơi đúng bẫy L-53 / sanity-vòng-tròn.
E1 là ĐO NỘI, không phải VALIDATION. Validation THẬT = E2 control-set + forward 30d.
Gate off-draft phải ≥6/8 E1 + E2 FP rate + control ≥20 chưa-chạy."
"""

CASES = ["BANK", "TUT", "CYS", "HEMI", "ON", "CAP", "AKE", "BTW"]
IGNITIONS = {
    "BANK": "2026-07-10", "TUT": "2026-07-08", "HEMI": "2026-07-20", "CAP": "2026-07-30",
    "CYS": None, "ON": None, "AKE": None, "BTW": None,
}

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()

# ─── CFG-PROVENANCE (L-64) ───
def _header():
    print("═" * 100)
    print(f"[CFG-PROVENANCE PHA-E-v2]")
    print(f"  yaml: {YAML_PATH.name}  md5: {yaml_md5}")
    print(f"  Values: t0_1.funding_pin_abs={cfg['t0_1']['funding_pin_abs']}, oi_over_min30_max={cfg['t0_1']['oi_over_min30_max']}, ret14_abs_max={cfg['t0_1']['ret14_abs_max']}, vol_med7_over_med30_max={cfg['t0_1']['vol_med7_over_med30_max']}")
    print(f"          h1.balance_delta_abs_min={cfg['h1']['balance_delta_abs_min']}, window_days_max={cfg['h1']['window_days_max']}")
    print(f"          h2.div_min_14d_max={cfg['h2']['div_min_14d_max']}, div_today_min={cfg['h2']['div_today_min']}, pos_over_min14_min={cfg['h2']['pos_over_min14_min']}, oi_over_min30_max={cfg['h2']['oi_over_min30_max']}")
    print(f"          h3.vol_mult_med14_min={cfg['h3']['vol_mult_med14_min']}, ret_abs_max={cfg['h3']['ret_abs_max']}")
    print(f"  spec_version: v4.0-draft · amendments: [GOM-RESTRUCT, ⑬, H1-đường-(a)]")
    print("═" * 100)

# ─── (1) H1 adapter historical replay ───
def _h1_adapter_historical():
    print(f"\n{'═'*100}\n[E1-v2 (1) H1 REPLAY từ adapter historical (66 snapshots VPS-synced)]\n{'═'*100}")

    # Load all snapshots, build per-token balance series
    balance_series = {tok: {} for tok in CASES}  # {token: {ingest_date: balance}}
    # Filter to date-format filenames only (skip _gap_log.json, etc.)
    all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                            if p.stem[:4].isdigit() and len(p.stem) == 10])
    n_snapshots = len(all_snapshots)
    print(f"  Loaded {n_snapshots} snapshots (window: {all_snapshots[0].stem} → {all_snapshots[-1].stem})")

    for snap_path in all_snapshots:
        ingest_date = snap_path.stem  # YYYY-MM-DD
        try:
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(snap, dict):
            continue
        for row in snap.get("rows", []):
            sym = row.get("symbol", "").upper()
            for tok in CASES:
                if sym == tok:
                    bal = row.get("exchange_balance_tokens")
                    try:
                        if bal is not None: balance_series[tok][ingest_date] = float(bal)
                    except: pass
                    break

    # Per-token: window |Δ|≥10% ≤3d → H1_first
    print(f"\n  {'token':<7} {'n_days':>7} {'H1_first':>13} {'kho_steps ≤3d ≥10%':>25}")
    h1_results = {}
    for tok in CASES:
        series = balance_series[tok]
        dates = sorted(series.keys())
        n = len(dates)
        h1_first = None
        kho_steps = []
        # Window ≤3d: for each i, compare balance[i] vs balance[i-1..i-3]
        for i in range(1, len(dates)):
            for lookback in [1, 2, 3]:
                if i - lookback < 0: continue
                d_start = dates[i - lookback]; d_end = dates[i]
                b_start = series.get(d_start); b_end = series.get(d_end)
                if b_start is None or b_end is None or b_start <= 0: continue
                delta_pct = abs(b_end - b_start) / b_start
                if delta_pct >= 0.10:
                    kho_steps.append((d_start, d_end, lookback, delta_pct))
                    if h1_first is None: h1_first = d_end
                    break
        h1_results[tok] = {"n_days": n, "h1_first": h1_first, "kho_steps": kho_steps}
        cov_flag = " [COVERAGE-NOTE]" if tok in ("AKE", "BTW") and n < 10 else ""
        print(f"  {tok:<7} {n:>7} {str(h1_first or 'N/A'):>13} {len(kho_steps):>10} windows{cov_flag}")
    # Print top kho steps per token
    print(f"\n  Chi tiết cửa sổ |Δ|≥10%/≤3d (top 5 per token, sorted by delta_pct desc):")
    for tok, res in h1_results.items():
        if not res["kho_steps"]: continue
        top = sorted(res["kho_steps"], key=lambda x: -x[3])[:5]
        print(f"    {tok}:")
        for d_start, d_end, lb, dp in top:
            print(f"      {d_start} → {d_end} ({lb}d): |Δ|={dp:.4f} ({dp*100:.2f}%)")
    return h1_results

# ─── (2) Warmup-boundary CASE substrate ───
def _warmup_case():
    print(f"\n{'═'*100}\n[E1-v2 (2) WARMUP-BOUNDARY per H trên CASE substrate — chứng minh vùng mù]\n{'═'*100}")
    print(f"  Warmup requirements: H2 = 14 pos + 30 oi · H3 = 14 vol · T0.1 = 14 funding + 30 oi + 15 px + 30 vol\n")
    print(f"  {'token':<7} {'DAILY rows':>11} {'first date':>12} {'H2 eligible-first':>19} {'H3 elig-first':>15} {'T0.1 elig-first':>17}")

    for tok in CASES:
        wb = openpyxl.load_workbook(str(CASE_DIR / f"CASE_{tok}.xlsx"), read_only=True, data_only=True)
        ws = wb["DAILY"]
        hdrs = {c: ws.cell(2, c).value for c in range(1, ws.max_column+1)}
        col_of = {v: k for k, v in hdrs.items() if v}
        rows = []
        for r in range(3, ws.max_row + 1):
            d = ws.cell(r, col_of.get("date", 1)).value
            if d is None: continue
            d = str(d)[:10]
            def _f(name):
                c = col_of.get(name)
                if c is None: return None
                v = ws.cell(r, c).value
                try:
                    fv = float(v); return fv if fv == fv else None
                except: return None
            rows.append({
                "date": d,
                "pos": _f("lsr_pos_r"),
                "oi": _f("oi_usd"),
                "vol": _f("vol_perp_usd"),
                "funding": _f("f_avg"),
                "px": _f("px_avg"),
            })
        wb.close()
        n = len(rows)
        first_date = rows[0]["date"] if rows else "-"

        # Find first date where trailing 14 pos + 30 oi are non-null (H2 eligible)
        def _elig_first(rows, need):
            # need = dict {col: n_required}
            for i in range(len(rows)):
                ok = True
                for col, req in need.items():
                    trail = rows[max(0, i - req + 1):i + 1]
                    if len(trail) < req or sum(1 for r in trail if r.get(col) is not None) < req:
                        ok = False; break
                if ok: return rows[i]["date"]
            return None

        h2_first = _elig_first(rows, {"pos": 14, "oi": 30})
        h3_first = _elig_first(rows, {"vol": 14})
        t01_first = _elig_first(rows, {"funding": 14, "oi": 30, "px": 15, "vol": 30})
        print(f"  {tok:<7} {n:>11} {first_date:>12} {str(h2_first or 'never'):>19} {str(h3_first or 'never'):>15} {str(t01_first or 'never'):>17}")

# ─── (3) DUAL-SUBSTRATE: STORE 06-01→08-24 ───
def _run_store_substrate(h1_results):
    print(f"\n{'═'*100}\n[E1-v2 (3) DUAL-SUBSTRATE — E1 chạy trên STORE 06-01→08-24 cạnh CASE]\n{'═'*100}")

    frames = []
    for m in ["05","06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists(): frames.append(pd.read_csv(p))
    store = pd.concat(frames, ignore_index=True)

    def _first_true(sym, eval_fn):
        df_sym = store[store["symbol"] == sym].sort_values("date").reset_index(drop=True)
        if df_sym.empty: return None
        # Iterate every date
        for _, row in df_sym.iterrows():
            date = str(row["date"])
            if date < "2026-06-01" or date > "2026-08-24": continue
            if eval_fn(df_sym, date) == "T": return date
        return None

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

    def _lead(first, ign):
        if not first or not ign: return "N/A"
        try:
            d1 = datetime.strptime(first, "%Y-%m-%d")
            d2 = datetime.strptime(ign, "%Y-%m-%d")
            return f"{(d2 - d1).days}d"
        except: return "?"

    print(f"\n  {'token':<7} | {'CASE-substrate':>32} | {'STORE 06-01→08-24':>32}")
    print(f"  {'':<7} | {'H1':>10} {'H2':>10} {'H3':>10} | {'H1':>10} {'H2':>10} {'H3':>10}")
    for tok in CASES:
        # CASE side already computed as N/A for H1/H2/H3 in previous run — use CASE-only formulas here too
        # For simplicity: use STORE h2/h3 formulas + H1 from adapter historical
        sym = tok + "USDT"
        store_h2 = _first_true(sym, _eval_h2)
        store_h3 = _first_true(sym, _eval_h3)
        h1_from_adapter = h1_results.get(tok, {}).get("h1_first")
        ign = IGNITIONS.get(tok)
        # CASE previous: BANK H2=08-15 H3=07-02, TUT H3=08-04, others N/A
        case_h2 = "2026-08-15" if tok == "BANK" else ("2026-08-04" if tok == "TUT" else "N/A")
        case_h3 = "2026-07-02" if tok == "BANK" else ("2026-08-04" if tok == "TUT" else "N/A")
        print(f"  {tok:<7} | {'N/A':>10} {case_h2:>10} {case_h3:>10} | {str(h1_from_adapter or 'N/A'):>10} {str(store_h2 or 'N/A'):>10} {str(store_h3 or 'N/A'):>10}")

    # Lead
    print(f"\n  LEAD vs ignition (STORE substrate):")
    print(f"  {'token':<7} {'ignition':>12} {'lead_H1':>10} {'lead_H2':>10} {'lead_H3':>10}")
    for tok in CASES:
        sym = tok + "USDT"
        store_h1 = h1_results.get(tok, {}).get("h1_first")
        store_h2 = _first_true(sym, _eval_h2)
        store_h3 = _first_true(sym, _eval_h3)
        ign = IGNITIONS.get(tok)
        print(f"  {tok:<7} {str(ign or 'N/A'):>12} {_lead(store_h1, ign):>10} {_lead(store_h2, ign):>10} {_lead(store_h3, ign):>10}")

# ─── Main ───
print(E1_CAVEAT)
_header()
h1 = _h1_adapter_historical()
_warmup_case()
_run_store_substrate(h1)

print(f"\n{'═'*100}\n[DEV → ANALYSIS ĐỀ NGHỊ]")
print(f"  E1 substrate: CASE window ngắn (~75d) → warmup 30-điểm OI nuốt vùng seat-lift")
print(f"    (H2 N/A 7/8 tokens, mâu thuẫn findings §6 seat-lift 6/8 tokens)")
print(f"  Đề nghị: E1 chạy trên STORE 06-01→08-24 (cùng lineage fapi-1d, warmup thỏa),")
print(f"           CASE làm cross-check duy nhất — hay operator giữ CASE-only và đọc N/A")
print(f"           như thuộc tính thiết kế?")
print(f"{'═'*100}")
print(f"\n[E1-v2 DỪNG] Bảng đầy đủ chờ operator điền + ký GOM-H off-draft.")
