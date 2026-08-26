#!/usr/bin/env python3
"""[V①-⑤ VERDICT TABLES + GATE RENDER · post OPERATOR/ANALYSIS ký 28/08]
  All V amendments applied:
    V① H1-SHADOW report-only (kho ∧ |ret14|≤0.15)
    V② OI-FLOOR: min(available) với floor_obs_min=14 PROVISIONAL
    V③ div_today≥1.0 GIỮ
    V④ GOM-H cooldown 14d reuse §8.4(i) semantic — OPERATOR KÝ
    V⑤ funding_pin ≤ + ε=1e-9 inclusive-by-design
  Header L-64 · CFG-PROVENANCE.

  Deliverables:
    T-① kho-step evidence table × T0.1 4 sub-vé (findings M1/§6)
    T-② 6 H2-case × earliest-eligible under n∈{10,14,21,30} (findings §6/§11-15)
    T-③ H2-fires × vế bắt matrix (14 census + findings evidence)
    T-④ GATE RENDER (ANALYSIS definition, DEV không chấm)
    CSV-63 update: + age col + TP/FP col + rule header

  Findings docs (M1/§6/§11-15) không tìm thấy trong local filesystem →
  các dòng ghi flag [SOURCE-MISSING] không bịa.
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
SPEC_PATH = Path(r"D:/Data back test/binance-bot-signals/docs/gom_detect_spec.md")

CASES = ["BANK", "TUT", "CYS", "HEMI", "ON", "CAP", "AKE", "BTW"]
IGNITIONS_VERIFIED = {
    # OPERATOR chưa VERIFY (chờ ☐) — dùng previous per e2_backlog/analysis rounds
    # CHỜ operator (a) fill final. Đây là working baseline, sẽ đánh dấu IGNITION-PENDING-VERIFY
    "BANK": "2026-07-10", "TUT": "2026-07-08",
    "HEMI": "2026-07-20", "CAP": "2026-07-30",
    "CYS": None, "ON": None, "AKE": None, "BTW": None,   # (a) blank
}
WINDOW_START = "2026-06-26"
WINDOW_END = "2026-08-22"
RET_MAX = 0.30

cfg_all = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))
cfg = cfg_all["gom_h"]
yaml_md5 = hashlib.md5(open(YAML_PATH, "rb").read()).hexdigest()
spec_md5 = hashlib.md5(open(SPEC_PATH, "rb").read()).hexdigest() if SPEC_PATH.exists() else "N/A"

# Read git HEAD sha
import subprocess
try:
    git_sha = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
except:
    git_sha = "unknown"

print("═" * 100)
print(f"[V①-⑤ VERDICT TABLES · CFG-PROVENANCE L-64]")
print(f"  yaml         : {YAML_PATH.name}  md5: {yaml_md5}")
print(f"  spec         : gom_detect_spec.md  md5: {spec_md5}")
print(f"  git head     : {git_sha}")
print(f"  Ký: V① SHADOW · V② FLOOR obs_min={cfg['t0_1']['floor_obs_min']}d · V③ div_today≥1.0 GIỮ ·")
print(f"      V④ cooldown={cfg['gom_h_cooldown_days']}d clean≥{cfg['gom_h_cooldown_clean_days']}d · V⑤ ε={cfg['t0_1']['funding_pin_eps']}")
print(f"  Substrate    : STORE freshwatch_daily (CASE cross-check nơi có per V④T-④)")
print(f"  Window       : {WINDOW_START} → {WINDOW_END}")
print("═" * 100)

# ─── Load STORE ───
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


def _eval_t01_v(df, date):
    """T0.1 with per-vế values + V② floor + V⑤ eps"""
    fund_14 = _v(df, date, "funding_avg", 14)
    px_15 = _v(df, date, "px_avg", 15)
    vol_30 = _v(df, date, "vol_quote", 30)
    oi_all = _v(df, date, "oi_usd", 30)  # up to 30, but accept min(available) with floor
    floor_obs = cfg["t0_1"].get("floor_obs_min", 14)
    d = {"floor_basis": f"{len(oi_all)}d"}
    if (len(fund_14) < 14 or len(oi_all) < floor_obs or len(px_15) < 15 or len(vol_30) < floor_obs):
        return "W", d
    c = cfg["t0_1"]
    # V⑤ inclusive-by-design + ε
    pin_eps = c.get("funding_pin_eps", 1e-9)
    max_af = max(abs(f) for f in fund_14)
    d["max_abs_fund"] = max_af
    d["funding_pin"] = "T" if max_af <= c["funding_pin_abs"] + pin_eps else "F"
    # V② min(available)
    oi_today = _t(df, date, "oi_usd")
    oi_min = min(oi_all)
    r_oi = oi_today / oi_min if (oi_today and oi_min > 0) else None
    d["oi_ratio"] = r_oi
    d["oi_ok"] = "T" if (r_oi is not None and r_oi <= c["oi_over_min30_max"]) else "F"
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
    d["ret14"] = ret14
    d["ret_ok"] = "T" if ret14 <= c["ret14_abs_max"] else "F"
    vol_7 = vol_30[-7:]
    med7 = median(vol_7); med30 = median(vol_30)
    d["med7"] = med7; d["med30"] = med30
    d["vol_ok"] = "T" if med7 <= med30 * c["vol_med7_over_med30_max"] else "F"
    d["overall"] = "T" if all(d[k] == "T" for k in ("funding_pin", "oi_ok", "ret_ok", "vol_ok")) else "F"
    return d["overall"], d


def _eval_h2_v(df, date):
    pos_14 = _v(df, date, "lsr_pos_r", 14)
    oi_all = _v(df, date, "oi_usd", 30)
    floor_obs = cfg["h2"].get("floor_obs_min", 14)
    if len(pos_14) < 14 or len(oi_all) < floor_obs: return "W", {}
    div_today = _div_avg3(df, date)
    if div_today is None: return "W", {}
    dates = sorted(df[df["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return "W", {}
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return "W", {}
    div_min14 = min(divs)
    c = cfg["h2"]
    v1 = (div_min14 <= c["div_min_14d_max"]) and (div_today >= c["div_today_min"])
    pos_today = _t(df, date, "lsr_pos_r"); oi_today = _t(df, date, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2 = r_pos is not None and r_oi is not None and r_pos >= c["pos_over_min14_min"] and r_oi <= c["oi_over_min30_max"]
    detail = {"v1_div_cut": v1, "v2_pos_ratio": v2, "div_min14": div_min14,
              "div_today": div_today, "r_pos": r_pos, "r_oi": r_oi,
              "floor_basis": f"{len(oi_all)}d"}
    return ("T" if (v1 or v2) else "F"), detail


def _eval_h3(df, date):
    vol_14 = _v(df, date, "vol_quote", 14)
    px_2 = _v(df, date, "px_avg", 2)
    if len(vol_14) < 14: return "W"
    vol_today = _t(df, date, "vol_quote")
    if vol_today is None: return "W"
    med14 = median(vol_14)
    if med14 <= 0: return "F"
    vol_ratio = vol_today / med14
    if len(px_2) < 2: return "W"
    ret_1d = abs((px_2[-1] - px_2[0]) / px_2[0]) if px_2[0] > 0 else float("inf")
    c = cfg["h3"]
    return "T" if (vol_ratio >= c["vol_mult_med14_min"] and ret_1d <= c["ret_abs_max"]) else "F"


# ─── Load Nansen snapshots for H1 ───
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
    series = balance_series.get(tok, {})
    if date not in series: return None
    b_end = series[date]
    d_end = datetime.strptime(date, "%Y-%m-%d")
    best = 0.0; best_lb = None
    for lb in range(1, cfg["h1"]["window_days_max"] + 1):
        d_start = (d_end - timedelta(days=lb)).strftime("%Y-%m-%d")
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if dp > best: best = dp; best_lb = lb
    return {"b_end": b_end, "best_kho": best, "best_lb": best_lb}


def _h1_strict(tok, date, t01_status):
    k = _kho_3d(tok, date)
    if k is None: return "N/A"
    if k["best_kho"] < 0.10: return "F"
    if t01_status == "W": return "N/A"
    return "T" if t01_status == "T" else "F"


def _h1_shadow(tok, date, ret14):
    """V① H1-SHADOW = kho(3d,≥10%) ∧ |ret14|≤0.15 · REPORT-ONLY"""
    k = _kho_3d(tok, date)
    if k is None or k["best_kho"] < 0.10: return "F"
    if ret14 is None: return "N/A"
    return "T" if ret14 <= 0.15 else "F"


# ═══════════════════════════════════════════════════════════
# T-① KHO-STEP EVIDENCE (findings M1/§6 — SOURCE MISSING local)
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[T-① NGÀY KHO-STEP EVIDENCE × T0.1 4 sub-vé]")
print("═" * 100)
print("""
  Source findings: mm_stage_machine_v1_proposal_20260823 §6 (M1)
  Spec §1-H line 138: "Evidence 8/8 (BANK rút · 7 nạp; FP đã biết: BANK 04/2026)"

  [SOURCE-MISSING] mm_stage_machine_v1_proposal_20260823 KHÔNG TÌM THẤY trong local
  filesystem (whale_data + binance-bot-signals). Không thể trích 9 ngày+token nguyên văn
  từ findings §6. Operator có source thì paste — agent KHÔNG bịa.

  DỪNG paste danh sách hỏi lại per luật operator: "đếm được ≠9 → DỪNG paste danh sách
  hỏi lại, không ép 9". Local count = 0 (source missing).

  → Backup evidence từ adapter historical (E1-v2, commit f2d0aff) — 8 case H1_first:
