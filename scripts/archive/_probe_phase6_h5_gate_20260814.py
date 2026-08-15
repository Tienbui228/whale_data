"""
PHASE 6 — Gate §H5 backtest: h1-h4 build vs baseline vs negative.

Provenance:
  data-source : /root/Data_back_test/whale_data/data/raw/klines_1h + oi_hist_1h
                (VPS canonical store)
  machine     : VPS 5.223.67.21
  date-range  : per-case windows khai trong POSITIVES / NEGATIVES / NEG_WINDOWS
  code-commit : scripts/compute_h_daily.py @ VPS HEAD

Windows:
  BANK  build   2026-06-29→2026-07-14  baseline 2026-06-08→2026-06-28
  TUT   build   2026-06-26→2026-07-12  baseline 2026-06-05→2026-06-25
  AKE   build   2026-06-26→2026-07-07  NO BASELINE (store starts Jun26)
  CYS   build   2026-07-20→2026-08-06  baseline 2026-06-29→2026-07-19
        [CYS build = 2w accumulation trước GOM-C C5 fire 08-07 — xác định từ data]
  BANANAS31 negative 2026-07-01→2026-07-20  [serial pump / crowd-nuôi]
  APR       negative 2026-07-01→2026-08-04  [range thật / im thật]
  XPIN      negative 2026-07-31→2026-08-07  [crowd-giả-gom / markup book mỏng — adversarial]

PASS §H5: ≥1 metric tách build khỏi CẢ [baseline] VÀ [negative] (không-chồng-IQR)
  trên ≥3/4 positive case, VÀ nhất-quán-dấu trên mọi case pass.
  AKE (no baseline): tách negative coi là thỏa điều kiện baseline (ghi rõ).
  3/4 với dấu lẫn lộn = FAIL.

Run on VPS: python3 _probe_phase6_h5_gate_20260814.py
"""

import sys, math, json, io
from pathlib import Path
from datetime import date, timedelta

import pandas as pd

REPO = Path("/root/Data_back_test/whale_data")
RAW  = REPO / "data" / "raw"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts.compute_h_daily import compute_symbol, BOOK_THIN_FRAC, H1_MIN_HOURS

NaN = float("nan")


def ok(x):
    try:
        return x == x and not math.isinf(float(x))
    except Exception:
        return False


def fp_s(v, fmt=".4f"):
    return format(float(v), fmt) if ok(v) else "NaN "


# ── Funding intervals ─────────────────────────────────────────────────────────────
funding: dict = {}
_fp = REPO / "data" / "config" / "funding_intervals.json"
if _fp.exists():
    with open(_fp) as _f:
        funding = json.load(_f)

# ── Parquet cache (per dt, all symbols) ──────────────────────────────────────────
_klines_cache: dict[str, pd.DataFrame] = {}
_oi_cache: dict[str, pd.DataFrame] = {}


def _get_klines_df(dt: str) -> pd.DataFrame:
    if dt not in _klines_cache:
        pq = RAW / "klines_1h" / f"date={dt}" / "part-0.parquet"
        if not pq.exists():
            _klines_cache[dt] = pd.DataFrame()
        else:
            df = pd.read_parquet(pq)
            df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
            _klines_cache[dt] = df.sort_values(["symbol", "as_of_ts_ms"]).reset_index(drop=True)
    return _klines_cache[dt]


def _get_oi_df(dt: str) -> pd.DataFrame:
    if dt not in _oi_cache:
        pq = RAW / "oi_hist_1h" / f"date={dt}" / "part-0.parquet"
        if not pq.exists():
            _oi_cache[dt] = pd.DataFrame()
        else:
            df = pd.read_parquet(pq)
            df = df.drop_duplicates(subset=["symbol", "as_of_ts_ms"], keep="first")
            _oi_cache[dt] = df.sort_values(["symbol", "as_of_ts_ms"]).reset_index(drop=True)
    return _oi_cache[dt]


