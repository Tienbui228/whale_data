#!/usr/bin/env python3
"""GOM-H DAILY RUNNER (PHA D2) — report-only per (token, day).

Operator ký chat 27/08 GOM-RESTRUCT PHA D2.

Compose: GOM-H = H1 ∨ (H2 ∧ T0.1); H3 chỉ nâng confidence.

Data sources:
  - Store freshwatch daily CSV: data/export/freshwatch_daily_2026-*.csv
    Cols: date, symbol, px_avg, vol_quote, vol_source, taker_buy_pct, taker_source,
          funding_avg/min/max, funding_n, oi_usd, lsr_pos_r, lsr_acc_r, lsr_global_r,
          taker_ratio, low_conf, src_ratio, data_ok
  - H1 adapter: scripts/adapter_h1_nansen.py read_adapter_daily(ingest_date)
  - Config: screen_thresholds.yaml gom_h: PROVISIONAL-UNSIGNED

Warmup (điểm-non-null per ⑨):
  - H2: 14 pos_r non-null + 30 oi_usd non-null
  - H3: 14 vol_quote non-null
  - T0.1: 14 funding_avg + 30 oi_usd + 14 ret + 7+30 vol non-null
  Thiếu = "N/A-WARMUP" (không False, không im).

Output:
  - scratch/gom_h_daily_<date>.csv (append-only, khóa (token,date))
  - stdout Telegram block "CAMPAIGN-PRE (soi on-chain) [REPORT-ONLY · PROVISIONAL-UNSIGNED]"

Usage:
  python scripts/gom_h_daily.py --date 2026-08-23    # target date (D-1 typical)
  python scripts/gom_h_daily.py --date auto           # yesterday UTC
"""
from __future__ import annotations
import sys, io, argparse, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from statistics import median
import pandas as pd
import yaml

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
FW_SYMS = REPO / "data/config/freshwatch_symbols.txt"
YAML_PATH = REPO / "screen_thresholds.yaml"
SCRATCH_DIR = REPO / "scratch"
SPEC_VERSION = "v4.0-draft"
AMENDMENTS = ["GOI-NHE-20260829", "V④-RT-2CHỐT-ANALYSIS-20260828",
              "⑬-COLUMN-MANIFEST-20260826", "GOM-RESTRUCT-20260824"]

# ─── Warmup thresholds (điểm-non-null) ───
WARMUP_H2_POS_N = 14
WARMUP_H2_OI_N = 30
WARMUP_H3_VOL_N = 14
WARMUP_T01_FUNDING_N = 14
WARMUP_T01_OI_N = 30
WARMUP_T01_VOL_MED30_N = 30


def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""): h.update(c)
    return h.hexdigest()


def _load_cfg():
    with open(YAML_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_universe():
    with open(FW_SYMS, encoding="utf-8") as f:
        return sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})


