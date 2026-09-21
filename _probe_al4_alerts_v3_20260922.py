"""AL4 · bản gọn v3 · master label ngắn thay chuỗi ngày dài.

Nhãn master ngắn (thay chuỗi ngày):
  · `master: CONFIRMED`  — nếu btier CONFIRMED state ±3d
  · `master: CROSS L1`    — nếu btier CROSS state ±3d (đã pass L1)
  · `class-L1 dd/mm`      — nếu class event ±3d
  · `u1-PASS dd/mm`       — nếu u1 event ±3d
  · `chuông <first>-<last>` — nếu bell events, gộp thành date range
"""
import sys, os, csv, subprocess
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

CSV_ALERTS = REPO / "data/logs/gom_e_t1_alerts.csv"
KLINES_1H = REPO / "data/raw/klines_1h"

# Load fires 09-09..09-20
fires = []
with CSV_ALERTS.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["fire"] != "True" or row["cooldown_blocked"] == "True": continue
        d = row["date"]
        if not ("2026-09-09" <= d <= "2026-09-20"): continue
        fires.append({"date": d, "sym": row["symbol"]})
seen = set(); uniq = []
for f in fires:
    k = (f["date"], f["sym"])
    if k in seen: continue
    seen.add(k); uniq.append(f)

# Load perp OHLC
_ohlc_cache = {}
def _load_daily_ohlc(sym, d_start_iso, d_end_iso):
    key = (sym, d_start_iso, d_end_iso)
    if key in _ohlc_cache: return _ohlc_cache[key]
    import pandas as pd
    d_start = datetime.strptime(d_start_iso, "%Y-%m-%d").date()
    d_end = datetime.strptime(d_end_iso, "%Y-%m-%d").date()
    out = {}
    for k in range((d_end - d_start).days + 1):
        d = d_start + timedelta(days=k)
        p = KLINES_1H / f"date={d.isoformat()}" / "part-0.parquet"
        if not p.exists(): continue
        try:
            df = pd.read_parquet(p, columns=["symbol", "open", "high", "low", "close"])
            r = df[df["symbol"] == sym]
            if r.empty: continue
            out[d.isoformat()] = (float(r.iloc[0]["open"]), float(r["high"].max()),
                                   float(r["low"].min()), float(r.iloc[-1]["close"]))
        except Exception: continue
    _ohlc_cache[key] = out
    return out

# Load master signals from events_build for 09-06..09-20
master_signals = {}
def _run_events(target):
    from events_build import build_events
    rows, _ = build_events(target)
    for r in rows:
        tok = r["tok"]
        kind = r["kind"]; t = r["type"]
        key = (target, tok)
        if kind == "event" and t == "bell":
            master_signals.setdefault(key, []).append(("bell", None))
        elif kind == "event" and t == "class" and r.get("tier") == "L1":
            master_signals.setdefault(key, []).append(("class-L1", r.get("d_cross")))
        elif kind == "event" and t == "u1" and r.get("verdict") == "PASS":
            master_signals.setdefault(key, []).append(("u1-PASS", r.get("d_cross")))
        elif kind == "state" and t == "btier" and r.get("tier") in ("CONFIRMED", "CROSS"):
            master_signals.setdefault(key, []).append(("btier-" + r["tier"], r.get("k")))

_d_start = datetime(2026, 9, 6).date()
_d_end = datetime(2026, 9, 20).date()
for k in range((_d_end - _d_start).days + 1):
    d = (_d_start + timedelta(days=k)).isoformat()
    try:
        _run_events(d)
    except Exception as e:
        print(f"[warn] {d}: {e}", file=sys.stderr)

def _bare(s): return s[:-4] if s.endswith("USDT") else s
def _fmt(x): return f"{x*100:+.0f}%" if x is not None else "-"

def _master_label(sym: str, fire_dates: list) -> str:
    """Aggregate master signals within ±3d of any fire · trả short label."""
    bare = _bare(sym)
    bell_dates = []; has_confirmed = False; has_cross = False
    class_dates = []; u1_dates = []
    for fd in fire_dates:
        fd_d = datetime.strptime(fd, "%Y-%m-%d").date()
        for k in range(-3, 4):
            d = (fd_d + timedelta(days=k)).isoformat()
            for sig_type, _ in master_signals.get((d, bare), []):
                if sig_type == "bell":
                    if d not in bell_dates: bell_dates.append(d)
                elif sig_type == "btier-CONFIRMED":
                    has_confirmed = True
                elif sig_type == "btier-CROSS":
                    has_cross = True
                elif sig_type == "class-L1":
                    if d not in class_dates: class_dates.append(d)
                elif sig_type == "u1-PASS":
                    if d not in u1_dates: u1_dates.append(d)
    labels = []
    if has_confirmed: labels.append("master: CONFIRMED")
    elif has_cross: labels.append("master: CROSS L1")
    if class_dates and not has_confirmed and not has_cross:
        labels.append(f"class-L1 {class_dates[0][5:]}")
    if u1_dates and not has_confirmed:
        labels.append(f"u1-PASS {u1_dates[0][5:]}")
    if bell_dates:
        first, last = sorted(bell_dates)[0][5:], sorted(bell_dates)[-1][5:]
        labels.append(f"chuông {first}" if first == last else f"chuông {first}-{last}")
    return " · ".join(labels)

