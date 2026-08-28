"""EX-SOPH micro-table · 2 nấc ứng viên {vol1.0_tk45 · vol1.5_tk45} · zero-call · KÝ 01/09

Re-run harness LOẠI SOPH khỏi pass-set LẪN control pool → so cạnh bản có-SOPH:
  {fires · episodes · hits · lift · CI-90%} + Δlift "DQ-DELIST mua"
Kèm n_episodes_SOPH per nấc (SOPH 26 fires = mấy cụm?)
"""
import sys, io, csv, hashlib, glob, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
OUT_CSV = ROOT / "docs" / "reports" / "ma_ex_soph_micro_20260828.csv"

TP_THRESHOLD = 0.50
RET_ABS_MAX = 0.03
EPISODE_GAP = 14
N_MATCHED_DRAWS = 1000
N_JOINT_BOOT = 10_000
SEED = 42

NAC_LIST = [(1.0, 45.0), (1.5, 45.0)]
SOPH_TOKEN = "SOPHUSDT"

# Load store
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
DATA_LAST = max(all_df["date_str"].unique())

# Per-symbol features (reuse pattern from grid v1)
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
                if med14 > 0:
                    rec["vol_ratio"] = vols[i] / med14
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

def run_nac(vol_x, taker_max, exclude_syms=None):
    exclude = set(exclude_syms or [])
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
    if not fires:
        return {"n_fires": 0, "n_episodes": 0, "n_uncens": 0, "hits": 0,
                "rate": 0, "matched_rate": None, "lift": None, "ci_5": None, "ci_95": None}
    eps = cluster_gap(fires)
    ep_summary = []
    for ep in eps:
        sym = ep[0]["symbol"]
        last_d = date.fromisoformat(ep[-1]["date"]); dl = date.fromisoformat(DATA_LAST)
        ep_uncens = (dl - last_d).days >= 30
        fwds = [w["fwd"] for w in ep if w["fwd"] is not None]
        best = max(fwds) if fwds else None
        hit = best is not None and best >= TP_THRESHOLD
        ep_summary.append({"sym": sym, "n": len(ep), "uncens": ep_uncens, "hit": hit})
    n_uncens = sum(1 for e in ep_summary if e["uncens"])
    n_hits = sum(1 for e in ep_summary if e["uncens"] and e["hit"])
    pass_rate = n_hits / n_uncens if n_uncens else 0
    pass_ep_lens = [e["n"] for e in ep_summary if e["uncens"]]
    if not pass_ep_lens:
        return {"n_fires": n_fires, "n_episodes": len(eps), "n_uncens": n_uncens, "hits": n_hits,
                "rate": pass_rate, "matched_rate": None, "lift": None, "ci_5": None, "ci_95": None}

    # Matched control (excluding same syms)
    fires_set = {(f["symbol"], f["date"]) for f in fires}
    control_pool = {}
    for sym, feats in sym_features.items():
        if sym in exclude: continue
        idx_list = [i for i, f in enumerate(feats) if f["quiet_regime"] and f["uncens"] and (sym, f["date"]) not in fires_set]
        if idx_list: control_pool[sym] = idx_list

    random.seed(SEED)
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
                best = max(fwds)
                picked = best >= TP_THRESHOLD; break
        if picked is not None: matched_outcomes.append(picked)

    matched_rate = sum(matched_outcomes) / len(matched_outcomes) if matched_outcomes else 0
    lift = pass_rate / matched_rate if matched_rate > 0 else None

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
    lifts_sorted = sorted(lifts)
    ci_5 = lifts_sorted[int(len(lifts_sorted) * 0.05)] if lifts_sorted else None
    ci_95 = lifts_sorted[int(len(lifts_sorted) * 0.95)] if lifts_sorted else None

    return {"n_fires": n_fires, "n_episodes": len(eps), "n_uncens": n_uncens, "hits": n_hits,
            "rate": pass_rate, "matched_rate": matched_rate,
            "lift": lift, "ci_5": ci_5, "ci_95": ci_95}

# ── Count SOPH episodes per nấc ──
soph_ep_counts = {}
for vol_x, taker in NAC_LIST:
    soph_fires = []
    feats = sym_features.get(SOPH_TOKEN, [])
    for f in feats:
        if (f["vol_ratio"] is not None and f["vol_ratio"] >= vol_x and
            f["ret_1d"] is not None and abs(f["ret_1d"]) <= RET_ABS_MAX and
            f["taker"] is not None and f["taker"] <= taker):
            soph_fires.append({"symbol": SOPH_TOKEN, "date": f["date"]})
    n_soph_fires = len(soph_fires)
    if soph_fires:
        # Cluster
        srtd = sorted(soph_fires, key=lambda x: x["date"])
        eps = []; cur = []; prev = None
        for r in srtd:
            cd = date.fromisoformat(r["date"])
            if prev is not None and (cd - prev).days >= EPISODE_GAP:
                if cur: eps.append(cur); cur = []
            cur.append(r); prev = cd
        if cur: eps.append(cur)
        n_soph_eps = len(eps)
    else:
        n_soph_eps = 0
    soph_ep_counts[(vol_x, taker)] = (n_soph_fires, n_soph_eps)

