"""ANNEX-125c · SPOTCVD-20260901 · zero-call · KÝ 01/09

Control cụm-hóa · bảng cuối:
  (1) QUIET-CONTROL PER-EPISODE: tập quiet-days (px_min30≤1.3, không đòi CVD) →
      luật-4 <14d-gap cluster per-token → mỗi cụm best_fwd_30d
      + chiều dài cụm (số window) — cờ [LENGTH-MISMATCH] nếu pass-cụm dài hơn hẳn
  (2) BẢNG VERDICT per-episode: {pass · quiet-episodized · lift} + luật-check
      hits=3 <[5] → luật-2 vùng Nhiễu (nguyên văn, KHÔNG kết luận)
  (3) Cross-ref: ENSO = FORMULA-NEAR (U-v3 annex, oi 5.6%) ∧ CVD+ pre-D_cross · n=1

CSV + md5 + wc. KHÔNG kết luận · bảng cho ANALYSIS.
"""
import sys, io, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
D3_CSV = ROOT / "docs" / "reports" / "spot_cvd_d3_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_annex125c_20260828.csv"

TP_THRESHOLD = 0.50
EPISODE_GAP = 14
PX_MIN30_MAX = 1.30
LUAT_2_MIN_HITS = 5  # hits < 5 → vùng Nhiễu (luật-2)

