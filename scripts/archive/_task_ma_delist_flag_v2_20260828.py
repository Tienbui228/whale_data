"""MA-D3 DELIST-FLAG v2 · ERRATA v1 · KÝ 01/09 · zero-call

ERRATA v1: "DEATH-MIMICRY 94.77%" RÚT — alpha-graduation ≠ death trên spot-51 universe
+ zero-discrimination (94.77% ≈ base 96.1%). L-48/L-51 context-inversion đăng sổ.

Flag v2 sources (SỬA NGHĨA):
  (1) spot_status ≠ TRADING (exchangeInfo public) — halt thật
  (2) network-withdrawal curated (khuôn triage SOPH · cite nguồn từng dòng)
  (3) deposit-closed: N/A-SOURCE (sapi/capital cần auth · KHÔNG proxy bừa)
  (4) walletset BROAD-QUIET: chỉ đếm khi ≥3 ĐÊM data · walletset mới sống 1-2 đêm
      → N/A-IMMATURE

Kỳ vọng: flag co về ~1-3 tokens (SOPH chắc)

Output bảng DEATH-MIMICRY THẬT:
  Per-token {flag-v2 · n_fires · fire_rate}
  So cặp fire-rate {flagged vs unflagged}
  %fire-mass-v2
"""
import sys, io, csv, hashlib, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from collections import Counter

ROOT = Path(r"D:\Data back test\whale_data")
MA_CSV = ROOT / "docs" / "reports" / "ma_shadow_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "ma_delist_flag_v2_20260828.csv"
S6_MAP = ROOT / "scratch" / "s6_fw139_binance_spot_map_20260827.csv"

# ── (2) NETWORK-WITHDRAWAL curated list (cite từng dòng) ──
NETWORK_WITHDRAWAL_CURATED = {
    "SOPHUSDT": {
        "reason": "Binance ngừng deposit/withdrawal SOPH qua BSC network 2026-08-21 08:00 UTC (infrastructure adjustment · Monitoring Tag từ 2026-08-11)",
        "cites": [
            "https://www.cryptometer.io/news/binance-flags-five-tokens-as-possible-delisting-risks/",
            "https://crypto.news/binance-flags-5-tokens-as-possible-delisting-risks/",
            "https://bitcoinfoundation.org/news/crypto-companies-news/binance-puts-5-altcoins-on-delisting-watch-as-movr-and-glmr-prices-tumble/",
        ],
        "source_file": "docs/handover/soph_triage_20260827.md",
    },
    # Kỳ vọng thêm 1-2 token nếu ANALYSIS thấy pattern tương tự · hiện chỉ SOPH có evidence public
}

