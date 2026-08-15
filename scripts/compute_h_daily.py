#!/usr/bin/env python3
"""
§H1 daily H-texture compute: h1_skew, h2_oiw, h3_conc, h4_cloc.
Appends one row per symbol to data/gom_h_daily.csv (Zone-A style, append-only).

Usage:
  python scripts/compute_h_daily.py --date 2026-08-13 [--verbose] [--dry-run]

Spec: gom_detect_spec.md §H1-§H4 (v3.0-FINAL, signed 2026-08-14).
Formulas copied verbatim per L-31 (see §H1 block below).

§H1 formulas (copy nguyên văn — L-31):
  h1_skew  = mean(taker_buy% | giờ ret<0) − mean(taker_buy% | giờ ret>0)
             · yêu cầu ≥5 giờ mỗi phía, thiếu → NaN
             · Δ8: LOẠI giờ funding-settlement khỏi mẫu (theo _interval_h
               từng token: 8h→00/08/16 UTC · 4h→thêm 04/12/20 · 1h→không
               loại được, ghi cờ settle_1h_unfiltered) — taker-spike cơ
               học quanh settle nhiễm skew không vì gom
  h2_oiw   = Σ ΔOI⁺(giờ ret≤0) / Σ ΔOI⁺(mọi giờ)
             · CHỈ có nơi OI-hist 1h tồn tại (retention 30d) — NaN nếu
               thiếu, KHÔNG bịa
  h3_conc  = vol top-3 giờ / vol ngày   (thấp = rải = drip)
  h4_cloc  = mean((close−low)/(high−low) | giờ ret<0)   (cao = wick-buying)
             · Δ7 guard book-mỏng: giờ có range < max(0.25 ×
               median(range-giờ, 14d), 3 tick) → NaN không vào mẫu
               (CLV trên range 2-tick = máy sinh số ngẫu nhiên).
               0.25 = quy ước khai báo, không fit — đổi qua BOOK_THIN_FRAC + log.

Guards (§H1-addendum, dedup from Phase 0c, operator dir-3, 2026-08-14):
  Δ-dedup: df.drop_duplicates(["symbol","as_of_ts_ms"], keep="first")
           TRƯỚC mọi Δ/aggregate. Double/triple-write from backfill-over Jun10-21 gap.
  Δ8:      Exclude settlement hours. Distinct-hour count for h1 guard.
  Δ7:      book_thin_nan hours excluded from h4_cloc denominator.
  h1 guard: ≥5 distinct hours each side after Δ8, else NaN.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ── Paths ───────────────────────────────────────────────────────────────────────
REPO  = Path(__file__).resolve().parent.parent
RAW   = REPO / "data" / "raw"
DATA  = REPO / "data"

FUNDING_INTERVALS_PATH = DATA / "config" / "funding_intervals.json"
GOM_STATE_PATH         = DATA / "gom_state.json"
GOM_E_STATE_PATH       = DATA / "gom_e_state.json"
LEDGER                 = DATA / "gom_h_daily.csv"           # archived Aug13 data; not written
# Active forward-experiment ledger (carve-out A, H-tier archived 14/08/2026)
H2PRIME_LEDGER         = DATA / "gom_h2prime_daily.csv"

# ── Config constants ─────────────────────────────────────────────────────────────
# Δ7 book-thin guard — kept for compute_h_day_archived(); not used in active path
BOOK_THIN_FRAC: float = 0.25
TICK_3_FLOOR: float = 0.0

H1_MIN_HOURS: int = 5
WATCHLIST_LOOKBACK_DAYS: int = 30

# ── Ledger headers ───────────────────────────────────────────────────────────────
# ARCHIVED header (Aug13 data in gom_h_daily.csv — schema frozen, not appended to)
LEDGER_HEADER = [
    "date", "symbol",
    "h1_skew", "h2_oiw", "h3_conc", "h4_cloc",
    "flag_h_drip", "flag_h_wick", "flag_h_oiw",
    "guard_dup_klines", "guard_dup_oi",
    "guard_settle_excl", "guard_settle_1h_unfilt",
    "guard_book_thin_nan",
    "in_watchlist", "source",
]

# Active header — h2r watchlist forward experiment (carve-out A, operator ký 14/08/2026)
# h2r = rate_neg/rate_pos (ratio, scale-free, comparison column CHÍNH)
# h2r_log = ln(h2r) — symmetric, sign-readable (>0 = absorb nghiêng giờ đỏ)
# rate_neg_usd_hr — context-only, scale-dependent, KHÔNG dùng để so
# h2_old_share — chạy song song 30 ngày đối chiếu, rồi drop (log 1 dòng khi drop)
# flag_h_drip/wick/oiw: KHÔNG có — H không còn detection-tier (archived 14/08/2026)
H2PRIME_HEADER = [
    "date", "symbol",
    "h2r",              # rate_neg/rate_pos — ratio, scale-free
    "h2r_log",          # ln(h2r)
    "rate_neg_usd_hr",  # Σ ΔOI⁺(ret≤0)/n_neg_hrs [context-only]
    "h2_old_share",     # Σ ΔOI⁺(ret≤0)/Σ ΔOI⁺(all) — legacy, parallel 30d then drop
    "n_neg_hrs", "n_pos_hrs",
    "guard_dup_oi",
    "in_watchlist", "source",
]

MS_PER_HOUR = 3_600_000


def _nan(x) -> bool:
    try:
        return math.isnan(float(x))
    except Exception:
        return True


def fmt(v, prec=6) -> str:
    return "" if _nan(v) else str(round(float(v), prec))


# ── Funding / settlement ─────────────────────────────────────────────────────────

def load_funding_intervals() -> dict[str, int]:
    if not FUNDING_INTERVALS_PATH.exists():
        return {}
    with open(FUNDING_INTERVALS_PATH, encoding="utf-8") as f:
        return json.load(f)


def settle_hours_for(interval_h: int) -> set[int]:
    """UTC hours that are funding-settlement hours."""
    if interval_h <= 1:
        return set()  # 1h: cannot exclude — flag settle_1h_unfiltered
    return {h for h in range(0, 24, interval_h)}


# ── Watchlist (Phase 2 inline) ───────────────────────────────────────────────────

def build_watchlist(today_str: str) -> set[str]:
    """
    Watchlist(t) = T1 ∪ T2 ∪ T3 — recomputed each run, KHÔNG list tĩnh.
    T1: GOM-E registry (gom_e_state.json) — RỖNG pending GOM-E v0.9.2.
    T2: CASE_INDEX.xlsx status≠CLOSED — NOT on VPS; skipped with WARNING.
    T3: gom_state.json entries where last_gom_date within 30d.
    """
    cutoff = (date.fromisoformat(today_str) - timedelta(days=WATCHLIST_LOOKBACK_DAYS)).isoformat()
    wl: set[str] = set()

    # T1 — GOM-E (empty pending deploy)
    if GOM_E_STATE_PATH.exists():
        try:
            ge = json.load(open(GOM_E_STATE_PATH, encoding="utf-8"))
            for sym in ge:
                wl.add(sym if sym.endswith("USDT") else sym + "USDT")
        except Exception:
            pass

    # T2 — CASE_INDEX not on VPS
    # TODO(T2): sync CASE_INDEX.xlsx open cases or add override config
    print("  [watchlist-T2] CASE_INDEX not on VPS — skipped", file=sys.stderr)

    # T3 — D-tier fires last 30d
    if GOM_STATE_PATH.exists():
        gs = json.load(open(GOM_STATE_PATH, encoding="utf-8"))
        for sym, v in gs.items():
            if v.get("last_gom_date", "") >= cutoff:
                wl.add(sym if sym.endswith("USDT") else sym + "USDT")

    return wl


# ── Data loading ─────────────────────────────────────────────────────────────────

def load_klines_day(dt: str) -> tuple[pd.DataFrame, int]:
    """Load klines_1h, dedup. Returns (df_clean, dup_dropped_count)."""
    pq = RAW / "klines_1h" / f"date={dt}" / "part-0.parquet"
    if not pq.exists():
        return pd.DataFrame(), 0
    df = pd.read_parquet(pq)
    n_raw = len(df)
    # Δ-dedup: drop double/triple-write before any Δ or aggregate
    # (double-write from backfill-over Jun10-21 gap — probe 0c, 2026-08-14, operator dir-3)
    df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
    return df.sort_values(["symbol", "as_of_ts_ms"]).reset_index(drop=True), n_raw - len(df)


def load_oi_day(dt: str, watchlist: set[str]) -> tuple[pd.DataFrame, int]:
    """Load oi_hist_1h for watchlist symbols, dedup."""
    pq = RAW / "oi_hist_1h" / f"date={dt}" / "part-0.parquet"
    if not pq.exists() or not watchlist:
        return pd.DataFrame(), 0
    df = pd.read_parquet(pq)
    df = df[df["symbol"].isin(watchlist)].copy()
    n_raw = len(df)
    df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
    return df.sort_values(["symbol", "as_of_ts_ms"]).reset_index(drop=True), n_raw - len(df)


def range_medians_14d(target_dt: str, symbols: set[str]) -> dict[str, float]:
    """Per-symbol median(hourly range) over 14 days ending day before target_dt (Δ7)."""
    target = date.fromisoformat(target_dt)
    buckets: dict[str, list[float]] = {s: [] for s in symbols}
    for delta in range(1, 15):
        dt_str = (target - timedelta(days=delta)).isoformat()
        pq = RAW / "klines_1h" / f"date={dt_str}" / "part-0.parquet"
        if not pq.exists():
            continue
        df = pd.read_parquet(pq, columns=["symbol", "as_of_ts_ms", "high", "low"])
        df = df[df["symbol"].isin(symbols)]
        df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
        for sym, grp in df.groupby("symbol"):
            rng = (grp["high"] - grp["low"]).dropna()
            buckets[sym].extend(rng[rng > 0].tolist())
    return {
        sym: float(pd.Series(vals).median()) if vals else float("nan")
        for sym, vals in buckets.items()
    }


# ── Per-symbol compute ────────────────────────────────────────────────────────────

def compute_symbol(
    sym: str,
    sk: pd.DataFrame,            # klines for this symbol (deduped, sorted)
    so: pd.DataFrame,            # OI for this symbol (deduped, sorted; may be empty)
    interval_h: int,
    med14: float,
    in_wl: bool,
) -> dict:
    """Compute h1-h4 for one symbol. Returns result dict."""

    sk = sk.copy()
    sk["hour_utc"] = (sk["as_of_ts_ms"] // MS_PER_HOUR) % 24
    sk["ret"]      = (sk["close"] - sk["open"]) / sk["open"].clip(lower=1e-12)
    sk["tbuy_pct"] = sk["taker_buy_base_vol"] / sk["base_volume"].clip(lower=1e-12)
    sk["rng"]      = sk["high"] - sk["low"]

    # Δ8 — exclude settlement hours from h1_skew sample
    settle_hrs   = settle_hours_for(interval_h)
    settle_1h_uf = (interval_h == 1)

    if settle_hrs:
        mask_settle = sk["hour_utc"].isin(settle_hrs)
        sk_h1       = sk[~mask_settle]
        settle_excl = int(mask_settle.sum())
    else:
        sk_h1       = sk
        settle_excl = 0

    # ── h1_skew ────────────────────────────────────────────────────────────────────
    # h1_skew = mean(taker_buy% | ret<0) − mean(taker_buy% | ret>0)
    # ≥5 distinct hours each side after Δ8, else NaN
    neg_h = sk_h1[sk_h1["ret"] < 0]
    pos_h = sk_h1[sk_h1["ret"] > 0]
    if len(neg_h) >= H1_MIN_HOURS and len(pos_h) >= H1_MIN_HOURS:
        h1 = float(neg_h["tbuy_pct"].mean() - pos_h["tbuy_pct"].mean())
    else:
        h1 = float("nan")

    # ── h3_conc ────────────────────────────────────────────────────────────────────
    # h3_conc = vol top-3 hours / vol day
    vols     = sk["base_volume"].dropna().sort_values(ascending=False)
    vol_day  = float(vols.sum())
    vol_top3 = float(vols.head(3).sum())
    h3       = vol_top3 / vol_day if vol_day > 0 else float("nan")

    # ── h4_cloc ────────────────────────────────────────────────────────────────────
    # h4_cloc = mean((close−low)/(high−low) | ret<0)
    # Δ7: exclude hours with range < max(BOOK_THIN_FRAC × median_range_14d, TICK_3_FLOOR)
    thin_floor = max(BOOK_THIN_FRAC * med14, TICK_3_FLOOR) if not _nan(med14) and med14 > 0 else 0.0
    sk_neg_all = sk[sk["ret"] < 0]
    if thin_floor > 0:
        sk_neg = sk_neg_all[sk_neg_all["rng"] >= thin_floor]
    else:
        sk_neg = sk_neg_all
    book_thin_nan = len(sk_neg_all) - len(sk_neg)

    if len(sk_neg) >= 1:
        cloc = (sk_neg["close"] - sk_neg["low"]) / sk_neg["rng"].clip(lower=1e-12)
        h4   = float(cloc.mean())
    else:
        h4 = float("nan")

    # ── h2_oiw ─────────────────────────────────────────────────────────────────────
    # h2_oiw = Σ ΔOI⁺(ret≤0) / Σ ΔOI⁺(all)
    # CHỈ where OI-hist 1h exists; NaN if missing
    h2 = float("nan")
    if in_wl and not so.empty:
        so = so.copy()
        so = so.sort_values("as_of_ts_ms").reset_index(drop=True)
        so["hour_utc"]  = (so["as_of_ts_ms"] // MS_PER_HOUR) % 24
        so["delta_oi"]  = so["sum_open_interest"].diff()      # NaN at row 0
        so["doi_pos"]   = so["delta_oi"].clip(lower=0.0)

        # Align OI delta with klines ret by hour_utc
        sk_hr = sk[["hour_utc", "ret"]].set_index("hour_utc")
        so_hr = so.dropna(subset=["delta_oi"])[["hour_utc", "doi_pos"]].set_index("hour_utc")
        merged = so_hr.join(sk_hr, how="inner")
        sum_all = float(merged["doi_pos"].sum())
        sum_neg = float(merged.loc[merged["ret"] <= 0, "doi_pos"].sum())
        h2      = sum_neg / sum_all if sum_all > 0 else float("nan")

    return {
        "h1": h1, "h2": h2, "h3": h3, "h4": h4,
        "settle_excl": settle_excl,
        "settle_1h_uf": settle_1h_uf,
        "book_thin_nan": book_thin_nan,
    }


# ── Main day compute ──────────────────────────────────────────────────────────────

def compute_h_day_archived(target_dt: str, verbose: bool = False) -> list[dict]:
    """ARCHIVED 14/08/2026 — full-universe h1-h4 compute (gate §H5 FAIL, gomh_gate_closure_20260814.md).
    Kept for reference. Active path: compute_h2prime_day(). NOT called from main().
    """
    print(f"  [h-compute ARCHIVED] date={target_dt}  BOOK_THIN_FRAC={BOOK_THIN_FRAC}")

    funding  = load_funding_intervals()
    watchlist = build_watchlist(target_dt)
    print(f"  [watchlist] T3+T1={len(watchlist)} symbols")

    df_k, dup_klines = load_klines_day(target_dt)
    if df_k.empty:
        print(f"ERROR: klines_1h missing for {target_dt}", file=sys.stderr)
        return []
    print(f"  [klines] loaded {len(df_k)} rows (dup_dropped={dup_klines})")

    df_oi, dup_oi = load_oi_day(target_dt, watchlist)
    print(f"  [oi]     loaded {len(df_oi)} rows (dup_dropped={dup_oi})")

    symbols = sorted(df_k["symbol"].unique())
    print(f"  [symbols] {len(symbols)} in klines")

    # Δ7: precompute median 14d ranges for all symbols
    med14 = range_medians_14d(target_dt, set(symbols))

    rows: list[dict] = []
    for sym in symbols:
        sk = df_k[df_k["symbol"] == sym]
        so = df_oi[df_oi["symbol"] == sym] if not df_oi.empty else pd.DataFrame()
        in_wl = sym in watchlist
        iv_h  = funding.get(sym, 8)

        res = compute_symbol(sym, sk, so, iv_h, med14.get(sym, float("nan")), in_wl)

        row = {
            "date": target_dt,
            "symbol": sym,
            "h1_skew": fmt(res["h1"]),
            "h2_oiw":  fmt(res["h2"]),
            "h3_conc": fmt(res["h3"]),
            "h4_cloc": fmt(res["h4"]),
            "flag_h_drip": "",   # θ EMPTY — pending §H5 gate
            "flag_h_wick": "",
            "flag_h_oiw":  "",
            "guard_dup_klines":       dup_klines,
            "guard_dup_oi":           dup_oi,
            "guard_settle_excl":      res["settle_excl"],
            "guard_settle_1h_unfilt": int(res["settle_1h_uf"]),
            "guard_book_thin_nan":    res["book_thin_nan"],
            "in_watchlist": int(in_wl),
            "source": "klines-1h+store1h-dedup",
        }
        rows.append(row)

        if verbose:
            h1s = f"{res['h1']:+.4f}" if not _nan(res["h1"]) else " NaN "
            h2s = f"{res['h2']:.4f}"  if not _nan(res["h2"]) else " NaN "
            h3s = f"{res['h3']:.4f}"  if not _nan(res["h3"]) else " NaN "
            h4s = f"{res['h4']:.4f}"  if not _nan(res["h4"]) else " NaN "
            tag = "WL" if in_wl else "  "
            sf  = f"S{res['settle_excl']}" if res["settle_excl"] else "  "
            bt  = f"BT{res['book_thin_nan']}" if res["book_thin_nan"] else "   "
            s1u = "1Hu" if res["settle_1h_uf"] else "   "
            print(f"    {sym:>16}  h1={h1s}  h2={h2s}  h3={h3s}  h4={h4s}  {tag} {sf} {bt} {s1u}")

    return rows


def append_to_ledger(rows: list[dict]) -> None:
    """ARCHIVED write path — gom_h_daily.csv schema frozen at Aug13 data. Not called in active path."""
    write_header = not LEDGER.exists()
    with open(LEDGER, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_HEADER)
        if write_header:
            w.writeheader()
        w.writerows(rows)
        f.flush()
    if len(rows) == 0:
        print("RAISE: zero rows written to ledger — guard triggered", file=sys.stderr)
        sys.exit(1)


# ── h2′ rate-normalized (carve-out A, active) ────────────────────────────────────

def compute_h2_prime(
    sym: str,
    sk: pd.DataFrame,   # klines for this symbol (deduped, sorted)
    so: pd.DataFrame,   # OI for this symbol (deduped, sorted)
    interval_h: int,
) -> dict:
    """h2r = rate_neg / rate_pos (ratio, scale-free, comparison column CHINH).
    rate_neg = sum(DOI+(ret<=0)) / n_neg_hrs  [USD-OI per red hour]
    rate_pos = sum(DOI+(ret>0))  / n_pos_hrs  [USD-OI per green hour]
    h2r_log  = ln(h2r)  -- symmetric, sign-readable (>0 = absorb nghieng gio do)

    Guard (operator ky 14/08/2026):
      >=5 hrs each side AND rate_pos>0 AND rate_neg>0 -> else NaN, KHONG cap.
      (ngay cuc doan dang thay rieng; cap lam hong phan phoi forward-read)

    h2_old_share = sum(DOI+(ret<=0))/sum(DOI+(all)) -- song song 30 ngay roi drop.
    Carve-out A -- gom_detect_spec SH archived 14/08/2026; gomh_gate_closure_20260814.md.
    """
    NaN = float("nan")
    empty = {"h2r": NaN, "h2r_log": NaN, "rate_neg": NaN, "h2_share": NaN, "n_neg": 0, "n_pos": 0}
    if so.empty:
        return empty

    sk2 = sk.copy()
    sk2["hour_utc"] = (sk2["as_of_ts_ms"] // MS_PER_HOUR) % 24
    sk2["ret"]      = (sk2["close"] - sk2["open"]) / sk2["open"].clip(lower=1e-12)

    so2 = so.copy().sort_values("as_of_ts_ms").reset_index(drop=True)
    so2["hour_utc"] = (so2["as_of_ts_ms"] // MS_PER_HOUR) % 24
    so2["delta_oi"] = so2["sum_open_interest"].diff()
    so2["doi_pos"]  = so2["delta_oi"].clip(lower=0.0)

    sk_hr  = sk2[["hour_utc", "ret"]].set_index("hour_utc")
    so_hr  = so2.dropna(subset=["delta_oi"])[["hour_utc", "doi_pos"]].set_index("hour_utc")
    merged = so_hr.join(sk_hr, how="inner")

    neg_mask = merged["ret"] <= 0
    pos_mask = merged["ret"] > 0
    n_neg    = int(neg_mask.sum())
    n_pos    = int(pos_mask.sum())
    sum_neg  = float(merged.loc[neg_mask, "doi_pos"].sum())
    sum_pos  = float(merged.loc[pos_mask, "doi_pos"].sum())
    sum_all  = float(merged["doi_pos"].sum())
    h2_share = sum_neg / sum_all if sum_all > 0 else NaN

    # Guard: >=5 hrs each side AND both rates > 0 -> else NaN, no cap
    if n_neg < 5 or n_pos < 5 or sum_neg <= 0 or sum_pos <= 0:
        return {"h2r": NaN, "h2r_log": NaN, "rate_neg": NaN,
                "h2_share": h2_share, "n_neg": n_neg, "n_pos": n_pos}

    rate_neg = sum_neg / n_neg
    rate_pos = sum_pos / n_pos
    h2r      = rate_neg / rate_pos
    h2r_log  = math.log(h2r)
    return {"h2r": h2r, "h2r_log": h2r_log, "rate_neg": rate_neg,
            "h2_share": h2_share, "n_neg": n_neg, "n_pos": n_pos}


def compute_h2prime_day(target_dt: str, verbose: bool = False) -> list[dict]:
    """Active daily compute: watchlist-only h2' forward experiment (carve-out A).
    Scope: watchlist symbols with both klines + OI 1h data.
    h1/h3/h4 full-universe DISABLED — H-tier archived 14/08/2026 (FAIL gate §H5).
    """
    print(f"  [h2-prime] date={target_dt}  scope=watchlist-only  [h1/h3/h4 DISABLED 14/08/2026]")

    funding   = load_funding_intervals()
    watchlist = build_watchlist(target_dt)
    print(f"  [watchlist] T3+T1={len(watchlist)} symbols")

    if not watchlist:
        print("  [h2-prime] watchlist empty — 0 rows", file=sys.stderr)
        return []

    df_k, dup_k  = load_klines_day(target_dt)
    df_oi, dup_oi = load_oi_day(target_dt, watchlist)
    print(f"  [klines] {len(df_k)} rows (dup_dropped={dup_k})")
    print(f"  [oi]     {len(df_oi)} rows (dup_dropped={dup_oi})")

    rows: list[dict] = []
    for sym in sorted(watchlist):
        sk = df_k[df_k["symbol"] == sym] if not df_k.empty else pd.DataFrame()
        so = df_oi[df_oi["symbol"] == sym] if not df_oi.empty else pd.DataFrame()
        if sk.empty or so.empty:
            continue

        iv_h = funding.get(sym, 8)
        res  = compute_h2_prime(sym, sk, so, iv_h)

        row = {
            "date":            target_dt,
            "symbol":          sym,
            "h2r":             fmt(res["h2r"], 6),
            "h2r_log":         fmt(res["h2r_log"], 6),
            "rate_neg_usd_hr": fmt(res["rate_neg"], 2),
            "h2_old_share":    fmt(res["h2_share"], 6),
            "n_neg_hrs":       res["n_neg"],
            "n_pos_hrs":       res["n_pos"],
            "guard_dup_oi":    dup_oi,
            "in_watchlist":    1,
            "source":          "oi-1h+klines-1h-watchlist-dedup",
        }
        rows.append(row)

        if verbose:
            h2r_s  = f"{res['h2r']:+.4f}"     if not _nan(res["h2r"])     else " NaN "
            h2rl_s = f"{res['h2r_log']:+.4f}" if not _nan(res["h2r_log"]) else " NaN "
            print(f"    {sym:>16}  h2r={h2r_s}  h2r_log={h2rl_s}  n_neg={res['n_neg']}  n_pos={res['n_pos']}")

    return rows


def append_to_h2prime_ledger(rows: list[dict]) -> None:
    write_header = not H2PRIME_LEDGER.exists()
    with open(H2PRIME_LEDGER, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=H2PRIME_HEADER)
        if write_header:
            w.writeheader()
        w.writerows(rows)
        f.flush()
    if len(rows) == 0:
        print("RAISE: zero rows written — guard triggered", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="§H1 h2' watchlist forward (h1/h3/h4 archived 14/08)")
    ap.add_argument("--date",    default=date.today().isoformat(), help="YYYY-MM-DD")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="Compute but do not write ledger")
    args = ap.parse_args()

    rows = compute_h2prime_day(args.date, verbose=args.verbose)
    if not rows:
        sys.exit(1)

    n_h2r = sum(1 for r in rows if r["h2r"] != "")
    print(f"\n  watchlist={len(rows)}  h2r_valid={n_h2r}")

    if args.dry_run:
        print("  [dry-run] ledger NOT written")
        return

    append_to_h2prime_ledger(rows)
    print(f"  → ledger appended: {len(rows)} rows → {H2PRIME_LEDGER}")


if __name__ == "__main__":
    main()
