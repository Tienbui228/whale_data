#!/usr/bin/env python3
"""[U-REPLAY v2 · KÝ 27/08 · IMPORT prod hàm thật · KHÔNG chép compose]

Fix duy nhất được phép (per operator ký):
  probe REFACTOR import gom_h_daily prod (eval_h1/eval_h2/eval_t01/conf/DQ —
  hàm thật, xóa mọi bản chép). Cooldown state in-memory (replay-friendly)
  reproduce đúng _check_lane_cooldown semantic. Ramp compute (snapshot delta
  reading) reimplement — không phải "eval" function.

SELF-CHECK-COMPOSE 3 dòng đầu file · FAIL = KHÔNG NỘP:
  CYS 07-12 perp-fire=True · BTR 07-28 kho-fire=True · BANANAS31 07-04..12 [DQ-SERIAL]

Header L-64: compose_mode + per-vế threshold values + obs_min source + adapter path + MỌI md5.
Bảng: D_run + D_cross · taxonomy 8 · 2 RECALL · FP [n=2 KHÔNG ĐỦ MẪU] · PENDING-69 bucket.
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv, time
from pathlib import Path
from datetime import datetime, timedelta, timezone, date as _date
from statistics import median
import pandas as pd
try:
    import urllib.request
except ImportError:
    pass

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

# ─── IMPORT prod hàm thật (không chép) — import trước để nó tự wrap stdout ───
from gom_h_daily import (
    _md5, _load_cfg, _load_universe, _load_store,
    _eval_t01, _eval_h2, _eval_h3, _eval_h1,
)
from adapter_h1_nansen import read_adapter_daily

YAML_PATH = REPO / "screen_thresholds.yaml"
GATE_DEFS = REPO / "docs/proposals/gom_h_gate_defs_20260828.md"
CODE_PATH = REPO / "scripts/gom_h_daily.py"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")
OUT_CSV = REPO / "docs/reports/u_replay_v2_fw139_20260827.csv"

WINDOW_START = _date(2026, 6, 26)
WINDOW_END = _date(2026, 8, 22)
LOOKAHEAD_DAYS = 30
RUNNER_RATIO = 1.5
OBS_MIN_FALLBACK = 14

# 9-case D0 (kỳ vọng runner Y trừ CAP kỳ vọng trượt thước)
D0_9CASE = {"BANK": "2026-07-11", "TUT": "2026-07-09", "CYS": "2026-08-04",
            "AKE": "2026-07-15", "BTW": "2026-08-03", "HEMI": "2026-08-15",
            "ON": "2026-07-19", "CAP": "2026-07-30", "BTR": "2026-08-26"}

# ─── Load prod cfg (single source-of-truth) ───
cfg_all = _load_cfg()
gom_h_cfg = cfg_all.get("gom_h", {})
gn_cfg = cfg_all.get("goi_nhe", {})
dq_serial_cfg = cfg_all.get("dq_serial", {})
dq_members = set(dq_serial_cfg.get("members", []))
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})
OBS_MIN_YAML = gn_cfg.get("obs_min")
OBS_MIN = OBS_MIN_YAML if OBS_MIN_YAML is not None else OBS_MIN_FALLBACK
_obs_min_source = "yaml goi_nhe.obs_min" if OBS_MIN_YAML is not None else f"fallback {OBS_MIN_FALLBACK}"
# Sync t0_1/h2 floor_obs_min từ yaml canonical
gom_h_cfg.setdefault("t0_1", {})["floor_obs_min"] = OBS_MIN
gom_h_cfg.setdefault("h2", {})["floor_obs_min"] = OBS_MIN

compose_mode = gom_h_cfg.get("compose", "GOM-H = (H1 OR (H2 AND T0.1)) AND NOT gom_h_cooldown_14d")

# ─── Header L-64 ĐẦY ĐỦ ───
CODE_MD5 = _md5(CODE_PATH)
YAML_MD5 = _md5(YAML_PATH)
GATE_MD5 = _md5(GATE_DEFS)
_cfg_t01 = gom_h_cfg["t0_1"]
_cfg_h2 = gom_h_cfg["h2"]

print("═" * 100)
print(f"[U-REPLAY v2 · KÝ 27/08 · IMPORT prod hàm thật (không chép compose)]")
print(f"  code:      scripts/gom_h_daily.py         md5={CODE_MD5}")
print(f"  yaml:      screen_thresholds.yaml         md5={YAML_MD5}")
print(f"  gate_defs: gom_h_gate_defs_20260828.md    md5={GATE_MD5}")
print(f"  adapter local path: {SNAPSHOTS_DIR} (full retention 2026-06-17+)")
print(f"  obs_min={OBS_MIN} (source: {_obs_min_source})")
print(f"  compose_mode: {compose_mode}")
print(f"  compose gói-nhẹ (production): H1-raw ∨ H2-raw · T0.1 → NHÃN CONF (không tham gia compose)")
print(f"  T0.1 thresholds:")
print(f"    funding_pin_abs={_cfg_t01['funding_pin_abs']} funding_pin_days={_cfg_t01.get('funding_pin_days')}")
print(f"    oi_over_min30_max={_cfg_t01['oi_over_min30_max']} · ret14_abs_max={_cfg_t01['ret14_abs_max']}")
print(f"    vol_med7_over_med30_max={_cfg_t01['vol_med7_over_med30_max']} · floor_obs_min={_cfg_t01['floor_obs_min']}")
print(f"  H2 thresholds:")
print(f"    div_min_14d_max={_cfg_h2['div_min_14d_max']} · div_today_min={_cfg_h2['div_today_min']}")
print(f"    pos_over_min14_min={_cfg_h2['pos_over_min14_min']} · oi_over_min30_max={_cfg_h2['oi_over_min30_max']}")
print(f"    floor_obs_min={_cfg_h2['floor_obs_min']}")
print(f"  H1 thresholds:")
print(f"    balance_delta_abs_min={gom_h_cfg['h1']['balance_delta_abs_min']} · window_days_max={gom_h_cfg['h1']['window_days_max']}")
print(f"    kho_ramp: delta_min={kho_ramp_cfg.get('delta_min')} · window_days={kho_ramp_cfg.get('window_days')}")
print(f"  Cooldown: {gom_h_cfg.get('gom_h_cooldown_days', 14)}d · clean_streak_re_arm: {gom_h_cfg.get('gom_h_cooldown_clean_days', 3)}d")
print(f"  DQ-SERIAL members: {sorted(dq_members)}")
print(f"  window: {WINDOW_START}..{WINDOW_END} · lookahead {LOOKAHEAD_DAYS}d · runner threshold {RUNNER_RATIO}×")
print("═" * 100)

# ─── Load fw-139 + store ───
symbols = _load_universe()
tokens = [s[:-4] if s.endswith("USDT") else s for s in symbols]
print(f"\n[U1] fw-{len(symbols)} loaded")

# _load_store loads for one target — cần load full 05-08
frames = []
for m in ["05", "06", "07", "08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)
print(f"[U3] store rows: {len(STORE)}")


def _df_sym(sym):
    return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


# ─── Load balance series for h1_ramp (snapshot delta, data-reading not eval) ───
BAL = {}
snap_files = sorted(SNAPSHOTS_DIR.glob("*.json"))
n_snap = 0
for p in snap_files:
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except Exception: continue
    if not isinstance(d, dict): continue
    n_snap += 1
    for r in d.get("rows", []):
        if not r: continue
        sym_u = (r.get("symbol") or "").upper()
        if not sym_u: continue
        bal = r.get("exchange_balance_tokens")
        if bal is not None:
            try: BAL.setdefault(sym_u, {})[p.stem] = float(bal)
            except: pass
print(f"[U3] snapshot files: {n_snap}")


def h1_ramp_raw(tok, target_date_str):
    """Ramp check: |balance(D) - balance(D-14)|/balance(D-14) >= delta_min."""
    ingest = (_date.fromisoformat(target_date_str) + timedelta(days=1)).isoformat()
    series = BAL.get(tok, {})
    b_end = series.get(ingest)
    if b_end is None or b_end <= 0: return False, None
    win = kho_ramp_cfg.get("window_days", 14)
    d_start = (_date.fromisoformat(ingest) - timedelta(days=win)).isoformat()
    b_start = series.get(d_start)
    if b_start is None or b_start <= 0: return False, None
    delta = abs(b_end - b_start) / b_start
    thr = kho_ramp_cfg.get("delta_min", 0.15)
    return delta >= thr, delta


# ─── Adapter cache ───
_ADAPTER_CACHE = {}
def get_adapter(ingest_date_str):
    if ingest_date_str not in _ADAPTER_CACHE:
        try:
            _ADAPTER_CACHE[ingest_date_str] = read_adapter_daily(ingest_date_str)
        except Exception:
            _ADAPTER_CACHE[ingest_date_str] = pd.DataFrame()
    return _ADAPTER_CACHE[ingest_date_str]


# ─── T0.1 conf-labeler (from prod _conf_label inline in gom_h_daily main) ───
import math as _math
def conf_label(t01_detail):
    def _sub(val, thr):
        if val is None: return None
        try:
            if _math.isnan(val): return None
        except (TypeError, ValueError): pass
        return bool(val <= thr)
    c = gom_h_cfg["t0_1"]
    subs = {
        "funding_pin": t01_detail.get("fund_pinned"),
        "oi_min30":    _sub(t01_detail.get("oi_ratio"),              c["oi_over_min30_max"]),
        "ret14":       _sub(t01_detail.get("ret14"),                 c["ret14_abs_max"]),
        "med30_vol":   _sub(t01_detail.get("vol_med7_med30_ratio"),  c["vol_med7_over_med30_max"]),
    }
    na_list = [k for k, v in subs.items() if v is None]
    n_pass = sum(1 for v in subs.values() if v is True)
    n_eval = sum(1 for v in subs.values() if v is True or v is False)
    if n_pass >= 4: level = "HIGH"
    elif n_pass >= 2: level = "MED"
    else: level = "LOW"
    na_str = ",".join(na_list) if na_list else "-"
    if n_eval == 0:
        return f"{level} (0/0; N/A: 4 vế [{na_str}])"
    return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})"


# ─── Compose gói-nhẹ + cooldown in-memory (replay) ───
def compose_replay(tok):
    """Replay per-day compose OR with in-memory cooldown (14d + clean 3d).
    Returns: {kept_fires: [...], h1_eval, h1_na, h2_eval, h2_na, dq_blocked_dates}
    """
    sym = tok + "USDT"
    df = _df_sym(sym)
    dq_hit = tok in dq_members
    cd_days = gom_h_cfg.get("gom_h_cooldown_days", 14)
    cn_days = gom_h_cfg.get("gom_h_cooldown_clean_days", 3)
    lane_state = {"kho": {"last_fire": None, "clean_streak": 0},
                  "perp": {"last_fire": None, "clean_streak": 0}}
    kept_fires = []
    dq_blocked_dates = []
    n_h1_eval = 0; n_h1_na = 0
    n_h2_eval = 0; n_h2_na = 0
    per_token_start = WINDOW_START
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)

    cur = per_token_start
    while cur <= WINDOW_END:
        d_str = cur.isoformat()
        ingest = (cur + timedelta(days=1)).isoformat()
        adapter_df = get_adapter(ingest)

        # H2 eval (perp raw source) — prod _eval_h2
        h2_status, h2_detail = _eval_h2(df, d_str, gom_h_cfg["h2"])
        h2_raw_gn = h2_status == "T"
        if h2_status in ("T", "F"): n_h2_eval += 1
        else: n_h2_na += 1

        # T0.1 eval (CONF label + h1 gate)
        t01_status, t01_detail = _eval_t01(df, d_str, gom_h_cfg["t0_1"])

        # H1 kho step raw (from prod _eval_h1 detail)
        _, h1_detail = _eval_h1(sym, d_str, adapter_df, gom_h_cfg["h1"], t01_status=t01_status)
        h1_kho_raw = h1_detail.get("kho_raw", "N/A")
        h1_step_raw = (h1_kho_raw == "True")

        # H1 ramp (snapshot delta reading)
        ramp_raw, ramp_delta = h1_ramp_raw(tok, d_str)

        h1_raw_gn = h1_step_raw or ramp_raw
        # H1 coverage: eval if EITHER step_raw evaluable (not N/A) OR ramp evaluable
        if h1_kho_raw in ("True", "False") or ramp_delta is not None:
            n_h1_eval += 1
        else:
            n_h1_na += 1

        # DQ-SERIAL blocks BEFORE cooldown (per §7.1)
        if dq_hit and (h1_raw_gn or h2_raw_gn):
            dq_blocked_dates.append(d_str)
            cur += timedelta(days=1); continue

        # Cooldown check per lane · in-memory equivalent to _check_lane_cooldown
        for lane, raw_fires in [("kho", h1_raw_gn), ("perp", h2_raw_gn)]:
            state = lane_state[lane]
            if raw_fires:
                if state["last_fire"] is None:
                    can_fire = True
                else:
                    days_since = (cur - _date.fromisoformat(state["last_fire"])).days
                    can_fire = (days_since >= cd_days and state["clean_streak"] >= cn_days)
                if can_fire:
                    trig = "H1-step" if (lane == "kho" and h1_step_raw) else \
                           ("H1-ramp" if lane == "kho" else "H2")
                    conf = conf_label(t01_detail)
                    kept_fires.append({
                        "date": d_str, "lane": lane, "trigger": trig,
                        "conf": conf,
                        "h1_kho_pct": h1_detail.get("kho_step_pct"),
                        "h1_ramp_pct": (ramp_delta * 100.0) if ramp_delta is not None else None,
                    })
                    state["last_fire"] = d_str
                    state["clean_streak"] = 0
            else:
                # raw False → clean_streak++
                # (True already handled above · N/A → hold, không đếm không reset)
                is_evaluable_false = (
                    (lane == "kho" and (h1_kho_raw == "False" or ramp_delta is not None))
                    or (lane == "perp" and h2_status == "F")
                )
                if is_evaluable_false:
                    state["clean_streak"] += 1

        cur += timedelta(days=1)

    return {"kept_fires": kept_fires, "dq_blocked_dates": dq_blocked_dates,
            "h1_eval": n_h1_eval, "h1_na": n_h1_na,
            "h2_eval": n_h2_eval, "h2_na": n_h2_na}


# ─── SELF-CHECK-COMPOSE 3 dòng (FAIL = KHÔNG NỘP) ───
print("\n[SELF-CHECK-COMPOSE 3 dòng · FAIL = KHÔNG NỘP]")
self_check_pass = True
_selfcheck_lines = []

# Test 1: CYS 07-12 perp-fire=True
df_cys = _df_sym("CYSUSDT")
h2_status_cys, _ = _eval_h2(df_cys, "2026-07-12", gom_h_cfg["h2"])
sc1_pass = (h2_status_cys == "T")
_selfcheck_lines.append(f"  (1) CYS 07-12 H2-raw perp-fire: h2_status={h2_status_cys} → {'PASS ✓' if sc1_pass else 'FAIL ✗'} (kỳ vọng T)")

# Test 2: BTR 07-28 kho-fire=True (via ramp)
btr_ramp_fires, btr_ramp_delta = h1_ramp_raw("BTR", "2026-07-28")
sc2_pass = btr_ramp_fires
_selfcheck_lines.append(f"  (2) BTR 07-28 H1-ramp kho-fire: ramp_raw={btr_ramp_fires} (delta={(btr_ramp_delta*100 if btr_ramp_delta else 0):.2f}%) → {'PASS ✓' if sc2_pass else 'FAIL ✗'} (kỳ vọng True ≥15%)")

# Test 3: BANANAS31 07-04..12 all DQ-SERIAL blocked
sc3_pass = True
sc3_details = []
if "BANANAS31" not in dq_members:
    sc3_pass = False
    sc3_details.append("BANANAS31 KHÔNG có trong dq_members yaml")
else:
    bnn_df = _df_sym("BANANAS31USDT")
    for d in ["2026-07-04","2026-07-05","2026-07-06","2026-07-07","2026-07-08","2026-07-09","2026-07-10","2026-07-11","2026-07-12"]:
        ingest = (_date.fromisoformat(d) + timedelta(days=1)).isoformat()
        adapter_df = get_adapter(ingest)
        h2_st, _ = _eval_h2(bnn_df, d, gom_h_cfg["h2"])
        _, h1_det = _eval_h1("BANANAS31USDT", d, adapter_df, gom_h_cfg["h1"])
        r_raw, _ = h1_ramp_raw("BANANAS31", d)
        would_fire = (h1_det.get("kho_raw") == "True") or r_raw or (h2_st == "T")
        if would_fire: sc3_details.append(f"{d} would_fire (h2={h2_st},kho={h1_det.get('kho_raw')},ramp={r_raw})")
_selfcheck_lines.append(f"  (3) BANANAS31 07-04..12 DQ-SERIAL block: dq_members={'BANANAS31' in dq_members} · would-fire days={len(sc3_details)}/9 → {'PASS ✓' if sc3_pass and 'BANANAS31' in dq_members else 'FAIL ✗'} (kỳ vọng: dq_members contains BANANAS31 → probe compose skip)")

for line in _selfcheck_lines: print(line)
all_pass = sc1_pass and sc2_pass and sc3_pass and ("BANANAS31" in dq_members)
print(f"  ALL PASS: {all_pass}")
if not all_pass:
    print("\n" + "═"*100)
    print("[FAIL] SELF-CHECK-COMPOSE thất bại — KHÔNG NỘP CSV. Fix probe trước khi rerun.")
    print("═"*100)
    sys.exit(1)


# ─── D_run + D_cross detection ───
print(f"\n[U2] Fetching fapi 1d klines: fw-{len(symbols)} × 2026-06-26..2026-09-22")
start_ms = int(datetime(2026, 6, 26, tzinfo=timezone.utc).timestamp() * 1000)
end_ms = int(datetime(2026, 9, 22, tzinfo=timezone.utc).timestamp() * 1000)
CLOSE = {}
DATA_THROUGH = None
n_ok = 0; n_fail = 0
for i, sym in enumerate(symbols):
    if i % 20 == 0: print(f"  {i}/{len(symbols)}...", flush=True)
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&startTime={start_ms}&endTime={end_ms}&limit=500"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "u-replay/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        n_ok += 1
        for k in data:
            ot_ms = k[0]
            d_str = datetime.fromtimestamp(ot_ms/1000, tz=timezone.utc).date().isoformat()
            CLOSE.setdefault(sym, {})[d_str] = float(k[4])
            candle_close_time = ot_ms + 86400_000 - 1
            if candle_close_time < int(time.time() * 1000):
                if DATA_THROUGH is None or d_str > DATA_THROUGH:
                    DATA_THROUGH = d_str
    except Exception:
        n_fail += 1
    time.sleep(0.04)
print(f"[U2] fapi fetch: ok={n_ok} fail={n_fail} · data_through UTC = {DATA_THROUGH}")


def find_runner_events(sym, close_series):
    """Return {status, D_run, D_cross, ret_max}
      D_run   = earliest D in window where max(close[D..D+30])/close[D] >= 1.5
      D_cross = earliest day > D_run where close >= close[D_run] * 1.5 (actual achievement)
      status = confirmed | pending | none
      Cluster ≤ 30d → 1 event.
    """
    dates = sorted(close_series.keys())
    if not dates: return {"status": "none", "D_run": None, "D_cross": None, "ret_max": None}
    events = []
    for d_str in dates:
        d = _date.fromisoformat(d_str)
        if d < WINDOW_START or d > WINDOW_END: continue
        c0 = close_series.get(d_str)
        if not c0 or c0 <= 0: continue
        max_c = None; confirmed = False; pending = False; cross_date = None
        for k in range(0, LOOKAHEAD_DAYS + 1):
            fd = (d + timedelta(days=k)).isoformat()
            c = close_series.get(fd)
            if c is None:
                if DATA_THROUGH and fd > DATA_THROUGH: pending = True
                continue
            if max_c is None or c > max_c: max_c = c
            if c / c0 >= RUNNER_RATIO:
                confirmed = True
                if cross_date is None: cross_date = fd
        ret_max = (max_c / c0 - 1) if max_c else None
        if confirmed:
            events.append({"D_run": d_str, "D_cross": cross_date, "ret_max": ret_max, "status": "confirmed"})
        elif pending and (max_c is None or ret_max < RUNNER_RATIO - 1):
            events.append({"D_run": d_str, "D_cross": None, "ret_max": ret_max, "status": "pending"})
    if not events:
        return {"status": "none", "D_run": None, "D_cross": None, "ret_max": None}
    events.sort(key=lambda e: e["D_run"])
    clustered = [events[0]]
    for e in events[1:]:
        last = clustered[-1]
        if (_date.fromisoformat(e["D_run"]) - _date.fromisoformat(last["D_run"])).days <= LOOKAHEAD_DAYS:
            if e["ret_max"] and (last["ret_max"] is None or e["ret_max"] > last["ret_max"]):
                last["ret_max"] = e["ret_max"]
            if e["status"] == "confirmed" and last["status"] == "pending":
                last["status"] = "confirmed"
                last["D_cross"] = e["D_cross"]
            if e["D_cross"] and (last["D_cross"] is None or e["D_cross"] < last["D_cross"]):
                last["D_cross"] = e["D_cross"]
        else:
            clustered.append(e)
    confirmed_ev = [e for e in clustered if e["status"] == "confirmed"]
    pending_ev = [e for e in clustered if e["status"] == "pending"]
    if confirmed_ev: return {**confirmed_ev[0], "status": "confirmed"}
    if pending_ev: return {**pending_ev[0], "status": "pending"}
    return {"status": "none", "D_run": None, "D_cross": None, "ret_max": None}


# ─── Assembly ───
print("\n[U3/U4] Replay compose + assemble rows...")
rows_out = []
self_check_9case = []
for i, tok in enumerate(tokens):
    if i % 20 == 0: print(f"  {i}/{len(tokens)}...", flush=True)
    sym = tok + "USDT"
    close_series = CLOSE.get(sym, {})
    ev = find_runner_events(sym, close_series)
    runner_status = {"confirmed": "Y", "pending": "PENDING", "none": "N"}[ev["status"]]
    D_run = ev["D_run"]
    D_cross = ev["D_cross"]
    ret_max = ev["ret_max"]

    if runner_status == "N" and close_series:
        cw = {d: c for d, c in close_series.items()
              if WINDOW_START <= _date.fromisoformat(d) <= WINDOW_END}
        if cw:
            ds = sorted(cw.keys()); base = cw[ds[0]]
            if base > 0: ret_max = max(cw[d] / base - 1 for d in ds)

    # 9-case SELF-CHECK
    if tok in D0_9CASE:
        ret_str = f"{ret_max*100:.1f}%" if ret_max is not None else "N/A"
        flag = ""
        if runner_status == "N": flag = " ← TRƯỢT THƯỚC"
        elif runner_status == "PENDING": flag = " ← PENDING"
        self_check_9case.append(f"  {tok:6} D0={D0_9CASE[tok]} runner={runner_status:8} ret_max={ret_str:>8} D_run={str(D_run):>10} D_cross={str(D_cross):>10}{flag}")

    # Compose replay
    rep = compose_replay(tok)
    kept = rep["kept_fires"]

    # Pre/post D_run
    def pick_pre_post(anchor_date_str):
        if anchor_date_str is None:
            return (min(kept, key=lambda f: f["date"]) if kept else None), None
        ad = _date.fromisoformat(anchor_date_str)
        pre = [f for f in kept if _date.fromisoformat(f["date"]) < ad]
        post = [f for f in kept if _date.fromisoformat(f["date"]) >= ad]
        return (min(pre, key=lambda f: f["date"]) if pre else None,
                min(post, key=lambda f: f["date"]) if post else None)

    pre_run, post_run = pick_pre_post(D_run)
    pre_cross, post_cross = pick_pre_post(D_cross)

    lead_vs_run = None
    if pre_run and D_run:
        lead_vs_run = (_date.fromisoformat(D_run) - _date.fromisoformat(pre_run["date"])).days
    lead_vs_cross = None
    if pre_cross and D_cross:
        lead_vs_cross = (_date.fromisoformat(D_cross) - _date.fromisoformat(pre_cross["date"])).days

    # Taxonomy 8 nhãn (rule code):
    # DQ-SERIAL: token in dq_members AND at least 1 dq-block day AND runner=Y no pre_run
    # NO-KHO-DATA: h1_na == full_window AND h2 câm too (rare) OR just h1_na high
    # PERP-CÂM: h2_eval count > 0 AND 0 T (all F)
    # D0-CROSSING: pre_run.date == D_run OR D_run+1 (edge borderline)
    # FORMULA-MISS: evaluable but no signal (both lanes eval, none fired)
    # NO-SIGNAL-thật: like FORMULA-MISS but no obvious eligible signal
    # LATE-VS-ANCHOR: fires post-D_run but none pre-D_run
    # EDGE-CENSOR: window < obs_min (D_run at window start) → NOT-EVALUABLE, remove from denom

    def classify_sot(runner_status, kept, pre_run, pre_cross, D_run, D_cross, per_token_start, rep, tok):
        # DQ block
        if tok in dq_members: return "DQ-SERIAL"
        # NO-KHO-DATA: h1_na dominant (>= 50% of window days)
        total_days = rep["h1_eval"] + rep["h1_na"]
        if total_days > 0 and rep["h1_na"] / total_days >= 0.5:
            return "NO-KHO-DATA"
        # Edge censor vs D_run (only when NO pre-signal EVER)
        if runner_status == "Y" and D_run and pre_run is None and pre_cross is None:
            days_lead_possible = (_date.fromisoformat(D_run) - per_token_start).days
            if days_lead_possible < OBS_MIN:
                return "EDGE-CENSOR"
        # D0-CROSSING: pre_run.date is D_run itself or D_run-1
        if pre_run and D_run:
            gap = (_date.fromisoformat(D_run) - _date.fromisoformat(pre_run["date"])).days
            if gap <= 1: return "D0-CROSSING"
        # LATE-VS-ANCHOR: fires exist but all post-D_run (may still have pre-D_cross)
        if runner_status == "Y" and pre_run is None and kept:
            return "LATE-VS-ANCHOR"
        # PERP-CÂM: h2 evaluable but no fires
        if rep["h2_eval"] > 0 and not kept and rep["h1_eval"] > 0:
            return "PERP-CÂM"
        # FORMULA-MISS: eval both lanes fine, no fire
        if rep["h1_eval"] + rep["h2_eval"] >= OBS_MIN * 2 and not kept:
            return "FORMULA-MISS"
        # NO-SIGNAL-thật
        if not kept: return "NO-SIGNAL-thật"
        return "—"

    per_token_start = WINDOW_START
    df = _df_sym(sym)
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)

    sot_cause = "—"
    if runner_status == "Y":
        if not pre_run:
            sot_cause = classify_sot(runner_status, kept, pre_run, pre_cross, D_run, D_cross, per_token_start, rep, tok)
    elif runner_status == "PENDING":
        sot_cause = "PENDING-RUNNER-BUCKET"
    else:  # N
        sot_cause = "—"

    rows_out.append({
        "token": tok,
        "runner": runner_status,
        "ret_max": f"{ret_max*100:.2f}%" if ret_max is not None else "",
        "D_run": D_run or "",
        "D_cross": D_cross or "",
        "pre_run_date": pre_run["date"] if pre_run else "",
        "pre_run_lane": pre_run["lane"] if pre_run else "",
        "pre_run_trigger": pre_run["trigger"] if pre_run else "",
        "pre_run_conf": pre_run["conf"] if pre_run else "",
        "lead_vs_D_run": lead_vs_run if lead_vs_run is not None else "",
        "pre_cross_date": pre_cross["date"] if pre_cross else "",
        "lead_vs_D_cross": lead_vs_cross if lead_vs_cross is not None else "",
        "post_run_date": post_run["date"] if post_run else "",
        "post_run_lane": post_run["lane"] if post_run else "",
        "coverage_h1_eval": rep["h1_eval"],
        "coverage_h1_na": rep["h1_na"],
        "coverage_h2_eval": rep["h2_eval"],
        "coverage_h2_na": rep["h2_na"],
        "n_kept_fires": len(kept),
        "sot_cause": sot_cause,
    })


# ─── U5 metrics ───
confirmed = [r for r in rows_out if r["runner"] == "Y"]
pending = [r for r in rows_out if r["runner"] == "PENDING"]
non_runners = [r for r in rows_out if r["runner"] == "N"]
# EDGE-CENSOR (rút khỏi mẫu số cả hai anchor — no pre-signal at all + D_run edge)
edge_censor_both = [r for r in confirmed if r["sot_cause"] == "EDGE-CENSOR"]
# DQ-SERIAL: separately rút (bị chặn structurally)
dq_out = [r for r in confirmed if r["sot_cause"] == "DQ-SERIAL"]

confirmed_evaluable = [r for r in confirmed if r["sot_cause"] not in ("EDGE-CENSOR", "DQ-SERIAL")]
with_pre_run = [r for r in confirmed_evaluable if r["pre_run_date"]]
with_pre_cross = [r for r in confirmed_evaluable if r["pre_cross_date"]]
recall_vs_run = len(with_pre_run) / len(confirmed_evaluable) if confirmed_evaluable else 0
recall_vs_cross = len(with_pre_cross) / len(confirmed_evaluable) if confirmed_evaluable else 0

n_non = len(non_runners)
total_fires_non = sum(r["n_kept_fires"] for r in non_runners)
window_days = (WINDOW_END - WINDOW_START).days + 1
fp_load = total_fires_non / (n_non * window_days / 30) if n_non > 0 else 0

# PENDING bucket metrics
pending_with_pre_run = [r for r in pending if r["pre_run_date"]]
pending_recall = len(pending_with_pre_run) / len(pending) if pending else 0

# ─── Write CSV ───
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    # SELF-CHECK 3 lines đầu file
    f.write(f"# SELF-CHECK-COMPOSE-1: CYS 2026-07-12 H2-raw perp-fire = True (h2_status={h2_status_cys}) · {'PASS' if sc1_pass else 'FAIL'}\n")
    f.write(f"# SELF-CHECK-COMPOSE-2: BTR 2026-07-28 H1-ramp kho-fire = True (ramp_delta={btr_ramp_delta*100 if btr_ramp_delta else 0:.2f}%) · {'PASS' if sc2_pass else 'FAIL'}\n")
    f.write(f"# SELF-CHECK-COMPOSE-3: BANANAS31 in dq_members = {'BANANAS31' in dq_members} · kỳ 07-04..12 blocked · {'PASS' if sc3_pass else 'FAIL'}\n")
    f.write(f"#\n")
    # Header L-64
    f.write(f"# code md5={CODE_MD5} · yaml md5={YAML_MD5} · gate_defs md5={GATE_MD5}\n")
    f.write(f"# obs_min={OBS_MIN} (source: {_obs_min_source}) · adapter path={SNAPSHOTS_DIR}\n")
    f.write(f"# compose_mode: {compose_mode}\n")
    f.write(f"# compose gói-nhẹ prod: H1-raw ∨ H2-raw · T0.1 → NHÃN CONF\n")
    f.write(f"# T0.1 thresholds: funding_pin_abs={_cfg_t01['funding_pin_abs']} · oi_over_min30_max={_cfg_t01['oi_over_min30_max']} · ret14_abs_max={_cfg_t01['ret14_abs_max']} · vol_med7_over_med30_max={_cfg_t01['vol_med7_over_med30_max']} · floor_obs_min={_cfg_t01['floor_obs_min']}\n")
    f.write(f"# H2 thresholds: div_min_14d_max={_cfg_h2['div_min_14d_max']} · div_today_min={_cfg_h2['div_today_min']} · pos_over_min14_min={_cfg_h2['pos_over_min14_min']} · oi_over_min30_max={_cfg_h2['oi_over_min30_max']} · floor_obs_min={_cfg_h2['floor_obs_min']}\n")
    f.write(f"# H1 thresholds: balance_delta_abs_min={gom_h_cfg['h1']['balance_delta_abs_min']} · window_days_max={gom_h_cfg['h1']['window_days_max']} · kho_ramp.delta_min={kho_ramp_cfg.get('delta_min')} · kho_ramp.window_days={kho_ramp_cfg.get('window_days')}\n")
    f.write(f"# Cooldown: {gom_h_cfg.get('gom_h_cooldown_days', 14)}d · clean_streak_re_arm: {gom_h_cfg.get('gom_h_cooldown_clean_days', 3)}d · DQ-SERIAL members: {sorted(dq_members)}\n")
    f.write(f"# data_through_utc={DATA_THROUGH} · window={WINDOW_START}..{WINDOW_END}\n")
    f.write(f"#\n")
    # 2 RECALL lines
    f.write(f"# RECALL vs D_run:   {len(with_pre_run)}/{len(confirmed_evaluable)} = {recall_vs_run*100:.1f}% (mẫu số sau rút EDGE-CENSOR={len(edge_censor_both)} + DQ-SERIAL={len(dq_out)})\n")
    f.write(f"# RECALL vs D_cross: {len(with_pre_cross)}/{len(confirmed_evaluable)} = {recall_vs_cross*100:.1f}%\n")
    # FP-load with n=2 note
    f.write(f"# FP-LOAD: {total_fires_non} kept fires trên {n_non} non-runner tokens × {window_days}d = {fp_load:.3f} fires/token/30d · [n={n_non} KHÔNG ĐỦ MẪU] (đối chiếu 0.845 census; PENDING loại)\n")
    # PENDING bucket
    f.write(f"# PENDING-BUCKET: {len(pending)} tokens · pre-fire on {len(pending_with_pre_run)} = {pending_recall*100:.1f}%\n")
    f.write(f"#\n")
    # Taxonomy legend
    f.write(f"# TAXONOMY 8 nhãn (rule code):\n")
    f.write(f"#   DQ-SERIAL       = tok in dq_members\n")
    f.write(f"#   EDGE-CENSOR     = (D_run - per_token_start) < obs_min → NOT-EVALUABLE, rút khỏi mẫu số\n")
    f.write(f"#   NO-KHO-DATA     = h1_na / (h1_eval + h1_na) >= 0.5\n")
    f.write(f"#   LATE-VS-ANCHOR  = kept fires tồn tại nhưng tất cả post-D_run\n")
    f.write(f"#   D0-CROSSING     = pre_run.date within [D_run-1, D_run] (borderline)\n")
    f.write(f"#   PERP-CÂM        = h2_eval > 0, không kept fires, h1_eval > 0\n")
    f.write(f"#   FORMULA-MISS    = h1_eval + h2_eval >= 2*obs_min, không kept fires\n")
    f.write(f"#   NO-SIGNAL-thật  = không kept fires, không match nhãn trên\n")
    f.write(f"#\n")
    # 9-case SELF-CHECK
    f.write(f"# 9-case SELF-CHECK:\n")
    for l in self_check_9case: f.write(f"# {l}\n")
    f.write(f"#\n")
    # SÓT list (excludes EDGE-CENSOR from denom)
    sot_list = [r for r in confirmed_evaluable if not r["pre_run_date"]]
    f.write(f"# SÓT list ({len(sot_list)} confirmed-evaluable không pre_run): {', '.join(r['token']+'('+r['sot_cause']+')' for r in sot_list) if sot_list else '—'}\n")
    f.write(f"#\n")
    if rows_out:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        for r in rows_out: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print("\n" + "═" * 100)
print(f"[U-REPLAY v2 OUTPUT]")
print(f"  file:  {OUT_CSV}")
print(f"  md5:   {md5_out}")
print(f"  wc -l: {n_lines}")
print("═" * 100)
print(f"\nRECALL vs D_run:   {len(with_pre_run)}/{len(confirmed_evaluable)} = {recall_vs_run*100:.1f}% (rút EDGE-CENSOR={len(edge_censor_both)} + DQ-SERIAL={len(dq_out)})")
print(f"RECALL vs D_cross: {len(with_pre_cross)}/{len(confirmed_evaluable)} = {recall_vs_cross*100:.1f}%")
print(f"FP-LOAD = {fp_load:.3f} fires/token/30d · [n={n_non} KHÔNG ĐỦ MẪU]")
print(f"n_confirmed={len(confirmed)} · n_edge_censor={len(edge_censor_both)} · n_dq={len(dq_out)} · n_pending={len(pending)} · n_non_runners={n_non}")
print(f"PENDING-BUCKET recall: {len(pending_with_pre_run)}/{len(pending)} = {pending_recall*100:.1f}%")

print("\n[9-case SELF-CHECK]")
for l in self_check_9case: print(l)

# Sample 3 rows
print("\n[SAMPLE 3 dòng — BTR · CYS · APR]")
for tt in ["BTR", "CYS", "APR"]:
    r = next((r for r in rows_out if r["token"] == tt), None)
    if r:
        print(f"  {r['token']:8} runner={r['runner']:8} ret_max={r['ret_max']:>10} D_run={r['D_run']:>10} D_cross={r['D_cross']:>10} pre_run={r['pre_run_date']:>10} lane={r['pre_run_lane']:>4} lead_run={str(r['lead_vs_D_run']):>4} lead_cross={str(r['lead_vs_D_cross']):>4} sot={r['sot_cause']}")