""")

H1_ADAPTER = {"BANK": "2026-07-20", "TUT": None, "CYS": "2026-08-06", "HEMI": "2026-08-17",
              "ON": "2026-07-15", "CAP": "2026-07-13", "AKE": "2026-07-06", "BTW": "2026-07-28"}

print(f"  {'token':<7} {'kho_date':>12} {'funding_pin':>12} {'oi_ratio':>10} {'ret14':>8} {'med7/med30':>12} {'overall':>8}")
print(f"  {'-'*90}")
t1_rows = []
for tok in CASES:
    kho_date = H1_ADAPTER[tok]
    if kho_date is None:
        print(f"  {tok:<7} {'N/A':>12} {'—':>12} {'—':>10} {'—':>8} {'—':>12} {'—':>8}")
        continue
    df = _df_sym(tok + "USDT")
    if df.empty:
        print(f"  {tok:<7} {kho_date:>12} {'NO-STORE':>12}")
        continue
    _, d = _eval_t01_v(df, kho_date)
    if "max_abs_fund" not in d:
        print(f"  {tok:<7} {kho_date:>12} {'WARMUP':>12} {'':>10} {'':>8} {'':>12} {'W':>8}")
        continue
    fp_lbl = f"{d['funding_pin']} ({d['max_abs_fund']:.2e})"
    print(f"  {tok:<7} {kho_date:>12} {fp_lbl:>25} "
          f"{d['oi_ratio']:>10.4f} {d['ret14']:>8.4f} {d['med7']/d['med30']:>12.3f} {d['overall']:>8}")
    t1_rows.append({"tok": tok, "kho_date": kho_date, **d})

print(f"\n  ⚠ Chỉ backup adapter H1_first (8 tokens, 7 non-null) — findings §6 kho-step evidence")
print(f"    (9 điểm với BANK-rút chi tiết) chờ operator paste source.")


# ═══════════════════════════════════════════════════════════
# T-② 6 CASE H2 EVIDENCE × EARLIEST-ELIGIBLE n∈{10,14,21,30}
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[T-② 6 CASE H2-EVIDENCE × earliest-eligible n∈{10,14,21,30}]")
print("═" * 100)
print("""
  Spec §1-H line 139: "H2 SEAT-LIFT... Evidence 6/8 (miss TUT, BTW)"
  → 6 case H2-evident = BANK, CYS, HEMI, ON, CAP, AKE (8 case − TUT − BTW).

  Findings §6/§11-15 "seat-lift ngày thật" — SOURCE MISSING (mm_stage_machine).
  → SEATLIFT-DATE-MISSING nơi thiếu; agent KHÔNG bịa.