def load_klines_sym(dt: str, sym: str) -> pd.DataFrame:
    df = _get_klines_df(dt)
    if df.empty:
        return df
    return df[df["symbol"] == sym].copy()


def load_oi_sym(dt: str, sym: str) -> pd.DataFrame:
    """Direct OI load — NOT watchlist-gated (Phase 6 h2 rule: historical gate reads store)."""
    df = _get_oi_df(dt)
    if df.empty:
        return df
    return df[df["symbol"] == sym].copy()


def range_med14_sym(target_dt: str, sym: str) -> float:
    """Median hourly range over 14 days before target_dt (Δ7 guard). Uses klines cache."""
    target = date.fromisoformat(target_dt)
    vals: list[float] = []
    for delta in range(1, 15):
        dt_str = (target - timedelta(days=delta)).isoformat()
        df = _get_klines_df(dt_str)
        if df.empty:
            continue
        sub = df[df["symbol"] == sym]
        rng = (sub["high"] - sub["low"]).dropna()
        vals.extend(rng[rng > 0].tolist())
    return float(pd.Series(vals).median()) if vals else NaN


# ── Window compute ────────────────────────────────────────────────────────────────

def compute_window(sym: str, date_start: str, date_end: str) -> list[dict]:
    """Compute h1-h4 for each day in [date_start, date_end]. Returns list of day dicts."""
    d   = date.fromisoformat(date_start)
    end = date.fromisoformat(date_end)
    rows = []
    while d <= end:
        dt = d.isoformat()
        sk = load_klines_sym(dt, sym)
        if sk.empty:
            d += timedelta(days=1)
            continue
        so    = load_oi_sym(dt, sym)
        med14 = range_med14_sym(dt, sym)
        iv_h  = funding.get(sym, 8)
        res   = compute_symbol(sym, sk, so, iv_h, med14, in_wl=True)
        res["date"] = dt
        rows.append(res)
        d += timedelta(days=1)
    return rows


def wstats(rows: list[dict], key: str) -> dict:
    vals = [float(r[key]) for r in rows if ok(r.get(key, NaN))]
    if not vals:
        return {"n": 0, "med": NaN, "q1": NaN, "q3": NaN}
    s = pd.Series(vals)
    return {
        "n":   len(vals),
        "med": float(s.median()),
        "q1":  float(s.quantile(0.25)),
        "q3":  float(s.quantile(0.75)),
    }


def iqr_sep(a: dict, b: dict) -> bool | None:
    """True = IQRs do NOT overlap (separated). None = unknown (NaN boundary)."""
    if not (ok(a["q1"]) and ok(a["q3"]) and ok(b["q1"]) and ok(b["q3"])):
        return None
    return not (a["q1"] <= b["q3"] and b["q1"] <= a["q3"])


# ── Case definitions ──────────────────────────────────────────────────────────────

POSITIVES = [
    {
        "sym": "BANKUSDT", "label": "BANK",
        "build":    ("2026-06-29", "2026-07-14"),
        "baseline": ("2026-06-08", "2026-06-28"),
    },
    {
        "sym": "TUTUSDT", "label": "TUT",
        "build":    ("2026-06-26", "2026-07-12"),
        "baseline": ("2026-06-05", "2026-06-25"),
    },
    {
        "sym": "AKEUSDT", "label": "AKE",
        "build":    ("2026-06-26", "2026-07-07"),
        "baseline": None,  # NO BASELINE — store starts Jun26
    },
    {
        "sym": "CYSUSDT", "label": "CYS",
        "build":    ("2026-07-20", "2026-08-06"),
        "baseline": ("2026-06-29", "2026-07-19"),
    },
]

