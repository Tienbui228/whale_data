#!/usr/bin/env python3
"""[E2-CLOSE-PREP per operator 28/08]
  (1) CROSS-bug trace: đường tính kho_step _eval_h1 pre-fix vs adapter kho_step_pct
      → RERUN H1 bảng E1-v3 (8 case) với H1_fixed (kho ∧ T0.1) — CAP +17d còn sống?
      Paste H1-v4 cạnh v3.
  (2) H1_fixed=2: token/ngày/giá trị đủ 3 vế
  (3) BANANAS31 7 fires: per-fire nhánh + giá trị (H1 hay H2∧T0.1)
  (4) Table cho ANALYSIS: n token-days {H1_kho ∧ T0.1-từng-vé-riêng}
      Vế nào của T0.1 giết giao điểm (funding_pin?)
  DỪNG. Census 63-row CSV giữ nguyên chờ ANALYSIS chấm.
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

CASES = ["BANK", "TUT", "CYS", "HEMI", "ON", "CAP", "AKE", "BTW"]
IGNITIONS = {
    "BANK": "2026-07-10", "TUT": "2026-07-08", "HEMI": "2026-07-20", "CAP": "2026-07-30",
    "CYS": None, "ON": None, "AKE": None, "BTW": None,
}
H1_V3 = {  # E1-v3 adapter historical results
    "BANK": "2026-07-20", "TUT": None, "CYS": "2026-08-06", "HEMI": "2026-08-17",
    "ON":   "2026-07-15", "CAP": "2026-07-13", "AKE": "2026-07-06", "BTW": "2026-07-28",
}
WINDOW_START = "2026-06-30"

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()

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


def _t01_veles(df, date):
    """Return dict {funding_pin, oi_ok, ret_ok, vol_ok, overall} — per-vế status"""
    fund_14 = _v(df, date, "funding_avg", 14)
    oi_30 = _v(df, date, "oi_usd", 30)
    px_15 = _v(df, date, "px_avg", 15)
    vol_30 = _v(df, date, "vol_quote", 30)
    if len(fund_14) < 14 or len(oi_30) < 30 or len(px_15) < 15 or len(vol_30) < 30:
        return {"funding_pin": "W", "oi_ok": "W", "ret_ok": "W", "vol_ok": "W", "overall": "W"}
    c = cfg["t0_1"]
    max_af = max(abs(f) for f in fund_14)
    f_pin = max_af <= c["funding_pin_abs"]
    oi_today = _t(df, date, "oi_usd")
    oi_min30 = min(oi_30)
    oi_r = oi_today / oi_min30 if (oi_today and oi_min30 > 0) else None
    oi_ok = oi_r is not None and oi_r <= c["oi_over_min30_max"]
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    ret_ok = ret14 <= c["ret14_abs_max"]
    vol_7 = vol_30[-7:]
    vol_ok = median(vol_7) <= median(vol_30) * c["vol_med7_over_med30_max"]
    overall = "T" if all([f_pin, oi_ok, ret_ok, vol_ok]) else "F"
    return {
        "funding_pin": "T" if f_pin else "F", "max_abs_fund": max_af,
        "oi_ok": "T" if oi_ok else "F", "oi_ratio": oi_r,
        "ret_ok": "T" if ret_ok else "F", "ret14": ret14,
        "vol_ok": "T" if vol_ok else "F", "med7": median(vol_7), "med30": median(vol_30),
        "overall": overall,
    }


def _eval_t01(df, date):
    return _t01_veles(df, date)["overall"]


def _eval_h2(df, date):
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_30 = _v(df, date, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: return "W"
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
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    if pos_min14 <= 0 or oi_min30 <= 0: return "W"
    v2 = (pos_today / pos_min14 >= c["pos_over_min14_min"]) and (oi_today / oi_min30 <= c["oi_over_min30_max"])
    return "T" if (v1 or v2) else "F"


def _h2_veles(df, date):
    """Return which H2 vế fired"""
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_30 = _v(df, date, "oi_usd", 30)
    if len(pos_14) < 14 or len(oi_30) < 30: return None
    div_today = _div_avg3(df, date)
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return None
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    r_pos = pos_today / pos_min14 if pos_min14 > 0 else None
    r_oi = oi_today / oi_min30 if oi_min30 > 0 else None
    v2 = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    return {
        "v1_div_cut": v1, "div_min14": div_min14, "div_today": div_today,
        "v2_pos_ratio": v2, "r_pos": r_pos, "r_oi": r_oi,
    }


# ─── Load Nansen snapshots ───
balance_series = {}
all_snapshots = sorted([p for p in SNAPSHOTS_DIR.glob("*.json")
                        if p.stem[:4].isdigit() and len(p.stem) == 10])
for snap_path in all_snapshots:
    ingest_date = snap_path.stem
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(snap, dict): continue
    for row in snap.get("rows", []):
        sym_u = row.get("symbol", "").upper()
        balance_series.setdefault(sym_u, {})
        bal = row.get("exchange_balance_tokens")
        try:
            if bal is not None: balance_series[sym_u][ingest_date] = float(bal)
        except: pass


def _kho_3d(tok, date):
    """Best |Δ|/b in ≤3d window ending `date` from balance_series (spec-correct)"""
    series = balance_series.get(tok, {})
    if date not in series: return None
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    best = 0.0; best_lb = None; best_bstart = None
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp; best_lb = lb; best_bstart = b_start
    return {"b_end": b_end, "best_kho": best, "best_lb": best_lb, "b_start": best_bstart}


# ═══════════════════════════════════════════════════════════
# (1) CROSS-BUG TRACE
# ═══════════════════════════════════════════════════════════
print("═" * 100)
print("[(1) CROSS-BUG TRACE · gom_h_daily.py pre-fix _eval_h1 vs adapter kho_step_pct]")
print("═" * 100)
print("""
Pre-fix _eval_h1 (before commit 927b519):
  ```
  kho_step = r.get("kho_step_pct")                                    # (a) adapter output
  threshold_pct = cfg_h1["balance_delta_abs_min"] * 100.0             # = 0.10 * 100 = 10.0
  ok = abs(float(kho_step)) >= threshold_pct                          # (b) single-value check
  ```

