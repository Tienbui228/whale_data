"""MA-D3 LIFT-GRID 8 nấc harness · KÝ 01/09 · zero-call

125d-harness nguyên văn áp lên MA:
  Grid: taker ∈ {40, 42.5, 45, 47.5} × vol_x ∈ {1.0, 1.5}  (8 nấc)
  ret_abs = 3% cố định
  Control mapping mirror CVD (khai L-64):
    pool = ngày GIÁ-PHẲNG (|ret1d| ≤ 3%) TRỪ pass-windows/nấc  (regime-leg của MA)

Per nấc:
  1. Fires = vol_ratio ≥ vol_x ∧ |ret| ≤ 3% ∧ taker ≤ taker_thresh
  2. Episodize <14d cluster per-token
  3. Uncensored episode (last_end + 30d ≤ data_last)
  4. best_fwd_30d per episode → hit ≥ +50%
  5. Length-matched bootstrap N=1000 seed=42 from control pool
  6. Joint bootstrap N=10k (mirror CI-addendum) → CI-90%
  7. % fire-mass mang delist_flag

DEATH-MIMICRY sẽ hiện: nấc fires-nhiều-lift-không.
KHÔNG kết luận · bảng đặt-dao cho ANALYSIS + Tiên ký 27/09.
"""
import sys, io, csv, hashlib, glob, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
DELIST_CSV = ROOT / "docs" / "reports" / "ma_delist_flag_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "ma_lift_grid_20260828.csv"

TP_THRESHOLD = 0.50
RET_ABS_MAX = 0.03
EPISODE_GAP = 14
N_MATCHED_DRAWS = 1000
N_JOINT_BOOT = 10_000
SEED = 42

# Grid
TAKER_GRID = [40.0, 42.5, 45.0, 47.5]
VOL_X_GRID = [1.0, 1.5]

