#!/usr/bin/env python3
"""[E1-v3 sửa nhãn, không đổi máy] Fix per operator 28/08:
  (1) Đổi quy ước lead = ignition − H_first (dương = SỚM); CAP H1 = +17d SỚM
  (2) Thêm cột runway_pre_ignition (ignition − 06-30) + caveat left-censor H1
      → TUT/BANK/HEMI: "handoff khả năng pre-window, không đánh giá được"
  (3) HEMI: paste store first_seen + eligible dates H2 (14-pos / 30-oi)
      → 07-12 có nằm trong warmup không? Nếu có → finding "min30 warmup mù"
  (4) CYS H2 07-12 store: print div/pos values → nhánh nào bật
  E1-v3 thay v2. Caveat giữ nguyên. DỪNG.
"""
from __future__ import annotations
import sys, io, hashlib
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"

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
# H1_first từ adapter historical E1-v2 (đã ký f2d0aff), tránh chạy lại 64 snapshot
H1_ADAPTER = {
    "BANK": "2026-07-20", "TUT": None, "CYS": "2026-08-06", "HEMI": "2026-08-17",
    "ON":   "2026-07-15", "CAP": "2026-07-13", "AKE": "2026-07-06", "BTW": "2026-07-28",
}
WINDOW_START = "2026-06-30"  # H1 adapter historical window (snapshots có từ 06-17 nhưng H1 doctrine 06-30→08-22)

cfg = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()


def _header():
    print("═" * 100)
    print(f"[CFG-PROVENANCE PHA-E-v3]")
    print(f"  yaml: {YAML_PATH.name}  md5: {yaml_md5}")
    print(f"  Values: h1.balance_delta_abs_min={cfg['h1']['balance_delta_abs_min']}, window_days_max={cfg['h1']['window_days_max']}")
    print(f"          h2.div_min_14d_max={cfg['h2']['div_min_14d_max']}, div_today_min={cfg['h2']['div_today_min']}, pos_over_min14_min={cfg['h2']['pos_over_min14_min']}, oi_over_min30_max={cfg['h2']['oi_over_min30_max']}")
    print(f"  H1 adapter window: {WINDOW_START} → 2026-08-22 (VPS-synced snapshots)")
    print(f"  spec_version: v4.0-draft · amendments: [GOM-RESTRUCT, ⑬, H1-đường-(a), E1-v3-labels]")
    print("═" * 100)


# Load STORE freshwatch_daily 05-08
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)


def _sym(tok): return tok + "USDT"


def _df_sym(sym):
    d = STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)
    return d


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


def _first_true(sym, eval_fn):
    df_sym = _df_sym(sym)
    if df_sym.empty: return None
    for _, row in df_sym.iterrows():
        date = str(row["date"])
        if date < "2026-06-01" or date > "2026-08-24": continue
        if eval_fn(df_sym, date) == "T": return date
    return None


def _lead_label(ign, first):
    """lead = ignition − H_first (dương = SỚM: cảnh báo trước)"""
    if not ign or not first: return "N/A", ""
    d_ign = datetime.strptime(ign, "%Y-%m-%d")
    d_first = datetime.strptime(first, "%Y-%m-%d")
    days = (d_ign - d_first).days
    if days > 0:  return f"+{days}d", "SỚM"
    if days < 0:  return f"{days}d", "TRỄ"
    return "0d", "ĐÚNG"


def _runway(ign):
    if not ign: return "N/A"
    d_ign = datetime.strptime(ign, "%Y-%m-%d")
    d_start = datetime.strptime(WINDOW_START, "%Y-%m-%d")
    return f"{(d_ign - d_start).days}d"


def _left_censor_flag(ign, tok):
    """H1 left-censor: ignition trong 14d đầu window → handoff khả năng pre-window"""
    if not ign: return ""
    d_ign = datetime.strptime(ign, "%Y-%m-%d")
    d_start = datetime.strptime(WINDOW_START, "%Y-%m-%d")
    days = (d_ign - d_start).days
    if days < 14: return " [LEFT-CENSOR — handoff pre-window, không đánh giá H1]"
    return ""