Đường tính (a) — adapter_h1_nansen.py:156-160:
  ```
  kho_step_pct = delta_pct if delta_pct is not None else None         # bot's field pass-through
  if kho_step_pct is None and bal + prev available:
      kho_step_pct = (bal - prev) / prev                              # ← FALLBACK: FRACTION
  ```

Đường tính (b): kho_step assumed PCT vs threshold 10.0 pct.

═══ CROSS 08-21 GIÁ TRỊ THẬT (raw Nansen snapshot) ═══
""")

snap_path = SNAPSHOTS_DIR / "2026-08-21.json"
snap = json.loads(snap_path.read_text(encoding="utf-8"))
cross_row = next((r for r in snap["rows"] if r.get("symbol","").upper()=="CROSS"), None)
print(f"  bot exchange_delta_pct    : {cross_row['exchange_delta_pct']}   ← BOT UNIT = PCT (–4.08%)")
print(f"  bot exchange_balance_tokens: {cross_row['exchange_balance_tokens']:.0f}")
print(f"  bot exchange_prev_tokens  : {cross_row['exchange_prev_tokens']:.0f}")
print(f"  bot exchange_delta_tokens : {cross_row['exchange_delta_tokens']:.0f}")
print(f"  ratio |bal−prev|/prev     : {abs(cross_row['exchange_delta_tokens'])/cross_row['exchange_prev_tokens']*100:.3f}%  (1-day)")

kho3 = _kho_3d("CROSS", "2026-08-21")
print(f"  probe _kho_3d best        : {kho3['best_kho']*100:.2f}% (lb={kho3['best_lb']}d)  ← 3-day spec-correct scan")

print(f"""
═══ TRACE 4.24% pass gate 10%? ═══
  Pre-fix code path (a→b):
    kho_step = -4.081963 (from bot delta_pct, PCT unit, 1-day)
    threshold_pct = 10.0 (pct)
    check: abs(-4.081963) >= 10.0 → False
    → CROSS PRE-FIX GATE-CHECK LÀ FAIL

  Vậy 4.24% (probe 3-day) KHÔNG PASS gate 10% dưới bất kỳ đường code nào.
  Cũng chưa có đường code nào ép fire CROSS 08-21.