# Compute per token
by_token = {}
for x in uniq:
    by_token.setdefault(x["sym"], []).append(x)

d_now = "2026-09-20"
tok_data = {}
for tok, entries in by_token.items():
    fires_sorted = sorted(set(x["date"] for x in entries))
    label = _master_label(tok, fires_sorted)
    anchor = fires_sorted[0]
    ohlc = _load_daily_ohlc(tok, anchor, d_now)
    if anchor not in ohlc:
        tok_data[tok] = {"fires": fires_sorted, "label": label, "ret_max": None,
                         "ret_now": None, "dd": None, "days": None}
        continue
    close_anchor = ohlc[anchor][3]
    if close_anchor <= 0:
        tok_data[tok] = {"fires": fires_sorted, "label": label, "ret_max": None,
                         "ret_now": None, "dd": None, "days": None}
        continue
    ret_max = 0.0; dd = 0.0; ret_now = 0.0
    anchor_d = datetime.strptime(anchor, "%Y-%m-%d").date()
    now_d = datetime.strptime(d_now, "%Y-%m-%d").date()
    for k in range(1, (now_d - anchor_d).days + 1):
        d = (anchor_d + timedelta(days=k)).isoformat()
        if d not in ohlc: continue
        _, high_d, low_d, close_d = ohlc[d]
        r_high = high_d / close_anchor - 1
        r_low = low_d / close_anchor - 1
        r_close = close_d / close_anchor - 1
        if r_high > ret_max: ret_max = r_high
        if r_low < dd: dd = r_low
        ret_now = r_close
    tok_data[tok] = {"fires": fires_sorted, "label": label, "ret_max": ret_max,
                     "ret_now": ret_now, "dd": dd, "days": (now_d - anchor_d).days}

# 3 groups
g1 = {k: v for k, v in tok_data.items() if v["label"]}
g2 = {k: v for k, v in tok_data.items() if len(v["fires"]) >= 2 and k not in g1}
g3 = {k: v for k, v in tok_data.items() if k not in g1 and k not in g2}

def _fdlist(dates): return "·".join(d[5:] for d in dates)

# Build
lines = []
lines.append("[GỬI TAY · bản gọn v3 · 28 cảnh báo GOM-E · master label ngắn · mới 1-12d]")
lines.append("PERP 1h OHLC · neo lần kêu đầu · đỉnh(high) · nay(close 20/09) · dd(low)")
lines.append("")

def _line(tok, v, show_label=True):
    fires = _fdlist(v["fires"])
    if v["ret_max"] is None:
        return f" {_bare(tok)} kêu {fires} · [no perp klines]"
    body = f" {_bare(tok)} kêu {fires} · đỉnh {_fmt(v['ret_max'])} nay {_fmt(v['ret_now'])} dd {_fmt(v['dd'])} · {v['days']}d"
    if show_label and v["label"]:
        body += f" · [{v['label']}]"
    return body

if g1:
    lines.append(f"★ Trùng master ({len(g1)})")
    for tok in sorted(g1.keys(), key=lambda k: -(g1[k]["ret_max"] if g1[k]["ret_max"] is not None else -999)):
        lines.append(_line(tok, g1[tok]))
    lines.append("")

if g2:
    lines.append(f"🔁 Kêu ≥2 lần ({len(g2)})")
    for tok in sorted(g2.keys(), key=lambda k: -(g2[k]["ret_max"] if g2[k]["ret_max"] is not None else -999)):
        lines.append(_line(tok, g2[tok], show_label=False))
    lines.append("")

if g3:
    g3_sorted = sorted(g3.items(), key=lambda kv: -(kv[1]["ret_max"] if kv[1]["ret_max"] is not None else -999))
    parts = [f"{_bare(k)} đỉnh {_fmt(v['ret_max'])} nay {_fmt(v['ret_now'])}/{v['days']}d" for k, v in g3_sorted]
    lines.append(f"Còn lại ({len(g3)}): " + " · ".join(parts))

print("\n".join(lines))
