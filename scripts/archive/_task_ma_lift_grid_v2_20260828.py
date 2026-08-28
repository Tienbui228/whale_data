"""MA-D3 LIFT-GRID v2 · re-emit %delist column with v2 flags + Δlift-vs-nấc-kề · KÝ 01/09

Grid lift/CI numbers GIỮ NGUYÊN (độc lập flag). Chỉ update:
  · %delist column từ flag_v2 (SOPH duy nhất)
  · THÊM cột Δlift-vs-nấc-kề (adjacent nấc trong sequence vol_x ASC, taker ASC)
"""
import sys, io, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
FLAG_V2_CSV = ROOT / "docs" / "reports" / "ma_delist_flag_v2_20260828.csv"
GRID_V1_CSV = ROOT / "docs" / "reports" / "ma_lift_grid_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "ma_lift_grid_v2_20260828.csv"

RET_ABS_MAX = 0.03

# Load flag_v2
flag_v2 = {}
with open(FLAG_V2_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("token,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 10: continue
        flag_v2[p[0]] = (p[9] == "True")  # flag_ANY_v2
n_flagged = sum(1 for v in flag_v2.values() if v)
print(f"[LOAD] flag_v2: {n_flagged}/{len(flag_v2)} flagged")
flagged_tokens = {t for t, v in flag_v2.items() if v}
print(f"  flagged: {sorted(flagged_tokens)}")

# Load grid v1 rows
grid_v1_rows = []
with open(GRID_V1_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("nac,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 13: continue
        grid_v1_rows.append({
            "nac": p[0], "vol_x": float(p[1]), "taker": float(p[2]),
            "n_fires": int(p[3]), "n_episodes": int(p[4]), "n_uncens": int(p[5]),
            "hits": int(p[6]), "rate": float(p[7]),
            "matched_rate": float(p[8]) if p[8] else 0,
            "lift": float(p[9]) if p[9] else None,
            "ci_5": float(p[10]) if p[10] else None,
            "ci_95": float(p[11]) if p[11] else None,
            "pct_delist_mass_v1": float(p[12]),  # v1 old
        })
print(f"[LOAD] grid v1: {len(grid_v1_rows)} nấc")

# ── Rebuild features to count fires per nấc per token (need SOPH count per nấc) ──
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)

sym_features = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    closes = g["close"].tolist(); vols = g["quote_vol"].tolist(); takers = g["taker_buy_pct"].tolist()
    dates = g["date_str"].tolist()
    n = len(closes)
    feats = []
    for i in range(n):
        rec = {"date": dates[i], "vol_ratio": None, "ret_1d": None, "taker": None}
        if i >= 14 and closes[i] is not None:
            vols_prev14 = [v for v in vols[i-14:i] if v is not None and v > 0]
            if len(vols_prev14) >= 14 and vols[i] is not None and vols[i] > 0:
                med14 = median(vols_prev14)
                if med14 > 0:
                    rec["vol_ratio"] = vols[i] / med14
        if i >= 1 and closes[i] is not None and closes[i-1] is not None and closes[i-1] > 0:
            rec["ret_1d"] = closes[i] / closes[i-1] - 1.0
        rec["taker"] = takers[i]
        feats.append(rec)
    sym_features[sym] = feats

# For each nac, count fires per token
def count_fires_per_token(vol_x, taker_max):
    counts = {}
    for sym, feats in sym_features.items():
        c = 0
        for f in feats:
            if (f["vol_ratio"] is not None and f["vol_ratio"] >= vol_x and
                f["ret_1d"] is not None and abs(f["ret_1d"]) <= RET_ABS_MAX and
                f["taker"] is not None and f["taker"] <= taker_max):
                c += 1
        if c: counts[sym] = c
    return counts

print(f"\n[RE-EMIT] %delist_v2 per nấc + Δlift-vs-nấc-kề")

# Compute per-nac %delist v2
prev_lift = None
for r in grid_v1_rows:
    counts = count_fires_per_token(r["vol_x"], r["taker"])
    n_total = sum(counts.values())
    n_flag = sum(v for k, v in counts.items() if k in flagged_tokens)
    r["pct_delist_mass_v2"] = n_flag / n_total * 100 if n_total else 0.0
    r["n_flagged_fires"] = n_flag
    r["n_total_fires_recount"] = n_total
    # Δlift-vs-nấc-kề (sequential order)
    if prev_lift is not None and r["lift"] is not None:
        r["delta_lift_vs_prev"] = r["lift"] - prev_lift
    else:
        r["delta_lift_vs_prev"] = None
    prev_lift = r["lift"]

# Print
print(f"\n{'nấc':<18} {'fires':>5} {'lift':>6} {'Δlift-kề':>9} {'%delist_v1':>10} {'%delist_v2':>10} {'n_SOPH':>7}")
for r in grid_v1_rows:
    li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
    dl = f"{r['delta_lift_vs_prev']:+.2f}" if r["delta_lift_vs_prev"] is not None else "—"
    print(f"{r['nac']:<18} {r['n_fires']:>5} {li:>6} {dl:>9} {r['pct_delist_mass_v1']*100:>9.1f}% {r['pct_delist_mass_v2']:>9.1f}% {r['n_flagged_fires']:>7}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# MA-D3 LIFT-GRID v2 · %delist v2 + Δlift-vs-nấc-kề · KÝ 01/09\n")
    f.write(f"# ERRATA v1: %delist_v1 (alpha_fullyDelisted) RÚT — L-48/L-51 context-inversion\n")
    f.write(f"# Grid lift/CI GIỮ NGUYÊN (độc lập flag) · nguồn: docs/reports/ma_lift_grid_20260828.csv md5 81494a70\n")
    f.write(f"# Flag v2 source: docs/reports/ma_delist_flag_v2_20260828.csv md5 177c9e6c ({n_flagged}/51 flagged: {sorted(flagged_tokens)})\n")
    f.write(f"#\n")
    f.write(f"# ─── Δlift-vs-nấc-kề (adjacent trong sequence vol_x ASC, taker ASC) ───\n")
    f.write(f"#   Nấc 1 (vol1.0_tk40.0): baseline, Δ=—\n")
    f.write(f"#   Nấc 2..8: Δ = lift(this) − lift(prev)\n")
    f.write(f"#\n")
    f.write(f"# ─── GRID RESULTS v2 ───\n")
    f.write(f"# {'nấc':<18} {'fires':>5} {'lift':>7} {'CI-90%':<15} {'Δlift-kề':>9} {'%delist_v2':>10} {'n_SOPH':>7}\n")
    for r in grid_v1_rows:
        li = f"{r['lift']:.2f}x" if r["lift"] is not None else "N/A"
        ci = f"[{r['ci_5']:.2f},{r['ci_95']:.2f}]" if r["ci_5"] is not None else "N/A"
        dl = f"{r['delta_lift_vs_prev']:+.2f}" if r["delta_lift_vs_prev"] is not None else "—"
        f.write(f"#   {r['nac']:<18} {r['n_fires']:>5} {li:>7} {ci:<15} {dl:>9} {r['pct_delist_mass_v2']:>9.1f}% {r['n_flagged_fires']:>7}\n")
    f.write(f"#\n")
    f.write(f"# DEATH-MIMICRY THẬT: SOPH fires {sum(r['n_flagged_fires'] for r in grid_v1_rows)}/8 nấc\n")
    f.write(f"# Range %delist_v2: {min(r['pct_delist_mass_v2'] for r in grid_v1_rows):.1f}% ~ {max(r['pct_delist_mass_v2'] for r in grid_v1_rows):.1f}%\n")
    f.write(f"# (v1: 90.5-95.9% zero-discrimination · v2: SOPH-only signal thật)\n")
    f.write(f"# KHÔNG kết luận — bảng đặt-dao cho ANALYSIS + Tiên ký 27/09\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["nac","vol_x","taker","n_fires","n_episodes","n_uncens",
                                       "hits","rate","matched_rate","lift","ci_5","ci_95",
                                       "delta_lift_vs_prev","pct_delist_mass_v2","n_flagged_fires"])
    w.writeheader()
    for r in grid_v1_rows:
        w.writerow({
            "nac": r["nac"], "vol_x": r["vol_x"], "taker": r["taker"],
            "n_fires": r["n_fires"], "n_episodes": r["n_episodes"], "n_uncens": r["n_uncens"],
            "hits": r["hits"], "rate": f"{r['rate']:.4f}",
            "matched_rate": f"{r['matched_rate']:.4f}",
            "lift": f"{r['lift']:.4f}" if r["lift"] is not None else "",
            "ci_5": f"{r['ci_5']:.4f}" if r["ci_5"] is not None else "",
            "ci_95": f"{r['ci_95']:.4f}" if r["ci_95"] is not None else "",
            "delta_lift_vs_prev": f"{r['delta_lift_vs_prev']:.4f}" if r["delta_lift_vs_prev"] is not None else "",
            "pct_delist_mass_v2": f"{r['pct_delist_mass_v2']:.4f}",
            "n_flagged_fires": r["n_flagged_fires"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
