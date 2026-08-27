"""(3) SURVEY DOM-LEVEL execution · KÝ 27/08 · SEED=42 reproducible · BscScan-free 0-Nansen

Nhóm A: tracker §10 rev9 (BANK · TUT · CYS · AKE · BTW · HEMI) — chép, cấm fetch
Nhóm B: 11 PERP-CÂM annex 17d45fbf (V③-v3 SÓT-VS-CROSS)
Nhóm C: 15 token control-52 chọn ngẫu SEED=42
Nhóm D: 10 fw-139 ngoài A∪B∪C cùng SEED=42

Reproducible: random.seed(42) · sample(pool, n) — script re-run cho same output.

BLOCKER (documented): BscScan V1 endpoint DEPRECATED (per API response 27/08);
  Etherscan V2 API cho BSC requires PAID plan ("Free API access is not supported for this chain").
  → SURVEY execute BLOCKED cho holder data.
  Skeleton bên dưới có token assembly + placeholder N/A-SOURCE-FREE-BLOCKED.
  → CẦN OPERATOR ký: (a) PRO API key path, hoặc (b) alternative source, hoặc (c) scope adjust.
"""
from __future__ import annotations
import sys, io, json, hashlib, csv, random, urllib.request
from pathlib import Path

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
from gom_h_daily import _load_universe, _md5

SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
OUT_CSV = REPO / "docs/reports/survey_dom_level_20260831.csv"
SEED = 42

