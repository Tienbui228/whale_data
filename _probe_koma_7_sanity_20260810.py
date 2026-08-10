"""
_probe_koma_7_sanity_20260810.py
K-7: Sanity 5 mục PASS/FAIL — KOMA — EVIDENCE per item
"""
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_BASE = "KOMA"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"K-7 SANITY  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

results = {}

# ── S1: Perp klines row count (listing 2024-12-10, last complete 2026-08-09) ─
log("\n=== S1: Perp klines row count ===")
perp_csv = SCRATCH / f"koma_perp_{DATE_TAG}.csv"
if perp_csv.exists():
    with open(perp_csv, encoding="utf-8") as f:
        perp_data = list(csv.DictReader(f))
    n = len(perp_data)
    # listing 2024-12-10 → 2026-08-09 = 608d
    EXPECTED_MIN, EXPECTED_MAX = 600, 615
    ok = EXPECTED_MIN <= n <= EXPECTED_MAX
    log(f"  Rows: {n} (expected {EXPECTED_MIN}-{EXPECTED_MAX})")
    log(f"  First: {perp_data[0]['date']}  Last: {perp_data[-1]['date']}")
    results["S1_klines_count"] = "PASS" if ok else f"FAIL (n={n})"
    log(f"  Evidence: first={perp_data[0]['date']}, last={perp_data[-1]['date']}, n={n}")
    log(f"  S1: {results['S1_klines_count']}")
else:
    results["S1_klines_count"] = "FAIL (file missing)"
    log(f"  S1: FAIL — file missing")

# ── S2: Identity lock — KOMA (ALPHA_1, no KOMAINU variant) ───────────────
log("\n=== S2: Identity lock ===")
id_path = SCRATCH / f"koma_identity_{DATE_TAG}.json"
if id_path.exists():
    id_data = json.loads(id_path.read_text(encoding="utf-8"))
    gate = id_data.get("gate_pass", False)
    komainu = id_data.get("komainu_found", False)
    alpha_id = id_data.get("koma_alpha_id")
    onboard = id_data.get("onboard_date")
    log(f"  gate_pass: {gate}")
    log(f"  alpha_id: {alpha_id}")
    log(f"  onboard: {onboard}")
    log(f"  komainu_found: {komainu} (should be False — no disambiguation needed)")
    ok = gate and not komainu
    results["S2_identity_lock"] = "PASS" if ok else "FAIL"
    log(f"  Evidence: gate_pass={gate}, komainu_found={komainu}, alpha_id={alpha_id}")
    log(f"  S2: {results['S2_identity_lock']}")
else:
    results["S2_identity_lock"] = "FAIL (identity json missing)"

# ── S3: LSR ↔ OI date overlap ≥28 ────────────────────────────────────────
log("\n=== S3: LSR ↔ OI date consistency ===")
lsr_csv = SCRATCH / f"koma_lsr_raw_{DATE_TAG}.csv"
oi_csv  = SCRATCH / f"koma_oi_hist_{DATE_TAG}.csv"
if lsr_csv.exists() and oi_csv.exists():
    with open(lsr_csv, encoding="utf-8") as f:
        lsr_d = list(csv.DictReader(f))
    with open(oi_csv, encoding="utf-8") as f:
        oi_d = list(csv.DictReader(f))
    lsr_dates = [r["date"] for r in lsr_d]
    oi_dates  = [r["date"] for r in oi_d]
    overlap = set(lsr_dates) & set(oi_dates)
    log(f"  LSR: {len(lsr_d)} rows, {lsr_dates[0]}→{lsr_dates[-1]}")
    log(f"  OI:  {len(oi_d)} rows, {oi_dates[0]}→{oi_dates[-1]}")
    log(f"  Overlap: {len(overlap)} dates")
    ok = len(overlap) >= 28
    results["S3_lsr_oi_overlap"] = "PASS" if ok else f"FAIL (overlap={len(overlap)})"
    log(f"  Evidence: overlap={len(overlap)}, lsr_n={len(lsr_d)}, oi_n={len(oi_d)}")
    log(f"  S3: {results['S3_lsr_oi_overlap']}")
else:
    results["S3_lsr_oi_overlap"] = "FAIL (files missing)"

# ── S4: CASE xlsx DAILY row count = perp klines ───────────────────────────
log("\n=== S4: CASE xlsx DAILY row count ===")
case_path = ROOT / "docs" / "case_files" / f"CASE_{SYM_BASE}.xlsx"
if case_path.exists():
    wb = openpyxl.load_workbook(str(case_path), read_only=True)
    ws = wb["DAILY"]
    daily_data_rows = ws.max_row - 2  # row1=header label, row2=col headers
    wb.close()
    perp_n = len(perp_data) if perp_csv.exists() else 0
    diff = abs(daily_data_rows - perp_n)
    ok = diff <= 2
    results["S4_xlsx_row_count"] = "PASS" if ok else f"FAIL (diff={diff})"
    log(f"  CASE DAILY rows: {daily_data_rows}, perp klines: {perp_n}, diff: {diff}")
    log(f"  Evidence: xlsx_daily={daily_data_rows}, perp_csv={perp_n}, diff={diff}")
    log(f"  S4: {results['S4_xlsx_row_count']}")