# ── Run 2 nấc: with SOPH + without SOPH ──
print(f"\n{'nấc':<15} {'set':<12} {'fires':>6} {'ep':>4} {'uncens':>6} {'hits':>4} {'rate':>6} {'lift':>6} {'CI-90%':<15}")
results = {}
for vol_x, taker_max in NAC_LIST:
    nac_name = f"vol{vol_x}_tk{taker_max}"
    with_soph = run_nac(vol_x, taker_max, exclude_syms=None)
    ex_soph = run_nac(vol_x, taker_max, exclude_syms=[SOPH_TOKEN])
    results[nac_name] = {"with": with_soph, "ex": ex_soph}
    for label, r in [("with-SOPH", with_soph), ("ex-SOPH", ex_soph)]:
        li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
        ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r["ci_5"] is not None else "N/A"
        print(f"  {nac_name:<15} {label:<12} {r['n_fires']:>5} {r['n_episodes']:>4} {r['n_uncens']:>6} "
              f"{r['hits']:>4} {r['rate']*100:>5.1f}% {li:>6} {ci:<15}")

# DQ-DELIST Δlift
print(f"\n[DQ-DELIST mua Δlift]")
for nac, res in results.items():
    d_lift = None
    if res["ex"]["lift"] is not None and res["with"]["lift"] is not None:
        d_lift = res["ex"]["lift"] - res["with"]["lift"]
    print(f"  {nac}: Δlift = {d_lift:+.2f}x" if d_lift is not None else f"  {nac}: Δlift = N/A")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# EX-SOPH micro-table · 2 nấc ứng viên {{vol1.0_tk45, vol1.5_tk45}} · zero-call · KÝ 01/09\n")
    f.write(f"# Re-run harness LOẠI SOPH khỏi pass-set LẪN control pool · seed={SEED}\n")
    f.write(f"# Matched bootstrap N={N_MATCHED_DRAWS} · joint CI N={N_JOINT_BOOT}\n")
    f.write(f"#\n")
    f.write(f"# ─── SOPH episodes per nấc (n_fires_SOPH / n_eps_SOPH) ───\n")
    for (vol_x, taker), (nf, ne) in soph_ep_counts.items():
        f.write(f"#   vol{vol_x}_tk{taker}: {nf} SOPH fires → {ne} SOPH episodes (gap<14d cluster)\n")
    f.write(f"#\n")
    f.write(f"# ─── COMPARE with-SOPH vs ex-SOPH per nấc ───\n")
    f.write(f"# {'nấc':<15} {'set':<12} {'fires':>6} {'ep':>4} {'uncens':>6} {'hits':>4} {'rate':>6} {'lift':>6} {'CI-90%':<15}\n")
    for nac, res in results.items():
        for label, r in [("with-SOPH", res["with"]), ("ex-SOPH", res["ex"])]:
            li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
            ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r["ci_5"] is not None else "N/A"
            f.write(f"#   {nac:<15} {label:<12} {r['n_fires']:>5} {r['n_episodes']:>4} {r['n_uncens']:>6} "
                    f"{r['hits']:>4} {r['rate']*100:>5.1f}% {li:>6} {ci:<15}\n")
    f.write(f"#\n")
    f.write(f"# ─── DQ-DELIST mua Δlift = lift(ex-SOPH) − lift(with-SOPH) ───\n")
    for nac, res in results.items():
        if res["ex"]["lift"] is not None and res["with"]["lift"] is not None:
            d_lift = res["ex"]["lift"] - res["with"]["lift"]
            f.write(f"#   {nac}: Δlift = {d_lift:+.2f}x (with={res['with']['lift']:.2f}x → ex={res['ex']['lift']:.2f}x)\n")
    f.write(f"# KHÔNG kết luận — bảng cho ANALYSIS + Tiên ký 27/09\n")
    f.write(f"#\n")
    # Records
    w = csv.DictWriter(f, fieldnames=["nac","set","n_fires","n_episodes","n_uncens",
                                       "hits","rate","matched_rate","lift","ci_5","ci_95"])
    w.writeheader()
    for nac, res in results.items():
        for label, r in [("with-SOPH", res["with"]), ("ex-SOPH", res["ex"])]:
            w.writerow({
                "nac": nac, "set": label,
                "n_fires": r["n_fires"], "n_episodes": r["n_episodes"], "n_uncens": r["n_uncens"],
                "hits": r["hits"], "rate": f"{r['rate']:.4f}",
                "matched_rate": f"{r['matched_rate']:.4f}" if r["matched_rate"] is not None else "",
                "lift": f"{r['lift']:.4f}" if r["lift"] is not None else "",
                "ci_5": f"{r['ci_5']:.4f}" if r["ci_5"] is not None else "",
                "ci_95": f"{r['ci_95']:.4f}" if r["ci_95"] is not None else "",
            })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