def _load_store(target_date: str) -> pd.DataFrame:
    """Load freshwatch_daily CSVs covering target_date + 30d lookback."""
    frames = []
    for m in ["05", "06", "07", "08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists():
            frames.append(pd.read_csv(p))
    df = pd.concat(frames, ignore_index=True)
    return df


def _values_upto(df_sym: pd.DataFrame, date: str, col: str, n: int) -> list[float]:
    """Return last n values of col up to and including date (dropna)."""
    df_sub = df_sym[df_sym["date"] <= date].sort_values("date").tail(n)
    vals = [float(v) for v in df_sub[col].tolist() if pd.notna(v)]
    return vals


def _compute_ret14(df_sym: pd.DataFrame, date: str) -> float:
    """|ret14| = |px_today − px_14d_ago| / px_14d_ago"""
    prices = _values_upto(df_sym, date, "px_avg", 15)
    if len(prices) < 15: return float("nan")
    px_14d = prices[0]; px_now = prices[-1]
    if px_14d <= 0: return float("nan")
    return abs(px_now - px_14d) / px_14d


def _compute_div_avg3(df_sym: pd.DataFrame, date: str) -> float:
    """avg3(pos_r) / avg3(acc_r) per M1 canonical (paired-NaN)."""
    df_sub = df_sym[df_sym["date"] <= date].sort_values("date").tail(3)
    pairs = []
    for _, r in df_sub.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
    if not pairs: return float("nan")
    avg_p = sum(p for p, _ in pairs) / len(pairs)
    avg_a = sum(a for _, a in pairs) / len(pairs)
    if avg_a < 1e-9: return float("nan")
    return avg_p / avg_a


def _compute_div_avg3_min14(df_sym: pd.DataFrame, date: str) -> float:
    """min(div_avg3) over last 14 days ending at date."""
    dates = sorted(df_sym[df_sym["date"] <= date]["date"].tolist())[-14:]
    if len(dates) < 14: return float("nan")
    divs = []
    for d in dates:
        v = _compute_div_avg3(df_sym, d)
        if pd.notna(v): divs.append(v)
    if not divs: return float("nan")
    return min(divs)


def _eval_t01(df_sym: pd.DataFrame, date: str, cfg_t01) -> tuple[str, dict]:
    """T0.1 compression eval → (status, detail).
    status ∈ {"T", "F", "N/A-WARMUP"}
    """
    detail = {}
    # Warmup: 14 funding + 30 oi + 14 ret (px) + 30 vol
    funding_14 = _values_upto(df_sym, date, "funding_avg", 14)
    oi_30 = _values_upto(df_sym, date, "oi_usd", 30)
    px_15 = _values_upto(df_sym, date, "px_avg", 15)
    vol_30 = _values_upto(df_sym, date, "vol_quote", 30)
    detail["n_funding_14"] = len(funding_14)
    detail["n_oi_30"] = len(oi_30)
    detail["n_px_15"] = len(px_15)
    detail["n_vol_30"] = len(vol_30)
    # [V② OI-FLOOR] Warmup floor: funding_14 + floor_obs_min oi + px_15 + vol_30
    floor_obs_min = cfg_t01.get("floor_obs_min", 14)
    if (len(funding_14) < WARMUP_T01_FUNDING_N or len(oi_30) < floor_obs_min
        or len(px_15) < 15 or len(vol_30) < WARMUP_T01_VOL_MED30_N):
        detail["floor_basis"] = f"{len(oi_30)}d"
        return "N/A-WARMUP", detail
    # 1) funding pinned 14d: all |f| ≤ pin_abs (+ ε for boundary inclusive per V⑤)
    pin_abs = cfg_t01["funding_pin_abs"]
    pin_eps = cfg_t01.get("funding_pin_eps", 1.0e-9)
    fund_pinned = all(abs(v) <= pin_abs + pin_eps for v in funding_14)
    detail["fund_pinned"] = fund_pinned
    # 2) OI ≤ 1.2 × min(oi available) — floor_basis = len(oi_30) (V②)
    oi_today = df_sym[df_sym["date"] == date]["oi_usd"].iloc[0] if not df_sym[df_sym["date"] == date].empty else float("nan")
    if pd.isna(oi_today):
        return "N/A-WARMUP", detail
    oi_min = min(oi_30)  # min(available), floor_obs_min already gated warmup
    detail["floor_basis"] = f"{len(oi_30)}d"
    oi_ok = oi_today <= cfg_t01["oi_over_min30_max"] * oi_min
    detail["oi_ratio"] = oi_today / oi_min if oi_min > 0 else float("nan")
    # 3) |ret14| ≤ 10%
    ret14 = _compute_ret14(df_sym, date)
    if pd.isna(ret14):
        return "N/A-WARMUP", detail
    ret_ok = ret14 <= cfg_t01["ret14_abs_max"]
    detail["ret14"] = ret14
    # 4) med7(vol) ≤ med30(vol)
    vol_7 = vol_30[-7:] if len(vol_30) >= 7 else vol_30
    med7 = median(vol_7) if vol_7 else 0
    med30 = median(vol_30) if vol_30 else 0
    vol_ok = med7 <= cfg_t01["vol_med7_over_med30_max"] * med30 if med30 > 0 else False
    detail["vol_med7_med30_ratio"] = med7 / med30 if med30 > 0 else float("nan")
    all_ok = fund_pinned and oi_ok and ret_ok and vol_ok
    return ("T" if all_ok else "F"), detail


def _eval_h2(df_sym: pd.DataFrame, date: str, cfg_h2) -> tuple[str, dict]:
    """H2 SEAT-LIFT eval."""
    detail = {}
    # [V② OI-FLOOR H2-vế-2] floor_obs_min replaces 30d hard req
    floor_obs_min = cfg_h2.get("floor_obs_min", 14)
    pos_14 = _values_upto(df_sym, date, "lsr_pos_r", 14)
    oi_30 = _values_upto(df_sym, date, "oi_usd", 30)
    detail["n_pos_14"] = len(pos_14); detail["n_oi_30"] = len(oi_30)
    detail["floor_basis"] = f"{len(oi_30)}d"
    if len(pos_14) < WARMUP_H2_POS_N or len(oi_30) < floor_obs_min:
        return "N/A-WARMUP", detail
    # div_avg3 today + min14
    div_today = _compute_div_avg3(df_sym, date)
    div_min14 = _compute_div_avg3_min14(df_sym, date)
    detail["div_today"] = div_today; detail["div_min14"] = div_min14
    if pd.isna(div_today) or pd.isna(div_min14):
        return "N/A-WARMUP", detail
    # Vế 1: min(div 14d) ≤ 0.6 ∧ div today ≥ 1.0
    v1 = (div_min14 <= cfg_h2["div_min_14d_max"]) and (div_today >= cfg_h2["div_today_min"])
    # Vế 2: pos_today / min(pos 14d) ≥ 1.25 ∧ oi ≤ 1.2 × min30
    pos_today = df_sym[df_sym["date"] == date]["lsr_pos_r"]
    pos_today = float(pos_today.iloc[0]) if not pos_today.empty and pd.notna(pos_today.iloc[0]) else float("nan")
    pos_min14 = min(pos_14)
    if pos_today == pos_today and pos_min14 > 0:
        pos_ratio = pos_today / pos_min14
        detail["pos_ratio"] = pos_ratio
    else:
        pos_ratio = float("nan")
    oi_today = df_sym[df_sym["date"] == date]["oi_usd"]
    oi_today = float(oi_today.iloc[0]) if not oi_today.empty and pd.notna(oi_today.iloc[0]) else float("nan")
    oi_min = min(oi_30)  # [V②] min(available) with floor_obs_min already gated
    if pd.isna(oi_today) or oi_min <= 0:
        return "N/A-WARMUP", detail
    oi_ratio = oi_today / oi_min
    v2 = (pd.notna(pos_ratio) and pos_ratio >= cfg_h2["pos_over_min14_min"]
          and oi_ratio <= cfg_h2["oi_over_min30_max"])
    return ("T" if (v1 or v2) else "F"), detail


def _eval_h3(df_sym: pd.DataFrame, date: str, cfg_h3) -> tuple[str, dict]:
    """H3 PROBE eval (confidence booster)."""
    detail = {}
    vol_14 = _values_upto(df_sym, date, "vol_quote", 14)
    px_2 = _values_upto(df_sym, date, "px_avg", 2)
    detail["n_vol_14"] = len(vol_14)
    if len(vol_14) < WARMUP_H3_VOL_N:
        return "N/A-WARMUP", detail
    vol_today_row = df_sym[df_sym["date"] == date]["vol_quote"]
    vol_today = float(vol_today_row.iloc[0]) if not vol_today_row.empty and pd.notna(vol_today_row.iloc[0]) else float("nan")
    if pd.isna(vol_today):
        return "N/A-WARMUP", detail
    med14 = median(vol_14)
    if med14 <= 0:
        return "F", detail
    vol_ratio = vol_today / med14
    detail["vol_ratio"] = vol_ratio
    if len(px_2) < 2:
        return "N/A-WARMUP", detail
    ret_1d = abs((px_2[-1] - px_2[0]) / px_2[0]) if px_2[0] > 0 else float("nan")
    detail["ret_1d"] = ret_1d
    ok = (vol_ratio >= cfg_h3["vol_mult_med14_min"]) and (ret_1d <= cfg_h3["ret_abs_max"])
    return ("T" if ok else "F"), detail


def _eval_h1(sym: str, target_date: str, adapter_df: pd.DataFrame, cfg_h1,
             t01_status: str = None) -> tuple[str, dict]:
    """H1 KHO-STEP eval from adapter output.
    Per spec §1-H (ký 24/08 amend GOM-RESTRUCT + H1-đường-(a) 28/08):
      H1 = |Δbalance| ≥[10%] trong ≤[3]d ∧ T0.1-compression đang bật tại ngày cuối cửa sổ
    kho_step_pct alone không đủ — phải AND với t01_status=="T" ngày target.

    detail["kho_raw"] = "True"/"False"/"N/A" — RAW kho check TRƯỚC T0.1 gate,
      used by V④-RT lane_kho cooldown reset (raw_condition per ANALYSIS 2-chốt).
    """
    detail = {}
    token = sym[:-4] if sym.endswith("USDT") else sym
    row = adapter_df[adapter_df["symbol"] == token]
    if row.empty:
        detail["flag"] = "MISSING-SYMBOL"
        detail["kho_raw"] = "N/A"
        return "N/A", detail
    r = row.iloc[0]
    flags = str(r.get("flags", "") or "")
    detail["flags"] = flags
    if "[API-FAILED]" in flags or "[MISSING-SNAPSHOT]" in flags:
        detail["kho_raw"] = "N/A"
        return "N/A", detail
    kho_step = r.get("kho_step_pct")
    detail["kho_step_pct"] = kho_step
    detail["t01_gate"] = t01_status
    if kho_step is None or pd.isna(kho_step):
        detail["kho_raw"] = "N/A"
        return "N/A", detail
    threshold_pct = cfg_h1["balance_delta_abs_min"] * 100.0  # config is fraction; step is pct
    kho_ok = abs(float(kho_step)) >= threshold_pct
    detail["kho_raw"] = "True" if kho_ok else "False"
    # Spec §1-H: ∧ T0.1-compression đang bật tại ngày cuối cửa sổ
    if not kho_ok:
        return "F", detail
    if t01_status is None or t01_status == "N/A-WARMUP":
        return "N/A", detail  # không xác định được T0.1 → H1 N/A
    if t01_status == "T":
        return "T", detail
    return "F", detail  # kho fire nhưng T0.1 không compression → không H1


def _check_lane_cooldown(sym: str, target: str, lane: str,
                          scratch_dir: Path,
                          cooldown_days: int = 14,
                          clean_days: int = 3) -> tuple[bool, str, int, int]:
    """V④-RT two-lane cooldown check per §8.4(i) mục con GOM-H (ANALYSIS 2 chốt 28/08).

    Args:
      lane: "kho" (H1-kho) hoặc "perp" (H2 ∧ T0.1) — hai lane độc lập, đồng hồ riêng.

    Returns: (in_cooldown, reason, days_since_last_fire, clean_streak)
      - in_cooldown=True → block THIS lane compose fire (mark F-COOLDOWN[lane])
      - Re-arm iff BOTH: days_since >= cooldown_days AND clean_streak >= clean_days
      - Raw_condition per lane:
          lane="kho"  → h1_raw column (kho_step ≥10% RAW, trước T0.1 gate)
          lane="perp" → h2t01_raw column ((H2 AND T0.1) RAW, aggregate)
      - N/A không đếm là sạch (đồng hồ đứng, không reset)
    """
    target_dt = datetime.strptime(target, "%Y-%m-%d")
    active_lanes_col = "active_lanes"
    raw_col = "h1_raw" if lane == "kho" else "h2t01_raw"

    # Step 1: find most recent lane fire (active_lanes contains this lane)
    last_lane_fire = None
    for lb in range(1, cooldown_days * 2 + 1):  # scan up to 2×cooldown for lane fire
        d = (target_dt - timedelta(days=lb)).strftime("%Y-%m-%d")
        csv_path = Path(scratch_dir) / f"gom_h_daily_{d}.csv"
        if not csv_path.exists():
            continue
        try:
            df = pd.read_csv(csv_path)
            row = df[df["symbol"] == sym]
            if row.empty:
                continue
            active_lanes = str(row.iloc[0].get(active_lanes_col, "") or "")
            if lane in active_lanes.split("+"):
                last_lane_fire = d
                break
        except Exception:
            continue

    if last_lane_fire is None:
        return False, "no-prev-lane-fire", 0, 0

    last_fire_dt = datetime.strptime(last_lane_fire, "%Y-%m-%d")
    days_since = (target_dt - last_fire_dt).days

    # Step 2: walk backward from target-1 to last_fire+1, count clean streak
    # Rule: raw==False → streak+1; raw==True → streak reset; raw==N/A → hold (không đếm, không reset)
    clean_streak = 0
    max_clean = 0
    for lb in range(1, days_since):
        d = (target_dt - timedelta(days=lb)).strftime("%Y-%m-%d")
        csv_path = Path(scratch_dir) / f"gom_h_daily_{d}.csv"
        if not csv_path.exists():
            continue  # missing CSV → hold (đồng hồ đứng)
        try:
            df = pd.read_csv(csv_path)
            row = df[df["symbol"] == sym]
            if row.empty:
                continue
            raw_val = str(row.iloc[0].get(raw_col, "N/A") or "N/A")
            if raw_val == "False":
                clean_streak += 1
                max_clean = max(max_clean, clean_streak)
            elif raw_val == "True":
                clean_streak = 0  # reset chuỗi sạch
            # N/A → hold (đồng hồ đứng)
        except Exception:
            continue

    # Re-arm needs BOTH conditions
    if days_since >= cooldown_days and max_clean >= clean_days:
        return False, f"re-arm(t={days_since}d,clean={max_clean}d)", days_since, max_clean

    return True, f"cooldown-lane={lane}-since-{last_lane_fire}(t={days_since}d,clean={max_clean}d)", days_since, max_clean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="auto",
                    help="YYYY-MM-DD or 'auto' (default) = yesterday UTC. Cron nên bỏ $(date...) subshell.")
    ap.add_argument("--output-dir", default=str(SCRATCH_DIR))
    ap.add_argument("--verbose", action="store_true", help="Print per-token detail")
    args = ap.parse_args()

    # [P0-CRON-FIX 28/08] default=auto → yesterday UTC.
    # Cron entry chuẩn (bỏ $(date...) subshell, tránh %-escape rủi ro):
    #   45 1 * * * cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/gom_h_daily.py >> data/logs/gom_h_daily.log 2>&1
    if args.date == "auto":
        target = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        target = args.date

    cfg = _load_cfg()
    gom_h_cfg = cfg.get("gom_h", {})
    symbols = _load_universe()
    store = _load_store(target)
    yaml_md5 = _md5(YAML_PATH)

    # ─── cfg-provenance header (L-64) ───
    print("═" * 100)
    print(f"[CFG-PROVENANCE gom_h_daily]")
    print(f"  Source: {YAML_PATH.relative_to(REPO)} (yaml load)")
    print(f"  yaml md5: {yaml_md5}")
    print(f"  Values ACTUALLY USED (gom_h section):")
    for key, val in gom_h_cfg.items():
        if isinstance(val, dict):
            print(f"    {key}:")
            for k, v in val.items():
                print(f"      {k}: {v}")
        else:
            print(f"    {key}: {val}")
    print(f"  spec_version: {SPEC_VERSION}")
    print(f"  amendments_applied: {AMENDMENTS}")
    print(f"  target_date: {target}  n_symbols: {len(symbols)}")
    print(f"  store rows: {len(store)}")
    print("═" * 100)

    # ─── Load H1 adapter (ingest_date = target + 1 day) ───
    try:
        # Ensure adapter module importable — script may be run from various cwd
        _adapter_path = REPO / "scripts"
        if str(_adapter_path) not in sys.path:
            sys.path.insert(0, str(_adapter_path))
        from adapter_h1_nansen import read_adapter_daily
        ingest_date = (datetime.strptime(target, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        adapter_df = read_adapter_daily(ingest_date)
        print(f"[H1 adapter] ingest_date={ingest_date}, rows={len(adapter_df)}")
    except Exception as e:
        print(f"[H1 adapter] FAIL: {type(e).__name__}: {e}")
        adapter_df = pd.DataFrame(columns=["symbol", "kho_step_pct", "flags"])

    # ─── Iterate per token ───
    results = []
    coverage = {
        "T0.1": {"T": 0, "F": 0, "N/A-WARMUP": 0, "N/A": 0},
        "H1":   {"T": 0, "F": 0, "N/A-WARMUP": 0, "N/A": 0},
        "H2":   {"T": 0, "F": 0, "N/A-WARMUP": 0, "N/A": 0},
        "H3":   {"T": 0, "F": 0, "N/A-WARMUP": 0, "N/A": 0},
    }
    n_fire = 0
    fires = []

    for sym in symbols:
        df_sym = store[store["symbol"] == sym].sort_values("date")
        if df_sym.empty:
            results.append({"symbol": sym, "date": target, "T0.1": "N/A",
                            "H1": "N/A", "H2": "N/A", "H3": "N/A", "GOM_H": "N/A", "conf": "-",
                            "flags": "MISSING-DATA"})
            for h in coverage: coverage[h]["N/A"] += 1
            continue

        t01_status, t01_detail = _eval_t01(df_sym, target, gom_h_cfg["t0_1"])
        h1_status, h1_detail = _eval_h1(sym, target, adapter_df, gom_h_cfg["h1"], t01_status)
        h2_status, h2_detail = _eval_h2(df_sym, target, gom_h_cfg["h2"])
        h3_status, h3_detail = _eval_h3(df_sym, target, gom_h_cfg["h3"])

        for h, s in [("T0.1", t01_status), ("H1", h1_status), ("H2", h2_status), ("H3", h3_status)]:
            if s == "T" or s == "F" or s in ("N/A-WARMUP", "N/A"):
                coverage[h][s] += 1

        # Compose GOM-H = (H1 ∨ (H2 ∧ T0.1)) AND NOT cooldown[lane]; H3 nâng conf
        # [V④-RT 2-chốt ANALYSIS 28/08] Two-lane independent cooldown:
        #   lane_kho = H1-kho status; lane_perp = (H2 ∧ T0.1) status
        h1_t = h1_status == "T"
        h2t01 = (h2_status == "T") and (t01_status == "T")

        # RAW conditions (trước cooldown gate) — for 3d-sạch counting in cooldown reset
        # h1_raw = kho ≥10% (raw, không ∧ T0.1); h2t01_raw = h2 ∧ t01 compose T (aggregate)
        h1_raw_str = h1_detail.get("kho_raw", "N/A")  # from _eval_h1
        if h2_status == "T" and t01_status == "T":
            h2t01_raw_str = "True"
        elif h2_status in ("W", "N/A-WARMUP", "N/A") or t01_status in ("W", "N/A-WARMUP", "N/A"):
            h2t01_raw_str = "N/A"
        else:
            h2t01_raw_str = "False"

        # [GOI-NHE-20260829] compose = H1-raw OR H2-raw · T0.1 → NHÃN CONF
        # h1_raw_gn = kho ≥10%/≤3d OR ramp ≥15%/≤14d (kho-ramp PROVISIONAL-KÝ-KÈM)
        # h2_raw_gn = H2 raw (independent of T0.1)
        # Compose OR without AND gate; T0.1 pass count → conf label
        goi_nhe_cfg = cfg.get("goi_nhe", {})
        dq_serial_cfg = cfg.get("dq_serial", {})
        dq_members = set(dq_serial_cfg.get("members", []))
        token_bare = sym[:-4] if sym.endswith("USDT") else sym
        dq_serial_hit = token_bare in dq_members

        # h1_raw = h1_kho_step OR h1_kho_ramp — PRODUCTION wire (was stub)
        h1_step_raw = (h1_raw_str == "True")
        # kho-ramp: |balance(D) - balance(D-14)| / balance(D-14) ≥ 0.15 via adapter
        # Adapter reads snapshot bal_date semantic §5 (SIGNED 28/08); ingest_date = target+1
        h1_ramp_raw = False
        try:
            ramp_cfg = goi_nhe_cfg.get("kho_ramp", {})
            ramp_thr = ramp_cfg.get("delta_min", 0.15)
            ramp_win = ramp_cfg.get("window_days", 14)
            # adapter_df has one row per token · we need balance series for D-14
            # Read from raw snapshot: ingest_date = target+1
            _snap_dir = Path("/root/Data_back_test/whale_data/data/raw/nansen_snapshots") \
                if _os_env.name == "posix" else Path("D:/Check onchain fresh wallets/snapshots")
            _target_dt = datetime.strptime(target, "%Y-%m-%d")
            _ingest_now = (_target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            _ingest_prev = (_target_dt + timedelta(days=1) - timedelta(days=ramp_win)).strftime("%Y-%m-%d")
            _snap_now = _snap_dir / f"{_ingest_now}.json"
            _snap_prev = _snap_dir / f"{_ingest_prev}.json"
            if _snap_now.exists() and _snap_prev.exists():
                import json as _json
                _d_now = _json.loads(_snap_now.read_text(encoding="utf-8"))
                _d_prev = _json.loads(_snap_prev.read_text(encoding="utf-8"))
                _b_now = next((r.get("exchange_balance_tokens")
                               for r in _d_now.get("rows", [])
                               if r.get("symbol", "").upper() == token_bare), None)
                _b_prev = next((r.get("exchange_balance_tokens")
                                for r in _d_prev.get("rows", [])
                                if r.get("symbol", "").upper() == token_bare), None)
                if _b_now is not None and _b_prev is not None and _b_prev > 0:
                    _ramp_delta = abs(_b_now - _b_prev) / _b_prev
                    if _ramp_delta >= ramp_thr:
                        h1_ramp_raw = True
        except Exception:
            pass  # ramp check fail-silent → treat as False (conservative)
        h1_raw_gn = h1_step_raw or h1_ramp_raw
        # h2_raw_gn: H2 raw regardless of T0.1
        h2_raw_gn = (h2_status == "T")

        # T0.1 conf mapping: count sub-vé pass on evaluable subset (skip N/A)
        def _conf_label(t01_detail):
            subs = {
                "funding_pin": t01_detail.get("fund_pinned"),
                "oi_min30":    (t01_detail.get("oi_ratio") is not None and
                                 t01_detail.get("oi_ratio") <= gom_h_cfg["t0_1"]["oi_over_min30_max"]),
                "ret14":       (t01_detail.get("ret14") is not None and
                                 t01_detail.get("ret14") <= gom_h_cfg["t0_1"]["ret14_abs_max"]),
                "med30_vol":   (t01_detail.get("vol_med7_med30_ratio") is not None and
                                 t01_detail.get("vol_med7_med30_ratio") <= gom_h_cfg["t0_1"]["vol_med7_over_med30_max"]),
            }
            na_list = [k for k, v in subs.items() if v is None]
            eval_pass = [k for k, v in subs.items() if v is True]
            eval_fail = [k for k, v in subs.items() if v is False]
            n_eval = len(eval_pass) + len(eval_fail)
            n_pass = len(eval_pass)
            if n_pass >= 4: level = "HIGH"
            elif n_pass >= 2: level = "MED"
            else: level = "LOW"
            na_str = ",".join(na_list) if na_list else "-"
            # Fix: return WITHOUT "conf=" prefix (caller adds it, avoid double)
            return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})"

        # Per-lane cooldown check (KEEP V④-RT semantic)
        cd_days = gom_h_cfg.get("gom_h_cooldown_days", 14)
        cn_days = gom_h_cfg.get("gom_h_cooldown_clean_days", 3)
        active_lanes = []
        suppressed_lanes = []
        suppressed_notes = []
        dq_notes = []

        # lane kho: check DQ-SERIAL first, then cooldown
        if h1_raw_gn:
            if dq_serial_hit:
                dq_notes.append(f"[DQ-SERIAL] {token_bare} lane=kho")
            else:
                in_cd_kho, cd_reason_kho, days_k, clean_k = _check_lane_cooldown(
                    sym, target, "kho", SCRATCH_DIR, cd_days, cn_days)
                if in_cd_kho:
                    suppressed_lanes.append("kho")
                    suppressed_notes.append(f"[SUPPRESSED {days_k}/14 lane=kho]")
                else:
                    active_lanes.append("kho")

        # lane perp: check DQ-SERIAL first, then cooldown
        if h2_raw_gn:
            if dq_serial_hit:
                dq_notes.append(f"[DQ-SERIAL] {token_bare} lane=perp")
            else:
                in_cd_perp, cd_reason_perp, days_p, clean_p = _check_lane_cooldown(
                    sym, target, "perp", SCRATCH_DIR, cd_days, cn_days)
                if in_cd_perp:
                    suppressed_lanes.append("perp")
                    suppressed_notes.append(f"[SUPPRESSED {days_p}/14 lane=perp]")
                else:
                    active_lanes.append("perp")

        conf_label_str = _conf_label(t01_detail) if (active_lanes or suppressed_lanes or dq_notes) else "-"

        # Compose GOM_H (GÓI-NHẸ: OR, no AND gate)
        if active_lanes:
            gom_h = "T"
            n_fire += 1
            active = []
            if "kho" in active_lanes: active.append("H1")
            if "perp" in active_lanes: active.append("H2")
            # [GOI-NHE tripwire runtime · SIGNED] record fire, check 0.4 trip
            tripwire_note = ""
            try:
                _tw_path = REPO / "lib/tripwire_e2.py"
                if _tw_path.exists():
                    if str(REPO) not in sys.path: sys.path.insert(0, str(REPO))
                    from lib.tripwire_e2 import record_fire
                    _tw_cfg = goi_nhe_cfg.get("tripwire_e2", {})
                    _tripped, _rate, _action = record_fire(
                        token_bare, target,
                        trailing_days=_tw_cfg.get("trailing_days", 30),
                        max_per_token=_tw_cfg.get("max_alert_per_token", 0.4),
                    )
                    if _tripped:
                        tripwire_note = _action
            except Exception:
                pass
            fires.append({"symbol": sym, "active": active, "conf": conf_label_str,
                          "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
                          "h1_detail": h1_detail,
                          "suppressed_note": " ".join(suppressed_notes),
                          "dq_note": " ".join(dq_notes),
                          "tripwire_note": tripwire_note})
        elif dq_notes:
            # DQ-SERIAL blocked, KHÔNG khởi cooldown per §7.1
            gom_h = "F-DQ-SERIAL"
            fires.append({"symbol": sym, "active": ["[DQ-SERIAL blocked]"],
                          "conf": conf_label_str,
                          "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
                          "h1_detail": h1_detail,
                          "suppressed_note": "", "dq_note": " ".join(dq_notes)})
        elif suppressed_lanes:
            # No new fire, but at least one lane suppressed
            gom_h = "F-COOLDOWN[" + "+".join(suppressed_lanes) + "]"
            fires.append({"symbol": sym, "active": [f"[suppressed:{'+'.join(suppressed_lanes)}]"],
                          "conf": conf_label_str,
                          "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
                          "h1_detail": h1_detail,
                          "suppressed_note": " ".join(suppressed_notes), "dq_note": ""})
        else:
            gom_h = "F" if (h1_status in ("F",) and h2_status in ("F","N/A-WARMUP") and t01_status in ("F","N/A-WARMUP")) else \
                    ("N/A-WARMUP" if "N/A-WARMUP" in (t01_status, h2_status) else "F")
            conf = "-"

        active_lanes_str = "+".join(active_lanes) if active_lanes else ""
        suppressed_note_str = " ".join(suppressed_notes) if suppressed_notes else ""
        dq_note_str = " ".join(dq_notes) if dq_notes else ""

        results.append({
            "symbol": sym, "date": target,
            "T0.1": t01_status, "H1": h1_status, "H2": h2_status, "H3": h3_status,
            "GOM_H": gom_h, "conf": conf_label_str,
            "active_lanes": active_lanes_str,        # kho | perp | kho+perp | ""
            "h1_raw": h1_raw_str,                     # kho_step pre-T01-gate
            "h2t01_raw": h2t01_raw_str,
            "h1_ramp_raw": "True" if h1_ramp_raw else "False",  # [GOI-NHE] kho-ramp check
            "dq_note": dq_note_str,                   # [GOI-NHE §7.1] [DQ-SERIAL] label
            "suppressed_note": suppressed_note_str,   # [V④-RT] "[SUPPRESSED n/14 lane=X]"
            "h1_kho_step_pct": h1_detail.get("kho_step_pct"),
            "h1_flags": h1_detail.get("flags", ""),
            "t01_fund_pinned": t01_detail.get("fund_pinned"),
            "t01_oi_ratio": t01_detail.get("oi_ratio"),
            "t01_ret14": t01_detail.get("ret14"),
            "h2_div_today": h2_detail.get("div_today"),
            "h2_div_min14": h2_detail.get("div_min14"),
            "h2_pos_ratio": h2_detail.get("pos_ratio"),
            "h3_vol_ratio": h3_detail.get("vol_ratio"),
        })

    # ─── Coverage summary ───
    print("\n" + "═" * 100)
    print(f"[COVERAGE per H — target {target}]")
    print(f"  {'H':<6} {'T':>5} {'F':>5} {'N/A-WARMUP':>12} {'N/A':>6} {'total':>7}")
    for h, cnts in coverage.items():
        total = sum(cnts.values())
        print(f"  {h:<6} {cnts['T']:>5} {cnts['F']:>5} {cnts['N/A-WARMUP']:>12} {cnts['N/A']:>6} {total:>7}")
    print(f"\n  GOM-H FIRE count: {n_fire} / {len(symbols)}")
    print("═" * 100)

    # ─── Write CSV output (append-only, khóa (token,date)) ───
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SCRATCH_DIR / f"gom_h_daily_{target}.csv"
    df_out = pd.DataFrame(results)
    df_out.to_csv(out_path, index=False)
    print(f"\n[OUTPUT] {out_path} (rows={len(df_out)}, md5={_md5(out_path)})")

    # ─── Telegram block ───
    print("\n" + "═" * 100)
    print("[TELEGRAM BLOCK — CAMPAIGN-PRE (soi on-chain) [REPORT-ONLY · PROVISIONAL-UNSIGNED]]")
    print("═" * 100)
    if n_fire == 0:
        print(f"CAMPAIGN-PRE {target}: 0 fires (fw-{len(symbols)})")
    else:
        print(f"CAMPAIGN-PRE {target}: {n_fire} fires (fw-{len(symbols)})")
        for f in fires:
            active_str = " + ".join(f["active"])
            print(f"  {f['symbol']}  [{active_str}]  conf={f['conf']}  H3={f['h3']}")
    # Footer
    print(f"\n---")
    print(f"spec_version: {SPEC_VERSION}")
    print(f"amendments_applied: {', '.join(AMENDMENTS)}")
    print(f"cfg-provenance: yaml_md5={yaml_md5[:12]}...")
    for h, cnts in coverage.items():
        total = sum(cnts.values())
        eval_n = cnts['T'] + cnts['F']
        print(f"  coverage {h}: n_fire={cnts['T']} n_NA={cnts['N/A']} n_warmup={cnts['N/A-WARMUP']} n_eval={eval_n} / total={total}")
    print(f"vol_source: {gom_h_cfg['h3']['vol_source']}")
    print("═" * 100)

    return 0


if __name__ == "__main__":
    sys.exit(main())