═══ VERDICT CROSS-BUG ═══
  KHÔNG PHẢI "bug thứ hai" ở gate check. Có thể là:
  (A) VPS report "5 fires CROSS/GWEI/TOSHI/TRIA [H1]" trong e2_backlog:105
      là paraphrase/typo; thực tế chỉ TOSHI (bot delta_pct=+11.18%) đủ single-day 10% gate.
      GWEI (-1.87%), CROSS (-4.08%), TRIA (-8.98%) đều fail single-day gate.
  (B) VPS gom_h_daily.py có scale conversion khác chưa xác định (không thấy trong code hiện).
  Cần: DEV cross-check log VPS 08-21 gom_h_daily thô — số kho_step_pct nào được compare.

  ⚠ BUG THẬT (đã fix trong commit 927b519):
    - Old code chỉ single-day (adapter delta_pct 1d), spec yêu cầu ≤3d window.
    - Old code không có ∧ T0.1 gate.
  Fix: _eval_h1_fixed dùng balance_series 3-day scan + T0.1 gate.
""")

# ═══════════════════════════════════════════════════════════
# (1-cont) H1-v4 bảng cạnh v3 (E1 8 case adapter historical, ∧ T0.1)
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[(1) BẢNG H1-v4 8 CASE — kho ∧ T0.1 tại H1_first ngày (v3 adapter historical)]")
print("═" * 100)

def _find_h1_v4(tok):
    """Scan window 06-30→08-22, find first date where kho 3d ≥10% AND t01=T"""
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty: return None
    start = datetime.strptime(WINDOW_START, "%Y-%m-%d")
    end = datetime.strptime("2026-08-22", "%Y-%m-%d")
    for i in range((end - start).days + 1):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        k = _kho_3d(tok, d)
        if k is None or k["best_kho"] < 0.10: continue
        t01 = _eval_t01(df, d)
        if t01 == "T": return d
    return None

print(f"\n  {'token':<7} {'H1_v3 (kho only)':>18} {'H1_v4 (kho ∧ T0.1)':>20} {'change':>15} {'lead_v4':>10}")
print(f"  {'-'*90}")

h1_v4 = {}
for tok in CASES:
    v3 = H1_V3[tok]
    v4 = _find_h1_v4(tok)
    h1_v4[tok] = v4
    ign = IGNITIONS[tok]
    if v3 == v4: change = "same"
    elif v4 is None: change = "DROP"
    else: change = f"→ {v4}"
    lead_v4 = ""
    if v4 and ign:
        d_ign = datetime.strptime(ign, "%Y-%m-%d")
        d_v4 = datetime.strptime(v4, "%Y-%m-%d")
        days = (d_ign - d_v4).days
        lead_v4 = f"{days:+d}d {'SỚM' if days > 0 else 'TRỄ' if days < 0 else 'ĐÚNG'}"
    print(f"  {tok:<7} {str(v3 or 'N/A'):>18} {str(v4 or 'N/A'):>20} {change:>15} {lead_v4:>10}")

# CAP special check
print(f"\n  CAP +17d SỚM CHECK:")
if h1_v4.get("CAP"):
    d_cap = datetime.strptime(h1_v4["CAP"], "%Y-%m-%d")
    d_ign = datetime.strptime(IGNITIONS["CAP"], "%Y-%m-%d")
    print(f"    H1_v4 = {h1_v4['CAP']}  lead = {(d_ign - d_cap).days:+d}d {'SỚM CÒN SỐNG ✓' if (d_ign - d_cap).days > 0 else 'DIED'}")
else:
    print(f"    H1_v4 = N/A  → CAP +17d SỚM CHẾT (T0.1 gate không pass 07-13)")

# ═══════════════════════════════════════════════════════════
# (2) H1_fixed=2 evidence
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[(2) H1_FIXED = 2 FIRES · giá trị đủ 3 vế (kho + T0.1 4 điều kiện)]")
print("═" * 100)

perfire_df = pd.read_csv(REPO / "scratch" / "e2_census_perfire_20260828.csv")
h1_fires = perfire_df[perfire_df["h1_fx"] == "T"]
print(f"\n  Fires với H1_fixed=T:")
for _, r in h1_fires.iterrows():
    tok, date = r["token"], r["date"]
    df = _df_sym(tok + "USDT")
    kho = _kho_3d(tok, date)
    v = _t01_veles(df, date)
    print(f"\n  ─── {tok} @ {date} ───")
    if kho:
        print(f"    kho: b_start={kho['b_start']:.0f} b_end={kho['b_end']:.0f} lb={kho['best_lb']}d |Δ|/b={kho['best_kho']*100:.2f}%  → PASS 10%")
    print(f"    T0.1 4 vé:")
    print(f"      funding_pin max|f|=|{v['max_abs_fund']:.2e}| ≤ 5e-5 → {v['funding_pin']}")
    print(f"      oi_ratio={v['oi_ratio']:.4f} ≤ 1.2                → {v['oi_ok']}")
    print(f"      ret14={v['ret14']:.4f} ≤ 0.10                     → {v['ret_ok']}")
    print(f"      med7/med30={v['med7']:.0f}/{v['med30']:.0f}={v['med7']/v['med30']:.3f} ≤ 1.0 → {v['vol_ok']}")
    print(f"    T0.1 overall: {v['overall']}   →  H1_fixed = kho(T) ∧ T0.1(T) = T")

# ═══════════════════════════════════════════════════════════
# (3) BANANAS31 per-fire branch
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[(3) BANANAS31 7 fires · per-fire nhánh + giá trị · XUNG ĐỘT ROW 14 material]")
print("═" * 100)

bn = perfire_df[perfire_df["token"] == "BANANAS31"]
df_bn = _df_sym("BANANAS31USDT")

for _, r in bn.iterrows():
    date = r["date"]
    print(f"\n  ─── BANANAS31 @ {date} ───")
    print(f"    active: {r['active']}  ·  conf: {r['conf']}")

    # H1 side
    kho = _kho_3d("BANANAS31", date)
    if kho and kho["best_lb"]:
        print(f"    H1 kho 3d: |Δ|/b={kho['best_kho']*100:.2f}% ({kho['best_lb']}d) — {'PASS' if kho['best_kho']>=0.10 else 'fail'} 10% gate")
    else:
        print(f"    H1 kho: MISSING balance (N/A)")

    # T0.1
    v = _t01_veles(df_bn, date)
    if v["overall"] in ("T", "F"):
        print(f"    T0.1: funding={v['funding_pin']} oi={v['oi_ok']} ret={v['ret_ok']} vol={v['vol_ok']} → {v['overall']}")

    # H2
    hv = _h2_veles(df_bn, date)
    if hv:
        v1_lbl = "div-cut" if hv["v1_div_cut"] else "-"
        v2_lbl = "pos-ratio" if hv["v2_pos_ratio"] else "-"
        print(f"    H2: div_min14={hv['div_min14']:.3f} div_today={hv['div_today']:.3f}  ·  r_pos={hv['r_pos']:.3f} r_oi={hv['r_oi']:.3f}")
        print(f"        vé1 div-cut: {hv['v1_div_cut']}   vé2 pos-ratio: {hv['v2_pos_ratio']}   → active {v1_lbl}/{v2_lbl}")

print(f"""
═══ BANANAS31 SUMMARY ═══
  Ngày 07-04: H1+H2+T01 (fire cả 3) — cần ANALYSIS chấm TP/FP row 14
  Ngày 07-05..07-12 (6 fires): H2+T01 only (kho không đủ 3d)
  Nhánh H2 chi phối = pos-ratio (per ⑪ analysis đã báo)
  → xung đột row 14 material: H1-mồi predicted-FP mode + H2-pos-ratio dominant