NEGATIVES = [
    {"sym": "BANANAS31USDT", "label": "BANANAS31", "start": "2026-07-01", "end": "2026-07-20"},
    {"sym": "APRUSDT",       "label": "APR",        "start": "2026-07-01", "end": "2026-08-04"},
    {"sym": "XPINUSDT",      "label": "XPIN",       "start": "2026-07-31", "end": "2026-08-07"},
]

METRICS     = ["h1", "h2", "h3", "h4"]
METRIC_KEYS = {"h1": "h1_skew", "h2": "h2_oiw", "h3": "h3_conc", "h4": "h4_cloc"}

# ── Run ───────────────────────────────────────────────────────────────────────────

buf = io.StringIO()
def P(*a, **kw): print(*a, **kw, file=buf)

P("=" * 100)
P("PHASE 6 — Gate §H5 backtest: h1-h4 build vs baseline vs negative")
P("=" * 100)
P()
P("PROVENANCE")
P(f"  data-source : {RAW}  (VPS canonical klines_1h + oi_hist_1h)")
P(f"  machine     : VPS 5.223.67.21")
P(f"  date-range  : per-case; see POSITIVES / NEGATIVES dicts")
P(f"  code-commit : scripts/compute_h_daily.py @ VPS HEAD")
P(f"  BOOK_THIN_FRAC={BOOK_THIN_FRAC}  H1_MIN_HOURS={H1_MIN_HOURS}")
P(f"  h2: OI-store direct (NOT watchlist-gated) — Phase 6 h2 rule")
P()

# Compute
print("Computing positive cases...", flush=True)
pos_data: dict = {}
for p in POSITIVES:
    sym, label = p["sym"], p["label"]
    b0, b1 = p["build"]
    print(f"  {label} build {b0}→{b1} ...", flush=True)
    build_rows = compute_window(sym, b0, b1)
    baseline_rows: list[dict] = []
    if p["baseline"]:
        bl0, bl1 = p["baseline"]
        print(f"  {label} baseline {bl0}→{bl1} ...", flush=True)
        baseline_rows = compute_window(sym, bl0, bl1)
    pos_data[label] = {
        "sym": sym,
        "build": build_rows,
        "baseline": baseline_rows,
        "has_baseline": p["baseline"] is not None,
        "build_range": (b0, b1),
        "baseline_range": p["baseline"],
    }

print("Computing negative cases...", flush=True)
neg_data: dict = {}
for n in NEGATIVES:
    sym, label = n["sym"], n["label"]
    print(f"  {label} {n['start']}→{n['end']} ...", flush=True)
    rows = compute_window(sym, n["start"], n["end"])
    if not rows:
        print(f"  WARNING: {label} ({sym}) — 0 rows loaded; symbol may be absent in store", flush=True)
    neg_data[label] = rows

# ── Stats table ───────────────────────────────────────────────────────────────────
W = 100
P("─" * W)
P("STATS TABLE  [n=days with valid metric · med · (q1, q3)]")
P("─" * W)

all_stats: dict = {}

for m in METRICS:
    P()
    P(f"  ── {METRIC_KEYS[m]} ──")
    P(f"  {'Case':>22} {'Window':>25} {'n':>3} {'median':>9} {'q1':>9} {'q3':>9}")
    P(f"  {'─'*22} {'─'*25} {'─'*3} {'─'*9} {'─'*9} {'─'*9}")

    all_stats[m] = {"build": {}, "baseline": {}, "neg": {}}

    for p in POSITIVES:
        label = p["label"]
        d = pos_data[label]
        b_st = wstats(d["build"], m)
        all_stats[m]["build"][label] = b_st
        P(f"  {label+' build':>22} {d['build_range'][0]}→{d['build_range'][1]} "
          f"{b_st['n']:>3} {fp_s(b_st['med']):>9} {fp_s(b_st['q1']):>9} {fp_s(b_st['q3']):>9}")

        if d["has_baseline"]:
            bl_st = wstats(d["baseline"], m)
            all_stats[m]["baseline"][label] = bl_st
            bl0, bl1 = d["baseline_range"]
            P(f"  {label+' baseline':>22} {bl0}→{bl1} "
              f"{bl_st['n']:>3} {fp_s(bl_st['med']):>9} {fp_s(bl_st['q1']):>9} {fp_s(bl_st['q3']):>9}")
        else:
            P(f"  {label+' baseline':>22} {'NO BASELINE — store starts Jun26':>46}")

    P(f"  {'─'*22}")
    for n in NEGATIVES:
        n_label = n["label"]
        n_st = wstats(neg_data[n_label], m)
        all_stats[m]["neg"][n_label] = n_st
        P(f"  {n_label+' [NEG]':>22} {n['start']}→{n['end']} "
          f"{n_st['n']:>3} {fp_s(n_st['med']):>9} {fp_s(n_st['q1']):>9} {fp_s(n_st['q3']):>9}")