# Load delist flags per token
delist_flag = {}
with open(DELIST_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("token,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 9: continue
        delist_flag[p[0]] = (p[8] == "True")  # flag_ANY column
print(f"[LOAD] delist_flag entries: {len(delist_flag)} · n_flagged={sum(1 for v in delist_flag.values() if v)}")

# Load store binance_spot
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
DATA_LAST = max(all_df["date_str"].unique())
print(f"[LOAD] binance_spot rows: {len(all_df)} · sym: {all_df['symbol'].nunique()} · last={DATA_LAST}")

# Per-symbol close series
sym_series = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    sym_series[sym] = {"dates": g["date_str"].tolist(),
                        "closes": g["close"].tolist(),
                        "vols": g["quote_vol"].tolist(),
                        "takers": g["taker_buy_pct"].tolist()}

# Compute per-day: vol_ratio, ret_1d, quiet_regime (|ret|≤3%), fwd_ret_30d, uncens
print(f"\n[COMPUTE] per-day features · vol_ratio + ret + fwd_ret_30d")
sym_features = {}  # {sym: [{date, vol_ratio, ret_1d, taker, quiet_regime, fwd_ret_30d, uncens}]}
for sym, s in sym_series.items():
    closes = s["closes"]; vols = s["vols"]; takers = s["takers"]; dates = s["dates"]
    n = len(closes)
    feats = []
    for i in range(n):
        rec = {"date": dates[i], "vol_ratio": None, "ret_1d": None, "taker": None,
               "quiet_regime": False, "fwd_ret_30d": None, "uncens": False}
        # med14
        if i >= 14 and closes[i] is not None:
            vols_prev14 = [v for v in vols[i-14:i] if v is not None and v > 0]
            if len(vols_prev14) >= 14 and vols[i] is not None and vols[i] > 0:
                med14 = median(vols_prev14)
                if med14 > 0:
                    rec["vol_ratio"] = vols[i] / med14
        # ret_1d
        if i >= 1 and closes[i] is not None and closes[i-1] is not None and closes[i-1] > 0:
            rec["ret_1d"] = closes[i] / closes[i-1] - 1.0
            rec["quiet_regime"] = abs(rec["ret_1d"]) <= RET_ABS_MAX
        rec["taker"] = takers[i] if takers[i] is not None else None
        # fwd_ret_30d
        if closes[i] is not None and closes[i] > 0:
            future = [c for c in closes[i+1:i+31] if c is not None]
            if len(future) >= 30:
                rec["fwd_ret_30d"] = max(future)/closes[i] - 1.0
                rec["uncens"] = True
        feats.append(rec)
    sym_features[sym] = feats

# Episode cluster helper
def cluster_by_gap(records, gap=EPISODE_GAP):
    """records = list of dicts with 'date' + 'symbol'. Cluster per-token by gap<14d."""
    by_sym = {}
    for r in records:
        by_sym.setdefault(r["symbol"], []).append(r)
    episodes = []
    for sym in sorted(by_sym):
        srtd = sorted(by_sym[sym], key=lambda x: x["date"])
        cur = []; prev_d = None
        for r in srtd:
            cd = date.fromisoformat(r["date"])
            if prev_d is not None and (cd - prev_d).days >= gap:
                if cur: episodes.append(cur); cur = []
            cur.append(r); prev_d = cd
        if cur: episodes.append(cur)
    return episodes

# ── GRID LOOP ──
print(f"\n[GRID-LOOP] {len(TAKER_GRID)}×{len(VOL_X_GRID)} = {len(TAKER_GRID)*len(VOL_X_GRID)} nấc")
grid_rows = []
random.seed(SEED)

for vol_x in VOL_X_GRID:
    for taker_max in TAKER_GRID:
        nac_name = f"vol{vol_x}_tk{taker_max}"

        # Fires per token
        fires = []
        for sym, feats in sym_features.items():
            for f in feats:
                if (f["vol_ratio"] is not None and f["vol_ratio"] >= vol_x and
                    f["ret_1d"] is not None and abs(f["ret_1d"]) <= RET_ABS_MAX and
                    f["taker"] is not None and f["taker"] <= taker_max):
                    fires.append({"symbol": sym, "date": f["date"], "fwd": f["fwd_ret_30d"], "uncens": f["uncens"]})

        n_fires = len(fires)
        if n_fires == 0:
            grid_rows.append({"nac": nac_name, "vol_x": vol_x, "taker": taker_max,
                              "n_fires": 0, "n_episodes": 0, "n_uncens": 0,
                              "hits": 0, "rate": 0, "lift": None, "ci_5": None, "ci_95": None,
                              "pct_delist_mass": 0.0})
            continue

        # Episodize
        eps = cluster_by_gap(fires)
        n_ep = len(eps)

        # Uncens: any window's uncens=True in episode is not enough — take episode uncens if last_date + 30d ≤ data_last
        ep_summary = []
        for ep in eps:
            sym = ep[0]["symbol"]
            last_date = ep[-1]["date"]
            last_d = date.fromisoformat(last_date); dl = date.fromisoformat(DATA_LAST)
            ep_uncens = (dl - last_d).days >= 30
            fwds = [w["fwd"] for w in ep if w["fwd"] is not None]
            if not fwds:
                ep_summary.append({"sym": sym, "n": len(ep), "best": None, "uncens": False, "hit": False})
                continue
            best = max(fwds)
            hit = best >= TP_THRESHOLD
            ep_summary.append({"sym": sym, "n": len(ep), "best": best, "uncens": ep_uncens, "hit": hit})

        uncens_eps = [e for e in ep_summary if e["uncens"]]
        n_uncens = len(uncens_eps)
        n_hits = sum(1 for e in uncens_eps if e["hit"])
        pass_rate = n_hits / n_uncens if n_uncens else 0

        # Fire-mass delist-flag %
        n_flagged = sum(1 for f in fires if delist_flag.get(f["symbol"], False))
        pct_delist = n_flagged / n_fires * 100

        # Matched-control bootstrap (mirror CVD): pool = quiet-regime days TRỪ pass fires
        # Build control-days per sym: quiet_regime=True AND uncens=True AND NOT in fires-set
        fires_set = {(f["symbol"], f["date"]) for f in fires}
        control_pool = {}  # {sym: [indices where quiet + uncens + not fire]}
        for sym, feats in sym_features.items():
            idx_list = []
            for i, f in enumerate(feats):
                if f["quiet_regime"] and f["uncens"] and (sym, f["date"]) not in fires_set:
                    idx_list.append(i)
            if idx_list: control_pool[sym] = idx_list

        # Length-matched bootstrap
        pass_ep_lens_uncens = [e["n"] for e in uncens_eps]
        if not pass_ep_lens_uncens:
            grid_rows.append({"nac": nac_name, "vol_x": vol_x, "taker": taker_max,
                              "n_fires": n_fires, "n_episodes": n_ep, "n_uncens": n_uncens,
                              "hits": n_hits, "rate": pass_rate,
                              "lift": None, "ci_5": None, "ci_95": None,
                              "pct_delist_mass": pct_delist})
            continue

        # Draw N_MATCHED_DRAWS
        matched_outcomes = []
        sym_list_ctrl = [s for s in control_pool.keys() if len(control_pool[s]) >= max(pass_ep_lens_uncens)]
        for _ in range(N_MATCHED_DRAWS):
            if not sym_list_ctrl: break
            L = random.choice(pass_ep_lens_uncens)
            # Try to pick block
            picked = None
            for _ in range(50):
                sym = random.choice(sym_list_ctrl)
                idxs = control_pool[sym]
                if len(idxs) < L: continue
                start_pos = random.randint(0, len(idxs) - L)
                # Take L consecutive indices in control_pool (they may not be adjacent in feats — that's ok for length-matched sample)
                block_idxs = idxs[start_pos:start_pos + L]
                fwds = [sym_features[sym][i]["fwd_ret_30d"] for i in block_idxs if sym_features[sym][i]["fwd_ret_30d"] is not None]
                if fwds:
                    best = max(fwds)
                    picked = (best, best >= TP_THRESHOLD)
                    break
            if picked: matched_outcomes.append(picked[1])

        if not matched_outcomes:
            grid_rows.append({"nac": nac_name, "vol_x": vol_x, "taker": taker_max,
                              "n_fires": n_fires, "n_episodes": n_ep, "n_uncens": n_uncens,
                              "hits": n_hits, "rate": pass_rate,
                              "lift": None, "ci_5": None, "ci_95": None,
                              "pct_delist_mass": pct_delist})
            continue

        matched_rate = sum(matched_outcomes) / len(matched_outcomes)
        lift_point = pass_rate / matched_rate if matched_rate > 0 else None

        # Joint bootstrap CI-90%
        pass_outcomes = [1 if e["hit"] else 0 for e in uncens_eps]
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

        grid_rows.append({"nac": nac_name, "vol_x": vol_x, "taker": taker_max,
                          "n_fires": n_fires, "n_episodes": n_ep, "n_uncens": n_uncens,
                          "hits": n_hits, "rate": pass_rate,
                          "matched_rate": matched_rate,
                          "lift": lift_point, "ci_5": ci_5, "ci_95": ci_95,
                          "pct_delist_mass": pct_delist})

        print(f"  {nac_name:<18} fires={n_fires:>4} ep={n_ep:>3} uncens={n_uncens:>3} hits={n_hits:>2} "
              f"rate={pass_rate:.1%} matched={matched_rate:.2%} lift={lift_point:.2f}x "
              f"CI=[{ci_5:.2f},{ci_95:.2f}]  delist%={pct_delist:.1f}%")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# MA-D3 LIFT-GRID 8 nấc harness · SPOTCVD 125d-harness nguyên văn trên MA · KÝ 01/09\n")
    f.write(f"# Grid: taker ∈ {TAKER_GRID} × vol_x ∈ {VOL_X_GRID} · ret_abs = {RET_ABS_MAX} cố định · seed={SEED}\n")
    f.write(f"# Control (L-64 mirror CVD): pool = ngày GIÁ-PHẲNG (|ret1d|≤{RET_ABS_MAX}) TRỪ pass-fires/nấc · regime-leg MA\n")
    f.write(f"# Episode <{EPISODE_GAP}d gap · uncens (last_end + 30d ≤ {DATA_LAST}) · best_fwd_30d max · hit ≥ +{TP_THRESHOLD:.0%}\n")
    f.write(f"# Length-matched bootstrap: N={N_MATCHED_DRAWS} draws per nấc · joint bootstrap CI: N={N_JOINT_BOOT} · seed={SEED}\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số cho mỗi nấc ───\n")
    f.write(f"#   pass-fires: subset all-days where vol_ratio ≥ vol_x AND |ret_1d| ≤ {RET_ABS_MAX} AND taker ≤ taker_max\n")
    f.write(f"#   pass-episodes uncens: fires cluster <14d, last_end + 30d ≤ {DATA_LAST}\n")
    f.write(f"#   matched-control: quiet-regime days TRỪ pass-fires (chống nhiễm) · length-matched\n")
    f.write(f"#   delist_flag_ANY (OR 3 sources): docs/reports/ma_delist_flag_20260828.csv md5 74a70b38\n")
    f.write(f"#\n")
    f.write(f"# ─── GRID RESULTS ───\n")
    f.write(f"# nấc               fires  eps  uncens hits rate  matched lift    CI-90%          %delist_mass\n")
    for r in grid_rows:
        li = f"{r['lift']:.2f}x" if r.get("lift") is not None else "N/A"
        ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r.get("ci_5") is not None else "N/A"
        mr = f"{r.get('matched_rate',0):.2%}" if r.get("matched_rate") is not None else "N/A"
        f.write(f"#   {r['nac']:<18} {r['n_fires']:>5}  {r['n_episodes']:>3}  {r['n_uncens']:>4}  "
                f"{r['hits']:>3}  {r['rate']:.1%}  {mr:>7}  {li:>7}  {ci:<16} {r['pct_delist_mass']:>6.1f}%\n")
    f.write(f"#\n")
    f.write(f"# DEATH-MIMICRY khám: nấc fires-nhiều-lift-không (%delist_mass cao + lift thấp)\n")
    f.write(f"# KHÔNG kết luận — bảng đặt-dao cho ANALYSIS + Tiên ký 27/09\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["nac","vol_x","taker","n_fires","n_episodes","n_uncens",
                                       "hits","rate","matched_rate","lift","ci_5","ci_95","pct_delist_mass"])
    w.writeheader()
    for r in grid_rows:
        w.writerow({
            "nac": r["nac"], "vol_x": r["vol_x"], "taker": r["taker"],
            "n_fires": r["n_fires"], "n_episodes": r["n_episodes"], "n_uncens": r["n_uncens"],
            "hits": r["hits"], "rate": f"{r['rate']:.4f}",
            "matched_rate": f"{r.get('matched_rate',0):.4f}" if r.get("matched_rate") is not None else "",
            "lift": f"{r['lift']:.4f}" if r.get("lift") is not None else "",
            "ci_5": f"{r['ci_5']:.4f}" if r.get("ci_5") is not None else "",
            "ci_95": f"{r['ci_95']:.4f}" if r.get("ci_95") is not None else "",
            "pct_delist_mass": f"{r['pct_delist_mass']:.4f}",
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