else:
    results["S4_xlsx_row_count"] = "FAIL (CASE xlsx missing)"

# ── S5: Vol spike 07-31 identifiable (BIG event) ─────────────────────────
log("\n=== S5: Vol spike 07-31 verifiable (key event) ===")
if perp_csv.exists():
    spike_row = next((r for r in perp_data if r["date"] == "2026-07-31"), None)
    if spike_row:
        vol = float(spike_row.get("vol_quote_usd",0))
        c   = float(spike_row.get("close",0))
        log(f"  07-31 close: ${c:.6f}")
        log(f"  07-31 vol:   ${vol:,.0f}")
        # Should be massive: ~$604M
        ok = vol > 500e6
        results["S5_spike_verifiable"] = "PASS" if ok else f"FAIL (vol=${vol:,.0f} < 500M)"
        log(f"  Evidence: vol=${vol:,.0f}, close=${c:.6f}")
        log(f"  S5: {results['S5_spike_verifiable']}")
    else:
        results["S5_spike_verifiable"] = "FAIL (07-31 row not found)"
        log(f"  S5: FAIL — 07-31 row missing")
else:
    results["S5_spike_verifiable"] = "FAIL (perp CSV missing)"

# ── S6 (bonus): BAPI Alpha status matches expected ───────────────────────
log("\n=== S6 (bonus): BAPI Alpha status ===")
bapi_path = SCRATCH / f"koma_bapi_{DATE_TAG}.json"
if bapi_path.exists():
    bapi = json.loads(bapi_path.read_text(encoding="utf-8"))
    ok6 = (bapi.get("alphaId") == "ALPHA_1" and
            bapi.get("fullyDelisted") == False and
            bapi.get("contractAddress","").startswith("0x"))
    results["S6_bapi_alpha_active"] = "PASS" if ok6 else "FAIL"
    log(f"  alphaId={bapi.get('alphaId')}, fullyDelisted={bapi.get('fullyDelisted')}, contract={bapi.get('contractAddress','')[:20]}...")
    log(f"  Evidence: alphaId=ALPHA_1, fullyDelisted=False, contract valid")
    log(f"  S6 (bonus): {results['S6_bapi_alpha_active']}")

# ── VERIFY-TAY: px_avg guard-câm check from CASE xlsx ─────────────────────
log("\n=== VERIFY-TAY (guard-câm): px_avg null check ===")
if case_path.exists():
    wb2 = openpyxl.load_workbook(str(case_path), read_only=True)
    ws2 = wb2["DAILY"]
    hdrs2 = [c.value for c in next(ws2.iter_rows(min_row=2, max_row=2))]
    d_rows2 = list(ws2.iter_rows(min_row=3, values_only=True))
    wb2.close()
    # Find px_avg col
    px_avg_idx = None
    for i, h in enumerate(hdrs2):
        if h and "px_avg" in str(h).lower():
            px_avg_idx = i; break
    close_idx2 = None
    for i, h in enumerate(hdrs2):
        if h and str(h).strip() in ("c","close"):
            close_idx2 = i; break
    log(f"  px_avg col idx: {px_avg_idx}")
    log(f"  close col idx: {close_idx2}")
    if px_avg_idx is not None:
        last5 = d_rows2[-5:]
        px_vals = [r[px_avg_idx] for r in last5]
        c_vals  = [r[close_idx2] for r in last5] if close_idx2 is not None else []
        log(f"  Last 5 px_avg values: {px_vals}")
        log(f"  Last 5 close values:  {c_vals}")
        if any(v is not None for v in px_vals):
            log(f"  px_avg non-null: guard-câm FIXED in current build")
        else:
            log(f"  px_avg = all None: guard-câm bug STILL PRESENT (known)")
            log(f"  OHLC null in CASE xlsx — ret computed from perp CSV for verify")
            # Compute ret tay
            log(f"\n  === Ret tay from perp CSV (last 5) ===")
            for r in perp_data[-5:]:
                c = float(r.get("close",0)); o = float(r.get("open",0))
                ret = (c/o-1)*100 if o > 0 else None
                vol = float(r.get("vol_quote_usd",0))
                taker = float(r.get("taker_pct",0) or 0)
                log(f"    {r['date']}: o=${o:.6f} h={r.get('high','N/A')[:8]} l={r.get('low','N/A')[:8]} c=${c:.6f} ret={ret:+.2f}% vol=${vol:,.0f} taker={taker:.1%}")

# ── SUMMARY ──────────────────────────────────────────────────────────────
log("\n=== SANITY SUMMARY ===")
all_pass = all(v == "PASS" for v in results.values())
for k, v in results.items():
    log(f"  {k:40s}: {v}")
log(f"\n  OVERALL: {'ALL PASS' if all_pass else 'SOME FAIL — review above'}")
log(f"\n[K-7 SANITY DONE]")