# ── 51 tokens ──
tokens_51 = []
with open(S6_MAP, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["has_binance_spot"] == "YES":
            tokens_51.append(r["symbol"] + "USDT")
print(f"[LOAD] 51 tokens")

# ── (1) exchangeInfo spot status ──
print(f"[FETCH-1] exchangeInfo spot status")
def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

ei = fetch_json("https://api.binance.com/api/v3/exchangeInfo")
ei_status = {s["symbol"]: s["status"] for s in ei.get("symbols", [])}
print(f"  {len(ei_status)} symbols · status of 51: {Counter(ei_status.get(t,'N/A') for t in tokens_51)}")

# ── Load MA fires ──
ma_fires = Counter()
n_days_per_sym = Counter()
with open(MA_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 8: continue
        n_days_per_sym[p[0]] += 1
        if p[7] == "True":
            ma_fires[p[0]] += 1

# ── Build per-token v2 flag ──
print(f"\n[FLAG v2 BUILD]")
rows = []
for tok in sorted(tokens_51):
    st = ei_status.get(tok, "N/A")
    flag_status = (st not in ["TRADING", "N/A"])
    net_curated = tok in NETWORK_WITHDRAWAL_CURATED
    # deposit-closed: N/A-SOURCE (no auth)
    # BROAD-QUIET: N/A-IMMATURE (walletset < 3 nights data)
    flag_any = flag_status or net_curated
    src = []
    if flag_status: src.append(f"spot_status={st}")
    if net_curated: src.append(f"network-withdrawal-curated")
    n_fire = ma_fires.get(tok, 0)
    n_days = n_days_per_sym.get(tok, 0)
    fire_rate = n_fire / n_days if n_days else 0.0
    rows.append({
        "token": tok, "n_fires": n_fire, "n_days": n_days, "fire_rate": fire_rate,
        "spot_status": st,
        "flag_status_not_trading": flag_status,
        "flag_network_withdrawal_curated": net_curated,
        "flag_deposit_closed": "N/A-SOURCE-NO-AUTH",
        "flag_walletset_broad_quiet": "N/A-IMMATURE-LT-3-NIGHTS",
        "flag_ANY_v2": flag_any,
        "sources": " | ".join(src) if src else "—",
    })

# Fire-mass v2
n_total_fires = sum(r["n_fires"] for r in rows)
n_v2_fires = sum(r["n_fires"] for r in rows if r["flag_ANY_v2"])
pct_v2 = n_v2_fires / n_total_fires * 100 if n_total_fires else 0

# Fire-rate compare (flagged vs unflagged)
flagged = [r for r in rows if r["flag_ANY_v2"]]
unflagged = [r for r in rows if not r["flag_ANY_v2"]]
flagged_fires = sum(r["n_fires"] for r in flagged)
flagged_days = sum(r["n_days"] for r in flagged)
unflagged_fires = sum(r["n_fires"] for r in unflagged)
unflagged_days = sum(r["n_days"] for r in unflagged)
rate_flagged = flagged_fires / flagged_days if flagged_days else 0
rate_unflagged = unflagged_fires / unflagged_days if unflagged_days else 0
rate_ratio = rate_flagged / rate_unflagged if rate_unflagged > 0 else float('inf')

print(f"\n[BẢNG DEATH-MIMICRY THẬT]")
print(f"  n_flagged (v2): {len(flagged)}/51 = {len(flagged)/51*100:.1f}%")
for r in flagged:
    print(f"    {r['token']:<14} n_fires={r['n_fires']:>3}/{r['n_days']} rate={r['fire_rate']:.2%}  ({r['sources']})")
print(f"\n  Fire-rate flagged   : {flagged_fires}/{flagged_days} = {rate_flagged:.2%}")
print(f"  Fire-rate unflagged : {unflagged_fires}/{unflagged_days} = {rate_unflagged:.2%}")
print(f"  Ratio (flagged/unflagged): {rate_ratio:.2f}x")
print(f"  %fire-mass v2: {n_v2_fires}/{n_total_fires} = {pct_v2:.2f}%")

# ── Errata banner + Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# MA-D3 DELIST-FLAG v2 · ERRATA v1 · KÝ 01/09\n")
    f.write(f"# ─── ERRATA (L-48/L-51 context-inversion) ───\n")
    f.write(f"#   RÚT v1 '\"DEATH-MIMICRY xác nhận 94.77%\" — alpha-graduation ≠ death trên spot-51 universe.\n")
    f.write(f"#   Zero-discrimination: 94.77% ≈ base 96.1% flagged tokens. Ref: v1 CSV md5 74a70b38 (SUPERSEDED).\n")
    f.write(f"#   Alpha fullyDelisted chỉ hợp lệ trên alpha-only universe (không spot listing).\n")
    f.write(f"#\n")
    f.write(f"# ─── FLAG v2 SOURCES ───\n")
    f.write(f"#   (1) spot_status ≠ TRADING (exchangeInfo public) — halt thật\n")
    f.write(f"#   (2) network-withdrawal curated (khuôn triage SOPH · cite nguồn từng dòng) — {len(NETWORK_WITHDRAWAL_CURATED)} tokens\n")
    for tok, info in NETWORK_WITHDRAWAL_CURATED.items():
        f.write(f"#       {tok}: {info['reason']}\n")
        for c in info["cites"]:
            f.write(f"#         · cite: {c}\n")
        f.write(f"#         · source_file: {info['source_file']}\n")
    f.write(f"#   (3) deposit-closed: N/A-SOURCE (sapi/capital cần auth · KHÔNG proxy bừa)\n")
    f.write(f"#   (4) walletset BROAD-QUIET: N/A-IMMATURE (walletset < 3 đêm data)\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số ───\n")
    f.write(f"#   51 tokens (s6 map has_binance_spot=YES)\n")
    f.write(f"#   MA fires source: docs/reports/ma_shadow_backtest_20260828.csv md5 b7e8277c\n")
    f.write(f"#   Total MA fires: {n_total_fires} across {n_days_per_sym.__len__()} tokens\n")
    f.write(f"#   Total MA days:  {sum(n_days_per_sym.values())} (per-day observations)\n")
    f.write(f"#\n")
    f.write(f"# ─── BẢNG DEATH-MIMICRY THẬT v2 ───\n")
    f.write(f"#   n_flagged: {len(flagged)}/51\n")
    for r in flagged:
        f.write(f"#     {r['token']:<14} n_fires={r['n_fires']}/{r['n_days']} rate={r['fire_rate']:.2%}  ({r['sources']})\n")
    f.write(f"#\n")
    f.write(f"# ─── FIRE-RATE COMPARE (flagged v2 vs unflagged) ───\n")
    f.write(f"#   flagged   fire_rate: {flagged_fires}/{flagged_days} = {rate_flagged:.2%}\n")
    f.write(f"#   unflagged fire_rate: {unflagged_fires}/{unflagged_days} = {rate_unflagged:.2%}\n")
    f.write(f"#   ratio (flagged/unflagged): {rate_ratio:.2f}x\n")
    f.write(f"#   %fire-mass v2: {n_v2_fires}/{n_total_fires} = {pct_v2:.2f}%\n")
    f.write(f"#\n")
    f.write(f"# KHÔNG kết luận — bảng cho ANALYSIS 27/09\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["token","n_fires","n_days","fire_rate","spot_status",
                                       "flag_status_not_trading","flag_network_withdrawal_curated",
                                       "flag_deposit_closed","flag_walletset_broad_quiet",
                                       "flag_ANY_v2","sources"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
