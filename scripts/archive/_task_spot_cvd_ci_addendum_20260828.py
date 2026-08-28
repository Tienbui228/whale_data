"""CI-ADDENDUM 125d · SPOTCVD-CLOSED-20260901 · zero-call · KÝ 01/09

Joint bootstrap từ data đã có (không draw block mới):
  N=10,000 vòng · seed=42
  Per vòng:
    tử = resample-có-hoàn-lại 5 pass-episode-uncens outcomes {1,1,1,0,0} → pass_rate_i
    mẫu = resample-có-hoàn-lại 1000 matched-outcomes (109 hits · 891 misses) → matched_rate_i
      · Nếu matched_rate_i = 0 → BỎ vòng (count skipped)
    lift_i = pass_rate_i / matched_rate_i
  CI = percentile [5%, 95%]

NHÁNH CƠ HỌC:
  CI_5% ≥ 2.0 → giữ CLOSED-THIN + append "lift 5.50× (CI-90% [a,b])"
  CI_5% < 2.0 → THAY văn bia sang GỘP KNOWN-GAP-LIGHT + reopen n≥5 + CI line
"""
import sys, io, csv, hashlib, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from statistics import quantiles

ROOT = Path(r"D:\Data back test\whale_data")
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_ci_addendum_20260828.csv"

# Inputs (fixed từ ANNEX-125d results, không re-run)
PASS_OUTCOMES = [1, 1, 1, 0, 0]  # ENSO hit, HOME hit, OPEN hit, CHEEMS miss, TUT miss
MATCHED_HITS = 109
MATCHED_MISSES = 891  # 1000 - 109
MATCHED_OUTCOMES = [1]*MATCHED_HITS + [0]*MATCHED_MISSES
N_ROUNDS = 10_000
SEED = 42
POINT_LIFT = 5.50

random.seed(SEED)

lifts = []
skipped = 0
for i in range(N_ROUNDS):
    # Numerator resample
    pass_sample = random.choices(PASS_OUTCOMES, k=len(PASS_OUTCOMES))
    pass_rate_i = sum(pass_sample) / len(pass_sample)
    # Denominator resample
    matched_sample = random.choices(MATCHED_OUTCOMES, k=len(MATCHED_OUTCOMES))
    matched_rate_i = sum(matched_sample) / len(matched_sample)
    if matched_rate_i == 0:
        skipped += 1
        continue
    lifts.append(pass_rate_i / matched_rate_i)

print(f"[BOOTSTRAP] N={N_ROUNDS} · seed={SEED} · skipped (matched_rate=0): {skipped}")
print(f"[BOOTSTRAP] valid lifts: {len(lifts)}")

