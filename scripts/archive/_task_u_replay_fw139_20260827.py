#!/usr/bin/env python3
"""[U-REPLAY fw-139 · KÝ 27/08 · run TRÊN rev4-FINAL v2.1]

Universe replay: RUNNER (close ≥ 1.5×/30d) vs GOM-H compose gói-nhẹ fires.
Header L-64: single snapshot pin (code md5 + yaml + gate_defs + adapter path).

U1 Universe: fw-139 · window 2026-06-26..2026-08-22 · per-token max(2026-06-26, first_seen).
U2 RUNNER: fapi klines 1d fresh k[4] · max(close[D..D+30])/close[D] ≥ 1.5.
   Right-censor: chưa đủ 30d → PENDING-RUNNER (bucket riêng, không N).
   Cluster: 2 qualifying days ≤30d → 1 event, D_run = sớm nhất; >30d → riêng.
U3 GOM-H compose gói-nhẹ replay cùng kỳ. H1 đọc LOCAL snapshot dir
   (D:/Check onchain fresh wallets/snapshots — full retention). DQ-SERIAL / cooldown
   14d / obs_min=14 như prod.
U4 CSV: token · runner · ret_max · D_run · first_fire_pre_Drun · first_fire_post ·
   coverage_H1/H2 · sót_cause.
U5 Header lines: RECALL + FP-load.
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv, time
from pathlib import Path
from datetime import datetime, timedelta, timezone, date as _date
from statistics import median
import pandas as pd
import yaml
try:
    import urllib.request
    import urllib.parse
except ImportError:
    pass

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
SYMBOLS_TXT = REPO / "data/config/freshwatch_symbols.txt"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")
GATE_DEFS = REPO / "docs/proposals/gom_h_gate_defs_20260828.md"
CODE_PATH = REPO / "scripts/gom_h_daily.py"
OUT_CSV = REPO / "docs/reports/u_replay_fw139_20260827.csv"

WINDOW_START = _date(2026, 6, 26)
WINDOW_END = _date(2026, 8, 22)
LOOKAHEAD_DAYS = 30
RUNNER_RATIO = 1.5

# 9-case D0 for SELF-CHECK
D0_9CASE = {"BANK": _date(2026,7,11), "TUT": _date(2026,7,9), "CYS": _date(2026,8,4),
            "AKE": _date(2026,7,15), "BTW": _date(2026,8,3), "HEMI": _date(2026,8,15),
            "ON": _date(2026,7,19), "CAP": _date(2026,7,30), "BTR": _date(2026,8,26)}

def _md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

cfg_all = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))
cfg = cfg_all["gom_h"]
dq_members = set(cfg_all.get("dq_serial", {}).get("members", []))
gn_cfg = cfg_all.get("goi_nhe", {})
kho_ramp_cfg = gn_cfg.get("kho_ramp", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
cfg["t0_1"]["floor_obs_min"] = OBS_MIN
cfg["h2"]["floor_obs_min"] = OBS_MIN

# ─── HEADER L-64 ───
CODE_MD5 = _md5(CODE_PATH)
YAML_MD5 = _md5(YAML_PATH)
GATE_MD5 = _md5(GATE_DEFS)
print("═" * 100)
print(f"[U-REPLAY fw-139 · KÝ 27/08 · rev4-FINAL v2.1]")
print(f"  code:      scripts/gom_h_daily.py         md5={CODE_MD5}")
print(f"  yaml:      screen_thresholds.yaml         md5={YAML_MD5}")
print(f"  gate_defs: gom_h_gate_defs_20260828.md    md5={GATE_MD5}")
print(f"  adapter local path: {SNAPSHOTS_DIR} (full retention 2026-06-17+)")
print(f"  obs_min={OBS_MIN} (source: yaml goi_nhe.obs_min)")
print(f"  window: {WINDOW_START}..{WINDOW_END} · lookahead {LOOKAHEAD_DAYS}d · runner threshold {RUNNER_RATIO}×")
print(f"  DQ-SERIAL members: {sorted(dq_members)}")
print("═" * 100)

# ─── Load fw-139 ───
symbols = [s.strip() for s in SYMBOLS_TXT.read_text(encoding="utf-8").splitlines() if s.strip()]
tokens = [s[:-4] if s.endswith("USDT") else s for s in symbols]
print(f"\n[U1] fw-{len(symbols)} loaded")

# ─── Load store CSVs ───
frames = []
for m in ["05","06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists(): frames.append(pd.read_csv(p))
STORE = pd.concat(frames, ignore_index=True)
print(f"[U3] store rows: {len(STORE)}")

# ─── Load snapshot balance + holders series (LOCAL full retention) ───
BAL = {}  # {token: {ingest_date_str: balance}}
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
print(f"[U3] snapshot files loaded: {n_snap} (LOCAL {SNAPSHOTS_DIR.name} full retention)")


# ─── Fetch fapi klines 1d fresh (k[4] = close) ───
def fetch_fapi_klines(sym, start_ms, end_ms):
    """fapi.binance.com/fapi/v1/klines · returns list of [openTime, open, high, low, close, ...]"""
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&startTime={start_ms}&endTime={end_ms}&limit=500"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "u-replay/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None


start_dt = datetime(2026, 6, 26, tzinfo=timezone.utc)
end_dt = datetime(2026, 9, 22, tzinfo=timezone.utc)  # + lookahead
start_ms = int(start_dt.timestamp() * 1000)
end_ms = int(end_dt.timestamp() * 1000)

print(f"\n[U2] Fetching fapi 1d klines: fw-{len(symbols)} × {start_dt.date()}..{end_dt.date()}")
CLOSE = {}  # {sym: {date_str: close_price}}
DATA_THROUGH = None  # latest closed UTC candle across all
n_ok = 0; n_fail = 0
for i, sym in enumerate(symbols):
    if i % 20 == 0: print(f"  {i}/{len(symbols)}...", flush=True)
    data = fetch_fapi_klines(sym, start_ms, end_ms)
    if not data:
        n_fail += 1
        continue
    n_ok += 1
    for k in data:
        # k[0] = openTime ms · k[4] = close
        ot_ms = k[0]
        d_str = datetime.fromtimestamp(ot_ms/1000, tz=timezone.utc).date().isoformat()
        CLOSE.setdefault(sym, {})[d_str] = float(k[4])
        # Track latest closed candle
        candle_close_time_ms = ot_ms + 86400_000 - 1
        if candle_close_time_ms < int(time.time() * 1000):
            if DATA_THROUGH is None or d_str > DATA_THROUGH:
                DATA_THROUGH = d_str
    time.sleep(0.05)  # rate limit courtesy
print(f"[U2] fapi fetch: ok={n_ok} fail={n_fail} · data_through UTC = {DATA_THROUGH}")


# ─── RUNNER detection: max(close[D..D+30])/close[D] ≥ 1.5 · cluster ≤30d · right-censor ───
def find_runners(sym, close_series):
    """Return list of D_run events (cluster ≤30d), + PENDING if any pending."""
    dates = sorted(close_series.keys())
    if not dates: return [], []
    events = []  # list of {D_run, ret_max, status: confirmed|pending}
    for d_str in dates:
        d = _date.fromisoformat(d_str)
        if d < WINDOW_START or d > WINDOW_END: continue
        close_d = close_series.get(d_str)
        if not close_d or close_d <= 0: continue
        # Lookahead 30d
        lookahead_max = None
        confirmed = False
        pending = False
        for k in range(0, LOOKAHEAD_DAYS + 1):
            fd = d + timedelta(days=k)
            fd_str = fd.isoformat()
            c = close_series.get(fd_str)
            if c is None:
                if DATA_THROUGH and fd_str > DATA_THROUGH:
                    pending = True
                continue
            if lookahead_max is None or c > lookahead_max: lookahead_max = c
            if c / close_d >= RUNNER_RATIO:
                confirmed = True
                break
        ret_max = (lookahead_max / close_d - 1) if lookahead_max else None
        if confirmed:
            events.append({"D_run": d_str, "ret_max": ret_max, "status": "confirmed"})
        elif pending and (lookahead_max is None or ret_max < RUNNER_RATIO - 1):
            # Right-censor: not confirmed AND some lookahead days missing
            events.append({"D_run": d_str, "ret_max": ret_max, "status": "pending"})
    # Cluster: merge events ≤30d apart, keep earliest
    if not events: return [], []
    events.sort(key=lambda e: e["D_run"])
    clustered = [events[0]]
    for e in events[1:]:
        last = clustered[-1]
        if (_date.fromisoformat(e["D_run"]) - _date.fromisoformat(last["D_run"])).days <= LOOKAHEAD_DAYS:
            # merge — keep earliest D_run, take max ret_max
            if e["ret_max"] and (last["ret_max"] is None or e["ret_max"] > last["ret_max"]):
                last["ret_max"] = e["ret_max"]
            if e["status"] == "confirmed" and last["status"] == "pending":
                last["status"] = "confirmed"
        else:
            clustered.append(e)
    # Reduce to single event per token (first confirmed OR pending)
    confirmed_only = [e for e in clustered if e["status"] == "confirmed"]
    pending_only = [e for e in clustered if e["status"] == "pending"]
    return confirmed_only, pending_only


# ─── GOM-H compose gói-nhẹ replay ───
def _df_sym(sym):
    return STORE[STORE["symbol"] == sym].sort_values("date").reset_index(drop=True)


def _v(df, d_str, col, n):
    s = df[df["date"] <= d_str].sort_values("date").tail(n)
    return [float(v) for v in s[col].tolist() if pd.notna(v)]


def _t(df, d_str, col):
    r = df[df["date"] == d_str][col]
    if r.empty: return None
    try: v = float(r.iloc[0]); return v if v == v else None
    except: return None


def _div_avg3(df, d_str):
    s = df[df["date"] <= d_str].sort_values("date").tail(3)
    pairs = []
    for _, r in s.iterrows():
        p = r.get("lsr_pos_r"); a = r.get("lsr_acc_r")
        try:
            if pd.notna(p) and pd.notna(a): pairs.append((float(p), float(a)))
        except: pass
    if not pairs: return None
    return sum(x[0] for x in pairs)/len(pairs) / (sum(x[1] for x in pairs)/len(pairs) or 1e-9)


def eval_h1_raw(tok, d_str):
    """Return (fires:bool|None, trigger:'step'|'ramp'|None, step_pct, ramp_pct)"""
    ingest = (_date.fromisoformat(d_str) + timedelta(days=1)).isoformat()
    series = BAL.get(tok, {})
    if ingest not in series: return None, None, None, None
    b_end = series[ingest]
    if b_end <= 0: return None, None, None, None
    # step 3d
    best_step = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - timedelta(days=lb)).isoformat()
        b_start = series.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if best_step is None or dp > best_step: best_step = dp
    # ramp 14d
    ramp = None
    d_start_r = (_date.fromisoformat(ingest) - timedelta(days=14)).isoformat()
    b_start_r = series.get(d_start_r)
    if b_start_r and b_start_r > 0:
        ramp = abs(b_end - b_start_r) / b_start_r
    step_fire = best_step is not None and best_step >= 0.10
    ramp_thr = kho_ramp_cfg.get("delta_min", 0.15)
    ramp_fire = ramp is not None and ramp >= ramp_thr
    if step_fire: return True, "step", best_step, ramp
    if ramp_fire: return True, "ramp", best_step, ramp
    return False, None, best_step, ramp


def eval_h2_t01(df, d_str):
    """Return (h2t01_fires, ve, coverage_ok)"""
    pos_14 = _v(df, d_str, "lsr_pos_r", 14)
    oi_all = _v(df, d_str, "oi_usd", 30)
    fund_14 = _v(df, d_str, "funding_avg", 14)
    px_15 = _v(df, d_str, "px_avg", 15)
    vol_30 = _v(df, d_str, "vol_quote", 30)
    if len(pos_14) < 14 or len(oi_all) < OBS_MIN: return None, None, False
    if len(fund_14) < 14 or len(px_15) < 15 or len(vol_30) < OBS_MIN: return None, None, False
    div_today = _div_avg3(df, d_str)
    if div_today is None: return None, None, False
    dates = sorted(df[df["date"] <= d_str]["date"].tolist())[-14:]
    if len(dates) < 14: return None, None, False
    divs = [_div_avg3(df, d) for d in dates]
    divs = [v for v in divs if v is not None]
    if not divs: return None, None, False
    div_min14 = min(divs)
    c_h2 = cfg["h2"]; c_t01 = cfg["t0_1"]
    # H2 raw
    v1_divcut = (div_min14 <= c_h2["div_min_14d_max"]) and (div_today >= c_h2["div_today_min"])
    pos_today = _t(df, d_str, "lsr_pos_r"); oi_today = _t(df, d_str, "oi_usd")
    pos_min14 = min(pos_14); oi_min = min(oi_all)
    r_pos = pos_today / pos_min14 if (pos_today is not None and pos_min14 > 0) else None
    r_oi = oi_today / oi_min if (oi_today is not None and oi_min > 0) else None
    v2_posratio = (r_pos is not None and r_oi is not None
                   and r_pos >= c_h2["pos_over_min14_min"]
                   and r_oi <= c_h2["oi_over_min30_max"])
    h2_raw = v1_divcut or v2_posratio
    if v1_divcut and v2_posratio: ve = "cả-hai"
    elif v1_divcut: ve = "div-cut"
    elif v2_posratio: ve = "pos-ratio"
    else: ve = None
    # T0.1 eval (for gói-nhẹ H2∧T0.1 lane)
    t01_pass = False
    if len(fund_14) >= 14:
        max_af = max(abs(f) for f in fund_14)
        eps = c_t01.get("funding_pin_eps", 1e-9)
        fund_pin = max_af <= c_t01["funding_pin_abs"] + eps
        oi_ok = (oi_today is not None and oi_min > 0
                 and oi_today / oi_min <= c_t01["oi_over_min30_max"])
        ret14_val = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
        ret_ok = ret14_val <= c_t01["ret14_abs_max"]
        med7 = median(vol_30[-7:]) if len(vol_30) >= 7 else 0
        med30 = median(vol_30) if vol_30 else 0
        vol_ok = med7 <= c_t01["vol_med7_over_med30_max"] * med30 if med30 > 0 else False
        t01_pass = fund_pin and oi_ok and ret_ok and vol_ok
    h2t01_fires = h2_raw and t01_pass
    return h2t01_fires, ve, True


def _conf_label(subs):
    na_list = [k for k, v in subs.items() if v is None]
    n_pass = sum(1 for v in subs.values() if v is True)
    n_eval = sum(1 for v in subs.values() if v is not None)
    if n_pass >= 4: level = "HIGH"
    elif n_pass >= 2: level = "MED"
    else: level = "LOW"
    na_str = ",".join(na_list) if na_list else "-"
    if n_eval == 0:
        return f"{level} (0/0; N/A: 4 vế)"
    return f"{level} ({n_pass}/{n_eval}; N/A: {na_str})"


def eval_t01_subs(df, d_str):
    fund_14 = _v(df, d_str, "funding_avg", 14)
    oi_all = _v(df, d_str, "oi_usd", 30)
    px_15 = _v(df, d_str, "px_avg", 15)
    vol_30 = _v(df, d_str, "vol_quote", 30)
    subs = {"funding_pin": None, "oi_min30": None, "ret14": None, "med30_vol": None}
    c = cfg["t0_1"]
    if len(fund_14) >= 14:
        max_af = max(abs(f) for f in fund_14)
        eps = c.get("funding_pin_eps", 1e-9)
        subs["funding_pin"] = max_af <= c["funding_pin_abs"] + eps
    if len(oi_all) >= OBS_MIN:
        oi_today = _t(df, d_str, "oi_usd"); oi_min = min(oi_all)
        if oi_today is not None and oi_min > 0:
            subs["oi_min30"] = (oi_today / oi_min) <= c["oi_over_min30_max"]
    if len(px_15) >= 15:
        ret14 = abs((px_15[-1] - px_15[0]) / px_15[0]) if px_15[0] > 0 else float("inf")
        subs["ret14"] = ret14 <= c["ret14_abs_max"]
    if len(vol_30) >= OBS_MIN:
        subs["med30_vol"] = median(vol_30[-7:]) <= median(vol_30) * c["vol_med7_over_med30_max"]
    return subs


def replay_compose(tok, per_token_start):
    """Replay per-day compose OR with cooldown 14d + re-arm 3d clean.
    Returns list of kept fires + coverage stats.
    """
    sym = tok + "USDT"
    df = _df_sym(sym)
    dq_hit = tok in dq_members
    kept_fires = []  # {date, lane, trigger, conf}
    n_h1_eval = 0; n_h2_eval = 0
    n_h1_na = 0; n_h2_na = 0
    # Two-lane cooldown: {kho, perp} independent
    lane_state = {"kho": {"last_fire": None, "clean_days": 0},
                  "perp": {"last_fire": None, "clean_days": 0}}
    cd_days = 14
    cn_days = 3
    cur = per_token_start
    while cur <= WINDOW_END:
        d_str = cur.isoformat()
        # H1 kho
        h1_fires, trig, step_pct, ramp_pct = eval_h1_raw(tok, d_str)
        if h1_fires is None: n_h1_na += 1
        else:
            n_h1_eval += 1
        # H2t01 perp
        h2t01_fires, ve, cov_ok = eval_h2_t01(df, d_str)
        if not cov_ok: n_h2_na += 1
        else: n_h2_eval += 1
        # DQ-SERIAL block
        if dq_hit:
            cur += timedelta(days=1); continue
        # Cooldown check per lane
        for lane, raw_fires, lane_trigger in [
            ("kho", h1_fires, trig or "step"),
            ("perp", h2t01_fires, "h2"),
        ]:
            state = lane_state[lane]
            if raw_fires is True:
                # Check cooldown
                if state["last_fire"] is None:
                    can_fire = True
                else:
                    days_since = (cur - _date.fromisoformat(state["last_fire"])).days
                    can_fire = days_since >= cd_days
                if can_fire:
                    subs = eval_t01_subs(df, d_str)
                    conf = _conf_label(subs)
                    kept_fires.append({"date": d_str, "lane": lane,
                                       "trigger": ("H1-"+trig) if lane == "kho" else "H2",
                                       "conf": conf, "step_pct": step_pct, "ramp_pct": ramp_pct})
                    state["last_fire"] = d_str
                    state["clean_days"] = 0
            elif raw_fires is False:
                state["clean_days"] += 1
        cur += timedelta(days=1)
    return kept_fires, n_h1_eval, n_h1_na, n_h2_eval, n_h2_na


# ─── U4 CSV assembly ───
print("\n[U3/U4] Replay compose + assemble rows...")
rows_out = []
self_check_lines = []
for i, tok in enumerate(tokens):
    if i % 20 == 0: print(f"  {i}/{len(tokens)}...", flush=True)
    sym = tok + "USDT"
    df = _df_sym(sym)
    per_token_start = WINDOW_START
    if not df.empty:
        first_seen = _date.fromisoformat(df["date"].min())
        per_token_start = max(WINDOW_START, first_seen)
    # RUNNER
    close_series = CLOSE.get(sym, {})
    confirmed, pending = find_runners(sym, close_series)
    if confirmed:
        runner_status = "Y"
        D_run = confirmed[0]["D_run"]
        ret_max = confirmed[0]["ret_max"]
    elif pending:
        runner_status = "PENDING"
        D_run = pending[0]["D_run"]
        ret_max = pending[0]["ret_max"]
    else:
        runner_status = "N"
        D_run = None
        # ret_max = max close ratio in window (best effort)
        if close_series:
            close_win = {d: c for d, c in close_series.items()
                         if WINDOW_START <= _date.fromisoformat(d) <= WINDOW_END}
            if close_win:
                dates_sorted = sorted(close_win.keys())
                base = close_win[dates_sorted[0]]
                if base > 0:
                    ret_max = max(close_win[d] / base - 1 for d in dates_sorted)
                else: ret_max = None
            else: ret_max = None
        else: ret_max = None

    # SELF-CHECK 9-case (always print status, flag if unexpected)
    if tok in D0_9CASE:
        d0 = D0_9CASE[tok]
        ret_str = f"{ret_max*100:.1f}%" if ret_max is not None else "N/A"
        flag = ""
        if runner_status == "N":
            flag = " ← TRƯỢT THƯỚC báo ANALYSIS"
        elif runner_status == "PENDING":
            flag = " ← PENDING chưa đủ 30d lookahead"
        self_check_lines.append(f"  SELF-CHECK: {tok:6} D0={d0} runner={runner_status:8} ret_max={ret_str:>8} D_run={D_run or '—':>10}{flag}")

    # Compose replay
    kept_fires, h1_eval, h1_na, h2_eval, h2_na = replay_compose(tok, per_token_start)

    # First fire pre/post D_run
    first_pre = None; first_post = None
    if D_run:
        d_run_dt = _date.fromisoformat(D_run)
        pre_fires = [f for f in kept_fires if _date.fromisoformat(f["date"]) < d_run_dt]
        post_fires = [f for f in kept_fires if _date.fromisoformat(f["date"]) >= d_run_dt]
        if pre_fires:
            first_pre = min(pre_fires, key=lambda f: f["date"])
            first_pre["lead"] = (d_run_dt - _date.fromisoformat(first_pre["date"])).days
        if post_fires:
            first_post = min(post_fires, key=lambda f: f["date"])
    else:
        # No D_run → still list first fire (post = None)
        if kept_fires:
            first_pre = min(kept_fires, key=lambda f: f["date"])
            first_pre["lead"] = None

    # sót_cause
    if tok in dq_members:
        sot_cause = "DQ-SERIAL"
    elif h1_eval == 0 and h2_eval == 0:
        sot_cause = "N/A-COVERAGE"
    elif not kept_fires:
        sot_cause = "NO-SIGNAL"
    elif runner_status == "Y" and first_pre is None:
        sot_cause = "NO-SIGNAL"  # runner có nhưng không có fire trước D_run
    else:
        sot_cause = "—"

    rows_out.append({
        "token": tok,
        "runner": runner_status,
        "ret_max": f"{ret_max*100:.2f}%" if ret_max is not None else "",
        "D_run": D_run or "",
        "pre_date": first_pre["date"] if first_pre else "",
        "pre_lane": first_pre["lane"] if first_pre else "",
        "pre_trigger": first_pre["trigger"] if first_pre else "",
        "pre_conf": first_pre["conf"] if first_pre else "",
        "pre_lead": first_pre.get("lead") if first_pre else "",
        "post_date": first_post["date"] if first_post else "",
        "post_lane": first_post["lane"] if first_post else "",
        "post_trigger": first_post["trigger"] if first_post else "",
        "coverage_h1_eval": h1_eval,
        "coverage_h1_na": h1_na,
        "coverage_h2_eval": h2_eval,
        "coverage_h2_na": h2_na,
        "n_fires_total": len(kept_fires),
        "sot_cause": sot_cause,
    })


# ─── U5 RECALL + FP-load ───
confirmed_runners = [r for r in rows_out if r["runner"] == "Y"]
confirmed_with_pre = [r for r in confirmed_runners if r["pre_date"]]
sot_confirmed = [r for r in confirmed_runners if not r["pre_date"]]

recall = len(confirmed_with_pre) / len(confirmed_runners) if confirmed_runners else 0

non_runners_no_pending = [r for r in rows_out if r["runner"] == "N"]
total_fires_non_runners = sum(r["n_fires_total"] for r in non_runners_no_pending)
n_non_runner_tokens = len(non_runners_no_pending)
# FP-load normalized: fires per token per 30d
window_days = (WINDOW_END - WINDOW_START).days + 1
fp_load = total_fires_non_runners / (n_non_runner_tokens * window_days / 30) if n_non_runner_tokens > 0 else 0


# ─── Write CSV ───
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    # Header lines (2 dòng đầu per operator)
    f.write(f"# U-REPLAY fw-{len(symbols)} · window {WINDOW_START}..{WINDOW_END} · rev4-FINAL code md5={CODE_MD5[:12]} · yaml md5={YAML_MD5[:12]} · gate_defs md5={GATE_MD5[:12]}\n")
    f.write(f"# data_through_utc={DATA_THROUGH} · snapshot_dir={SNAPSHOTS_DIR} · obs_min={OBS_MIN}\n")
    f.write(f"# RECALL: {len(confirmed_with_pre)}/{len(confirmed_runners)} confirmed runners có cờ trước D_run = {recall*100:.1f}%\n")
    f.write(f"# SÓT list: {', '.join(r['token']+f'('+r['sot_cause']+')' for r in sot_confirmed) if sot_confirmed else '—'}\n")
    f.write(f"# FP-LOAD: {total_fires_non_runners} kept fires trên {n_non_runner_tokens} non-runner tokens × {window_days}d = {fp_load:.3f} fires/token/30d (đối chiếu 0.845 census; PENDING loại)\n")
    f.write(f"# 9-case SELF-CHECK:\n")
    for line in self_check_lines: f.write(f"# {line}\n")
    f.write("#\n")
    if rows_out:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        for r in rows_out: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print("\n" + "═" * 100)
print(f"[U-REPLAY OUTPUT]")
print(f"  file:  {OUT_CSV}")
print(f"  md5:   {md5_out}")
print(f"  wc -l: {n_lines}")
print("═" * 100)
print(f"\nRECALL = {len(confirmed_with_pre)}/{len(confirmed_runners)} = {recall*100:.1f}%")
print(f"FP-LOAD = {fp_load:.3f} fires/token/30d (non-runners, PENDING loại)")
print(f"n_confirmed={len(confirmed_runners)} · n_pending={sum(1 for r in rows_out if r['runner']=='PENDING')} · n_non_runners={n_non_runner_tokens}")
if sot_confirmed:
    print(f"\nSÓT list ({len(sot_confirmed)}):")
    for r in sot_confirmed[:20]: print(f"  {r['token']:12} D_run={r['D_run']} ret_max={r['ret_max']} sot_cause={r['sot_cause']}")

print("\n[SELF-CHECK 9-case]")
for line in self_check_lines: print(line)

# Sample 3 rows
print("\n[SAMPLE 3 dòng — BTR · APR · một SÓT (nếu có)]")
targets = ["BTR", "APR"] + ([sot_confirmed[0]["token"]] if sot_confirmed else [])
for tt in targets:
    r = next((r for r in rows_out if r["token"] == tt), None)
    if r:
        print(f"  {r['token']:12} runner={r['runner']:8} ret_max={r['ret_max']:>10} D_run={r['D_run']:>10} pre={r['pre_date']:>10} lane={r['pre_lane']:>4} trig={r['pre_trigger']:>8} lead={str(r['pre_lead']):>5} sot_cause={r['sot_cause']}")
    else:
        print(f"  {tt:12} NOT IN OUTPUT")
