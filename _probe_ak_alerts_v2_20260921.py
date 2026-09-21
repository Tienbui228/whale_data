"""AK · bản gọn v2 · master ĐỦ + perp klines + đỉnh/hiện tại/dd."""
import sys, os, csv, json, tempfile, subprocess
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

CSV_ALERTS = REPO / "data/logs/gom_e_t1_alerts.csv"
KLINES_1H = REPO / "data/raw/klines_1h"

# ── Load fires 09-09..09-20 ──
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


# ── Perp klines_1h → daily OHLC per sym ──
_ohlc_cache = {}
def _load_daily_ohlc(sym: str, d_start_iso: str, d_end_iso: str) -> dict:
    """Trả {date_iso: (open,high,low,close)} bằng aggregate 1h klines."""
    cache_key = (sym, d_start_iso, d_end_iso)
    if cache_key in _ohlc_cache:
        return _ohlc_cache[cache_key]
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
            out[d.isoformat()] = (
                float(r.iloc[0]["open"]),
                float(r["high"].max()),
                float(r["low"].min()),
                float(r.iloc[-1]["close"]),
            )
        except Exception:
            continue
    _ohlc_cache[cache_key] = out
    return out


# ── AK1 · Chạy events_build cho từng ngày 09-06..09-20 vào tmp ──
tmp_events = Path(tempfile.mkdtemp(prefix="ak_events_"))
master_signals = {}   # (date, tok) → list of (type, value)
def _run_events_build(target: str):
    import sys as _sys
    if str(REPO / "scripts") not in _sys.path:
        _sys.path.insert(0, str(REPO / "scripts"))
    from events_build import build_events
    rows, _ = build_events(target)
    for r in rows:
        tok = r["tok"]
        t = r["type"]
        key = (target, tok)
        # Only significant signal types
        if t == "bell":
            master_signals.setdefault(key, []).append(("bell", r.get("dacc_bwd")))
        elif t == "class" and r.get("tier") == "L1":
            master_signals.setdefault(key, []).append(("class-L1", r.get("dacc")))
        elif t == "u1" and r.get("verdict") == "PASS":
            master_signals.setdefault(key, []).append(("u1-pass", (r.get("v1"), r.get("v2"))))
        elif t == "btier" and r.get("tier") in ("CONFIRMED", "CROSS"):
            master_signals.setdefault(key, []).append(("btier-" + r["tier"], r.get("k")))

_d_start = datetime(2026, 9, 6).date()
_d_end = datetime(2026, 9, 20).date()
for k in range((_d_end - _d_start).days + 1):
    d = (_d_start + timedelta(days=k)).isoformat()
    try:
        _run_events_build(d)
    except Exception as e:
        print(f"[warn] events_build {d} FAIL: {e}", file=sys.stderr)


# ── Gom fire theo token ──
by_token = {}
for x in uniq:
    by_token.setdefault(x["sym"], []).append(x)

def _bare(s): return s[:-4] if s.endswith("USDT") else s
def _fmt(x): return f"{x*100:+.0f}%" if x is not None else "-"


# ── Compute per token · neo LẦN KÊU ĐẦU · in đỉnh + hiện tại + dd ──
tok_data = {}
d_now = "2026-09-20"   # data cuối freshwatch/klines
for tok, entries in by_token.items():
    fires_sorted = sorted(set(x["date"] for x in entries))
    anchor = fires_sorted[0]

    # ── AK1 · master trùng ±3d quanh bất kỳ fire date ──
    bare = _bare(tok)
    hits = []
    for fd in fires_sorted:
        fd_d = datetime.strptime(fd, "%Y-%m-%d").date()
        for k in range(-3, 4):
            d = (fd_d + timedelta(days=k)).isoformat()
            sigs = master_signals.get((d, bare), [])
            for sig_type, val in sigs:
                hits.append((d, sig_type))
    hits = list(dict.fromkeys(hits))

    # ── AK3 · perp klines OHLC · anchor close ──
    ohlc = _load_daily_ohlc(tok, anchor, d_now)
    if anchor not in ohlc:
        tok_data[tok] = {"fires": fires_sorted, "master": hits, "ret_max": None,
                         "ret_now": None, "dd": None, "days": None, "note": "no perp klines"}
        continue
    close_anchor = ohlc[anchor][3]
    if close_anchor <= 0:
        tok_data[tok] = {"fires": fires_sorted, "master": hits, "ret_max": None,
                         "ret_now": None, "dd": None, "days": None, "note": "anchor close=0"}
        continue
    ret_max = 0.0; dd = 0.0; ret_now = None; last_close = close_anchor
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
        last_close = close_d
        ret_now = r_close
    if ret_now is None:
        ret_now = 0.0  # anchor day only
    tok_data[tok] = {
        "fires": fires_sorted, "master": hits,
        "ret_max": ret_max, "ret_now": ret_now, "dd": dd,
        "days": (now_d - anchor_d).days,
        "note": "",
    }


# ── Build compact body ──
lines = []
lines.append("[GỬI TAY · bản gọn v2 · 28 cảnh báo GOM-E · gộp theo token · mới 1-12d]")
lines.append("PERP 1h klines → daily OHLC · neo lần kêu đầu · đỉnh (high) · hiện tại (close 20/09) · dd (low)")
lines.append("")

# Group 1 ★ master hits
g1 = {k: v for k, v in tok_data.items() if v["master"]}
g2 = {k: v for k, v in tok_data.items() if len(v["fires"]) >= 2 and k not in g1}
g3 = {k: v for k, v in tok_data.items() if k not in g1 and k not in g2}

def _fdlist(dates): return "·".join(d[5:] for d in dates)

def _line(tok, v, show_master=False):
    fires = _fdlist(v["fires"])
    if v["ret_max"] is None:
        return f" {_bare(tok)} kêu {fires} · [{v['note']}]"
    base = f" {_bare(tok)} kêu {fires} · đỉnh {_fmt(v['ret_max'])} nay {_fmt(v['ret_now'])} dd {_fmt(v['dd'])} · {v['days']}d"
    if show_master and v["master"]:
        mh = "·".join(f"{d[5:]} {t}" for d, t in v["master"][:6])
        base += f" · [{mh}]"
    return base

if g1:
    lines.append(f"★ Trùng master ({len(g1)})")
    for tok in sorted(g1.keys(), key=lambda k: -(g1[k]["ret_max"] if g1[k]["ret_max"] is not None else -999)):
        lines.append(_line(tok, g1[tok], show_master=True))
    lines.append("")

if g2:
    lines.append(f"🔁 Kêu ≥2 lần ({len(g2)})")
    for tok in sorted(g2.keys(), key=lambda k: -(g2[k]["ret_max"] if g2[k]["ret_max"] is not None else -999)):
        lines.append(_line(tok, g2[tok]))
    lines.append("")

if g3:
    g3_sorted = sorted(g3.items(), key=lambda kv: -(kv[1]["ret_max"] if kv[1]["ret_max"] is not None else -999))
    parts = []
    for k, v in g3_sorted:
        if v["ret_max"] is None:
            parts.append(f"{_bare(k)} N/A")
        else:
            parts.append(f"{_bare(k)} đỉnh {_fmt(v['ret_max'])} nay {_fmt(v['ret_now'])}/{v['days']}d")
    lines.append(f"Còn lại ({len(g3)}): " + " · ".join(parts))

print("\n".join(lines))
