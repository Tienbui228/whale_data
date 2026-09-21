"""AJ · làm lại tin 28 cảnh báo · perp price · gom theo token · 3 nhóm."""
import sys, os, csv, json
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

CSV_ALERTS = REPO / "data/logs/gom_e_t1_alerts.csv"
FW_CSV = REPO / "data/export/freshwatch_daily_2026-09.csv"
BELL_AUDIT = REPO / "data/logs/u0_bell_audit.jsonl"

# Last date with data in freshwatch (thay TODAY khi 21/09 chưa export)
TODAY = "2026-09-20"

# ── Load fires 09-09..09-20 ──
fires = []
with CSV_ALERTS.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["fire"] != "True" or row["cooldown_blocked"] == "True": continue
        d = row["date"]
        if not ("2026-09-09" <= d <= "2026-09-20"): continue
        fires.append({"date": d, "sym": row["symbol"], "tags": row["tags"]})
# Dedupe (date, sym)
seen = set(); uniq = []
for f in fires:
    k = (f["date"], f["sym"])
    if k in seen: continue
    seen.add(k); uniq.append(f)

# ── Load freshwatch px_avg per (date, sym) ──
px_map = {}
with FW_CSV.open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            px_map[(row["date"], row["symbol"])] = float(row["px_avg"])
        except Exception:
            pass

def _ret_dd(sym: str, fire_date: str) -> tuple:
    """Trả (ret_max_pct, dd_max_pct, days_elapsed, note) dùng perp px_avg.
    Nếu fire_date >= TODAY (data cuối) → ret=0/dd=0/days=0/note='cùng ngày data cuối'."""
    close_fire = px_map.get((fire_date, sym))
    if close_fire is None or close_fire <= 0:
        return (None, None, None, "px_avg thiếu tại ngày kêu")
    fd = datetime.strptime(fire_date, "%Y-%m-%d").date()
    td = datetime.strptime(TODAY, "%Y-%m-%d").date()
    if fd >= td:
        return (0.0, 0.0, 0, "cùng ngày data cuối · chưa đủ 1d")
    ret_max = 0.0; dd = 0.0   # anchor: ret vs close_fire · nếu không có forward data → 0
    n_dp = 0
    for k in range(1, (td - fd).days + 1):
        d = (fd + timedelta(days=k)).isoformat()
        px = px_map.get((d, sym))
        if px is None: continue
        n_dp += 1
        r = px / close_fire - 1
        if r > ret_max: ret_max = r
        if r < dd: dd = r
    days = (td - fd).days
    note = "" if n_dp > 0 else "không data forward"
    return (ret_max, dd, days, note)

# ── Gom theo token ──
by_token = {}
for x in uniq:
    by_token.setdefault(x["sym"], []).append(x)

# ── Load master events cho ±3 ngày quanh mỗi fire ──
# U0-BELL: audit jsonl
bell_by_key = {}   # (date, tok) → dacc
if BELL_AUDIT.exists():
    for line in BELL_AUDIT.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            if e.get("tier") == "bell":
                bell_by_key[(e["target"], e["token"])] = e.get("dacc_bwd")
        except: pass  # L-66-OK

# B-tier: only current (target=today) is easy; historical needs replay. Skip for simplicity.
# Use bell only for master trùng · flag if bell ±3 days of any fire.
def _master_hits(sym: str, fire_dates: list) -> list:
    """Trả list dates (bell) trong ±3 ngày quanh mọi fire date của sym."""
    hits = []
    bare = sym[:-4] if sym.endswith("USDT") else sym
    for fd in fire_dates:
        fd_d = datetime.strptime(fd, "%Y-%m-%d").date()
        for k in range(-3, 4):
            d = (fd_d + timedelta(days=k)).isoformat()
            if (d, bare) in bell_by_key:
                hits.append((d, "bell", bell_by_key[(d, bare)]))
    return list(dict.fromkeys([(h[0], h[1]) for h in hits]))   # unique preserve order

# ── Build compact body ──
lines = []
lines.append("[GỬI TAY · 28 cảnh báo GOM-E · gộp theo token · mới 1-12 ngày]")
lines.append(f"PERP px_avg · ret từ ngày kêu tới {TODAY} · dd tối đa · d = ngày đã qua")
lines.append("")

# Compute for each token
tok_data = {}
skipped = []
for tok, entries in by_token.items():
    fire_dates = sorted(set(x["date"] for x in entries))
    r_e, dd_e, d_e, note = _ret_dd(tok, fire_dates[0])
    if r_e is None:
        skipped.append((tok, fire_dates, note or "px_avg không tìm được"))
        continue
    tok_data[tok] = {
        "fires": fire_dates,
        "ret": r_e,
        "dd": dd_e,
        "days": d_e,
        "note": note,
        "master_hits": _master_hits(tok, fire_dates),
    }

# Group 1: ★ Trùng master (bell ±3d)
g1 = {k: v for k, v in tok_data.items() if v["master_hits"]}
# Group 2: 🔁 Kêu ≥2 lần (không thuộc g1)
g2 = {k: v for k, v in tok_data.items() if len(v["fires"]) >= 2 and k not in g1}
# Group 3: còn lại, sort ret DESC
g3 = {k: v for k, v in tok_data.items() if k not in g1 and k not in g2}

def _fmt_pct(x): return f"{x*100:+.0f}%" if x is not None else "-"
def _bare(s): return s[:-4] if s.endswith("USDT") else s
def _fdlist(dates): return "·".join(d[5:] for d in dates)   # MM-DD

# Group 1
if g1:
    lines.append(f"★ Trùng master ({len(g1)})")
    for tok in sorted(g1.keys(), key=lambda k: -g1[k]["ret"]):
        v = g1[tok]
        mh = " · ".join(f"bell {d[5:]}" for d, _ in v["master_hits"])
        lines.append(f" {_bare(tok)} kêu {_fdlist(v['fires'])} · ret {_fmt_pct(v['ret'])} dd {_fmt_pct(v['dd'])} · {v['days']}d · [{mh}]")
    lines.append("")

# Group 2
if g2:
    lines.append(f"🔁 Kêu ≥2 lần ({len(g2)})")
    for tok in sorted(g2.keys(), key=lambda k: -g2[k]["ret"]):
        v = g2[tok]
        lines.append(f" {_bare(tok)} kêu {_fdlist(v['fires'])} · ret {_fmt_pct(v['ret'])} dd {_fmt_pct(v['dd'])} · {v['days']}d")
    lines.append("")

# Group 3 · 1 dòng gộp
if g3:
    g3_sorted = sorted(g3.items(), key=lambda kv: -kv[1]["ret"])
    parts = [f"{_bare(k)} {_fmt_pct(v['ret'])}/{v['days']}d" for k, v in g3_sorted]
    lines.append(f"Còn lại ({len(g3)}): " + " · ".join(parts))
    lines.append("")

# Skipped
if skipped:
    lines.append(f"[Không đo được ({len(skipped)}, alpha-only hoặc thiếu freshwatch): {', '.join(_bare(t) for t,_,_ in skipped)}]")

# Audit tags (below body · in stderr only for reference)
print("\n".join(lines))