# ═══════════════════════════════════════════════════════════════════════════════
# Nhóm A — chép §10 tracker rev9 (cấm fetch)
# Source: docs/proposals/phase_tag_v0_4_proven_case_findings_20260821.md §10
# ═══════════════════════════════════════════════════════════════════════════════
# Format: (token, top100_raw_from_tracker, note) · sửa 27/08: đủ 9 dòng per operator
NHOM_A = [
    ("BANK", 0.51,  "BANK §10 · 51%"),
    ("TUT",  0.83,  "TUT §10 · 83% (embedded text: 'kho 83% trên sàn, top-100')"),
    ("CYS",  0.81,  "CYS §10 · 81%"),
    ("AKE",  0.86,  "AKE §10 · 86% (+50%)"),
    ("BTW",  0.96,  "BTW §10 · 96%"),
    ("HEMI", None,  "HEMI §10 · row shows '770M' (raw supply count) — N/A-METRIC-MISMATCH"),
    ("ON",   None,  "ON §10 · KHÔNG có top-100 số — N/A-SOURCE-TRACKER"),
    ("CAP",  None,  "CAP §10 · KHÔNG có top-100 số — N/A-SOURCE-TRACKER"),
    ("BTR",  None,  "BTR §10/§15 · KHÔNG có top-100 số — N/A-SOURCE-TRACKER"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# Nhóm B — 11 PERP-CÂM từ V③-v3 SÓT-VS-CROSS · annex v2 md5 17d45fbfc7bccf382e64e570238e770d
# ═══════════════════════════════════════════════════════════════════════════════
NHOM_B = ["ACU", "ARIA", "ENSO", "FF", "FHE", "LIGHT", "MUBARAK", "SQD", "TRADOOR", "TUT", "XNY"]

# ═══════════════════════════════════════════════════════════════════════════════
# Nhóm C — 15 tokens control-52 chọn SEED=42
# control-52 = fw-139 - 9-case - DQ_members - Nhóm B (dedup) — theo V③-v3 build
# ═══════════════════════════════════════════════════════════════════════════════
D0_9CASE = {"BANK", "TUT", "CYS", "AKE", "BTW", "HEMI", "ON", "CAP", "BTR"}
DQ_MEMBERS = {"BANANAS31"}

symbols = _load_universe()
tokens_all = [s[:-4] if s.endswith("USDT") else s for s in symbols]
nhom_b_set = set(NHOM_B)
nhom_a_set = {t[0] for t in NHOM_A}
control_pool = [t for t in tokens_all if t not in D0_9CASE and t not in DQ_MEMBERS
                and t not in nhom_b_set and t not in nhom_a_set]

# Reproducible: seed(42), sort pool for determinism, then sample
random.seed(SEED)
pool_sorted = sorted(control_pool)
NHOM_C = random.sample(pool_sorted, min(15, len(pool_sorted)))

# ═══════════════════════════════════════════════════════════════════════════════
# Nhóm D — 10 fw-139 ngoài A∪B∪C · cùng SEED=42
# ═══════════════════════════════════════════════════════════════════════════════
excluded = nhom_a_set | nhom_b_set | set(NHOM_C) | D0_9CASE | DQ_MEMBERS
remaining_pool = sorted([t for t in tokens_all if t not in excluded])
# Continue seed state (already seed=42 above, next sample will differ from C)
NHOM_D = random.sample(remaining_pool, min(10, len(remaining_pool)))

# ═══════════════════════════════════════════════════════════════════════════════
# Load contract addresses per token (from Nansen snapshot latest)
# ═══════════════════════════════════════════════════════════════════════════════
CONTRACTS = {}
for p in sorted(SNAPS.glob("*.json"), reverse=True)[:5]:  # latest 5 snapshots
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if not r: continue
        s = (r.get("symbol") or "").upper()
        tok = r.get("token", "")
        if s and tok and s not in CONTRACTS:
            CONTRACTS[s] = tok

# ═══════════════════════════════════════════════════════════════════════════════
# Chain detection per contract (BSC 0x + heuristic)
# ═══════════════════════════════════════════════════════════════════════════════
def detect_chain(contract):
    """Naive: BSC uses 0x prefix + 40 hex (same as ETH). Nansen snapshot=BSC context.
    In real survey, need chain per-token mapping. For now: assume BSC (Nansen bot=BSC only)."""
    if not contract or not contract.startswith("0x"): return "unknown"
    return "bsc"  # Nansen bot CHAIN=bnb (per core_nansen.py)

# ═══════════════════════════════════════════════════════════════════════════════
# BscScan-free tokenholderlist — BLOCKED (V1 deprecated · V2 BSC = paid · WEB Cloudflare)
# Test 27/08: 3 paths tested, all blocked:
#   1. BscScan V1 API `/api?module=stats/token` → DEPRECATED (per response 27/08)
#   2. Etherscan V2 API chainid=56 → 402 Free access not supported for BSC (paid tier)
#   3. bscscan.com/token/generic-tokenholders2 web page → HTTP 403 Cloudflare challenge
# ═══════════════════════════════════════════════════════════════════════════════
def fetch_top100_holders_bscscan_free(contract):
    """DOCUMENTED FAIL — 3 free paths blocked 27/08.
    Returns dict with sentinel."""
    return {
        "status": "N/A-SOURCE-FREE-BLOCKED",
        "reason": "3 paths tested 27/08: V1 API deprecated · V2 API BSC paid · web Cloudflare-403",
        "top100_raw": None,
        "top100_ex_exchange": None,
        "top100_ex_structural": None,
        "n_holders_fetched": 0,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# Assemble rows
# ═══════════════════════════════════════════════════════════════════════════════
print("═" * 100)
print("[SURVEY DOM-LEVEL · KÝ 27/08 · SEED=42 reproducible · BscScan-free 0-Nansen]")
print("═" * 100)
print(f"random.seed({SEED}) · random.sample(sorted(pool), n)")
print(f"Nhóm A: {len(NHOM_A)} (chép §10 rev9)")
print(f"Nhóm B: {len(NHOM_B)} (PERP-CÂM annex 17d45fbf)")
print(f"Nhóm C: {len(NHOM_C)} (control-52 SEED=42)")
print(f"Nhóm D: {len(NHOM_D)} (fw-139 outside A∪B∪C SEED=42)")
print()
print(f"Nhóm A tokens: {[t[0] for t in NHOM_A]}")
print(f"Nhóm B tokens: {NHOM_B}")
print(f"Nhóm C tokens: {NHOM_C}")
print(f"Nhóm D tokens: {NHOM_D}")
print()

rows = []
# Nhóm A: source=tracker (no fetch)
for tok, top100_raw, note in NHOM_A:
    contract = CONTRACTS.get(tok + "USDT") or CONTRACTS.get(tok, "unknown")
    chain = detect_chain(contract)
    rows.append({
        "nhom": "A",
        "token": tok,
        "contract": contract,
        "chain": chain,
        "source": "tracker-§10-rev9",
        "top100_raw":         f"{top100_raw:.3f}" if top100_raw is not None else "N/A-METRIC",
        "top100_ex_exchange": "N/A-TRACKER-NO-BREAKDOWN",
        "top100_ex_structural": "N/A-TRACKER-NO-BREAKDOWN",
        "n_holders_fetched": "—",
        "status": "TRACKER-OK" if top100_raw else "N/A-METRIC-MISMATCH",
        "note": note,
    })

# Nhóm B/C/D: source=bscscan-free (all blocked)
for nhom, tokens_list in [("B", NHOM_B), ("C", NHOM_C), ("D", NHOM_D)]:
    for tok in tokens_list:
        contract = CONTRACTS.get(tok + "USDT") or CONTRACTS.get(tok, "unknown")
        chain = detect_chain(contract)
        if chain != "bsc":
            rows.append({
                "nhom": nhom, "token": tok, "contract": contract, "chain": chain,
                "source": "bscscan-free",
                "top100_raw": "N/A-SOURCE-CHAIN", "top100_ex_exchange": "N/A-SOURCE-CHAIN",
                "top100_ex_structural": "N/A-SOURCE-CHAIN", "n_holders_fetched": 0,
                "status": "N/A-SOURCE-CHAIN-NON-BSC",
                "note": f"chain={chain} not BSC — BscScan doesn't cover",
            })
            continue
        result = fetch_top100_holders_bscscan_free(contract)
        rows.append({
            "nhom": nhom, "token": tok, "contract": contract, "chain": chain,
            "source": "bscscan-free",
            "top100_raw": result["top100_raw"] or "N/A-SOURCE-FREE-BLOCKED",
            "top100_ex_exchange": result["top100_ex_exchange"] or "N/A-SOURCE-FREE-BLOCKED",
            "top100_ex_structural": result["top100_ex_structural"] or "N/A-SOURCE-FREE-BLOCKED",
            "n_holders_fetched": result["n_holders_fetched"],
            "status": result["status"],
            "note": result["reason"],
        })

# ═══════════════════════════════════════════════════════════════════════════════
# Bảng tóm — theo directive
# ═══════════════════════════════════════════════════════════════════════════════
from statistics import median
def _num(v):
    try: return float(v)
    except: return None

summary = []
for nhom in ["A", "B", "C", "D"]:
    grp = [r for r in rows if r["nhom"] == nhom]
    for thuoc in ["top100_raw", "top100_ex_exchange", "top100_ex_structural"]:
        vals = sorted([_num(r[thuoc]) for r in grp if _num(r[thuoc]) is not None])
        n_ge_80 = sum(1 for v in vals if v >= 0.80)
        n = len(vals)
        med = median(vals) if vals else None
        p25 = vals[int(n*0.25)] if n >= 4 else None
        p75 = vals[int(n*0.75)] if n >= 4 else None
        summary.append({
            "nhom": nhom, "thuoc": thuoc,
            "n_valid": n, "n_total": len(grp),
            "median": f"{med:.3f}" if med is not None else "—",
            "p25": f"{p25:.3f}" if p25 is not None else "—",
            "p75": f"{p75:.3f}" if p75 is not None else "—",
            "n_ge_0.80": n_ge_80,
        })

# Coverage per chain
chain_coverage = {}
for r in rows:
    ch = r["chain"]
    chain_coverage.setdefault(ch, {"total": 0, "success": 0})
    chain_coverage[ch]["total"] += 1
    if r["status"] in ("TRACKER-OK",) or ("N/A" not in r["status"]):
        chain_coverage[ch]["success"] += 1

# Print summary
print("[BẢNG TÓM — median / p25-p75 × nhóm × thước + đếm ≥0.80]")
print(f"  {'nhóm':>5} {'thước':>25} {'n_valid':>8} {'n_total':>8} {'median':>8} {'p25':>7} {'p75':>7} {'≥0.80':>7}")
for s in summary:
    print(f"  {s['nhom']:>5} {s['thuoc']:>25} {s['n_valid']:>8} {s['n_total']:>8} {s['median']:>8} {s['p25']:>7} {s['p75']:>7} {s['n_ge_0.80']:>7}")

print()
print("[CHAIN COVERAGE]")
for ch, c in chain_coverage.items():
    print(f"  {ch:>10}: {c['success']}/{c['total']}")

# Write CSV
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# SURVEY DOM-LEVEL · KÝ 27/08 · SEED={SEED} reproducible\n")
    f.write(f"# Nhóm A={len(NHOM_A)} (§10 tracker rev9) · B={len(NHOM_B)} (PERP-CÂM annex 17d45fbf) · C={len(NHOM_C)} (control-52 SEED=42) · D={len(NHOM_D)} (fw-139 outside A∪B∪C SEED=42)\n")
    f.write(f"# Reproducible: random.seed({SEED}); random.sample(sorted(pool), n)\n")
    f.write(f"# Nhóm C: {NHOM_C}\n")
    f.write(f"# Nhóm D: {NHOM_D}\n")
    f.write(f"# BLOCKER: 3 paths tested 27/08 free access - ALL BLOCKED:\n")
    f.write(f"#   1. BscScan V1 API `/api?module=stats/token`  → DEPRECATED (per response 27/08)\n")
    f.write(f"#   2. Etherscan V2 API `chainid=56`             → HTTP 402 'Free access not supported for BSC'\n")
    f.write(f"#   3. bscscan.com/token/generic-tokenholders2   → HTTP 403 Cloudflare challenge\n")
    f.write(f"#   → Nhóm B/C/D top100_dom = N/A-SOURCE-FREE-BLOCKED\n")
    f.write(f"#\n")
    f.write(f"# PRICE TABLE 2-cột trình operator ký (không tự chọn):\n")
    f.write(f"#   (a) Etherscan V2 paid tier:\n")
    f.write(f"#       Free tier: KHÔNG hỗ trợ BSC (docs: 'no free tier for BNB Chain')\n")
    f.write(f"#       Lite plan: $49/mo (5 calls/sec) · [tier THẤP NHẤT cho BSC access]\n")
    f.write(f"#       Standard:  $199/mo (10 calls/sec · 200K daily calls)\n")
    f.write(f"#       Source: https://apis.io/plans/etherscan/etherscan-plans-pricing/\n")
    f.write(f"#   (b) Alternative rẻ nhất: BSCTrace (MegaNode) - free tier BNB Chain\n")
    f.write(f"#       'Free tier for small projects · one paid tier for larger use'\n")
    f.write(f"#       Endpoints: JSON-RPC 2.0 + enhanced (nr_getAssetTransfers)\n")
    f.write(f"#       Source: https://www.bnbchain.org/en/blog/migration-guide-bscscan-api-to-bsctrace-api-via-meganode\n")
    f.write(f"#   (c) 🛑 LOẠI: Nansen (vi phạm 0-Nansen constraint + phá cap 2/day)\n")
    f.write(f"#   → CẦN OPERATOR KÝ (a) hoặc (b) · agent không tự chọn\n")
    f.write(f"#\n")
    f.write(f"# Nhóm A: source=tracker §10 rev9 (cấm fetch) · sửa 27/08 đủ 9 dòng\n")
    f.write(f"#   BANK 51% · TUT 83% · CYS 81% · AKE 86% · BTW 96% · HEMI N/A-METRIC-MISMATCH\n")
    f.write(f"#   ON N/A-SOURCE-TRACKER · CAP N/A-SOURCE-TRACKER · BTR N/A-SOURCE-TRACKER\n")
    f.write(f"#   thước ex-exchange/ex-structural: N/A-TRACKER-NO-BREAKDOWN\n")
    f.write(f"#\n")
    f.write(f"# BẢNG TÓM per nhóm × thước:\n")
    for s in summary:
        f.write(f"#   {s['nhom']} × {s['thuoc']}: n_valid={s['n_valid']}/{s['n_total']} median={s['median']} p25={s['p25']} p75={s['p75']} n≥0.80={s['n_ge_0.80']}\n")
    f.write(f"#\n")
    f.write(f"# CHAIN COVERAGE:\n")
    for ch, c in chain_coverage.items():
        f.write(f"#   {ch}: {c['success']}/{c['total']}\n")
    f.write(f"#\n")
    if rows:
        cols = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print()
print(f"[OUT] {OUT_CSV.name}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
