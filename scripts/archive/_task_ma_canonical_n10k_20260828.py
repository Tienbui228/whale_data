"""CANONICAL-N10K · 4 cells re-run · zero-call · KÝ 01/09

RE-RUN 4 cells {vol1.0_tk45 · vol1.5_tk45} × {with-SOPH · ex-SOPH} với N=10,000 draws:
  · seed per-cell cố định: seed = 42 + hash(cell) (khai trong header)
  · pool/censor y nguyên (từ ma_ex_soph_micro logic)
  · MC-error co ~3× (±0.3pp matched → ±0.05× lift)

BỘ SỐ CANONICAL duy nhất cho 2 ô ứng viên đóng góp §1-§2 GÓI-KÝ 27/09.
Grid-v2 8-nấc + micro-table đánh dấu [MC-N1000 · screening, superseded cho 2 ô dao] giữ exhibit.
"""
import sys, io, csv, hashlib, glob, random, hashlib as _h
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
OUT_CSV = ROOT / "docs" / "reports" / "ma_canonical_n10k_20260828.csv"

TP_THRESHOLD = 0.50
RET_ABS_MAX = 0.03
EPISODE_GAP = 14
N_MATCHED_DRAWS = 10_000   # CANONICAL 10k
N_JOINT_BOOT = 10_000
BASE_SEED = 42

NAC_LIST = [(1.0, 45.0), (1.5, 45.0)]
SET_LIST = ["with-SOPH", "ex-SOPH"]
SOPH_TOKEN = "SOPHUSDT"

def cell_seed(vol_x, taker, set_label):
    """Deterministic seed per cell."""
    key = f"{vol_x}_{taker}_{set_label}"
    h = int(_h.sha256(key.encode()).hexdigest()[:8], 16) % 100000
    return BASE_SEED + h

# Load store
print(f"[LOAD] store binance_spot")
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
DATA_LAST = max(all_df["date_str"].unique())

# Per-symbol features
sym_features = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    closes = g["close"].tolist(); vols = g["quote_vol"].tolist(); takers = g["taker_buy_pct"].tolist()
    dates = g["date_str"].tolist()
    n = len(closes)
    feats = []
    for i in range(n):
        rec = {"date": dates[i], "vol_ratio": None, "ret_1d": None, "taker": None,
               "quiet_regime": False, "fwd_ret_30d": None, "uncens": False}
        if i >= 14 and closes[i] is not None:
            vols_prev14 = [v for v in vols[i-14:i] if v is not None and v > 0]
            if len(vols_prev14) >= 14 and vols[i] is not None and vols[i] > 0:
                med14 = median(vols_prev14)
                if med14 > 0: rec["vol_ratio"] = vols[i] / med14
        if i >= 1 and closes[i] is not None and closes[i-1] is not None and closes[i-1] > 0:
            rec["ret_1d"] = closes[i] / closes[i-1] - 1.0
            rec["quiet_regime"] = abs(rec["ret_1d"]) <= RET_ABS_MAX
        rec["taker"] = takers[i]
        if closes[i] is not None and closes[i] > 0:
            future = [c for c in closes[i+1:i+31] if c is not None]
            if len(future) >= 30:
                rec["fwd_ret_30d"] = max(future)/closes[i] - 1.0
                rec["uncens"] = True
        feats.append(rec)
    sym_features[sym] = feats

def cluster_gap(rows, gap=EPISODE_GAP):
    by_sym = {}
    for r in rows: by_sym.setdefault(r["symbol"], []).append(r)
    eps = []
    for sym in sorted(by_sym):
        srtd = sorted(by_sym[sym], key=lambda x: x["date"])
        cur = []; prev = None
        for r in srtd:
            cd = date.fromisoformat(r["date"])
            if prev is not None and (cd - prev).days >= gap:
                if cur: eps.append(cur); cur = []
            cur.append(r); prev = cd
        if cur: eps.append(cur)
    return eps

