#!/usr/bin/env python3
"""
scripts/watchlist_daily.py — Watchlist daily per spec v1.3
Chạy 01:00 UTC sau candle 00:00 UTC đóng.

Usage:
  python3 scripts/watchlist_daily.py
  python3 scripts/watchlist_daily.py --date 2026-08-10
  python3 scripts/watchlist_daily.py --no-telegram
"""
import argparse, csv, math, os, pathlib, sys, urllib.error, urllib.parse, urllib.request
from statistics import mean

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT   = pathlib.Path(__file__).resolve().parent.parent
EXPORT_DIR  = REPO_ROOT / "data" / "export"
CONFIG_PATH = REPO_ROOT / "data" / "config" / "watchlist_thresholds.yaml"

# ── Load .env — same credentials as run_gom_daily ─────────────────────────────
_env_path = REPO_ROOT / ".env"
if _env_path.exists():
    for _ln in _env_path.read_text(encoding="utf-8").splitlines():
        _ln = _ln.strip()
        if _ln and not _ln.startswith("#") and "=" in _ln:
            _k, _, _v = _ln.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

NaN = float("nan")
def ok(x): return x == x and not math.isinf(x)

# ── Defaults (fallback nếu yaml missing/pyyaml không cài) ────────────────────
_DEFAULTS = {
    "hedge":    {"div_ratio_max": 0.5, "struct_n_min": 5,
                 "gap_tolerance_days": 2, "episode_break_days": 3},
    "list_b":   {"recent_hedge_days": 2, "div_delta_window": 5},
    "trends":   {"pos_trend_threshold": 0.01, "oi_trend_threshold": 0.02},
    "oi_guard": {"low_conf_usd": 1_000_000},
    "data":     {"min_history_rows": 14},
    "output":   {"telegram_hour_utc": 1, "log_csv": True,
                 "csv_path": "data/export/watchlist_log_{YYYY-MM}.csv"},
}

def _parse_val(s):
    s = s.split("#")[0].strip()
    if s in ("true", "True"): return True
    if s in ("false", "False"): return False
    try: return int(s.replace("_", ""))
    except: pass
    try: return float(s)
    except: pass
    return s.strip("\"'")

def load_config(path=CONFIG_PATH):
    cfg = {k: dict(v) for k, v in _DEFAULTS.items()}
    try:
        section = None
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if not line or line.lstrip().startswith("#"): continue
                if line[0] not in (" ", "\t") and ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip(); val = val.strip()
                    if not val or val.startswith("#"):
                        section = key
                        if section not in cfg: cfg[section] = {}
                    else:
                        if section:
                            cfg[section][key] = _parse_val(val)
                elif line[:2] == "  " and section:
                    key, _, val = line.strip().partition(":")
                    key = key.strip()
                    if key and val:
                        cfg[section][key] = _parse_val(val)
    except FileNotFoundError:
        print(f"INFO: {path} not found → defaults", file=sys.stderr)
    return cfg