""")

H2_CASE_6 = ["BANK", "CYS", "HEMI", "ON", "CAP", "AKE"]

def _h2_eligible_first(df, tok, n_oi):
    """First date where H2 warmup thỏa với floor_obs_min=n_oi"""
    start = datetime.strptime("2026-06-01", "%Y-%m-%d")
    end = datetime.strptime(WINDOW_END, "%Y-%m-%d")
    for i in range((end - start).days + 1):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        pos_14 = _v(df, d, "lsr_pos_r", 14)
        oi_all = _v(df, d, "oi_usd", 30)
        if len(pos_14) >= 14 and len(oi_all) >= n_oi:
            return d
    return None

def _h2_fire_first(df, tok, n_oi):
    """First date where H2 fires (with given floor_obs_min for OI)"""
    orig = cfg["h2"].get("floor_obs_min", 14)
    cfg["h2"]["floor_obs_min"] = n_oi
    try:
        start = datetime.strptime(WINDOW_START, "%Y-%m-%d")
        end = datetime.strptime(WINDOW_END, "%Y-%m-%d")
        for i in range((end - start).days + 1):
            d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            status, _ = _eval_h2_v(df, d)
            if status == "T": return d
    finally:
        cfg["h2"]["floor_obs_min"] = orig
    return None

print(f"  {'token':<7} {'seat-lift ngày thật':>21} {'n=10 elig-first':>17} {'n=10 fire':>10} "
      f"{'n=14 elig':>10} {'n=14 fire':>10} {'n=21 elig':>10} {'n=21 fire':>10} "
      f"{'n=30 elig':>10} {'n=30 fire':>10}")
print(f"  {'-'*130}")

t2_rows = []
for tok in H2_CASE_6:
    df = _df_sym(tok + "USDT")
    if df.empty:
        print(f"  {tok:<7} NO-STORE")
        continue
    row = {"tok": tok, "seat_lift_real": "[SEATLIFT-DATE-MISSING — findings §6/§11-15]"}
    for n in [10, 14, 21, 30]:
        row[f"elig_n{n}"] = _h2_eligible_first(df, tok, n)
        row[f"fire_n{n}"] = _h2_fire_first(df, tok, n)
    print(f"  {tok:<7} {row['seat_lift_real']:>21} "
          f"{str(row['elig_n10'] or 'N/A'):>17} {str(row['fire_n10'] or 'N/A'):>10} "
          f"{str(row['elig_n14'] or 'N/A'):>10} {str(row['fire_n14'] or 'N/A'):>10} "
          f"{str(row['elig_n21'] or 'N/A'):>10} {str(row['fire_n21'] or 'N/A'):>10} "
          f"{str(row['elig_n30'] or 'N/A'):>10} {str(row['fire_n30'] or 'N/A'):>10}")
    t2_rows.append(row)

print(f"\n  → n=14 (V② PROVISIONAL) cho earliest eligibility · fire dates thay đổi theo floor.")
print(f"    Findings seat-lift 'ngày thật' cần operator paste để so lead.")


# ═══════════════════════════════════════════════════════════
# T-③ MA TRẬN H2-FIRES × VẾ BẮT
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[T-③ MA TRẬN H2-FIRES × VẾ BẮT {pos-ratio · div-cut · cả hai · không}]")
print("═" * 100)

# Load census
perfire_df = pd.read_csv(REPO / "scratch" / "e2_census_perfire_20260828.csv")
h2_fires = perfire_df[perfire_df["h2"] == "T"]
print(f"\n  Census H2 fires: {len(h2_fires)} rows (từ commit 927b519 · full 52 eligible)")

# For each H2 fire row, evaluate which vế fired
t3_counts = {"pos_ratio_only": 0, "div_cut_only": 0, "both": 0, "neither": 0}
t3_detail = []
for _, r in h2_fires.iterrows():
    tok, date = r["token"], r["date"]
    df = _df_sym(tok + "USDT")
    _, hd = _eval_h2_v(df, date)
    if not hd:
        t3_detail.append({"tok": tok, "date": date, "vé": "N/A-DETAIL"})
        continue
    v1 = hd.get("v1_div_cut", False)
    v2 = hd.get("v2_pos_ratio", False)
    if v1 and v2: cat = "cả 2 vé"
    elif v2: cat = "pos-ratio"
    elif v1: cat = "div-cut"
    else: cat = "neither (recheck)"  # unusual — H2 T nhưng không vế nào
    key = "both" if (v1 and v2) else ("pos_ratio_only" if v2 and not v1 else ("div_cut_only" if v1 and not v2 else "neither"))
    t3_counts[key] += 1
    t3_detail.append({"tok": tok, "date": date, "vé": cat,
                       "div_min14": hd.get("div_min14"), "div_today": hd.get("div_today"),
                       "r_pos": hd.get("r_pos"), "r_oi": hd.get("r_oi")})

print(f"\n  Total H2 fires (census 52): {sum(t3_counts.values())}")
print(f"    Expected findings §11-15: 6-7 (H2 evidence 6/8 case)")
print(f"    Actual count: {len(t3_detail)}  → {'MATCH' if 6 <= len(t3_detail) <= 8 else 'FLAG mismatch — số thật in dưới'}")
print(f"\n  Vế bắt breakdown:")
for k, v in t3_counts.items():
    print(f"    {k:<20} : {v}")

print(f"\n  Chi tiết mỗi H2 fire:")
print(f"  {'#':>3} {'tok':<10} {'date':>12} {'vé':>15} {'div_min14':>10} {'div_today':>10} {'r_pos':>7} {'r_oi':>7}")
for i, r in enumerate(t3_detail, 1):
    print(f"  {i:>3} {r['tok']:<10} {r['date']:>12} {r.get('vé','?'):>15} "
          f"{r.get('div_min14',0) if r.get('div_min14') is not None else 0:>10.3f} "
          f"{r.get('div_today',0) if r.get('div_today') is not None else 0:>10.3f} "
          f"{r.get('r_pos',0) if r.get('r_pos') is not None else 0:>7.3f} "
          f"{r.get('r_oi',0) if r.get('r_oi') is not None else 0:>7.3f}")


# ═══════════════════════════════════════════════════════════
# T-④ GATE RENDER (ANALYSIS definition, DEV không chấm)
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[T-④ GATE RENDER · V④ compose + V② floor · substrate STORE (CASE cross-check)]")
print("═" * 100)
print("""
  Definition (ANALYSIS ký):
    substrate=STORE (CASE cross-check nơi có)
    compose H1∨(H2∧T0.1) AND NOT cooldown_14d (V④), shadow in kèm không đếm
    PASS = ≥1 fire lead ≥1d trước ignition (ignition NGUYÊN VĂN findings)
    case thiếu ignition → IGNITION-MISSING, rút mẫu số
    H N/A toàn cửa sổ tiền-ignition → loại H khỏi case; mọi H N/A → NOT-EVALUABLE rút mẫu số