def run_cell(vol_x, taker_max, set_label):
    exclude = {SOPH_TOKEN} if set_label == "ex-SOPH" else set()
    seed = cell_seed(vol_x, taker_max, set_label)
    random.seed(seed)

    fires = []
    for sym, feats in sym_features.items():
        if sym in exclude: continue
        for f in feats:
            if (f["vol_ratio"] is not None and f["vol_ratio"] >= vol_x and
                f["ret_1d"] is not None and abs(f["ret_1d"]) <= RET_ABS_MAX and
                f["taker"] is not None and f["taker"] <= taker_max):
                fires.append({"symbol": sym, "date": f["date"],
                              "fwd": f["fwd_ret_30d"], "uncens": f["uncens"]})
    n_fires = len(fires)
    eps = cluster_gap(fires)
    ep_summary = []
    for ep in eps:
        last_d = date.fromisoformat(ep[-1]["date"]); dl = date.fromisoformat(DATA_LAST)
        ep_uncens = (dl - last_d).days >= 30
        fwds = [w["fwd"] for w in ep if w["fwd"] is not None]
        best = max(fwds) if fwds else None
        hit = best is not None and best >= TP_THRESHOLD
        ep_summary.append({"sym": ep[0]["symbol"], "n": len(ep), "uncens": ep_uncens, "hit": hit})
    n_uncens = sum(1 for e in ep_summary if e["uncens"])
    n_hits = sum(1 for e in ep_summary if e["uncens"] and e["hit"])
    pass_rate = n_hits / n_uncens if n_uncens else 0
    pass_ep_lens = [e["n"] for e in ep_summary if e["uncens"]]
    if not pass_ep_lens:
        return {"seed": seed, "n_fires": n_fires, "n_ep": len(eps), "n_uncens": n_uncens, "hits": n_hits,
                "rate": pass_rate, "matched_rate": None, "lift": None, "ci_5": None, "ci_95": None,
                "n_matched_draws_used": 0}

    # Matched control
    fires_set = {(f["symbol"], f["date"]) for f in fires}
    control_pool = {}
    for sym, feats in sym_features.items():
        if sym in exclude: continue
        idx_list = [i for i, f in enumerate(feats) if f["quiet_regime"] and f["uncens"] and (sym, f["date"]) not in fires_set]
        if idx_list: control_pool[sym] = idx_list

    sym_list_ctrl = [s for s in control_pool if len(control_pool[s]) >= max(pass_ep_lens)]
    matched_outcomes = []
    for _ in range(N_MATCHED_DRAWS):
        if not sym_list_ctrl: break
        L = random.choice(pass_ep_lens)
        picked = None
        for _ in range(50):
            sym = random.choice(sym_list_ctrl)
            idxs = control_pool[sym]
            if len(idxs) < L: continue
            start_pos = random.randint(0, len(idxs) - L)
            block_idxs = idxs[start_pos:start_pos + L]
            fwds = [sym_features[sym][i]["fwd_ret_30d"] for i in block_idxs if sym_features[sym][i]["fwd_ret_30d"] is not None]
            if fwds:
                best = max(fwds); picked = best >= TP_THRESHOLD; break
        if picked is not None: matched_outcomes.append(picked)

    matched_rate = sum(matched_outcomes) / len(matched_outcomes) if matched_outcomes else 0
    lift_point = pass_rate / matched_rate if matched_rate > 0 else None

    # Joint bootstrap CI
    pass_outcomes = [1 if e["hit"] else 0 for e in ep_summary if e["uncens"]]
    lifts = []
    for _ in range(N_JOINT_BOOT):
        p_sample = random.choices(pass_outcomes, k=len(pass_outcomes))
        m_sample = random.choices(matched_outcomes, k=len(matched_outcomes))
        p_r = sum(p_sample) / len(p_sample)
        m_r = sum(m_sample) / len(m_sample)
        if m_r == 0: continue
        lifts.append(p_r / m_r)
    ls = sorted(lifts)
    ci_5 = ls[int(len(ls)*0.05)] if ls else None
    ci_95 = ls[int(len(ls)*0.95)] if ls else None

    return {"seed": seed, "n_fires": n_fires, "n_ep": len(eps), "n_uncens": n_uncens, "hits": n_hits,
            "rate": pass_rate, "matched_rate": matched_rate,
            "lift": lift_point, "ci_5": ci_5, "ci_95": ci_95,
            "n_matched_draws_used": len(matched_outcomes)}

# ── Run 4 cells ──
print(f"\n[RUN] 4 cells × N={N_MATCHED_DRAWS} draws (canonical)")
results = []
for vol_x, taker in NAC_LIST:
    for set_label in SET_LIST:
        r = run_cell(vol_x, taker, set_label)
        r["nac"] = f"vol{vol_x}_tk{taker}"
        r["set"] = set_label
        r["vol_x"] = vol_x; r["taker"] = taker
        results.append(r)
        li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
        ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r["ci_5"] is not None else "N/A"
        print(f"  {r['nac']:<15} {set_label:<12} seed={r['seed']:>7}  fires={r['n_fires']:>4} uncens={r['n_uncens']:>4} hits={r['hits']:>3} "
              f"rate={r['rate']*100:>5.1f}% matched={r['matched_rate']*100:>5.2f}% lift={li:>5} CI={ci:<15}")

# Δlift DQ-DELIST per nấc
print(f"\n[Δlift DQ-DELIST]")
for vol_x, taker in NAC_LIST:
    ws = next(r for r in results if r["vol_x"]==vol_x and r["taker"]==taker and r["set"]=="with-SOPH")
    ex = next(r for r in results if r["vol_x"]==vol_x and r["taker"]==taker and r["set"]=="ex-SOPH")
    if ws["lift"] is not None and ex["lift"] is not None:
        d = ex["lift"] - ws["lift"]
        print(f"  vol{vol_x}_tk{taker}: Δlift = {d:+.2f}x  (with={ws['lift']:.2f}x → ex={ex['lift']:.2f}x)")