# ── Separation analysis ───────────────────────────────────────────────────────────
P()
P("─" * W)
P("SEPARATION ANALYSIS per metric  (sep = IQR does NOT overlap)")
P("─" * W)
P("  AKE note: no baseline → only neg-sep required for AKE; ghi rõ trong line.")
P()

metric_verdict: dict[str, bool] = {}

for m in METRICS:
    P(f"Metric {METRIC_KEYS[m]}:")
    bs  = all_stats[m]["build"]
    bls = all_stats[m]["baseline"]
    ns  = all_stats[m]["neg"]

    per_case: dict = {}
    for p in POSITIVES:
        label = p["label"]
        b_st  = bs.get(label, {"n": 0})
        if b_st["n"] == 0:
            per_case[label] = {"sep": False, "dir": "?", "note": "NO_DATA"}
            P(f"  {label:>8}: NO_DATA")
            continue

        # Baseline separation
        if label in bls:
            base_ok = iqr_sep(b_st, bls[label])   # True/False/None
        else:
            base_ok = None  # AKE: skip, not required

        # Negative separation (all 3 must separate)
        neg_detail: dict[str, bool | None] = {}
        for n_label, n_st in ns.items():
            if n_st["n"] == 0:
                neg_detail[n_label] = None  # missing — treat as unknown
            else:
                neg_detail[n_label] = iqr_sep(b_st, n_st)

        all_neg_ok = all(v is True for v in neg_detail.values())

        # Overall separation: base_ok (True or None=skipped-AKE) AND all_neg_ok
        sep_ok = (base_ok is not False) and all_neg_ok

        # Direction: build_med vs avg(neg_meds)
        neg_meds = [n_st["med"] for n_st in ns.values() if ok(n_st.get("med", NaN))]
        if ok(b_st["med"]) and neg_meds:
            direction = "+" if b_st["med"] > sum(neg_meds) / len(neg_meds) else "-"
        else:
            direction = "?"

        per_case[label] = {
            "sep": sep_ok, "dir": direction,
            "base_ok": base_ok, "neg_detail": neg_detail,
        }

        base_str = "N/A(AKE)" if base_ok is None else ("YES" if base_ok else "NO ")
        neg_str  = "  ".join(f"{k[:6]}:{'Y' if v is True else 'N' if v is False else '?'}"
                             for k, v in neg_detail.items())
        P(f"  {label:>8}: base_sep={base_str}  neg_sep=[{neg_str}]  "
          f"overall={'SEP' if sep_ok else 'NO '}  dir={direction}")

    # Gate §H5 logic
    pass_labels = [k for k, v in per_case.items() if isinstance(v, dict) and v.get("sep")]
    n_pass = len(pass_labels)
    n_total = len(POSITIVES)   # 4
    dirs = [per_case[k]["dir"] for k in pass_labels if per_case[k]["dir"] != "?"]
    consistent_sign = (len(set(dirs)) == 1) if dirs else False
    gate_pass = (n_pass >= 3) and consistent_sign

    P(f"  → PASS cases: {pass_labels}  ({n_pass}/{n_total})")
    P(f"  → dirs: {dirs}  consistent_sign={consistent_sign}")
    P(f"  → Metric {METRIC_KEYS[m]}: {'PASS ✓' if gate_pass else 'FAIL ✗'}")
    P()
    metric_verdict[m] = gate_pass