# ─── (1)(2) BẢNG E1-v3 THAY V2 ───
def print_e1_v3_table():
    print(f"\n{'═'*100}\n[E1-v3 (1)(2) LEAD LABELS + RUNWAY-PRE-IGNITION]\n{'═'*100}")
    print(f"  Quy ước MỚI: lead = ignition − H_first (dương = SỚM: cảnh báo trước ignition)")
    print(f"  Runway window: {WINDOW_START} → ignition (nếu <14d → H1 LEFT-CENSOR)\n")

    header = f"  {'token':<7} {'ignition':>12} {'runway':>8} | {'H1_first':>12} {'lead_H1':>10} | {'H2_first':>12} {'lead_H2':>10} | {'H3_first':>12} {'lead_H3':>10}"
    print(header)
    print(f"  {'-'*len(header)}")

    for tok in CASES:
        ign = IGNITIONS.get(tok)
        h1 = H1_ADAPTER.get(tok)
        sym = _sym(tok)
        h2 = _first_true(sym, _eval_h2)
        h3 = _first_true(sym, _eval_h3)
        runway = _runway(ign)
        censor = _left_censor_flag(ign, tok)

        l1_d, l1_lbl = _lead_label(ign, h1)
        l2_d, l2_lbl = _lead_label(ign, h2)
        l3_d, l3_lbl = _lead_label(ign, h3)

        h1_disp = h1 or "N/A"
        h2_disp = h2 or "N/A"
        h3_disp = h3 or "N/A"
        l1_disp = f"{l1_d} {l1_lbl}".strip()
        l2_disp = f"{l2_d} {l2_lbl}".strip()
        l3_disp = f"{l3_d} {l3_lbl}".strip()

        print(f"  {tok:<7} {str(ign or 'N/A'):>12} {runway:>8} | {h1_disp:>12} {l1_disp:>10} | {h2_disp:>12} {l2_disp:>10} | {h3_disp:>12} {l3_disp:>10}")
        if censor:
            print(f"      →{censor}")

    print(f"\n  CAP H1 FIX: previous v2 hiển thị '+17d (post)' SAI CHIỀU.")
    print(f"    CAP ignition=2026-07-30, H1_first=2026-07-13 → lead = 30−13 = +17d SỚM (H1 cảnh báo trước 17 ngày).")


# ─── (3) HEMI 07-12 warmup analysis ───
def print_hemi_warmup():
    print(f"\n{'═'*100}\n[E1-v3 (3) HEMI 07-12 STORE — warmup H2 per-vế analysis]\n{'═'*100}")
    sym = "HEMIUSDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"  {sym} không có trong STORE — skip")
        return

    first_seen_store = df["date"].min()
    n_days_store = len(df)
    print(f"  STORE first_seen  : {first_seen_store}  (n_days={n_days_store})")
    print(f"  STORE last_seen   : {df['date'].max()}")
    print(f"  H2 warmup req: 14 lsr_pos_r + 30 oi_usd (per vế 2 pos-ratio)")
    print(f"                 14 pos + 14 div (per vế 1 div-cut)\n")

    # Compute first date where each requirement is met
    def _first_ok(col, n_req):
        dates = sorted(df["date"].tolist())
        for i, d in enumerate(dates):
            trail = df[df["date"] <= d].tail(n_req)
            nn = sum(1 for v in trail[col].tolist() if pd.notna(v))
            if nn >= n_req: return d
        return None

    first_pos14 = _first_ok("lsr_pos_r", 14)
    first_oi30 = _first_ok("oi_usd", 30)
    first_oi14 = _first_ok("oi_usd", 14)
    print(f"  first date đủ 14 pos    : {first_pos14}")
    print(f"  first date đủ 14 oi     : {first_oi14}")
    print(f"  first date đủ 30 oi     : {first_oi30}  ← vế 2 pos-ratio warmup gate")

    # Check 07-12 vs warmup gates
    target = "2026-07-12"
    ign = IGNITIONS["HEMI"]
    print(f"\n  Ngày HYP target: {target}  (ignition HEMI={ign})")
    if first_oi30 and target < first_oi30:
        gap = (datetime.strptime(first_oi30, "%Y-%m-%d") - datetime.strptime(target, "%Y-%m-%d")).days
        print(f"  → target {target} NẰM TRONG WARMUP (min30 gate = {first_oi30}, còn thiếu {gap}d)")
        print(f"  → Vế 2 pos-ratio KHÔNG THỂ eval ngày {target} (min30 oi warmup mù)")
        # Vế 1 div-cut check
        if first_pos14 and target >= first_pos14:
            print(f"  → Vế 1 div-cut ELIGIBLE ngày {target} (đủ 14 pos)")
        else:
            print(f"  → Vế 1 div-cut chưa eligible")
        print(f"\n  ═══ FINDING CHO ANALYSIS ═══")
        print(f"  \"HEMI un-hedge 07-12: vế 2 pos-ratio bị min30-oi-warmup che.")
        print(f"   STORE first_seen={first_seen_store}, cần 30d oi → first eligible={first_oi30}.")
        print(f"   Chỉ vế 1 div-cut còn eval được — bỏ sót nhánh dominant (92.3% fw-139 fires).\"")
    else:
        print(f"  → target {target} SAU warmup gate — H2 eval được cả 2 vế")

    # Actual H2 eval at 07-12 nếu có
    print(f"\n  H2 eval STORE tại {target} (raw):")
    v_res = _eval_h2(df, target)
    print(f"    _eval_h2 → {v_res}  (T=fire, F=fail, W=warmup)")


