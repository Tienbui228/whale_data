#!/usr/bin/env python3
"""
GOM-E mode-switch detector — T1 DAILY
Spec: proposals/gom_e_mode_switch_v092_20260812.md (FROZEN, commit 4c81a3d)
Gọi từ: run_gom_daily.py (subprocess, cron 01:25 UTC ngày D_run)

data-source: data/export/freshwatch_daily_YYYY-MM.csv (VPS canonical)
machine: VPS canonical (/root/Data_back_test/whale_data/)
date-range: forward-only từ ngày deploy
code-commit: see git log

L-21: CẤM Coinglass — oi_token = oi_usd / px_avg (daily store). CẤM OI thứ ba.
      Khoản chứng kiến: probe B1b PART2 → Coinglass lệch 22% so openInterestHist.
L-24: ĐỪNG lấy bar ngày-sai — T1-STORE capture EVAL=D_run-1, bar 00:00 UTC ngày EVAL.
L-25: KHÔNG nguồn mới ngoài 4 endpoint canonical (period=1h) cho T1-STORE.
L-28: RESTORE spec-intent cooldown exception — KHÔNG đổi luật.
      Root cause: code cũ dùng proxy tag-name (DENOM→NUM) thay e3-gốc (off→on).
      Sau khi MIXED branch thêm vào, [MIXED][DENOM-ASSIST] puts "MIXED" tại tags[0]
      → old DENOM→NUM exception fail → KOMA 08-03 block sai.
      Fix: exception quyết bằng e3-bool: last_fire_e3=False AND e3=True.
      Lưu last_fire_e3 trong state (migration fallback: tag=="NUM-DRIVEN" → e3=True).
      Canonical OOS fires: 47 (whipsaw-check 4 ca refire → 1-and-done, không loop).
L-41: ngày-đã-đóng — EVAL = D_run − 1. CẤM gen pos_canonical ngày D_run trước 00:05 D_run+1.
v2 boundary: "snapshot tại 00:00 UTC của ngày D = giá trị as_of_ts_ms == midnight_ms(D)"
             (proposals/archive/ratio_daily_canonical_20260731_v2.md)
             Ratio và OI cùng boundary: 00:00 UTC đầu ngày D. Nhất quán.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import traceback
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

import pandas as pd
import requests

# ── Repo paths ────────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).resolve().parent.parent
SCRIPTS_DIR  = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from fw_loader_utils import load_fw_csvs  # noqa: E402

# ── File paths ────────────────────────────────────────────────────────────────
STATE_PATH       = REPO_ROOT / "data" / "gom_e_state.json"
REF_STORE_PATH   = REPO_ROOT / "data" / "gom_e_ref_store.csv"
ALERT_LOG_PATH   = REPO_ROOT / "data" / "logs" / "gom_e_t1_alerts.csv"
LOG_PATH         = REPO_ROOT / "data" / "logs" / "gom_e_daily.log"

# ── §1 SPEC CONSTANTS (verbatim — đừng thay bằng magic numbers inline) ───────
# STATE 1 — HEDGE-FARM entry
H1_DIV_AVG3_MAX  = 0.85  # §1 H1: div_avg3 ≤ 0.85
H1_WINDOW        = 20    # §1 H1: 20 ngày gần nhất
H1_MIN_DAYS      = 10    # §1 H1: ≥10/20 ngày
H2_WINDOW        = 20    # §1 H2: 20 ngày
H2_MIN_DAYS      = 12    # §1 H2: f_avg > 0 ≥12/20 ngày
H3_GLSR_MIN      = 1.5   # §1 H3 điểm cộng: gLSR ≥ 1.5 đa số ngày
H3_MAJORITY_FRAC = 0.5   # "đa số" = > 50% của window

# STATE 1 — exit
EXIT_DIV_THRESH  = 1.0   # §1: div_avg3 > 1.0
EXIT_CONSEC      = 5     # §1: bền 5d liên tiếp

# STATE 2 — MODE-SWITCH fire conditions
E1_THAW          = 0.15  # §1 E1: div_raw(t) − min5d ≥ +0.15
E2_D_POS         = 0.15  # §1 E2: d_pos_2d ≥ +0.15
E4_PIN_MIN       = 10    # §1 E4 điểm cộng: pin_streak ≥ 10
E4_BREAK_WINDOW  = 3     # §1 E4: vỡ trong ≤3 ngày
OI_EXPAND_THRESH = 0.10  # §1 tag OI-EXPAND: d_oitok_2d > +0.10
COOLDOWN_DAYS    = 3     # §1: cooldown 3d, refire nếu tag đổi DENOM→NUM

# Pin band (from case study implementations: f_min ≥ 4e-5 AND f_avg ≤ 6e-5)
PIN_F_MIN_LOW    = 4e-5
PIN_F_AVG_HIGH   = 6e-5

# Binance 4 endpoint canonical (L-25: KHÔNG nguồn mới)
_BASE_FAPI       = "https://fapi.binance.com"
_EP_POS          = f"{_BASE_FAPI}/futures/data/topLongShortPositionRatio"
_EP_ACC          = f"{_BASE_FAPI}/futures/data/topLongShortAccountRatio"
_EP_GLSR         = f"{_BASE_FAPI}/futures/data/globalLongShortAccountRatio"
_EP_OIH          = f"{_BASE_FAPI}/futures/data/openInterestHist"
_EP_OI_NOW       = f"{_BASE_FAPI}/fapi/v1/openInterest"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _f(v) -> float:
    try:
        x = float(v)
        return x if not math.isnan(x) else float("nan")
    except (TypeError, ValueError):
        return float("nan")


def _bool_val(v, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and not math.isnan(float(v)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return default


def _midnight_ms(d: date) -> int:
    """v2 boundary: as_of_ts_ms == midnight_ms(D) = 00:00 UTC start of day D."""
    return int(datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)


def _log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} gom_e {msg}"
    print(line, file=sys.stderr)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)


# ── Metric computation ────────────────────────────────────────────────────────

def compute_metrics(df_sym: pd.DataFrame) -> pd.DataFrame:
    """Compute GOM-E derived columns for one symbol's time series.

    §1 variables: div_raw = pos_r/acc_r · div_avg3 · d_pos_2d · d_acc_2d
                  · d_oitok_2d · pin_streak · gLSR
    L-21: oi_token = oi_usd / px_avg (daily store, NOT Coinglass).
    v2 boundary: pos_r = lsr_pos_r = snapshot 00:00 UTC of day D (midnight_ms(D)).
    """
    df = df_sym.copy().sort_values("date").reset_index(drop=True)

    pos_r  = pd.to_numeric(df.get("lsr_pos_r"),     errors="coerce")
    acc_r  = pd.to_numeric(df.get("lsr_acc_r"),     errors="coerce")
    glsr   = pd.to_numeric(df.get("lsr_global_r"),  errors="coerce")
    f_avg  = pd.to_numeric(df.get("funding_avg"),   errors="coerce")
    f_min  = pd.to_numeric(df.get("funding_min"),   errors="coerce")
    oi_usd = pd.to_numeric(df.get("oi_usd"),        errors="coerce")
    px_avg = pd.to_numeric(df.get("px_avg"),        errors="coerce")

    # Mask low_conf rows (fn=1 trap per CLAUDE.md: "Ratio fn=1 → không dùng làm số chốt")
    if "low_conf" in df.columns:
        lc = df["low_conf"].apply(lambda x: _bool_val(x, False))
        pos_r  = pos_r.where(~lc)
        acc_r  = acc_r.where(~lc)
        glsr   = glsr.where(~lc)

    df["pos_r"]  = pos_r
    df["acc_r"]  = acc_r
    df["gLSR"]   = glsr
    df["f_avg"]  = f_avg
    df["f_min"]  = f_min

    # §1 div_raw = pos_r / acc_r
    df["div_raw"]  = pos_r / acc_r

    # §1 div_avg3 — Phụ lục A: 3-day rolling mean
    df["div_avg3"] = df["div_raw"].rolling(3, min_periods=1).mean()

    # §1 oi_token — L-21: oi_usd / px_avg, NOT Coinglass
    px_safe = px_avg.replace(0, float("nan"))
    df["oi_token"]   = oi_usd / px_safe

    # §1 d_pos_2d = pos_r(t) / pos_r(t-2) − 1
    df["d_pos_2d"]   = pos_r / pos_r.shift(2) - 1

    # §1 d_acc_2d = acc_r(t) / acc_r(t-2) − 1
    df["d_acc_2d"]   = acc_r / acc_r.shift(2) - 1

    # §1 d_oitok_2d = oi_token(t) / oi_token(t-2) − 1
    df["d_oitok_2d"] = df["oi_token"] / df["oi_token"].shift(2) - 1

    # pin_streak: consecutive days in pinned funding band [PIN_F_MIN_LOW, PIN_F_AVG_HIGH]
    pin_day = (f_min >= PIN_F_MIN_LOW) & (f_avg <= PIN_F_AVG_HIGH)
    streak, s = [], 0
    for p in pin_day.fillna(False):
        s = s + 1 if p else 0
        streak.append(s)
    df["pin_streak"] = streak

    # E1 min5d: min(div_raw over 5 closed days BEFORE t, NOT including t)
    # §5 T2: "min5d = min(div_raw trên 5 NẾN NGÀY ĐÓNG, KHÔNG tính forming)"
    # T1 all closed: window = shift(1).rolling(5)
    df["min5d_div"]   = df["div_raw"].shift(1).rolling(5, min_periods=1).min()
    df["min5d_count"] = df["div_raw"].shift(1).rolling(5, min_periods=1).count().astype(int)

    return df


# ── Registry logic ────────────────────────────────────────────────────────────

def eval_hedge_farm(df_sym: pd.DataFrame, target_date: str,
                    sym_state: dict) -> dict:
    """Evaluate H1/H2/H3 and update registry state for one symbol.

    §1 STATE 1 — HEDGE-FARM (điều kiện VÀO registry, loose):
      H1: div_avg3 ≤ 0.85 trong ≥10/20 ngày gần nhất
      H2: f_avg > 0 trong ≥12/20 ngày gần nhất
      H3: [điểm cộng] gLSR ≥ 1.5 đa số ngày
    RA registry: div_avg3 > 1.0 bền 5d HOẶC symbol hết data.
    """
    df = df_sym[df_sym["date"] <= target_date].tail(H1_WINDOW)
    if df.empty:
        return sym_state

    # H1: count days with div_avg3 ≤ H1_DIV_AVG3_MAX in last 20d
    h1_count = (df["div_avg3"] <= H1_DIV_AVG3_MAX).sum()
    h1_pass  = h1_count >= H1_MIN_DAYS

    # H2: count days with f_avg > 0 in last 20d
    h2_count = (df["f_avg"] > 0).sum()
    h2_pass  = h2_count >= H2_MIN_DAYS

    # H3 điểm cộng: gLSR ≥ H3_GLSR_MIN majority of days (> 50%)
    h3_count = (df["gLSR"] >= H3_GLSR_MIN).sum()
    h3_pass  = h3_count > len(df) * H3_MAJORITY_FRAC

    in_reg_now = sym_state.get("in_registry", False)

    if not in_reg_now:
        if h1_pass and h2_pass:
            sym_state["in_registry"] = True
            sym_state["entry_date"]  = target_date
            sym_state["days_in"]     = 1
            sym_state["h3"]          = h3_pass
            sym_state["f_avg_mean"]  = float(df["f_avg"].mean()) if not df["f_avg"].isna().all() else None
            sym_state.pop("exit_date", None)
            sym_state.pop("exit_reason", None)
    else:
        # Check exit condition: div_avg3 > EXIT_DIV_THRESH for EXIT_CONSEC consecutive days
        recent = df_sym[df_sym["date"] <= target_date].tail(EXIT_CONSEC)
        if len(recent) >= EXIT_CONSEC:
            all_above = (recent["div_avg3"] > EXIT_DIV_THRESH).all()
            if all_above:
                sym_state["in_registry"] = False
                sym_state["exit_date"]   = target_date
                sym_state["exit_reason"] = f"div_avg3>{EXIT_DIV_THRESH} bền {EXIT_CONSEC}d"
                return sym_state

        sym_state["days_in"] = (
            (pd.Timestamp(target_date) - pd.Timestamp(sym_state.get("entry_date", target_date))).days + 1
        )
        sym_state["h3"] = h3_pass
        sym_state["f_avg_mean"] = float(df["f_avg"].mean()) if not df["f_avg"].isna().all() else None

    return sym_state


def _in_candidate_set(sym_state: dict, target_date: str) -> bool:
    """True if symbol is in registry OR exited ≤3 days ago.

    §1 STATE 2: fire trên token TRONG registry HOẶC vừa ra ≤3 ngày.
    """
    if sym_state.get("in_registry"):
        return True
    exit_date = sym_state.get("exit_date")
    if exit_date:
        d_exit   = pd.Timestamp(exit_date)
        d_target = pd.Timestamp(target_date)
        if 0 <= (d_target - d_exit).days <= 3:
            return True
    return False


# ── Switch detection ──────────────────────────────────────────────────────────

def eval_mode_switch(df_sym: pd.DataFrame, target_date: str,
                     sym_state: dict) -> Optional[dict]:
    """Evaluate E1-E4 fire conditions for one symbol on target_date.

    §1 STATE 2 — MODE-SWITCH-CANDIDATE:
      E1 (div-thaw):  div_raw(t) − min(div_raw, 5d) ≥ +0.15
      E2 (tử số):     d_pos_2d ≥ +0.15
      E3 (cover):     d_oitok_2d ≤ 0
      E4 (điểm cộng): pin_streak ≥10 vừa VỠ trong ≤3 ngày
    FIRE = E1 AND E2
    Tags: [NUM-DRIVEN] if E3; [DENOM-ASSIST] if |d_acc_2d| > d_pos_2d; [OI-EXPAND] if d_oitok_2d > +0.10
    Cooldown: 3d same token, refire if tag changes DENOM→NUM.

    Returns fire dict or None.
    """
    row_df = df_sym[df_sym["date"] == target_date]
    if row_df.empty:
        return None
    row = row_df.iloc[-1]

    div_raw    = _f(row.get("div_raw"))
    min5d      = _f(row.get("min5d_div"))
    min5d_cnt  = int(row.get("min5d_count", 0)) if not math.isnan(_f(row.get("min5d_count", 0))) else 0
    d_pos_2d   = _f(row.get("d_pos_2d"))
    d_acc_2d   = _f(row.get("d_acc_2d"))
    d_oitok_2d = _f(row.get("d_oitok_2d"))
    pin_streak = _f(row.get("pin_streak"))

    # E1: div_raw(t) − min5d ≥ E1_THAW
    e1 = (not math.isnan(div_raw) and not math.isnan(min5d) and
          (div_raw - min5d) >= E1_THAW)

    # E2: d_pos_2d ≥ E2_D_POS
    e2 = (not math.isnan(d_pos_2d) and d_pos_2d >= E2_D_POS)

    # E3: d_oitok_2d ≤ 0
    e3 = (not math.isnan(d_oitok_2d) and d_oitok_2d <= 0)

    # E4 điểm cộng: pin_streak ≥ E4_PIN_MIN vừa VỠ trong ≤3 ngày
    # Check if max(pin_streak over [t-3..t-1]) ≥ E4_PIN_MIN AND current = 0
    e4 = False
    window_3d = df_sym[df_sym["date"] < target_date].tail(E4_BREAK_WINDOW)
    if not window_3d.empty:
        prev_max = window_3d["pin_streak"].max()
        if not math.isnan(prev_max) and prev_max >= E4_PIN_MIN and pin_streak == 0:
            e4 = True

    # FIRE = E1 AND E2
    if not (e1 and e2):
        return {"fire": False, "e1": e1, "e2": e2, "e3": e3, "e4": e4,
                "div_raw": div_raw, "min5d": min5d, "min5d_count": min5d_cnt,
                "d_pos_2d": d_pos_2d, "d_acc_2d": d_acc_2d,
                "d_oitok_2d": d_oitok_2d, "pin_streak": pin_streak}

    # Cooldown check
    # L-28: exception quyết bằng e3-bool (d_oitok≤0), không tag-name.
    # Proxy tag-name cũ (DENOM→NUM) phụ thuộc thứ-tự-append → MIXED+DENOM nuốt exception.
    # Exception: OI nở (E3=False, d_oitok>0: OI-EXPAND hoặc MIXED) → OI co (E3=True,
    #   d_oitok≤0: cover thật) = đổi cơ chế → refire sớm.
    # Chiều ngược (E3=True→False) và E3=True→True: block bình thường.
    last_fire_date = sym_state.get("last_fire_date")
    if last_fire_date:
        # Derive last_fire_e3: ưu tiên field mới; fallback derive từ last_fire_tag (migration).
        if "last_fire_e3" in sym_state:
            last_fire_e3 = sym_state["last_fire_e3"]
        elif sym_state.get("last_fire_tag"):
            last_fire_e3 = (sym_state["last_fire_tag"] == "NUM-DRIVEN")
        else:
            _log(f"WARN cooldown {target_date} {target_date}: last_fire_date có, thiếu e3+tag → giả định False")
            last_fire_e3 = False
        days_since = (pd.Timestamp(target_date) - pd.Timestamp(last_fire_date)).days
        if days_since < COOLDOWN_DAYS:
            if not (not last_fire_e3 and e3):           # exception: non-E3 → E3 only
                return {"fire": False, "e1": e1, "e2": e2, "e3": e3, "e4": e4,
                        "div_raw": div_raw, "min5d": min5d, "min5d_count": min5d_cnt,
                        "d_pos_2d": d_pos_2d, "d_acc_2d": d_acc_2d,
                        "d_oitok_2d": d_oitok_2d, "pin_streak": pin_streak,
                        "cooldown_blocked": True}

    # Determine tags (non-exclusive per spec §1)
    tags = []
    if e3:                                                        # E3: d_oitok_2d ≤ 0
        tags.append("NUM-DRIVEN")
    elif not math.isnan(d_oitok_2d) and 0 < d_oitok_2d <= OI_EXPAND_THRESH:
        tags.append("MIXED")                                     # (0, +0.10] — OI mở nhẹ
    if not math.isnan(d_acc_2d) and not math.isnan(d_pos_2d) and abs(d_acc_2d) > d_pos_2d:
        tags.append("DENOM-ASSIST")                              # |d_acc_2d| > d_pos_2d
    if not math.isnan(d_oitok_2d) and d_oitok_2d > OI_EXPAND_THRESH:
        tags.append("OI-EXPAND")                                 # long mới, bắt nghi ngờ

    tag_str = " ".join(f"[{t}]" for t in tags) if tags else "[UNTAGGED]"

    # SHORT-BASE flag: min5d_count < 5
    short_base = min5d_cnt < 5

    return {
        "fire": True, "e1": e1, "e2": e2, "e3": e3, "e4": e4,
        "div_raw": div_raw, "min5d": min5d, "min5d_count": min5d_cnt,
        "d_pos_2d": d_pos_2d, "d_acc_2d": d_acc_2d,
        "d_oitok_2d": d_oitok_2d, "pin_streak": pin_streak,
        "tags": tags, "tag_str": tag_str, "short_base": short_base,
    }


# ── T1-STORE ──────────────────────────────────────────────────────────────────

def _fetch_1h_bar(ep_url: str, symbol: str, midnight_ms: int, field: str) -> Optional[float]:
    """Fetch single 1h bar at 00:00 UTC (midnight_ms) from Binance endpoint.

    L-24: startTime+endTime bracket midnight_ms exactly.
    L-25: KHÔNG nguồn mới — cùng 4 endpoint canonical, period=1h.
    L-21: CẤM Coinglass.
    v2: bar 00:00-MỞ ngày EVAL = midnight_ms(EVAL).
    """
    try:
        params = {
            "symbol":    symbol,
            "period":    "1h",
            "startTime": midnight_ms,
            "endTime":   midnight_ms + 3_600_000,  # +1h window
            "limit":     1,
        }
        r = requests.get(ep_url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data:
            ts_ms = data[0].get("timestamp", data[0].get("time"))
            if ts_ms and int(ts_ms) == midnight_ms:
                return _f(data[0].get(field))
            # Bar ts mismatch — bar absent at exact mốc (L-24 guard)
            return None
        return None
    except Exception:
        return None


def _fetch_oi_1h(symbol: str, midnight_ms: int) -> Optional[float]:
    """Fetch openInterestHist 1h bar at midnight_ms. L-21/L-24/L-25."""
    try:
        params = {
            "symbol":       symbol,
            "period":       "1h",
            "contractType": "PERPETUAL",
            "startTime":    midnight_ms,
            "endTime":      midnight_ms + 3_600_000,
            "limit":        1,
        }
        r = requests.get(_EP_OIH, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data:
            ts_ms = data[0].get("timestamp", data[0].get("time"))
            if ts_ms and int(ts_ms) == midnight_ms:
                return _f(data[0].get("sumOpenInterest"))
        return None
    except Exception:
        return None


def capture_t1_store(capture_symbols: list[str], eval_date: date,
                     daily_df: pd.DataFrame, backfill_src: str = "t1_capture"):
    """Capture bar 00:00 UTC of eval_date for each symbol → gom_e_ref_store.csv.

    T1-STORE spec §5:
      T1 chạy 01:25 UTC D_run; EVAL = D_run − 1 (ngày đã đóng gần nhất — L-41).
      Capture bar 00:00 UTC ngày EVAL:
        v2: "snapshot tại 00:00 UTC của ngày D = midnight_ms(D)"
        (ratio_daily_canonical_20260731_v2.md)
      Capture set: registry ∪ vừa-ra-≤3d.
      Store: gom_e_ref_store.csv, append-only, 9 schema columns.
      pos_raw_1h ⟂ pos_canonical (hai cột độc lập — L-21/Note-2).
    Quan hệ ngày: forming=D_run · EVAL=D_run−1 · T2_ref=store[D_run−2]=EVAL−1.

    L-21: CẤM Coinglass. L-24: bar 00:00-MỞ = midnight_ms(EVAL). L-25: 4 endpoint.
    """
    eval_str   = eval_date.strftime("%Y-%m-%d")
    m_ms       = _midnight_ms(eval_date)

    # pos_canonical, acc_canonical, oi_canonical = daily values already in freshwatch CSV
    eval_daily = daily_df[daily_df["date"] == eval_str] if not daily_df.empty else pd.DataFrame()

    REF_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not REF_STORE_PATH.exists()

    cols = ["date", "symbol",
            "pos_raw_1h", "acc_raw_1h", "oi_raw_1h",
            "pos_canonical", "acc_canonical", "oi_canonical",
            "backfill_src"]

    rows = []
    for sym in capture_symbols:
        # Fetch 1h bars at midnight_ms(EVAL) — L-24: exact bracket
        pos_raw = _fetch_1h_bar(_EP_POS,  sym, m_ms, "longShortRatio")
        acc_raw = _fetch_1h_bar(_EP_ACC,  sym, m_ms, "longShortRatio")
        oi_raw  = _fetch_oi_1h(sym, m_ms)

        # pos_canonical / acc_canonical: from T1 canonical pipeline daily value
        # v2: same 00:00 UTC boundary, different source (daily store)
        canon_row = eval_daily[eval_daily["symbol"] == sym] if not eval_daily.empty else pd.DataFrame()
        if not canon_row.empty:
            pos_can  = _f(canon_row.iloc[0].get("lsr_pos_r"))
            acc_can  = _f(canon_row.iloc[0].get("lsr_acc_r"))
            px       = _f(canon_row.iloc[0].get("px_avg"))
            oi_usd_v = _f(canon_row.iloc[0].get("oi_usd"))
            oi_can   = oi_usd_v / px if px and not math.isnan(px) and px != 0 else float("nan")
        else:
            pos_can = acc_can = oi_can = float("nan")

        rows.append({
            "date": eval_str, "symbol": sym,
            "pos_raw_1h": "" if pos_raw is None else round(pos_raw, 6),
            "acc_raw_1h": "" if acc_raw is None else round(acc_raw, 6),
            "oi_raw_1h":  "" if oi_raw  is None else round(oi_raw, 2),
            "pos_canonical": "" if math.isnan(pos_can) else round(pos_can, 6),
            "acc_canonical": "" if math.isnan(acc_can) else round(acc_can, 6),
            "oi_canonical":  "" if math.isnan(oi_can)  else round(oi_can, 2),
            "backfill_src": backfill_src,
        })

    with open(REF_STORE_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ── Alert log ─────────────────────────────────────────────────────────────────

def _append_alert_log(target_date: str, symbol: str, fire_result: dict,
                      days_in_mode: int):
    ALERT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cols = ["ts_utc", "date", "symbol", "fire", "e1", "e2", "e3", "e4",
            "div_raw", "min5d", "min5d_count", "d_pos_2d", "d_acc_2d",
            "d_oitok_2d", "pin_streak", "tags", "days_in_mode",
            "cooldown_blocked", "short_base"]
    write_hdr = not ALERT_LOG_PATH.exists()
    row = {
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": target_date, "symbol": symbol,
        "fire": fire_result.get("fire", False),
        "e1": fire_result.get("e1", ""), "e2": fire_result.get("e2", ""),
        "e3": fire_result.get("e3", ""), "e4": fire_result.get("e4", ""),
        "div_raw": fire_result.get("div_raw", ""),
        "min5d":   fire_result.get("min5d", ""),
        "min5d_count": fire_result.get("min5d_count", ""),
        "d_pos_2d":   fire_result.get("d_pos_2d", ""),
        "d_acc_2d":   fire_result.get("d_acc_2d", ""),
        "d_oitok_2d": fire_result.get("d_oitok_2d", ""),
        "pin_streak":  fire_result.get("pin_streak", ""),
        "tags": fire_result.get("tag_str", ""),
        "days_in_mode": days_in_mode,
        "cooldown_blocked": fire_result.get("cooldown_blocked", False),
        "short_base": fire_result.get("short_base", False),
    }
    with open(ALERT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if write_hdr:
            w.writeheader()
        w.writerow(row)


# ── Main daily run ────────────────────────────────────────────────────────────

def run_daily(target_date: str, store_dir: Path,
              do_t1_store: bool = True, fw_filter: Optional[Path] = None,
              dry_run: bool = False):
    """Main T1 daily function.

    target_date = YYYY-MM-DD (= EVAL date, ngày đã đóng = D_run − 1, L-41).
    store_dir   = data/export/ with freshwatch_daily_YYYY-MM.csv files.
    do_t1_store = True in production (False in backtest to skip live API calls).
    fw_filter   = optional path to freshwatch_symbols.txt (filter universe).
    dry_run     = True → skip ALL writes (state + T1-STORE + log). Read-only.

    Returns (table_a_lines, table_b_lines) for Telegram/stdout.
    """
    _log(f"run_daily start date={target_date}")

    df_all = load_fw_csvs(store_dir, target_date, lookback_days=60)
    if df_all.empty:
        _log("ERROR: no data loaded")
        return ["[GOM-E] No data"], []

    symbols = sorted(df_all["symbol"].unique())

    # Filter to freshwatch universe if filter file provided
    if fw_filter and fw_filter.exists():
        with open(fw_filter, encoding="utf-8") as f:
            fw_syms = {ln.strip() for ln in f if ln.strip()}
        symbols = [s for s in symbols if s in fw_syms]

    state = _load_state()

    registry_rows  = []  # Bảng A
    alert_rows     = []  # Bảng B
    capture_set    = []  # T1-STORE capture set: registry ∪ vừa-ra-≤3d

    for sym in symbols:
        df_sym = df_all[df_all["symbol"] == sym].copy()
        if df_sym.empty or df_sym["date"].max() < target_date:
            continue

        df_sym = compute_metrics(df_sym)

        sym_state = state.get(sym, {})

        # Update registry (H1/H2/H3)
        sym_state = eval_hedge_farm(df_sym, target_date, sym_state)
        state[sym] = sym_state

        in_reg     = sym_state.get("in_registry", False)
        entry_date = sym_state.get("entry_date", "")
        days_in    = sym_state.get("days_in", 0)

        # Bảng A: all current registry members
        if in_reg:
            last_row = df_sym[df_sym["date"] == target_date]
            if not last_row.empty:
                r = last_row.iloc[-1]
                new_flag = (entry_date == target_date)
                registry_rows.append({
                    "symbol": sym,
                    "days_in_mode": days_in,
                    "div_avg3": round(_f(r.get("div_avg3")), 3),
                    "gLSR": round(_f(r.get("gLSR")), 3),
                    "f_avg": round(_f(r.get("f_avg")), 6),
                    "new": new_flag,
                })
            capture_set.append(sym)

        # vừa-ra ≤3d also enters capture_set (not in registry but recent exit)
        elif _in_candidate_set(sym_state, target_date):
            capture_set.append(sym)

        # Mode-switch evaluation for candidate set
        if _in_candidate_set(sym_state, target_date):
            fire_res = eval_mode_switch(df_sym, target_date, sym_state)
            if fire_res is None:
                continue

            # Log to alert CSV
            _append_alert_log(target_date, sym, fire_res, days_in)

            if fire_res.get("fire"):
                # Update state with last fire info
                state[sym]["last_fire_date"]  = target_date
                state[sym]["last_fire_e3"]    = fire_res["e3"]          # L-28: e3-bool, không tags[0]
                state[sym]["last_fire_tag"]   = fire_res.get("tags", [""])[0] if fire_res.get("tags") else ""  # audit only
                state[sym]["last_fire_days_in_mode"] = days_in

                alert_rows.append({
                    "symbol": sym,
                    "e1_val": round(fire_res["div_raw"] - fire_res["min5d"], 3),
                    "e2_val": round(fire_res["d_pos_2d"], 3),
                    "e3": fire_res["e3"],
                    "e4": fire_res["e4"],
                    "d_oitok_2d": round(fire_res["d_oitok_2d"], 3),
                    "tag_str": fire_res["tag_str"],
                    "days_in_mode": days_in,
                    "short_base": fire_res["short_base"],
                })

    if not dry_run:
        _save_state(state)
        _log(f"state saved symbols={len(state)}")

    # T1-STORE (production only — skip in backtest or dry-run)
    if do_t1_store and capture_set and not dry_run:
        eval_d = datetime.strptime(target_date, "%Y-%m-%d").date()
        n_stored = capture_t1_store(capture_set, eval_d, df_all)
        _log(f"t1_store captured={n_stored} eval={target_date}")

    # Format output
    table_a = _format_table_a(registry_rows, target_date)
    table_b = _format_table_b(alert_rows, target_date)

    n_cand = len(capture_set)
    n_reg  = sum(1 for s in state.values() if s.get("in_registry"))
    summary = (f"[GOM-E T1] {target_date} | scanned={len(symbols)} "
               f"registry={n_reg} candidates={n_cand} alerts={len(alert_rows)}")
    print(summary)
    # AG2/21-09 · Bảng B TRƯỚC Bảng A · alerts ưu tiên hiển thị · slice không cắt B.
    if alert_rows:
        print("\n".join(table_b))
    print("\n".join(table_a))

    return table_a, table_b


def _format_table_a(rows: list, target_date: str) -> list[str]:
    lines = [f"— BẢNG A HEDGE-FARM REGISTRY {target_date} ({len(rows)} tokens) —"]
    for r in sorted(rows, key=lambda x: x["days_in_mode"], reverse=True):
        new_tag = " [NEW]" if r["new"] else ""
        lines.append(
            f"  {r['symbol']}{new_tag} | {r['days_in_mode']}d | "
            f"div_avg3={r['div_avg3']} | gLSR={r['gLSR']} | f_avg={r['f_avg']:.5f}"
        )
    return lines


def _format_table_b(rows: list, target_date: str) -> list[str]:
    lines = [f"— BẢNG B MODE-SWITCH ALERTS {target_date} ({len(rows)} fires) —"]
    for r in sorted(rows, key=lambda x: x["days_in_mode"], reverse=True):
        sb = " [SHORT-BASE]" if r["short_base"] else ""
        lines.append(
            f"  {r['symbol']}{sb} | {r['tag_str']} | E1={r['e1_val']:+.3f} "
            f"E2={r['e2_val']:+.3f} OI={r['d_oitok_2d']:+.3f} "
            f"E3={'✓' if r['e3'] else '✗'} E4={'✓' if r['e4'] else '✗'} "
            f"| {r['days_in_mode']}d in mode"
        )
    return lines


# ── Backtest mode (for gate testing) ─────────────────────────────────────────

def run_backtest(symbols: list[str], store_dir: Path, date_from: str, date_to: str):
    """Run T1 evaluation for given symbols over historical date range.

    GATE RE-RUN: does NOT write state or T1-STORE (read-only on historical data).
    Used for: ⛔ COMMIT GATE — ON 17–18/07 positive #1.
    """
    print(f"=== GOM-E BACKTEST {date_from}→{date_to} symbols={symbols} ===")
    df_all = load_fw_csvs(store_dir, date_to, lookback_days=90)
    if df_all.empty:
        print("ERROR: no data loaded"); return

    # Filter to requested symbols and date range
    df_all = df_all[df_all["symbol"].isin(symbols)].copy()

    # Date sequence
    d_cur = datetime.strptime(date_from, "%Y-%m-%d").date()
    d_end = datetime.strptime(date_to, "%Y-%m-%d").date()
    dates = []
    while d_cur <= d_end:
        dates.append(d_cur.strftime("%Y-%m-%d"))
        d_cur += timedelta(days=1)

    for sym in symbols:
        df_sym_full = df_all[df_all["symbol"] == sym].copy()
        if df_sym_full.empty:
            print(f"  {sym}: no data in store"); continue

        df_sym_full = compute_metrics(df_sym_full)

        print(f"\n=== {sym} ===")
        print(f"  data range: {df_sym_full['date'].min()} → {df_sym_full['date'].max()}")
        print(f"  rows: {len(df_sym_full)}")
        print()

        # Print header
        print(f"  {'date':12s} | {'in_reg':6s} | {'div_r':6s} | {'div_a3':7s} | "
              f"{'min5d':6s} | {'E1_d':7s} | {'d_pos2d':8s} | {'d_oi2d':8s} | "
              f"{'pin_s':6s} | E1 E2 E3 E4 | tag")

        bt_state = {}

        for t_date in dates:
            df_up_to = df_sym_full[df_sym_full["date"] <= t_date]
            if df_up_to.empty or df_up_to["date"].max() < t_date:
                continue

            # Registry evaluation (stateful)
            bt_state = eval_hedge_farm(df_sym_full[df_sym_full["date"] <= t_date], t_date, bt_state)

            in_reg = bt_state.get("in_registry", False)
            days_in = bt_state.get("days_in", 0)

            row_df = df_sym_full[df_sym_full["date"] == t_date]
            if row_df.empty:
                continue
            row = row_df.iloc[-1]

            div_raw    = _f(row.get("div_raw"))
            div_avg3   = _f(row.get("div_avg3"))
            min5d      = _f(row.get("min5d_div"))
            d_pos_2d   = _f(row.get("d_pos_2d"))
            d_oitok_2d = _f(row.get("d_oitok_2d"))
            pin_streak = _f(row.get("pin_streak"))
            e1_delta   = (div_raw - min5d) if not (math.isnan(div_raw) or math.isnan(min5d)) else float("nan")

            # Check fire
            candidate = in_reg or _in_candidate_set(bt_state, t_date)
            fire_res = eval_mode_switch(df_sym_full[df_sym_full["date"] <= t_date], t_date, bt_state) if candidate else None

            e1 = fire_res.get("e1", False) if fire_res else False
            e2 = fire_res.get("e2", False) if fire_res else False
            e3 = fire_res.get("e3", False) if fire_res else False
            e4 = fire_res.get("e4", False) if fire_res else False
            fire = fire_res.get("fire", False) if fire_res else False
            tag_str = fire_res.get("tag_str", "") if fire_res else ""

            if fire and fire_res:
                bt_state["last_fire_date"] = t_date
                bt_state["last_fire_e3"]   = fire_res["e3"]             # L-28: e3-bool, không tags[0]
                bt_state["last_fire_tag"]  = fire_res.get("tags", [""])[0] if fire_res.get("tags") else ""  # audit only

            # Mark expected fire window
            marker = " *** FIRE ***" if fire else ""
            flag   = " ◀ GATE CHECK" if t_date in ("2026-07-17", "2026-07-18") else ""

            print(f"  {t_date} | {'Y':6s}" if in_reg else f"  {t_date} | {'N':6s}", end="")
            print(f" | {div_raw:6.3f} | {div_avg3:7.3f} | "
                  f"{min5d:6.3f} | {e1_delta:+7.3f} | {d_pos_2d:+8.3f} | {d_oitok_2d:+8.3f} | "
                  f"{pin_streak:6.0f} | {'✓' if e1 else '✗'} {'✓' if e2 else '✗'} "
                  f"{'✓' if e3 else '✗'} {'✓' if e4 else '✗'} | "
                  f"{tag_str}{marker}{flag}")


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="GOM-E mode-switch detector T1")
    ap.add_argument("--daily",     action="store_true", help="Run daily (production)")
    ap.add_argument("--backtest",  nargs="+",           help="Backtest symbols: SYM [SYM...]")
    ap.add_argument("--store",     default=str(REPO_ROOT / "data" / "export"),
                    help="Path to freshwatch_daily CSV directory")
    ap.add_argument("--date",      default=None,
                    help="Target date YYYY-MM-DD (default: yesterday)")
    ap.add_argument("--date-from", default="2026-07-01",
                    help="Backtest from date (default: 2026-07-01)")
    ap.add_argument("--date-to",   default=None,
                    help="Backtest to date (default: --date)")
    ap.add_argument("--fw-filter", default=None,
                    help="Path to freshwatch_symbols.txt for universe filter")
    ap.add_argument("--no-store",  action="store_true",
                    help="Skip T1-STORE API fetch (backtest/debug mode)")
    ap.add_argument("--dry-run",   action="store_true",
                    help="Read-only: skip ALL writes (state.json + T1-STORE + log). Safe for Q1 registry check.")
    args = ap.parse_args()

    store_dir = Path(args.store)
    fw_filter = Path(args.fw_filter) if args.fw_filter else None

    if args.daily:
        if args.date:
            target_date = args.date
        else:
            # L-41: D_run-1 = yesterday (ngày đã đóng gần nhất)
            target_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
        run_daily(target_date, store_dir,
                  do_t1_store=not args.no_store and not args.dry_run,
                  fw_filter=fw_filter,
                  dry_run=args.dry_run)

    elif args.backtest:
        target_date = args.date or (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
        date_from   = args.date_from
        date_to     = args.date_to or target_date
        run_backtest(args.backtest, store_dir, date_from, date_to)

    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
