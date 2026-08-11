#!/usr/bin/env python3
"""
GOM-E mode-switch detector — T2 INTRADAY EARLY-WARNING
Spec: proposals/gom_e_mode_switch_v092_20260812.md §5 T2 (FROZEN, commit 4c81a3d)
Entrypoint RIÊNG: không đụng T1 state/log. Cooldown T2 độc lập với T1.

data-source:
  - live 1h bars: Binance /futures/data endpoints (public, 4 canonical)
  - D-2 ref: data/gom_e_ref_store.csv (T1 store) — KHÔNG fetch live (Note-1)
  - min5d: data/export/ freshwatch_daily CSV (daily store)
  - candidate set: data/gom_e_state.json (T1 state last write)
machine: VPS canonical
date-range: forward-only từ ngày deploy
code-commit: see git log

L-21: CẤM Coinglass. CẤM mọi nguồn OI thứ ba — Coinglass lệch 22% vs openInterestHist.
      oi_now = /fapi/v1/openInterest.openInterest (tokens). oi_close_Dm2 = T1 store.
L-24: pos_close_Dm2 = T1 store[date=D-2].pos_raw_1h (bar 00:00 UTC ngày D-2). KHÔNG fetch live.
L-25: KHÔNG nguồn mới ngoài 4 endpoint canonical period=1h.
L-41: forming=D_run (hôm nay). EVAL=D_run-1. D-2=D_run-2.
Note-1 (RETIRED): live-fetch rule replaced by T1-STORE. Store thiếu → suppress_no_ref.
Note-3 thứ-tự: 0(PRECOND) → 1(ref D-2) → 2(compute prov) → 3(daily_quota) → 4(t1_dup) → 5(oi_expand) → 6(ping/no_signal)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import pandas as pd
import requests

# ── Repo paths ────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from fw_loader_utils import load_fw_csvs  # noqa: E402

# ── File paths ────────────────────────────────────────────────────────────────
STATE_PATH    = REPO_ROOT / "data" / "gom_e_state.json"       # T1 state (read-only here)
REF_STORE_PATH= REPO_ROOT / "data" / "gom_e_ref_store.csv"    # T1 store (read-only)
T1_ALERT_PATH = REPO_ROOT / "data" / "logs" / "gom_e_t1_alerts.csv"
T2_LOG_PATH   = REPO_ROOT / "data" / "logs" / "gom_e_t2_log.csv"
T2_STATE_PATH = REPO_ROOT / "data" / "gom_e_t2_state.json"    # T2 cooldown state

# ── §5 T2 config constants (from spec, quy ước khai báo — đổi qua config + log) ──
FORMING_FRAC     = 2 / 3          # §5: 2/3 × daily threshold (khai báo, không fit)
E1_PROV_THRESH   = FORMING_FRAC * 0.15   # = 0.10
E2_PROV_THRESH   = FORMING_FRAC * 0.15   # = 0.10
OI_EXPAND_THRESH = 0.10           # d_oitok_prov > +0.10 → suppress_oi_expand
COOLDOWN_DAYS_T2 = 3              # T2 cooldown, độc lập với T1
MIN5D_SHORT_BASE = 5              # min5d_count < 5 → SHORT-BASE flag

# LOG SCHEMA — spec §5 verbatim (23 fields, append-only)
T2_LOG_COLS = [
    "ts_utc", "symbol",
    "pos_now", "acc_now", "div_raw_prov",
    "pos_close_Dm2", "acc_close_Dm2",
    "d_pos_2d_prov", "d_acc_2d_prov",
    "oi_now", "oi_close_Dm2", "d_oitok_prov",
    "min5d",
    "pos_close_Dm2_canon", "gap_pct",
    "ref_method", "ref_bar_ts",
    "pass_E1", "pass_E2", "tag", "verdict",
    "t1_confirmed_at_close", "price_Tplus1",
]

# Binance 4 endpoint canonical (L-25: KHÔNG nguồn mới)
_BASE_FAPI = "https://fapi.binance.com"
_EP_POS    = f"{_BASE_FAPI}/futures/data/topLongShortPositionRatio"
_EP_ACC    = f"{_BASE_FAPI}/futures/data/topLongShortAccountRatio"
_EP_OI_NOW = f"{_BASE_FAPI}/fapi/v1/openInterest"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _f(v) -> float:
    try:
        x = float(v)
        return x if not math.isnan(x) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _csv_val(v) -> str:
    """Format for CSV: empty string if nan/None, else rounded str."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    try:
        return str(round(float(v), 6))
    except Exception:
        return str(v)