# Robust check for §1 deploy: which cells CI_5% > 1
print(f"\n[ROBUST-CHECK CI_5%>1]")
for r in results:
    ok = r["ci_5"] is not None and r["ci_5"] > 1.0
    print(f"  {r['nac']:<15} {r['set']:<12} CI_5%={r['ci_5']:.2f}x  {'✓ ROBUST' if ok else '✗ mấp mé'}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# CANONICAL-N10K · 4 cells re-run · zero-call · KÝ 01/09\n")
    f.write(f"# CANONICAL bộ số cho 2 ô dao (grid-v2 + micro-table [MC-N1000 · screening, superseded])\n")
    f.write(f"# Config: N_MATCHED_DRAWS={N_MATCHED_DRAWS} · N_JOINT_BOOT={N_JOINT_BOOT} · TP={TP_THRESHOLD}\n")
    f.write(f"# Seed per-cell: BASE={BASE_SEED} + sha256(f'{{vol_x}}_{{taker}}_{{set_label}}')[:8] % 100000\n")
    f.write(f"# Seeds table:\n")
    for r in results:
        f.write(f"#   {r['nac']:<15} {r['set']:<12} seed={r['seed']}\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 MC-precision ───\n")
    f.write(f"#   N=10,000 draws/cell · MC error co ~3× vs N=1000 (±0.3pp matched → ±~0.05× lift)\n")
    f.write(f"#\n")
    f.write(f"# ─── RESULTS ───\n")
    f.write(f"# {'nac':<15} {'set':<12} {'seed':>7} {'fires':>6} {'uncens':>6} {'hits':>4} {'rate':>7} {'matched':>8} {'lift':>6} {'CI-90%':<15}\n")
    for r in results:
        li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
        ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r["ci_5"] is not None else "N/A"
        f.write(f"#   {r['nac']:<15} {r['set']:<12} {r['seed']:>7} {r['n_fires']:>6} {r['n_uncens']:>6} {r['hits']:>4} "
                f"{r['rate']*100:>6.2f}% {r['matched_rate']*100:>7.2f}% {li:>6} {ci:<15}\n")
    f.write(f"#\n")
    f.write(f"# ─── Δlift DQ-DELIST ───\n")
    for vol_x, taker in NAC_LIST:
        ws = next(r for r in results if r["vol_x"]==vol_x and r["taker"]==taker and r["set"]=="with-SOPH")
        ex = next(r for r in results if r["vol_x"]==vol_x and r["taker"]==taker and r["set"]=="ex-SOPH")
        if ws["lift"] is not None and ex["lift"] is not None:
            d = ex["lift"] - ws["lift"]
            f.write(f"#   vol{vol_x}_tk{taker}: Δlift = {d:+.2f}x  (with={ws['lift']:.2f}x → ex={ex['lift']:.2f}x)\n")
    f.write(f"#\n")
    f.write(f"# ─── ROBUST-CHECK (CI_5% > 1 = robust; ≤1 = mấp mé) ───\n")
    for r in results:
        ok = r["ci_5"] is not None and r["ci_5"] > 1.0
        f.write(f"#   {r['nac']:<15} {r['set']:<12} CI_5%={r['ci_5']:.2f}x  {'ROBUST' if ok else 'mấp mé'}\n")
    f.write(f"#\n")
    f.write(f"# KHÔNG kết luận — bộ số CANONICAL cho GÓI-KÝ 27/09 §1-§2 (thay N=1000 [MC-screening])\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["nac","set","vol_x","taker","seed","n_fires","n_episodes","n_uncens",
                                       "hits","rate","matched_rate","lift","ci_5","ci_95","n_matched_draws_used"])
    w.writeheader()
    for r in results:
        w.writerow({
            "nac": r["nac"], "set": r["set"], "vol_x": r["vol_x"], "taker": r["taker"],
            "seed": r["seed"], "n_fires": r["n_fires"], "n_episodes": r["n_ep"], "n_uncens": r["n_uncens"],
            "hits": r["hits"], "rate": f"{r['rate']:.4f}",
            "matched_rate": f"{r['matched_rate']:.4f}" if r["matched_rate"] is not None else "",
            "lift": f"{r['lift']:.4f}" if r["lift"] is not None else "",
            "ci_5": f"{r['ci_5']:.4f}" if r["ci_5"] is not None else "",
            "ci_95": f"{r['ci_95']:.4f}" if r["ci_95"] is not None else "",
            "n_matched_draws_used": r["n_matched_draws_used"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
