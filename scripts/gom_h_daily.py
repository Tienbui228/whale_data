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
AMENDMENTS = ["GOM-RESTRUCT-20260824", "⑬-COLUMN-MANIFEST-20260826"]

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
    """
    detail = {}
    token = sym[:-4] if sym.endswith("USDT") else sym
    row = adapter_df[adapter_df["symbol"] == token]
    if row.empty:
        detail["flag"] = "MISSING-SYMBOL"
        return "N/A", detail
    r = row.iloc[0]
    flags = str(r.get("flags", "") or "")
    detail["flags"] = flags
    if "[API-FAILED]" in flags or "[MISSING-SNAPSHOT]" in flags:
        return "N/A", detail
    kho_step = r.get("kho_step_pct")
    detail["kho_step_pct"] = kho_step
    detail["t01_gate"] = t01_status
    if kho_step is None or pd.isna(kho_step):
        return "N/A", detail
    threshold_pct = cfg_h1["balance_delta_abs_min"] * 100.0  # config is fraction; step is pct
    kho_ok = abs(float(kho_step)) >= threshold_pct
    # Spec §1-H: ∧ T0.1-compression đang bật tại ngày cuối cửa sổ
    if not kho_ok:
        return "F", detail
    if t01_status is None or t01_status == "N/A-WARMUP":
        return "N/A", detail  # không xác định được T0.1 → H1 N/A
    if t01_status == "T":
        return "T", detail
    return "F", detail  # kho fire nhưng T0.1 không compression → không H1


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

        # Compose GOM-H = H1 ∨ (H2 ∧ T0.1); H3 nâng conf
        h1_t = h1_status == "T"
        h2t01 = (h2_status == "T") and (t01_status == "T")
        # If H1 has data and either fires
        if h1_t or h2t01:
            gom_h = "T"
            n_fire += 1
            active = []
            if h1_t: active.append("H1")
            if h2t01: active.append("H2+T0.1")
            conf = "conf-boosted" if h3_status == "T" else "normal"
            fires.append({"symbol": sym, "active": active, "conf": conf,
                          "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
                          "h1_detail": h1_detail})
        else:
            gom_h = "F" if (h1_status in ("F",) and h2_status in ("F","N/A-WARMUP") and t01_status in ("F","N/A-WARMUP")) else \
                    ("N/A-WARMUP" if "N/A-WARMUP" in (t01_status, h2_status) else "F")
            conf = "-"

        results.append({
            "symbol": sym, "date": target,
            "T0.1": t01_status, "H1": h1_status, "H2": h2_status, "H3": h3_status,
            "GOM_H": gom_h, "conf": conf,
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