""")

# ═══════════════════════════════════════════════════════════
# (4) T0.1 sub-vé kill table
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[(4) T0.1 SUB-VẾ KILL — n token-days {H1_kho ∧ T0.1-vế-riêng} · vế nào giết giao điểm]")
print("═" * 100)

# Full 52 eligible from census
eligible_tokens = perfire_df["token"].unique().tolist()
# Actually need full 52 from earlier; re-derive
fw_symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
CASES_SET = set(CASES)
candidates = [s[:-4] if s.endswith("USDT") else s for s in fw_symbols
              if (s[:-4] if s.endswith("USDT") else s) not in CASES_SET]

# Scan all candidate tokens × days for kho_ok, and check each T0.1 vé
start_dt = datetime.strptime("2026-06-26", "%Y-%m-%d")
end_dt = datetime.strptime("2026-08-22", "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

kho_ok_count = 0
kho_ok_and_fund = 0
kho_ok_and_oi = 0
kho_ok_and_ret = 0
kho_ok_and_vol = 0
kho_ok_and_all = 0
kho_ok_details = []  # list of (tok, date, veles)

# Only scan tokens with STORE data (eligible list)
for tok in candidates:
    df = _df_sym(tok + "USDT")
    if df.empty: continue
    # Also gate by |ret|<30% (matches census roster)
    px0 = df[df["date"] <= "2026-06-26"].tail(1)["px_avg"]
    px1 = df[df["date"] <= "2026-08-22"].tail(1)["px_avg"]
    if px0.empty or px1.empty: continue
    p0 = float(px0.iloc[0]); p1 = float(px1.iloc[0])
    if p0 <= 0 or abs((p1-p0)/p0) >= 0.30: continue

    for d in window_days:
        kho = _kho_3d(tok, d)
        if kho is None or kho["best_kho"] < 0.10: continue
        kho_ok_count += 1
        v = _t01_veles(df, d)
        if v["overall"] == "W": continue  # skip warmup for cleaner comparison
        if v["funding_pin"] == "T": kho_ok_and_fund += 1
        if v["oi_ok"] == "T": kho_ok_and_oi += 1
        if v["ret_ok"] == "T": kho_ok_and_ret += 1
        if v["vol_ok"] == "T": kho_ok_and_vol += 1
        if v["overall"] == "T": kho_ok_and_all += 1
        kho_ok_details.append((tok, d, v))

print(f"\n  Roster: full 52 eligible (|ret|<30% same as census)")
print(f"  Window: 2026-06-26 → 2026-08-22")
print(f"\n  Total (tok, day) with H1 kho ≥10% (3d) : {kho_ok_count}")
print(f"\n  Của những (tok, day) đó, số ngày mỗi T0.1 vé pass:")
print(f"    {'vé':<15} {'n_pass':>8} {'%':>8}")
if kho_ok_count > 0:
    for lbl, n in [("funding_pin", kho_ok_and_fund), ("oi_ok", kho_ok_and_oi),
                    ("ret_ok", kho_ok_and_ret), ("vol_ok", kho_ok_and_vol)]:
        print(f"    {lbl:<15} {n:>8} {n/kho_ok_count*100:>7.1f}%")
    print(f"    {'ALL 4 pass':<15} {kho_ok_and_all:>8} {kho_ok_and_all/kho_ok_count*100:>7.1f}%  ← final H1_fixed=T")

print(f"""
  ⇒ Vế nào GIẾT giao điểm nhiều nhất = vé có %pass THẤP nhất.
  ⇒ Data này cho ANALYSIS đọc câu hỏi "ngưỡng T0.1-trong-H1" (funding_pin có quá chặt?).