lifts_sorted = sorted(lifts)
ci_5 = lifts_sorted[int(len(lifts_sorted) * 0.05)]
ci_95 = lifts_sorted[int(len(lifts_sorted) * 0.95)]
median_lift = lifts_sorted[len(lifts_sorted) // 2]
p25 = lifts_sorted[int(len(lifts_sorted) * 0.25)]
p75 = lifts_sorted[int(len(lifts_sorted) * 0.75)]

print(f"\n[CI RESULT]")
print(f"  point lift    : {POINT_LIFT:.2f}×")
print(f"  bootstrap med : {median_lift:.2f}×")
print(f"  CI-90%        : [{ci_5:.2f}×, {ci_95:.2f}×]")
print(f"  IQR (25-75)   : [{p25:.2f}×, {p75:.2f}×]")

# NHÁNH CƠ HỌC
CUTLINE_CI = 2.0
if ci_5 >= CUTLINE_CI:
    branch = "CLOSED-THIN-KEEP"
    print(f"\n[NHÁNH] CI_5% = {ci_5:.2f}× ≥ {CUTLINE_CI} → GIỮ CLOSED-THIN (append CI line vào văn bia)")
    verdict_line = f"lift {POINT_LIFT:.2f}× (CI-90% [{ci_5:.2f}×, {ci_95:.2f}×], joint bootstrap N={N_ROUNDS//1000}k · seed={SEED})"
    verdict_text = None  # unchanged, only append line
else:
    branch = "GỘP-KNOWN-GAP-LIGHT"
    print(f"\n[NHÁNH] CI_5% = {ci_5:.2f}× < {CUTLINE_CI} → THAY sang GỘP KNOWN-GAP-LIGHT")
    verdict_line = f"lift {POINT_LIFT:.2f}× point · CI-90% [{ci_5:.2f}×, {ci_95:.2f}×] joint bootstrap N={N_ROUNDS//1000}k · seed={SEED}"
    verdict_text = (f"SPOT-CVD-SHADOW GỘP KNOWN-GAP-LIGHT 01/09 (CI-amendment) — point lift {POINT_LIFT:.2f}× "
                    f"nhưng joint bootstrap N={N_ROUNDS//1000}k CI-90% [{ci_5:.2f}×, {ci_95:.2f}×]: CI_5% < 2.0 "
                    f"→ hai vế (a) chết-sạch (CI_5% có phần dưới 1.3) hoặc (c) thin-signal cùng khả năng · "
                    f"gap có tên · reopen khi n ≥ 5 hits (evidence-ceil operator ký tương lai). "
                    f"GÓI ĐÓNG y nguyên: bundle MA-only 3 ô [1.0×]/[3%]/[45%] · D4/HYPER/D5 CANCELLED · "
                    f"store spot-51 giữ (MA + case). Vận hành KHÔNG đổi (chỉ tinh chỉnh văn bia · changelog "
                    f"CI-amendment cùng ngày).")

print(f"\n[VERDICT LINE]: {verdict_line}")
if verdict_text:
    print(f"\n[NEW VĂN BIA]:\n  {verdict_text}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# CI-ADDENDUM 125d · SPOTCVD-CLOSED-20260901 · zero-call · KÝ 01/09\n")
    f.write(f"# Joint bootstrap từ data ANNEX-125d (không draw block mới)\n")
    f.write(f"# N={N_ROUNDS} vòng · seed={SEED}\n")
    f.write(f"# Tử: resample-có-hoàn-lại 5 pass-ep-uncens outcomes {PASS_OUTCOMES} (3 hits · 2 miss)\n")
    f.write(f"# Mẫu: resample-có-hoàn-lại 1000 matched-outcomes ({MATCHED_HITS} hits · {MATCHED_MISSES} miss)\n")
    f.write(f"# Skip rule: matched_rate_i = 0 → bỏ vòng\n")
    f.write(f"# lift_i = pass_rate_i / matched_rate_i\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số ───\n")
    f.write(f"#   n_rounds_total: {N_ROUNDS}\n")
    f.write(f"#   n_skipped (matched_rate=0): {skipped}\n")
    f.write(f"#   n_valid_lifts: {len(lifts)}\n")
    f.write(f"#\n")
    f.write(f"# ─── CI RESULT ───\n")
    f.write(f"#   point lift          : {POINT_LIFT:.2f}×\n")
    f.write(f"#   bootstrap median    : {median_lift:.2f}×\n")
    f.write(f"#   IQR (25-75)         : [{p25:.2f}×, {p75:.2f}×]\n")
    f.write(f"#   CI-90% [5%, 95%]    : [{ci_5:.2f}×, {ci_95:.2f}×]\n")
    f.write(f"#\n")
    f.write(f"# ─── NHÁNH CƠ HỌC (theo ANALYSIS ký trước) ───\n")
    f.write(f"#   Cutline CI_5% ≥ 2.0 → giữ CLOSED-THIN (append line)\n")
    f.write(f"#   Cutline CI_5% < 2.0 → THAY sang GỘP KNOWN-GAP-LIGHT\n")
    f.write(f"#   BRANCH TRÚNG: {branch}\n")
    f.write(f"#\n")
    f.write(f"# ─── VERDICT LINE (append vào changelog) ───\n")
    f.write(f"#   {verdict_line}\n")
    f.write(f"#\n")
    if verdict_text:
        f.write(f"# ─── VĂN BIA MỚI VERBATIM (thay bản CLOSED-THIN) ───\n")
        for chunk in verdict_text.split(". "):
            if chunk.strip():
                f.write(f"#   {chunk.strip().rstrip('.')}.\n")
        f.write(f"#\n")
    f.write(f"# Vận hành KHÔNG đổi (GÓI ĐÓNG y nguyên · CI-amendment cùng ngày)\n")
    f.write(f"#\n")
    # Distribution rows: histogram bins
    w = csv.DictWriter(f, fieldnames=["bin_low","bin_high","n_lifts_in_bin"])
    w.writeheader()
    # 20 bins from 0 to max lift
    max_lift = max(lifts)
    bin_w = max_lift / 20
    bins = [0]*20
    for L in lifts:
        b = min(int(L / bin_w), 19)
        bins[b] += 1
    for i, cnt in enumerate(bins):
        w.writerow({"bin_low":f"{i*bin_w:.3f}", "bin_high":f"{(i+1)*bin_w:.3f}", "n_lifts_in_bin":cnt})

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
print(f"\n[BRANCH-KEY] {branch}")