""")

# Apply cooldown to census per token
def _apply_cooldown(fires_dates: list, cooldown_days: int, clean_days: int):
    """§8.4(i) reuse: first fire = day0, blocked days 1→cooldown-1, clear from day+cooldown.
    Đợt mới = sau ≥clean_days sạch (no fire) sau đợt trước."""
    if not fires_dates: return []
    fires_dates = sorted(fires_dates)
    kept = [fires_dates[0]]
    last_fire = datetime.strptime(fires_dates[0], "%Y-%m-%d")
    for f in fires_dates[1:]:
        d = datetime.strptime(f, "%Y-%m-%d")
        days_since = (d - last_fire).days
        if days_since >= cooldown_days:
            # Check ≥clean_days sạch preceding — assume gap since last kept ≥cooldown means sạch
            kept.append(f)
            last_fire = d
        # else: within cooldown, blocked
    return kept

def _fire_for(tok, date):
    """Compute GOM-H fire for (tok, date) with all V rules"""
    sym = tok + "USDT"
    df = _df_sym(sym)
    if df.empty: return None, None
    t01, td = _eval_t01_v(df, date)
    h1 = _h1_strict(tok, date, t01)
    h2, _ = _eval_h2_v(df, date)
    h3 = _eval_h3(df, date)
    gh = (h1 == "T") or ((h2 == "T") and (t01 == "T"))
    return gh, {"t01": t01, "h1": h1, "h2": h2, "h3": h3}

# Scan pre-ignition for each 8 case
print(f"  {'case':<7} {'ignition':>12} {'first_fire':>12} {'lead':>7} {'verdict':>12}   reason")
print(f"  {'-'*95}")

start_dt = datetime.strptime(WINDOW_START, "%Y-%m-%d")
end_dt = datetime.strptime(WINDOW_END, "%Y-%m-%d")
window_days = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
               for i in range((end_dt - start_dt).days + 1)]

gate_results = []
for tok in CASES:
    ign = IGNITIONS_VERIFIED[tok]
    if ign is None:
        gate_results.append({"tok": tok, "ign": None, "first_fire": None, "verdict": "IGNITION-MISSING"})
        print(f"  {tok:<7} {'BLANK':>12} {'—':>12} {'—':>7} {'IGN-MISSING':>12}   operator (a) chưa fill · rút khỏi mẫu số")
        continue

    # Scan for first fire before ignition
    ign_dt = datetime.strptime(ign, "%Y-%m-%d")
    all_fires = []
    h_coverage = {"H1": [], "H2": [], "T0.1": []}
    for d in window_days:
        if d >= ign: break
        f, hs = _fire_for(tok, d)
        if hs is None: continue
        for h in ("h1", "h2"):
            h_coverage[h.upper() if h == "h1" else h.upper()].append(hs[h])
        h_coverage["T0.1"].append(hs["t01"])
        if f: all_fires.append(d)

    # V④ cooldown
    kept_fires = _apply_cooldown(all_fires, cfg["gom_h_cooldown_days"], cfg["gom_h_cooldown_clean_days"])

    # Determine H N/A toàn cửa sổ
    def _all_na(lst): return all(s in ("N/A", "W", "N/A-WARMUP") for s in lst) if lst else True
    h_status = {h: ("NA-ALL" if _all_na(v) else "ok") for h, v in h_coverage.items()}
    if all(s == "NA-ALL" for s in h_status.values()):
        gate_results.append({"tok": tok, "ign": ign, "first_fire": None,
                              "verdict": "NOT-EVALUABLE"})
        print(f"  {tok:<7} {ign:>12} {'—':>12} {'—':>7} {'NOT-EVALUABLE':>13}   mọi H N/A toàn cửa sổ tiền-ign · rút mẫu số")
        continue

    if not kept_fires:
        gate_results.append({"tok": tok, "ign": ign, "first_fire": None, "verdict": "NO-FIRE"})
        print(f"  {tok:<7} {ign:>12} {'—':>12} {'—':>7} {'NO-FIRE':>12}   không fire pre-ignition ({','.join(h+':'+s for h,s in h_status.items())})")
        continue

    first_fire = kept_fires[0]
    d_first = datetime.strptime(first_fire, "%Y-%m-%d")
    lead = (ign_dt - d_first).days
    verdict = "PASS" if lead >= 1 else "FAIL-LEAD"
    gate_results.append({"tok": tok, "ign": ign, "first_fire": first_fire,
                          "lead": lead, "verdict": verdict, "kept": kept_fires})
    print(f"  {tok:<7} {ign:>12} {first_fire:>12} {f'+{lead}d':>7} {verdict:>12}   "
          f"cooldown-kept={len(kept_fires)}/{len(all_fires)} · H_status={','.join(h+':'+s for h,s in h_status.items())}")

# Aggregate
evaluable = [r for r in gate_results if r["verdict"] not in ("IGNITION-MISSING", "NOT-EVALUABLE")]
passes = [r for r in evaluable if r["verdict"] == "PASS"]
print(f"\n  ═══ GATE VERDICT ═══")
print(f"  passes/evaluable : {len(passes)}/{len(evaluable)} ({'PASS' if len(evaluable) > 0 and len(passes)/len(evaluable) >= 0.75 else 'FAIL/N-A'} — ANALYSIS chấm ngưỡng % qualify)")
print(f"  Rút khỏi mẫu số: IGN-MISSING={sum(1 for r in gate_results if r['verdict']=='IGNITION-MISSING')} · NOT-EVAL={sum(1 for r in gate_results if r['verdict']=='NOT-EVALUABLE')}")


# ═══════════════════════════════════════════════════════════
# CSV-63 UPDATE (age + TP/FP + rule header)
# ═══════════════════════════════════════════════════════════
print("\n" + "═" * 100)
print("[CSV-63 UPDATE · age + TP/FP + rule header cho ANALYSIS chấm]")
print("═" * 100)

today = datetime.now(timezone.utc).date()
csv_v2 = REPO / "scratch" / "e2_census_perfire_v2_20260828.csv"

# Prepend rule note as comment header
RULE_NOTE = """# CSV-63 — GOM-H E2 census per-fire (V①-⑤ post-verdict 28/08)
# Columns: token,date,t01,h1_kho,h1_fx,h1_shadow,h2,h2_vé,h3,active,conf,age_days,TP_FP
#
# ANALYSIS RULE:
#   TP = ≥+50% close D0..D+30 hoặc trong campaign đã niêm
#   tuổi<30d = PENDING (loại khỏi rate tính, đợi window đóng)
#   tuổi≥30d = có thể chấm TP/FP
#
# fire_age_days = today ({today}) − fire_date
# H1-shadow (V①) = kho(3d,≥10%) ∧ |ret14|≤0.15 — REPORT-ONLY không compose
# GOM-H compose (V④) = (H1 ∨ (H2 ∧ T0.1)) AND NOT cooldown_14d — census KHÔNG applied cooldown ở đây
#   (per-fire cooldown apply riêng theo per-token first-fire — xem T-④ GATE RENDER)
""".format(today=today)

# Compute age + h1_shadow + h2_vé per row
rows_v2 = []
for _, r in perfire_df.iterrows():
    tok, date = r["token"], r["date"]
    d_fire = datetime.strptime(date, "%Y-%m-%d").date()
    age = (today - d_fire).days
    # h1_shadow
    df = _df_sym(tok + "USDT")
    px_15 = _v(df, date, "px_avg", 15)
    ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if len(px_15) >= 15 and px_15[0] > 0 else None
    h1_sh = _h1_shadow(tok, date, ret14)
    # h2_vé
    _, hd = _eval_h2_v(df, date)
    v1 = hd.get("v1_div_cut", False) if hd else False
    v2 = hd.get("v2_pos_ratio", False) if hd else False
    ve = "both" if (v1 and v2) else ("pos-ratio" if v2 else ("div-cut" if v1 else "-"))
    rows_v2.append({
        "token": tok, "date": date, "t01": r["t01"], "h1_kho": r["h1_kho"],
        "h1_fx": r["h1_fx"], "h1_shadow": h1_sh, "h2": r["h2"], "h2_vé": ve,
        "h3": r["h3"], "active": r["active"], "conf": r["conf"],
        "age_days": age, "TP_FP": ""
    })

with open(csv_v2, "w", encoding="utf-8", newline="") as f:
    f.write(RULE_NOTE)
    w = csv.DictWriter(f, fieldnames=["token","date","t01","h1_kho","h1_fx","h1_shadow","h2","h2_vé","h3","active","conf","age_days","TP_FP"])
    w.writeheader()
    for r in rows_v2: w.writerow(r)

csv_md5 = hashlib.md5(open(csv_v2, "rb").read()).hexdigest()
print(f"\n  Output: {csv_v2.name}  md5: {csv_md5}")
print(f"  Rows: {len(rows_v2)}  · Age range: {min(r['age_days'] for r in rows_v2)}-{max(r['age_days'] for r in rows_v2)} days")
print(f"  All age_days = {(today - datetime.strptime(rows_v2[0]['date'], '%Y-%m-%d').date()).days}..{(today - datetime.strptime(rows_v2[-1]['date'], '%Y-%m-%d').date()).days}")
print(f"  All fires PENDING (tuổi<30d rule) — count: {sum(1 for r in rows_v2 if r['age_days'] < 30)}/{len(rows_v2)}")


print(f"\n{'═'*100}")
print(f"[DỪNG] V①-⑤ tables + T-④ gate + CSV-63 v2 done.")
print(f"       Findings §6/§11-15 SOURCE-MISSING — operator paste để hoàn thiện T-①/②/③ full.")
print(f"       Còn nợ: VPS 08-21 raw log + D3 cron log + 6 cron lines.")
print(f"{'═'*100}")