""")

# Detail dump of kho_ok days for ANALYSIS reference
print(f"\n  Chi tiết {kho_ok_count} kho-ok (tok,day) — dump cho ANALYSIS:")
print(f"  {'tok':<10} {'date':>12} {'funding_pin':>13} {'oi':>4} {'ret':>4} {'vol':>4} {'ovr':>4}")
for tok, d, v in kho_ok_details[:60]:  # first 60 rows
    print(f"  {tok:<10} {d:>12} {v['funding_pin']:>13} {v['oi_ok']:>4} {v['ret_ok']:>4} {v['vol_ok']:>4} {v['overall']:>4}")
if len(kho_ok_details) > 60:
    print(f"  ... {len(kho_ok_details) - 60} more rows omitted (see CSV)")

# Also write CSV for ANALYSIS
detail_csv = REPO / "scratch" / "e2_h1_kho_ok_t01_veles_20260828.csv"
detail_df = pd.DataFrame([{
    "token": tok, "date": d, **v
} for tok, d, v in kho_ok_details])
detail_df.to_csv(detail_csv, index=False)
print(f"\n  [CSV] {detail_csv.name}  md5: {hashlib.md5(open(detail_csv,'rb').read()).hexdigest()}")

print(f"\n{'═'*100}")
print(f"[DỪNG] E2-close-prep (1)(2)(3)(4) done · Census 63-row CSV giữ nguyên chờ ANALYSIS.")
print(f"       (5) sáng mai — D3 cron log paste separate.")
print(f"{'═'*100}")
