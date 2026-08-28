"""ANNEX-125d · SPOTCVD-20260901 · zero-call · KÝ 01/09 · VÒNG CUỐI

MATCHED-CONTROL bootstrap:
  · Pool = quiet-days (px_min30 ≤ 1.3) TRỪ windows in pass-set (chống nhiễm)
  · Per-token cluster như cũ (luật-4 <14d gap)
  · Bootstrap N=1000 draws:
    - L = random pick từ 5 pass-episode uncens lengths (có hoàn lại)
    - Pick random (token, start_idx) sao cho có ≥ L consecutive quiet windows liên tiếp
      ∧ uncensored (last window end + 30d ≤ data_last)
    - best_fwd_30d = max fwd across L windows in block
    - hit ≥ +50%?
  · Table: {n_draws · matched-rate · per-L breakdown} + lift = 0.60 / matched-rate

Cutline auto-select văn bia:
  · lift ≤ 1.3× → CLOSED-DEAD (b)-sạch
  · lift ≥ 2.0× → CLOSED-THIN
  · giữa       → KNOWN-GAP-LIGHT
"""
import sys, io, csv, hashlib, glob, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
from statistics import median, mean
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
D3_CSV = ROOT / "docs" / "reports" / "spot_cvd_d3_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_annex125d_20260828.csv"

TP_THRESHOLD = 0.50
PX_MIN30_MAX = 1.30
N_DRAWS = 1000
SEED = 42
PASS_RATE = 0.60  # 3/5 uncens episodes hit
random.seed(SEED)