# ─── (4) CYS 07-12 store: which vế bật ───
def print_cys_0712_analysis():
    print(f"\n{'═'*100}\n[E1-v3 (4) CYS 07-12 STORE — H2 branch analysis]\n{'═'*100}")
    sym = "CYSUSDT"
    df = _df_sym(sym)
    if df.empty:
        print(f"  {sym} không có trong STORE — skip")
        return

    target = "2026-07-12"
    print(f"  Ngày target: {target}  (E1-v2 STORE H2_first = 2026-07-12)")
    print(f"  STORE first_seen: {df['date'].min()}, n_days={len(df)}\n")

    # Warmup check
    pos_14 = _v(df, target, "lsr_pos_r", 14)
    oi_30 = _v(df, target, "oi_usd", 30)
    print(f"  Warmup: pos_14 n={len(pos_14)} · oi_30 n={len(oi_30)}")
    if len(pos_14) < 14 or len(oi_30) < 30:
        print(f"  → WARMUP — H2 không thể fire (mâu thuẫn E1-v2 kết quả?)")
        return

    # Vế 1 div-cut
    dates14 = sorted(df[df["date"] <= target]["date"].tolist())[-14:]
    divs = [_div_avg3(df, d) for d in dates14]
    divs_clean = [v for v in divs if v is not None]
    div_today = _div_avg3(df, target)
    div_min14 = min(divs_clean) if divs_clean else None
    c = cfg["h2"]
    print(f"\n  Vế 1 div-cut (div_min14 ≤ {c['div_min_14d_max']} ∧ div_today ≥ {c['div_today_min']}):")
    print(f"    div_min14  = {div_min14}")
    print(f"    div_today  = {div_today}")
    v1_c1 = (div_min14 is not None) and (div_min14 <= c["div_min_14d_max"])
    v1_c2 = (div_today is not None) and (div_today >= c["div_today_min"])
    v1 = v1_c1 and v1_c2
    print(f"    div_min14 ≤ {c['div_min_14d_max']}? {v1_c1}   ·  div_today ≥ {c['div_today_min']}? {v1_c2}   → VẾ 1 = {v1}")

    # Vế 2 pos-ratio
    pos_today = _t(df, target, "lsr_pos_r"); oi_today = _t(df, target, "oi_usd")
    pos_min14 = min(pos_14); oi_min30 = min(oi_30)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min30 if (oi_today is not None and oi_min30 > 0) else None
    print(f"\n  Vế 2 pos-ratio (pos/min14 ≥ {c['pos_over_min14_min']} ∧ oi/min30 ≤ {c['oi_over_min30_max']}):")
    print(f"    pos_today  = {pos_today}   ·  pos_min14 = {pos_min14}   →  ratio = {r_pos}")
    print(f"    oi_today   = {oi_today}   ·  oi_min30  = {oi_min30}   →  ratio = {r_oi}")
    v2_c1 = (r_pos is not None) and (r_pos >= c["pos_over_min14_min"])
    v2_c2 = (r_oi is not None) and (r_oi <= c["oi_over_min30_max"])
    v2 = v2_c1 and v2_c2
    print(f"    pos/min14 ≥ {c['pos_over_min14_min']}? {v2_c1}   ·  oi/min30 ≤ {c['oi_over_min30_max']}? {v2_c2}   → VẾ 2 = {v2}")

    print(f"\n  KẾT LUẬN: H2 fire = vế1({v1}) ∨ vế2({v2}) = {v1 or v2}")
    if v1 and not v2:  print(f"    → Nhánh DIV-CUT bật (div compression)")
    elif v2 and not v1: print(f"    → Nhánh POS-RATIO bật (seat-lift pos surge)")
    elif v1 and v2:    print(f"    → CẢ 2 NHÁNH BẬT")


# ─── Main ───
print(E1_CAVEAT)
_header()
print_e1_v3_table()
print_hemi_warmup()
print_cys_0712_analysis()

print(f"\n{'═'*100}")
print(f"[E1-v3 DỪNG] Bảng thay v2 · caveat giữ nguyên · chờ operator [ ] + ký GOM-H off-draft.")
print(f"{'═'*100}")