# ── Live fetch (1h bars, oi_now) ──────────────────────────────────────────────

def _fetch_latest_closed_1h(ep_url: str, symbol: str, field: str) -> tuple[Optional[float], Optional[int]]:
    """Fetch latest CLOSED 1h bar from Binance endpoint.
    Returns (value, bar_ts_ms). Uses limit=2; index [-2] = confirmed closed bar.
    L-25: cùng 4 endpoint canonical, period=1h.
    """
    try:
        r = requests.get(ep_url, params={"symbol": symbol, "period": "1h", "limit": 2}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data:
            idx = -2 if len(data) >= 2 else -1
            row = data[idx]
            ts_ms = int(row.get("timestamp", row.get("time", 0)))
            return _f(row.get(field)), ts_ms
        return None, None
    except Exception:
        return None, None


def _fetch_oi_now(symbol: str) -> Optional[float]:
    """L-21: oi_now from /fapi/v1/openInterest (tokens, NOT USD, NOT Coinglass)."""
    try:
        r = requests.get(_EP_OI_NOW, params={"symbol": symbol}, timeout=15)
        r.raise_for_status()
        return _f(r.json().get("openInterest"))
    except Exception:
        return None


# ── T1 store read ─────────────────────────────────────────────────────────────

def _read_store_d2(d_minus_2: str) -> dict[str, dict]:
    """Read T1 store rows for date=D-2. Returns {symbol: row_dict}.
    L-24: nguồn duy nhất cho pos_close_Dm2. KHÔNG fetch live.
    """
    if not REF_STORE_PATH.exists():
        return {}
    try:
        df = pd.read_csv(REF_STORE_PATH, dtype=str)
        rows = df[df["date"] == d_minus_2]
        out = {}
        for _, r in rows.iterrows():
            out[r["symbol"]] = {
                "pos_raw_1h":    _f(r.get("pos_raw_1h",    "")),
                "acc_raw_1h":    _f(r.get("acc_raw_1h",    "")),
                "oi_raw_1h":     _f(r.get("oi_raw_1h",     "")),
                "pos_canonical": _f(r.get("pos_canonical", "")),
            }
        return out
    except Exception:
        return {}


# ── State helpers ─────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_t2_state(s: dict):
    T2_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(T2_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2, default=str)


def _in_candidate_set(sym_state: dict, run_date: str) -> bool:
    """Registry ∪ vừa-ra-≤3d (same definition as T1 §1 STATE 2)."""
    if sym_state.get("in_registry"):
        return True
    exit_date = sym_state.get("exit_date")
    if exit_date:
        d_exit = pd.Timestamp(exit_date)
        d_run  = pd.Timestamp(run_date)
        if 0 <= (d_run - d_exit).days <= 3:
            return True
    return False


def _t1_fired_today(symbol: str, run_date: str) -> bool:
    """T1 đã bắn symbol hôm nay → T2 câm (t1_dup). Đọc gom_e_t1_alerts.csv."""
    if not T1_ALERT_PATH.exists():
        return False
    try:
        df = pd.read_csv(T1_ALERT_PATH, dtype=str)
        hits = df[
            (df["date"] == run_date) &
            (df["symbol"] == symbol) &
            (df["fire"].str.lower() == "true")
        ]
        return not hits.empty
    except Exception:
        return False


def _t2_daily_quota_hit(symbol: str, run_date: str, t2_state: dict) -> bool:
    """1 ping / symbol / day limit."""
    return t2_state.get(symbol, {}).get("last_ping_date") == run_date


def _t2_cooldown_blocked(symbol: str, run_date: str, t2_state: dict) -> bool:
    """T2 cooldown 3d (độc lập T1). Same tag doesn't refire."""
    last_ping = t2_state.get(symbol, {}).get("last_ping_date")
    if last_ping:
        days_since = (pd.Timestamp(run_date) - pd.Timestamp(last_ping)).days
        if days_since < COOLDOWN_DAYS_T2:
            return True
    return False


# ── Log append ────────────────────────────────────────────────────────────────

def _log_row(row: dict):
    T2_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_hdr = not T2_LOG_PATH.exists()
    full = {col: row.get(col, "") for col in T2_LOG_COLS}
    with open(T2_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=T2_LOG_COLS)
        if write_hdr:
            w.writeheader()
        w.writerow(full)


def _make_row(run_ts: str, sym: str, extras: dict) -> dict:
    """Build base log row, extras override."""
    base = {
        "ts_utc": run_ts, "symbol": sym,
        "ref_method": "1h-series",
        "t1_confirmed_at_close": "", "price_Tplus1": "",
    }
    base.update(extras)
    return base


# ── Main T2 poll ──────────────────────────────────────────────────────────────

def run_t2_poll(run_date: str, store_dir: Path):
    """One T2 poll cycle.

    run_date = forming day D_run (= today UTC, L-41).
    D-2 = D_run − 2 (ref date in T1 store).
    eval_date = D_run − 1 (for min5d daily store lookup).
    """
    now_utc  = datetime.now(timezone.utc)
    run_ts   = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    d_run    = datetime.strptime(run_date, "%Y-%m-%d").date()
    d_minus2 = (d_run - timedelta(days=2)).strftime("%Y-%m-%d")
    eval_str = (d_run - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"=== GOM-E T2 POLL {run_ts} ===")
    print(f"  forming={run_date}  EVAL={eval_str}  D-2={d_minus2}")

    t1_state = _load_json(STATE_PATH)
    t2_state = _load_json(T2_STATE_PATH)
    store_d2 = _read_store_d2(d_minus2)

    # Load min5d daily series up to EVAL (D_run-1 = last closed day)
    try:
        df_daily = load_fw_csvs(store_dir, eval_str, lookback_days=60)
    except Exception as e:
        print(f"  WARN: daily store load error: {e}")
        df_daily = pd.DataFrame()

    candidates = sorted(sym for sym, st in t1_state.items() if _in_candidate_set(st, run_date))
    print(f"  candidates: {len(candidates)}  store_d2_entries: {len(store_d2)}")

    n_ping = 0
    n_suppress = 0
    n_no_ref = 0

    for sym in candidates:

        # ── Step 0: PRECOND ────────────────────────────────────────────────────
        sym_d2 = store_d2.get(sym)
        if sym_d2 is None:
            # Missing D-2 entry → suppress_no_ref (always log per Note-3)
            _log_row(_make_row(run_ts, sym, {"verdict": "suppress_no_ref"}))
            n_no_ref += 1
            continue

        pos_close_Dm2 = sym_d2["pos_raw_1h"]
        acc_close_Dm2 = sym_d2["acc_raw_1h"]
        oi_close_Dm2  = sym_d2["oi_raw_1h"]
        pos_canon_Dm2 = sym_d2["pos_canonical"]

        # min5d from daily store (5 closed days BEFORE forming, shift(1).rolling(5))
        min5d, min5d_count = float("nan"), 0
        if not df_daily.empty:
            df_sym = df_daily[df_daily["symbol"] == sym].sort_values("date")
            if not df_sym.empty:
                pos_s = pd.to_numeric(df_sym["lsr_pos_r"], errors="coerce")
                acc_s = pd.to_numeric(df_sym["lsr_acc_r"], errors="coerce")
                if "low_conf" in df_sym.columns:
                    lc = df_sym["low_conf"].apply(
                        lambda x: str(x).strip().lower() in ("true", "1", "yes"))
                    pos_s = pos_s.where(~lc)
                    acc_s = acc_s.where(~lc)
                div_s = pos_s / acc_s
                s_min = div_s.shift(1).rolling(5, min_periods=1).min()
                s_cnt = div_s.shift(1).rolling(5, min_periods=1).count()
                if len(s_min) > 0:
                    min5d = float(s_min.iloc[-1])
                    v_cnt = float(s_cnt.iloc[-1])
                    min5d_count = int(v_cnt) if not math.isnan(v_cnt) else 0

        short_base = min5d_count < MIN5D_SHORT_BASE

        # ── Step 1: Fetch live 1h bars ─────────────────────────────────────────
        pos_now, pos_ts = _fetch_latest_closed_1h(_EP_POS, sym, "longShortRatio")
        acc_now, _      = _fetch_latest_closed_1h(_EP_ACC, sym, "longShortRatio")
        oi_now          = _fetch_oi_now(sym)

        if pos_now is None or math.isnan(pos_now):
            continue
        if acc_now is None or math.isnan(acc_now) or acc_now == 0:
            continue

        # ref_bar_ts: timestamp of live bar (informational; D-2 ref_bar_ts from store)
        ref_bar_ts = str(pos_ts) if pos_ts else ""

        # ── Step 2: Compute _prov ──────────────────────────────────────────────
        div_raw_prov  = pos_now / acc_now
        d_pos_2d_prov = (pos_now / pos_close_Dm2 - 1) if (not math.isnan(pos_close_Dm2) and pos_close_Dm2 != 0) else float("nan")
        d_acc_2d_prov = (acc_now / acc_close_Dm2 - 1) if (not math.isnan(acc_close_Dm2) and acc_close_Dm2 != 0) else float("nan")
        d_oitok_prov  = float("nan")
        if (oi_now is not None and not math.isnan(oi_now) and
                not math.isnan(oi_close_Dm2) and oi_close_Dm2 != 0):
            d_oitok_prov = oi_now / oi_close_Dm2 - 1

        e1_delta = (div_raw_prov - min5d) if not (math.isnan(div_raw_prov) or math.isnan(min5d)) else float("nan")
        pass_E1  = not math.isnan(e1_delta) and e1_delta >= E1_PROV_THRESH
        pass_E2  = not math.isnan(d_pos_2d_prov) and d_pos_2d_prov >= E2_PROV_THRESH

        # OI-EXPAND suppress trigger
        oi_expand_blocks = not math.isnan(d_oitok_prov) and d_oitok_prov > OI_EXPAND_THRESH

        # gap_pct: seam measurement (Note-2 — only measure, not evaluate)
        gap_pct = float("nan")
        if not math.isnan(pos_canon_Dm2) and pos_canon_Dm2 != 0 and not math.isnan(pos_close_Dm2):
            gap_pct = (pos_close_Dm2 - pos_canon_Dm2) / pos_canon_Dm2

        # Tags (from §5 T2)
        tag_parts = []
        if not math.isnan(d_oitok_prov):
            if d_oitok_prov <= 0:
                tag_parts.append("NUM-DRIVEN")    # canonical §1 — was "NUM-forming", aligned 11/08
            elif not oi_expand_blocks:  # 0 < d_oitok_prov ≤ 0.10
                tag_parts.append("MIXED")
        if (not math.isnan(d_acc_2d_prov) and not math.isnan(d_pos_2d_prov) and
                abs(d_acc_2d_prov) > d_pos_2d_prov):
            tag_parts.append("DENOM-ASSIST")
        if short_base:
            tag_parts.append("SHORT-BASE")
        tag_str = " ".join(f"[{t}]" for t in tag_parts) if tag_parts else ""

        # Shared row fields
        common = {
            "pos_now": _csv_val(pos_now), "acc_now": _csv_val(acc_now),
            "div_raw_prov": _csv_val(div_raw_prov),
            "pos_close_Dm2": _csv_val(pos_close_Dm2), "acc_close_Dm2": _csv_val(acc_close_Dm2),
            "d_pos_2d_prov": _csv_val(d_pos_2d_prov), "d_acc_2d_prov": _csv_val(d_acc_2d_prov),
            "oi_now": _csv_val(oi_now), "oi_close_Dm2": _csv_val(oi_close_Dm2),
            "d_oitok_prov": _csv_val(d_oitok_prov), "min5d": _csv_val(min5d),
            "pos_close_Dm2_canon": _csv_val(pos_canon_Dm2), "gap_pct": _csv_val(gap_pct),
            "ref_method": "1h-series", "ref_bar_ts": ref_bar_ts,
            "pass_E1": pass_E1, "pass_E2": pass_E2, "tag": tag_str,
        }

        # ── Step 3: daily_quota ────────────────────────────────────────────────
        if _t2_daily_quota_hit(sym, run_date, t2_state):
            if pass_E1 and pass_E2:
                _log_row(_make_row(run_ts, sym, {**common, "verdict": "suppress_daily_quota"}))
                n_suppress += 1
            continue

        # ── Step 4: t1_dup ─────────────────────────────────────────────────────
        if _t1_fired_today(sym, run_date):
            if pass_E1 and pass_E2:
                _log_row(_make_row(run_ts, sym, {**common, "verdict": "suppress_t1_dup"}))
                n_suppress += 1
            continue

        # ── Step 5: oi_expand suppress ────────────────────────────────────────
        if oi_expand_blocks:
            if pass_E1:
                _log_row(_make_row(run_ts, sym, {**common, "verdict": "suppress_oi_expand"}))
                n_suppress += 1
            continue

        # ── Step 6: ping or no_signal ─────────────────────────────────────────
        if pass_E1 and pass_E2:
            if _t2_cooldown_blocked(sym, run_date, t2_state):
                continue  # Cooldown: no_signal, KHÔNG log

            sb_label = "·SHORT-BASE" if short_base else ""
            ping_msg = (
                f"⚡ MODE-SWITCH FORMING {sym} "
                f"[INTRADAY-PROVISIONAL·SUSPECT{sb_label}] — "
                f"pos_prov {pos_now:.4f} vs close D-2 {pos_close_Dm2:.4f} "
                f"({d_pos_2d_prov:+.1%}) · div_prov {div_raw_prov:.4f} · "
                f"oiΔ_prov {d_oitok_prov:+.1%}. Chấm chính thức tại close."
            )
            print(f"\n  {ping_msg}")
            tag_display = tag_str if tag_str else "[UNTAGGED]"
            print(f"  Tags: {tag_display} | E1_prov={e1_delta:+.4f} E2_prov={d_pos_2d_prov:+.4f}")

            _log_row(_make_row(run_ts, sym, {**common, "verdict": "ping"}))
            t2_state.setdefault(sym, {})["last_ping_date"] = run_date
            n_ping += 1

        # no_signal: KHÔNG log (tránh nổ dòng registry × poll × ngày)

    _save_t2_state(t2_state)
    print(f"\n=== T2 DONE: pings={n_ping}  suppressed(oi_expand/dup/quota)={n_suppress}  no_ref={n_no_ref} ===")


def main():
    ap = argparse.ArgumentParser(description="GOM-E T2 intraday early-warning poll")
    ap.add_argument("--poll",  action="store_true", help="Run one poll cycle (production)")
    ap.add_argument("--store", default=str(REPO_ROOT / "data" / "export"),
                    help="Path to freshwatch_daily CSV directory")
    ap.add_argument("--date",  default=None,
                    help="Forming date YYYY-MM-DD (default: today UTC = D_run)")
    args = ap.parse_args()

    if args.poll:
        run_date  = args.date or datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        store_dir = Path(args.store)
        run_t2_poll(run_date, store_dir)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