# ── Load pass-windows (D3 pass-set for exclusion) ──
pass_windows = set()  # {(sym, date)}
with open(D3_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 9 or p[8] != "True": continue
        pass_windows.add((p[0], p[1]))
print(f"[LOAD] pass_windows to exclude: {len(pass_windows)}")

# ── Load store binance_spot ──
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
DATA_LAST = max(all_df["date_str"].unique())
print(f"[LOAD] binance_spot rows: {len(all_df)} · sym: {all_df['symbol'].nunique()} · last={DATA_LAST}")

# Build per-symbol closes + dates arrays
sym_series = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    sym_series[sym] = {"dates": g["date_str"].tolist(), "closes": g["close"].tolist()}

# ── Compute quiet-days per token, EXCLUDING pass-set ──
print(f"[BUILD] quiet-days per token (px_min30 ≤ {PX_MIN30_MAX}, exclude pass-set)")
# For each symbol, mark each index as (is_quiet, fwd_ret_30d, uncensored)
sym_marked = {}
for sym, s in sym_series.items():
    closes = s["closes"]; dates = s["dates"]; n = len(closes)
    marks = []  # list of (is_quiet, fwd_ret, uncens_30d) per index i (i = window_end)
    for i in range(n):
        if i < 29:
            marks.append((False, None, False)); continue
        wc = closes[i-29:i+1]
        end_close = closes[i]; min_close = min(wc)
        if min_close <= 0 or end_close <= 0:
            marks.append((False, None, False)); continue
        px = end_close / min_close
        is_quiet = px <= PX_MIN30_MAX
        # Exclude pass-set
        if (sym, dates[i]) in pass_windows: is_quiet = False
        # Forward return
        future = closes[i+1:i+31]
        uncens = len(future) == 30
        fwd = max(future)/end_close - 1.0 if future else None
        marks.append((is_quiet, fwd, uncens))
    sym_marked[sym] = marks

# ── Pass-episode uncensored lengths (5 lengths as operator specified) ──
# From D3 pass-windows: 3 uncens ep sizes (ENSO=11, HOME=4, OPEN=14) + 2 non-hit uncens (CHEEMS=27, TUT=4)
# Rebuild via cluster
by_sym = {}
for (sym, dt) in pass_windows:
    by_sym.setdefault(sym, []).append(dt)
EPISODE_GAP = 14
pass_ep_lens_uncens = []
for sym, dts in by_sym.items():
    dts.sort()
    cur = []; prev = None
    eps = []
    for dt in dts:
        d = date.fromisoformat(dt)
        if prev is not None and (d - prev).days >= EPISODE_GAP:
            if cur: eps.append(cur); cur = []
        cur.append(dt); prev = d
    if cur: eps.append(cur)
    for ep in eps:
        # Check uncensored: last date + 30d ≤ data_last
        end_date = ep[-1]
        end_d = date.fromisoformat(end_date)
        data_last_d = date.fromisoformat(DATA_LAST)
        if (data_last_d - end_d).days >= 30:
            pass_ep_lens_uncens.append(len(ep))

print(f"[PASS-EP uncens lens]: {sorted(pass_ep_lens_uncens)}")

# ── BOOTSTRAP N=1000 matched draws ──
print(f"\n[BOOTSTRAP] N={N_DRAWS} · seed={SEED} · sample L from pass-ep uncens lengths")
sym_list = list(sym_series.keys())
draws = []  # each: (L, sym, start_idx, best_fwd, hit)
failed_pick = 0

for draw_i in range(N_DRAWS):
    L = random.choice(pass_ep_lens_uncens)
    # Try up to 100 times to find valid block
    picked = None
    for attempt in range(100):
        sym = random.choice(sym_list)
        marks = sym_marked[sym]
        n = len(marks)
        # Need L consecutive quiet-uncens indices
        if n < L: continue
        # Random start
        start = random.randint(0, n - L)
        # Check L consecutive quiet + all uncens
        block = marks[start:start+L]
        if all(m[0] and m[2] for m in block):
            fwds = [m[1] for m in block if m[1] is not None]
            if fwds:
                best = max(fwds)
                picked = (L, sym, start, best, best >= TP_THRESHOLD)
                break
    if picked is None:
        failed_pick += 1
        continue
    draws.append(picked)

print(f"[BOOTSTRAP] valid draws: {len(draws)}/{N_DRAWS} · failed_pick: {failed_pick}")

n_hit = sum(1 for _,_,_,_,h in draws if h)
matched_rate = n_hit / len(draws) if draws else 0
lift = PASS_RATE / matched_rate if matched_rate > 0 else float('inf')
print(f"[MATCHED-RATE] {n_hit}/{len(draws)} = {matched_rate:.2%}")
print(f"[LIFT] pass_rate {PASS_RATE:.2%} / matched_rate = {lift:.2f}x")

# Per-L breakdown
per_l = {}
for L, sym, start, best, hit in draws:
    per_l.setdefault(L, {"n": 0, "hits": 0})
    per_l[L]["n"] += 1
    per_l[L]["hits"] += int(hit)
print(f"\n[PER-L breakdown]:")
for L in sorted(per_l):
    s = per_l[L]
    r = s["hits"]/s["n"] if s["n"] else 0
    print(f"  L={L:2d}: {s['hits']:3d}/{s['n']:3d} = {r:.2%}")

# ── CUTLINE văn bia auto-select ──
if lift <= 1.3:
    ban_bia_key = "CLOSED-DEAD"
    ban_bia_text = (f"SPOT-CVD-SHADOW CLOSED-DEAD 01/09 — matched-control bootstrap "
                    f"(N={len(draws)} draws · length-matched · seed={SEED}): "
                    f"lift = {lift:.2f}× ≤ 1.3× → không phân biệt được với quiet-random cùng length. "
                    f"Rule chết sạch (b), không dấu vết ăn gian. GÓI ĐÓNG: "
                    f"bundle → MA-only 3 ô [1.0×]/[3%]/[45%] · store spot-51 giữ (MA consumer + đọc-case) · "
                    f"D4-fixture/HYPER/D5 CANCELLED (render CVD không tồn tại nữa).")
elif lift >= 2.0:
    ban_bia_key = "CLOSED-THIN"
    ban_bia_text = (f"SPOT-CVD-SHADOW CLOSED-THIN 01/09 — matched-control bootstrap "
                    f"(N={len(draws)} draws · length-matched · seed={SEED}): "
                    f"lift = {lift:.2f}× ≥ 2× → tín hiệu THẬT nhưng n=3 hits (luật-2 vùng Nhiễu). "
                    f"Đóng vì không đủ base sample chấm số. Store spot-51 + case-file lưu, "
                    f"chờ n≥5 hits (evidence-ceil operator ký tương lai). GÓI ĐÓNG: "
                    f"bundle → MA-only 3 ô [1.0×]/[3%]/[45%] · D4-fixture/HYPER/D5 CANCELLED.")
else:
    ban_bia_key = "KNOWN-GAP-LIGHT"
    ban_bia_text = (f"SPOT-CVD-SHADOW KNOWN-GAP-LIGHT 01/09 — matched-control bootstrap "
                    f"(N={len(draws)} draws · length-matched · seed={SEED}): "
                    f"lift = {lift:.2f}× (1.3 < x < 2). Không đủ chết sạch (b), không đủ thin-signal (c). "
                    f"Gap có tên, chờ chủ tương lai. GÓI ĐÓNG: "
                    f"bundle → MA-only 3 ô [1.0×]/[3%]/[45%] · D4-fixture/HYPER/D5 CANCELLED.")

print(f"\n[CUTLINE] văn bia trúng: {ban_bia_key}")
print(f"[VĂN BIA]:\n  {ban_bia_text}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# ANNEX-125d · SPOTCVD-20260901 · zero-call · KÝ 01/09 · VÒNG CUỐI\n")
    f.write(f"# Source: D3 CSV md5 7154bcd0806248ba1687d08391b415b9 · Store: 51 sym binance_spot · last={DATA_LAST}\n")
    f.write(f"# Bootstrap: N={N_DRAWS} draws · seed={SEED} · pool=quiet-days (px_min30 ≤ {PX_MIN30_MAX}) TRỪ pass-windows\n")
    f.write(f"# L (block length) rút từ pass-ep uncens lengths: {sorted(pass_ep_lens_uncens)}\n")
    f.write(f"# Censor rule: block uncens ⇔ tất cả L windows có fwd_ret_30d đầy đủ (last end + 30d ≤ data_last)\n")
    f.write(f"# Best-of rule: best_fwd_30d = max fwd across L windows trong block\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số ───\n")
    f.write(f"#   PASS episodes uncens: n=5 · rate={PASS_RATE:.2%} · lens={sorted(pass_ep_lens_uncens)}\n")
    f.write(f"#   MATCHED draws valid: {len(draws)}/{N_DRAWS} · failed_pick={failed_pick}\n")
    f.write(f"#\n")
    f.write(f"# ─── MATCHED-RATE + LIFT ───\n")
    f.write(f"#   matched-rate: {n_hit}/{len(draws)} = {matched_rate:.2%}\n")
    f.write(f"#   pass-rate   : {PASS_RATE:.2%}\n")
    f.write(f"#   LIFT        : {PASS_RATE:.2%} / {matched_rate:.2%} = {lift:.2f}x\n")
    f.write(f"#\n")
    f.write(f"# ─── PER-L BREAKDOWN ───\n")
    for L in sorted(per_l):
        s = per_l[L]
        r = s["hits"]/s["n"] if s["n"] else 0
        f.write(f"#   L={L:2d}: {s['hits']:3d}/{s['n']:3d} = {r:.2%}\n")
    f.write(f"#\n")
    f.write(f"# ─── CUTLINE AUTO-SELECT ───\n")
    f.write(f"#   Cutline rule: lift ≤ 1.3× → CLOSED-DEAD · lift ≥ 2.0× → CLOSED-THIN · giữa → KNOWN-GAP-LIGHT\n")
    f.write(f"#   VĂN BIA TRÚNG: {ban_bia_key}\n")
    f.write(f"#\n")
    f.write(f"# ─── VĂN BIA VERBATIM (merge upstream banner + changelog) ───\n")
    for line in ban_bia_text.split("."):
        if line.strip(): f.write(f"#   {line.strip()}.\n")
    f.write(f"#\n")
    f.write(f"# KHÔNG kết luận cửa nào ngoài văn bia cutline-auto — bàn ANALYSIS lưu bảng\n")
    f.write(f"#\n")
    # Draws detail (compact)
    w = csv.DictWriter(f, fieldnames=["draw_i","L","symbol","start_idx","best_fwd_ret_30d","hit_ge_50pct"])
    w.writeheader()
    for i, (L, sym, start, best, hit) in enumerate(draws):
        w.writerow({"draw_i":i, "L":L, "symbol":sym, "start_idx":start,
                    "best_fwd_ret_30d":f"{best:.6f}", "hit_ge_50pct":hit})

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")

# Print structured result for wrapper to use
print(f"\n[VERDICT-KEY] {ban_bia_key}")
print(f"[LIFT-NUM] {lift:.4f}")