# ── Per-day detail (build windows only, for paste to ANALYSIS) ─────────────────────
P("─" * W)
P("PER-DAY BUILD DETAIL (h1..h4 mỗi ngày trong build window — operator & ANALYSIS đọc)")
P("─" * W)

for p in POSITIVES:
    label = p["label"]
    d = pos_data[label]
    P(f"\n  {label} build {d['build_range'][0]}→{d['build_range'][1]}:")
    P(f"  {'date':>12} {'h1_skew':>9} {'h2_oiw':>9} {'h3_conc':>8} {'h4_cloc':>8}")
    P(f"  {'─'*12} {'─'*9} {'─'*9} {'─'*8} {'─'*8}")
    for r in d["build"]:
        P(f"  {r['date']:>12} {fp_s(r.get('h1',NaN)):>9} {fp_s(r.get('h2',NaN)):>9} "
          f"{fp_s(r.get('h3',NaN)):>8} {fp_s(r.get('h4',NaN)):>8}")

P()
P("─" * W)
P("PER-DAY NEGATIVE DETAIL")
P("─" * W)
for n in NEGATIVES:
    n_label = n["label"]
    P(f"\n  {n_label} negative {n['start']}→{n['end']}:")
    P(f"  {'date':>12} {'h1_skew':>9} {'h2_oiw':>9} {'h3_conc':>8} {'h4_cloc':>8}")
    P(f"  {'─'*12} {'─'*9} {'─'*9} {'─'*8} {'─'*8}")
    for r in neg_data.get(n_label, []):
        P(f"  {r['date']:>12} {fp_s(r.get('h1',NaN)):>9} {fp_s(r.get('h2',NaN)):>9} "
          f"{fp_s(r.get('h3',NaN)):>8} {fp_s(r.get('h4',NaN)):>8}")

# ── Final verdict ─────────────────────────────────────────────────────────────────
P()
P("═" * W)
P("GATE §H5 VERDICT (provisional — paste to ANALYSIS + operator; agent KHÔNG tự ký)")
P("─" * W)

any_pass = any(metric_verdict.values())
for m in METRICS:
    P(f"  {METRIC_KEYS[m]:>12}: {'PASS' if metric_verdict[m] else 'FAIL'}")

P()
if any_pass:
    pass_ms = [METRIC_KEYS[m] for m, v in metric_verdict.items() if v]
    P(f"  GATE §H5: CONDITIONAL PASS — metric(s) {pass_ms} tách sạch build vs baseline+negative")
    P(f"  → Kết quả về ANALYSIS đọc → đề xuất θ1-θ4 + K (neo median-negative + đệm)")
    P(f"  → Operator ký θ → H-tier ACTIVE")
    P(f"  Agent KHÔNG điền θ — θ CONFIRM-tier, điền sau gate, không đoán trước")
else:
    P(f"  GATE §H5: FAIL — không có metric nào tách sạch ≥3/4 positive + nhất-quán-dấu")
    P(f"  Kết luận: texture 1h không vượt daily cho loài này (số đủ, không giải thích thêm)")
    P(f"  → Archive spec H-tier: đóng hướng bằng số, collector không cần giữ")

P()
P("  Agent KHÔNG tự ký verdict. DỪNG — paste + chờ operator / ANALYSIS.")
P("═" * W)

# ── Write output ──────────────────────────────────────────────────────────────────
OUT     = REPO / "_probe_phase6_h5_gate_20260814.txt"
content = buf.getvalue()
OUT.write_text(content, encoding="utf-8")
print(f"\nOutput: {OUT}")
print(content)