# ── Load pass-windows (D3) ──
pass_rows = []
with open(D3_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 9: continue
        if p[8] == "True":
            pass_rows.append({"symbol": p[0], "date": p[1],
                              "px_min30": float(p[7])})
print(f"[LOAD] D3 pass-windows: {len(pass_rows)}")

# ── Load store binance_spot ──
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
print(f"[LOAD] binance_spot rows: {len(all_df)} · sym: {all_df['symbol'].nunique()}")
DATA_LAST = max(all_df["date_str"].unique())

sym_series = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    sym_series[sym] = {"dates": g["date_str"].tolist(), "closes": g["close"].tolist()}

def _fwd_ret(sym, end_date, n_days=30):
    s = sym_series.get(sym)
    if not s: return None, True
    try: idx = s["dates"].index(end_date)
    except ValueError: return None, True
    end_close = s["closes"][idx]
    if end_close <= 0: return None, True
    future = s["closes"][idx+1:idx+1+n_days]
    if not future: return None, True
    censored = len(future) < n_days
    return max(future)/end_close - 1.0, censored

# ── Cluster function (luật-4) ──
def cluster_episodes(rows):
    """rows: [{symbol, date, ...}] · Return list of episodes (each = list of rows)."""
    by_sym = {}
    for r in rows: by_sym.setdefault(r["symbol"], []).append(r)
    episodes = []
    for sym in sorted(by_sym):
        srtd = sorted(by_sym[sym], key=lambda x: x["date"])
        cur = []; prev_date = None
        for r in srtd:
            cur_date = date.fromisoformat(r["date"])
            if prev_date is not None and (cur_date - prev_date).days >= EPISODE_GAP:
                if cur: episodes.append(cur); cur = []
            cur.append(r); prev_date = cur_date
        if cur: episodes.append(cur)
    return episodes

def summarize_episodes(episodes, label):
    """Return dict with n_ep · uncens · hits · rate + length stats."""
    ep_recs = []
    for ep in episodes:
        sym = ep[0]["symbol"]
        n_win = len(ep)
        fwds = [_fwd_ret(sym, w["date"], 30) for w in ep]
        valid = [(f,c) for f,c in fwds if f is not None]
        if not valid:
            ep_recs.append({"sym":sym,"n":n_win,"best":None,"cens":True,"hit":False})
            continue
        best = max(f for f,c in valid)
        # censored if any window in ep is censored (conservative)
        cens = any(c for f,c in valid) or len(valid) < len(fwds)
        hit = (best >= TP_THRESHOLD)
        ep_recs.append({"sym":sym,"n":n_win,"best":best,"cens":cens,"hit":hit})
    uncens = [e for e in ep_recs if not e["cens"]]
    n_hit = sum(1 for e in uncens if e["hit"])
    rate = n_hit / len(uncens) if uncens else 0.0
    lens = [e["n"] for e in ep_recs]
    lens_uncens = [e["n"] for e in uncens]
    print(f"\n[{label}] n_ep={len(episodes)} · uncens={len(uncens)} · hits≥+50%={n_hit} · rate={rate:.2%}")
    if lens:
        print(f"  len (all ep): median={median(lens):.1f} · p75={sorted(lens)[int(len(lens)*0.75)]}" if len(lens)>=4 else f"  len (all ep): median={median(lens):.1f}")
    if lens_uncens:
        print(f"  len (uncens): median={median(lens_uncens):.1f} · p75={sorted(lens_uncens)[int(len(lens_uncens)*0.75)]}" if len(lens_uncens)>=4 else f"  len (uncens): median={median(lens_uncens):.1f}")
    return {"n_ep": len(episodes), "uncens": len(uncens), "hits": n_hit, "rate": rate,
            "recs": ep_recs,
            "med_len_all": median(lens) if lens else 0,
            "med_len_uncens": median(lens_uncens) if lens_uncens else 0,
            "p75_len_all": sorted(lens)[int(len(lens)*0.75)] if len(lens)>=4 else (lens[-1] if lens else 0),
            "p75_len_uncens": sorted(lens_uncens)[int(len(lens_uncens)*0.75)] if len(lens_uncens)>=4 else (lens_uncens[-1] if lens_uncens else 0)}

# ── (1) PASS episodes (từ D3) ──
pass_eps = cluster_episodes(pass_rows)
pass_stats = summarize_episodes(pass_eps, "PASS 3-leg")

# ── (2) QUIET-CONTROL: build quiet-days (px_min30 ≤ 1.3) then episodize ──
print(f"\n[QUIET-CONTROL] build quiet-days (px_min30 ≤ {PX_MIN30_MAX})")
quiet_rows = []
for sym, s in sym_series.items():
    closes = s["closes"]; dates = s["dates"]; n = len(closes)
    for i in range(29, n):
        wc = closes[i-29:i+1]
        if len(wc) < 30: continue
        end_close = closes[i]; min_close = min(wc)
        if min_close <= 0 or end_close <= 0: continue
        px = end_close / min_close
        if px <= PX_MIN30_MAX:
            quiet_rows.append({"symbol": sym, "date": dates[i], "px_min30": px})
print(f"[QUIET-CONTROL] quiet-day rows: {len(quiet_rows)}")

quiet_eps = cluster_episodes(quiet_rows)
quiet_stats = summarize_episodes(quiet_eps, "QUIET-CONTROL episodized")

# ── LENGTH-MISMATCH flag (bidirectional) ──
p_med = pass_stats["med_len_all"]; q_med = quiet_stats["med_len_all"]
p_p75 = pass_stats["p75_len_all"]; q_p75 = quiet_stats["p75_len_all"]
if p_med > q_med * 1.5:
    flag = "[LENGTH-MISMATCH pass>quiet] best-of-nhiều-lá ăn gian PASS xác suất per-episode"
elif q_med > p_med * 1.5:
    ratio = q_med / p_med if p_med else 0
    flag = f"[LENGTH-MISMATCH quiet>pass · quiet {ratio:.1f}× dài hơn pass] best-of-nhiều-lá ăn gian QUIET xác suất per-episode — quiet 100% hit rate là nhân tạo (episode length quá dài · max fwd_30d across nhiều window)"
else:
    flag = "[LENGTH-OK]"
print(f"\n[LENGTH] pass med={p_med:.1f} p75={p_p75} · quiet med={q_med:.1f} p75={q_p75}")
print(f"  {flag}")

# ── BẢNG VERDICT (per-episode) ──
lift_ep = pass_stats["rate"] - quiet_stats["rate"]
lift_x = pass_stats["rate"] / quiet_stats["rate"] if quiet_stats["rate"] else 0
print(f"\n[BẢNG VERDICT per-episode uncens]")
print(f"  pass 3-leg              : {pass_stats['hits']}/{pass_stats['uncens']}  = {pass_stats['rate']:.2%}")
print(f"  quiet-episodized        : {quiet_stats['hits']}/{quiet_stats['uncens']}  = {quiet_stats['rate']:.2%}")
print(f"  lift pass vs quiet-ep   : {lift_ep:+.2%} ({lift_x:.2f}x)")

# Luật-2 check
n_hits_pass = pass_stats["hits"]
if n_hits_pass < LUAT_2_MIN_HITS:
    luat_2_note = f"hits={n_hits_pass} <[{LUAT_2_MIN_HITS}] → luật-2 vùng Nhiễu (KHÔNG kết luận cửa (a)/(b) — bàn ANALYSIS)"
else:
    luat_2_note = f"hits={n_hits_pass} ≥[{LUAT_2_MIN_HITS}] → luật-2 KHÔNG kích (đủ sample chấm được)"
print(f"\n[LUẬT-2] {luat_2_note}")

# ── (3) Cross-ref ENSO ──
enso_ep = next((e for e in pass_stats["recs"] if e["sym"]=="ENSOUSDT"), None)
cross_ref = ""
if enso_ep:
    cross_ref = (f"ENSO = FORMULA-NEAR (U-v3 annex, oi 5.6%) ∧ CVD+ episode pre-D_cross "
                 f"(best_fwd_30d={enso_ep['best']:+.2%}, hit={enso_ep['hit']}) · n=1 · ghi sổ, không mở việc")
    print(f"\n[CROSS-REF] {cross_ref}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# ANNEX-125c · SPOTCVD-20260901 · zero-call · KÝ 01/09\n")
    f.write(f"# Source: D3 CSV md5 7154bcd0806248ba1687d08391b415b9 (125 pass-windows)\n")
    f.write(f"# Store: {len(all_df)} rows binance_spot · {all_df['symbol'].nunique()} sym · last={DATA_LAST}\n")
    f.write(f"# TP threshold: fwd_ret_30d ≥ +{TP_THRESHOLD:.0%} · Episode gap <{EPISODE_GAP}d\n")
    f.write(f"# Quiet filter: px_min30 ≤ {PX_MIN30_MAX} (KHÔNG đòi CVD 2-chân)\n")
    f.write(f"# Censor rule: window <30d data sau end → censored (episode censored nếu bất kỳ window trong episode censored)\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số ───\n")
    f.write(f"#   PASS 3-leg CVD: n_windows={len(pass_rows)} · n_episodes={pass_stats['n_ep']} · uncens={pass_stats['uncens']}\n")
    f.write(f"#   QUIET-CONTROL px_min30≤1.3: n_days={len(quiet_rows)} · n_episodes={quiet_stats['n_ep']} · uncens={quiet_stats['uncens']}\n")
    f.write(f"#\n")
    f.write(f"# ─── LENGTH stats (số window/episode) ───\n")
    f.write(f"#   PASS  ep length: median={p_med:.1f}  p75={p_p75}  (all ep)\n")
    f.write(f"#   QUIET ep length: median={q_med:.1f}  p75={q_p75}  (all ep)\n")
    f.write(f"#   FLAG: {flag}\n")
    f.write(f"#\n")
    f.write(f"# ─── BẢNG VERDICT (per-episode uncens · fwd_30d ≥ +{TP_THRESHOLD:.0%}) ───\n")
    f.write(f"#   pass 3-leg              : {pass_stats['hits']}/{pass_stats['uncens']}  = {pass_stats['rate']:.2%}\n")
    f.write(f"#   quiet-episodized        : {quiet_stats['hits']}/{quiet_stats['uncens']}  = {quiet_stats['rate']:.2%}\n")
    f.write(f"#   lift pass vs quiet-ep   : {lift_ep:+.2%} ({lift_x:.2f}x)\n")
    f.write(f"#\n")
    f.write(f"# ─── LUẬT-2 CHECK ───\n")
    f.write(f"#   {luat_2_note}\n")
    f.write(f"#\n")
    if cross_ref:
        f.write(f"# ─── CROSS-REF ENSO (n=1 · ghi sổ) ───\n")
        f.write(f"#   {cross_ref}\n")
        f.write(f"#\n")
    f.write(f"# KHÔNG kết luận — bảng cho ANALYSIS\n")
    f.write(f"#\n")
    # Records: emit quiet-episodes summary (compact)
    w = csv.DictWriter(f, fieldnames=["control_set","symbol","n_windows","best_fwd_ret_30d","hit_ge_50pct","censored"])
    w.writeheader()
    for e in pass_stats["recs"]:
        w.writerow({"control_set":"pass_3leg","symbol":e["sym"],"n_windows":e["n"],
                    "best_fwd_ret_30d":f"{e['best']:.6f}" if e["best"] is not None else "",
                    "hit_ge_50pct":e["hit"], "censored":e["cens"]})
    # quiet: only include top-20 largest episodes to keep CSV manageable
    quiet_sorted = sorted(quiet_stats["recs"], key=lambda x: -x["n"])
    for e in quiet_sorted[:20]:
        w.writerow({"control_set":"quiet_top20_by_len","symbol":e["sym"],"n_windows":e["n"],
                    "best_fwd_ret_30d":f"{e['best']:.6f}" if e["best"] is not None else "",
                    "hit_ge_50pct":e["hit"], "censored":e["cens"]})

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