# ── Data loading ──────────────────────────────────────────────────────────────
def load_token_data(export_dir=None, min_rows=14):
    if export_dir is None: export_dir = EXPORT_DIR
    td = {}
    for fpath in sorted(pathlib.Path(export_dir).glob("freshwatch_daily_*.csv")):
        with open(fpath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sym = row.get("symbol", "")
                if not sym: continue
                def _f(k, r=row):
                    try: return float(r[k])
                    except: return NaN
                td.setdefault(sym, []).append({
                    "date": row.get("date", ""),
                    "px":   _f("px_avg"),
                    "pos":  _f("lsr_pos_r"),
                    "acc":  _f("lsr_acc_r"),
                    "oi":   _f("oi_usd"),
                    "fund": _f("funding_avg"),
                })
    for sym in td:
        td[sym].sort(key=lambda r: r["date"])
    return {s: v for s, v in td.items() if len(v) >= min_rows}

# ── Core math ─────────────────────────────────────────────────────────────────
def avg3(arr, i, field):
    vals = [arr[j][field] for j in range(max(0, i-2), i+1) if ok(arr[j][field])]
    return mean(vals) if vals else NaN

def calc_div(arr, i):
    a3p = avg3(arr, i, "pos"); a3a = avg3(arr, i, "acc")
    if not ok(a3p) or not ok(a3a) or a3a == 0: return NaN
    return a3p / a3a

# ── Episode detection ─────────────────────────────────────────────────────────
def detect_episodes(arr, cfg):
    """
    Returns list[dict] parallel to arr. Mỗi phần tử:
      in_hedge, episode_id, hedge_start_date, hedge_start_px (CỐ ĐỊNH), struct_n

    Gap tolerance: div > div_max liên tục <= gap_tol ngày → noise, in_hedge stays True.
    Episode break: div > div_max liên tục >= ep_break ngày → in_hedge = False.
    hedge_start_px SET MỘT LẦN khi episode bắt đầu, không tính lại.
    """
    div_max  = cfg["hedge"]["div_ratio_max"]
    ep_break = cfg["hedge"]["episode_break_days"]

    out = []
    ep_id = 0; ep_si = None; ep_spx = None
    in_hedge = False; n_above = 0

    for i, row in enumerate(arr):
        dr = calc_div(arr, i)

        if ok(dr) and dr <= div_max:
            if not in_hedge:            # new episode starts
                ep_id += 1
                ep_si  = i
                ep_spx = row["px"] if ok(row["px"]) else None
            in_hedge = True
            n_above  = 0
        else:                           # div > max or NaN
            if in_hedge:
                n_above += 1
                if n_above >= ep_break: # gap too long → episode ends
                    in_hedge = False
                    n_above  = 0

        sn = (i - ep_si + 1) if (in_hedge and ep_si is not None) else 0
        out.append({
            "in_hedge":        in_hedge,
            "episode_id":      ep_id if in_hedge else 0,
            "hedge_start_date": arr[ep_si]["date"] if (in_hedge and ep_si is not None) else "",
            "hedge_start_px":  ep_spx if in_hedge else None,
            "struct_n":        sn,
        })
    return out

# ── Trend calculations ─────────────────────────────────────────────────────────
def pos_trend(arr, i, thr):
    now = avg3(arr, i, "pos"); prev = avg3(arr, max(0, i-5), "pos")
    if not ok(now) or not ok(prev) or prev == 0: return "NaN"
    chg = (now - prev) / prev
    return "BẬT" if chg >= thr else ("GIẢM" if chg <= -thr else "PHẲNG")

def oi_trend(arr, i, thr, low_conf):
    raw = arr[i].get("oi", NaN)
    if not ok(raw) or raw < low_conf: return "LOW_CONF"
    now = avg3(arr, i, "oi"); prev = avg3(arr, max(0, i-5), "oi")
    if not ok(now) or not ok(prev) or prev == 0: return "NaN"
    chg = (now - prev) / prev
    return "TĂNG" if chg >= thr else ("GIẢM" if chg <= -thr else "PHẲNG")

_OI_NOTE = {
    "GIẢM":     "short cover thật (OI rút)",
    "TĂNG":     "long mới (không phải short rút)",
    "PHẲNG":    "",
    "LOW_CONF": "OI<$1M, bỏ qua",
    "NaN":      "OI NaN",
}

def div_5d_ago(arr, i):
    """div tại i-5, fallback i-4..i-2. NaN nếu không có giá trị hợp lệ."""
    for delta in range(5, 1, -1):
        j = i - delta
        if j < 0: continue
        dr = calc_div(arr, j)
        if ok(dr): return dr
    return NaN

# ── Snapshot ─────────────────────────────────────────────────────────────────
def snapshot(sym, arr, ep_data, i, cfg):
    pos_thr  = cfg["trends"]["pos_trend_threshold"]
    oi_thr   = cfg["trends"]["oi_trend_threshold"]
    low_conf = cfg["oi_guard"]["low_conf_usd"]
    ep = ep_data[i]
    dr = calc_div(arr, i)
    px = arr[i]["px"]
    d5 = div_5d_ago(arr, i)
    dd = (dr - d5) if (ok(dr) and ok(d5)) else NaN
    pt = pos_trend(arr, i, pos_thr)
    ot = oi_trend(arr, i, oi_thr, low_conf)
    spx = ep["hedge_start_px"]
    px_dist = (px - spx) / spx * 100 if (ok(px) and spx and ok(spx)) else NaN
    return {
        "sym": sym, "date": arr[i]["date"],
        "div_ratio": dr, "div_5d_ago": d5, "div_delta": dd,
        "struct_n": ep["struct_n"], "episode_id": ep["episode_id"],
        "in_hedge": ep["in_hedge"],
        "hedge_start_date": ep["hedge_start_date"],
        "hedge_start_px":  spx,
        "px_now": px, "px_dist": px_dist,
        "pos_trend": pt, "oi_trend": ot, "oi_note": _OI_NOTE.get(ot, ""),
        "lsr_pos": arr[i].get("pos", NaN),
        "lsr_acc": arr[i].get("acc", NaN),
        "fund": arr[i].get("fund", NaN),
    }

# ── Filters ───────────────────────────────────────────────────────────────────
def in_list_a(s, cfg):
    dr = s["div_ratio"]
    return ok(dr) and dr <= cfg["hedge"]["div_ratio_max"] and s["struct_n"] >= cfg["hedge"]["struct_n_min"]

def in_list_b(s, ep_data, i, cfg):
    recent = cfg["list_b"]["recent_hedge_days"]          # 2
    cond_a = any(ep_data[max(0, i-k)]["in_hedge"] for k in range(recent + 1))  # T, T-1, T-2
    cond_b = ok(s["div_delta"]) and s["div_delta"] > 0  # đang nới
    cond_c = s["pos_trend"] == "BẬT"                    # short rút
    return cond_a and cond_b and cond_c

# ── Run for a single date ─────────────────────────────────────────────────────
def run_date(target_date, token_data, cfg, ep_cache=None):
    """
    ep_cache: dict sym→ep_data (pre-computed). Nếu None sẽ tính lại per token.
    Returns (snaps_a, snaps_b).
    """
    snaps_a, snaps_b = [], []
    for sym, arr in token_data.items():
        ep = ep_cache[sym] if ep_cache else detect_episodes(arr, cfg)
        idx = next((i for i, r in enumerate(arr) if r["date"] == target_date), None)
        if idx is None: continue
        s = snapshot(sym, arr, ep, idx, cfg)
        if in_list_a(s, cfg):       snaps_a.append(s)
        if in_list_b(s, ep, idx, cfg): snaps_b.append(s)
    return snaps_a, snaps_b

# ── Formatters ────────────────────────────────────────────────────────────────
def _s(v, fmt, fb="?"):
    try: return format(v, fmt) if ok(v) else fb
    except: return fb

def format_output(snaps_a, snaps_b, date_str):
    lines = [
        f"WATCHLIST {date_str} — không phải tín hiệu, soi on-chain trước khi hành động",
        f"hedge_start_px = giá ngày đầu episode (CỐ ĐỊNH), không phải đỉnh/VWAP",
        "",
        f"=== LIST A — Hedge Tracker ({len(snaps_a)} tokens, div≤0.5 + struct_n≥5) ===",
        f"{'symbol':>18} {'div':>6} {'sn':>4} {'start':>12} {'start_px':>11} {'px_now':>11} {'dist%':>7} {'pos':>7} {'acc':>7} {'fund%':>8}",
        "─" * 98,
    ]
    for s in sorted(snaps_a, key=lambda x: x["div_ratio"] if ok(x["div_ratio"]) else 99):
        spx = f"{s['hedge_start_px']:.6f}" if s['hedge_start_px'] and ok(s['hedge_start_px']) else "?"
        fd  = f"{s['fund']*100:+.3f}%" if ok(s['fund']) else "?"
        lines.append(
            f"{s['sym']:>18} {_s(s['div_ratio'],'.3f'):>6} {s['struct_n']:>4} "
            f"{s['hedge_start_date']:>12} {spx:>11} {_s(s['px_now'],'.6f'):>11} "
            f"{_s(s['px_dist'],'+.1f')+'%':>7} "
            f"{_s(s['lsr_pos'],'.4f'):>7} {_s(s['lsr_acc'],'.4f'):>7} {fd:>8}"
        )
    lines += [
        "",
        f"=== LIST B — Cover Monitor ({len(snaps_b)} tokens, div nới + pos BẬT + vừa/đang hedge ≤2d) ===",
        f"div_delta > 0 = nới (short rút). Sort: div_delta DESC (nới mạnh nhất đầu).",
        f"{'symbol':>18} {'div_now':>7} {'div_5d':>7} {'delta':>7} {'pos_tr':>7} {'oi_tr':>8} "
        f"{'start':>12} {'start_px':>11} {'px_now':>11} {'fund%':>8}  oi_note",
        "─" * 118,
    ]
    for s in sorted(snaps_b, key=lambda x: -(x["div_delta"] if ok(x["div_delta"]) else -99)):
        spx = f"{s['hedge_start_px']:.6f}" if s['hedge_start_px'] and ok(s['hedge_start_px']) else "?"
        fd  = f"{s['fund']*100:+.3f}%" if ok(s['fund']) else "?"
        lines.append(
            f"{s['sym']:>18} {_s(s['div_ratio'],'.3f'):>7} {_s(s['div_5d_ago'],'.3f'):>7} "
            f"{_s(s['div_delta'],'+.3f'):>7} {s['pos_trend']:>7} {s['oi_trend']:>8} "
            f"{s['hedge_start_date']:>12} {spx:>11} {_s(s['px_now'],'.6f'):>11} {fd:>8}  {s['oi_note']}"
        )
    return "\n".join(lines)

# ── Telegram formatter — TOP 20 List A, full List B, slim columns ────────────
def format_output_tg(snaps_a, snaps_b, date_str, top_a=20):
    sorted_a = sorted(snaps_a, key=lambda x: x["div_ratio"] if ok(x["div_ratio"]) else 99)
    tg_a = sorted_a[:top_a]
    lines = [
        f"WATCHLIST {date_str} — không phải tín hiệu, soi on-chain trước khi hành động",
        f"hedge_start_px = giá ngày đầu episode (CỐ ĐỊNH)",
        "",
        f"=== LIST A — TOP {len(tg_a)}/{len(snaps_a)} (div thấp nhất = hedge mạnh nhất) ===",
        f"{'sym':>16} {'div':>6} {'sn':>4} {'start':>12} {'dist%':>7} {'fund%':>8}",
        "─" * 62,
    ]
    for s in tg_a:
        fd = f"{s['fund']*100:+.3f}%" if ok(s["fund"]) else "?"
        lines.append(
            f"{s['sym']:>16} {_s(s['div_ratio'],'.3f'):>6} {s['struct_n']:>4} "
            f"{s['hedge_start_date']:>12} {_s(s['px_dist'],'+.1f')+'%':>7} {fd:>8}"
        )
    lines += [
        "",
        f"=== LIST B — Cover Monitor ({len(snaps_b)} tokens) ===",
        "div_delta>0 + pos BẬT + hedge ≤2d trước. Sort: delta DESC.",
        f"{'sym':>16} {'div':>6} {'Δdiv':>7} {'pos':>7} {'oi':>8} {'start':>12}  note",
        "─" * 78,
    ]
    for s in sorted(snaps_b, key=lambda x: -(x["div_delta"] if ok(x["div_delta"]) else -99)):
        lines.append(
            f"{s['sym']:>16} {_s(s['div_ratio'],'.3f'):>6} {_s(s['div_delta'],'+.3f'):>7} "
            f"{s['pos_trend']:>7} {s['oi_trend']:>8} {s['hedge_start_date']:>12}  {s['oi_note']}"
        )
    return "\n".join(lines)


# ── CSV log ───────────────────────────────────────────────────────────────────
_CSV_FIELDS = [
    "run_date", "symbol", "list", "div_ratio", "div_5d_ago", "div_delta",
    "struct_n", "episode_id", "hedge_start_date", "hedge_start_px",
    "px_now", "px_dist_pct", "pos_trend", "oi_trend", "oi_note", "funding_pct",
]

def append_csv(snaps_a, snaps_b, run_date_str, cfg):
    ym = run_date_str[:7]
    p  = REPO_ROOT / cfg["output"]["csv_path"].replace("{YYYY-MM}", ym)
    p.parent.mkdir(parents=True, exist_ok=True)
    is_new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        if is_new: w.writeheader()
        def _row(s, lst):
            spx = s["hedge_start_px"]
            fd  = s["fund"] * 100 if ok(s["fund"]) else NaN
            return {
                "run_date": run_date_str, "symbol": s["sym"], "list": lst,
                "div_ratio":  _s(s["div_ratio"],  ".4f"),
                "div_5d_ago": _s(s["div_5d_ago"], ".4f"),
                "div_delta":  _s(s["div_delta"],  "+.4f"),
                "struct_n": s["struct_n"], "episode_id": s["episode_id"],
                "hedge_start_date": s["hedge_start_date"],
                "hedge_start_px":  f"{spx:.6f}" if spx and ok(spx) else "",
                "px_now":      _s(s["px_now"], ".6f"),
                "px_dist_pct": _s(s["px_dist"], "+.2f"),
                "pos_trend": s["pos_trend"], "oi_trend": s["oi_trend"],
                "oi_note":   s["oi_note"],
                "funding_pct": _s(fd, "+.4f"),
            }
        for s in snaps_a: w.writerow(_row(s, "A"))
        for s in snaps_b: w.writerow(_row(s, "B"))

def send_telegram(text: str) -> bool:
    """Send Telegram message using same credentials as GOM Daily (.env)."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("WARN: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skip send",
              file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    ok_all = True
    for chunk in chunks:
        payload = urllib.parse.urlencode(
            {"chat_id": TG_CHAT_ID, "text": chunk}
        ).encode("utf-8")
        try:
            req = urllib.request.Request(url, payload)
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status != 200:
                    print(f"WARN: Telegram HTTP {r.status}", file=sys.stderr)
                    ok_all = False
        except Exception as e:
            print(f"WARN: Telegram send failed: {e}", file=sys.stderr)
            ok_all = False
    return ok_all

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Watchlist daily v1.3")
    ap.add_argument("--date", help="YYYY-MM-DD (default: latest in store)")
    ap.add_argument("--no-telegram", action="store_true", default=False)
    args = ap.parse_args()

    cfg = load_config()
    td  = load_token_data(EXPORT_DIR, cfg["data"]["min_history_rows"])
    if not td:
        print("ERROR: no token data.", file=sys.stderr); sys.exit(1)

    target = args.date or max(r["date"] for arr in td.values() for r in arr)
    print(f"INFO: target_date={target}  tokens={len(td)}", file=sys.stderr)

    # Pre-compute episode detection once for all tokens
    ep_cache = {sym: detect_episodes(arr, cfg) for sym, arr in td.items()}

    snaps_a, snaps_b = run_date(target, td, cfg, ep_cache)
    out = format_output(snaps_a, snaps_b, target)
    print(out)

    if cfg["output"]["log_csv"]:
        append_csv(snaps_a, snaps_b, target, cfg)
    if not args.no_telegram:
        tg_out = format_output_tg(snaps_a, snaps_b, target)
        ok_tg = send_telegram(tg_out)
        print(f"INFO: Telegram {'OK' if ok_tg else 'FAIL'}", file=sys.stderr)

if __name__ == "__main__":
    main()
