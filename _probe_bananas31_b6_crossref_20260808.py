"""
_probe_bananas31_b6_crossref_20260808.py
B-6: VPS cross-ref, freshwatch, gom_scan, ledger grep, BscScan check.
"""
import sys, io, csv, json, urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYMBOL = "BANANAS31"
SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
CONTRACT = "0x3d4f0513e8a29669b960f9dbca61861548a9a760"

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("="*70)
log(f"BANANAS31 B-6 CROSS-REF  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("="*70)

# ── 1. freshwatch 2026-07 — BANANAS31 rows ────────────────────────────────────
log("\n--- freshwatch 2026-07 (BANANAS31 rows) ---")
fw_path = SCRATCH / "freshwatch_daily_2026-07.csv"
fw_rows = []
if fw_path.exists():
    with open(fw_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","") or row.get("Symbol","")
            if "BANANA" in sym.upper():
                fw_rows.append(row)
    log(f"  freshwatch rows for BANANAS31: {len(fw_rows)}")
    if fw_rows:
        # Show headers
        log(f"  Columns: {list(fw_rows[0].keys())}")
        # Show last 5 rows
        log(f"  Last 5 rows:")
        for r in fw_rows[-5:]:
            log(f"    {r}")
else:
    log(f"  freshwatch 2026-07: NOT FOUND at {fw_path}")

# freshwatch 2026-06 if exists
fw6_path = SCRATCH / "freshwatch_daily_2026-06.csv"
if fw6_path.exists():
    with open(fw6_path, encoding="utf-8") as f:
        rows6 = [r for r in csv.DictReader(f)
                 if "BANANA" in (r.get("symbol","") or r.get("Symbol","")).upper()]
    log(f"  freshwatch 2026-06 rows: {len(rows6)}")

# ── 2. screen_thresholds.yaml ─────────────────────────────────────────────────
log("\n--- screen_thresholds.yaml ---")
thresh = Path(r"D:\Data back test\whale_data\screen_thresholds.yaml")
if thresh.exists():
    with open(thresh, encoding="utf-8") as f:
        for line in f:
            if "BANANA" in line.upper():
                log(f"  {line.rstrip()}")
else:
    log("  screen_thresholds.yaml not found")

# ── 3. gom_scan.py output check ────────────────────────────────────────────────
log("\n--- gom_scan output (BANANAS31) ---")
gom_report = Path(r"D:\Data back test\whale_data\docs\reports\gom_gate6_full_20260808.txt")
if gom_report.exists():
    with open(gom_report, encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "BANANA" in content.upper():
        lines = [l for l in content.split("\n") if "BANANA" in l.upper()]
        log(f"  Found {len(lines)} BANANA lines in gom_gate6_full:")
        for l in lines[:10]:
            log(f"    {l}")
    else:
        log(f"  BANANAS31 not in gom_gate6_full_20260808.txt (checked, clean)")
else:
    log(f"  gom_gate6_full_20260808.txt not found")

# Also check scratch gom diag
gom_diag = Path(r"D:\Data back test\whale_data\docs\reports\gom_diag_20260808.txt")
if gom_diag.exists():
    with open(gom_diag, encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "BANANA" in content.upper():
        lines = [l for l in content.split("\n") if "BANANA" in l.upper()]
        log(f"  Found in gom_diag_20260808.txt: {lines[:5]}")
    else:
        log(f"  BANANAS31 not in gom_diag_20260808.txt")

# ── 4. Grep BANANAS31 trong case files ────────────────────────────────────────
log("\n--- Grep BANANAS31 in case files ---")
for f in CASE_DIR.glob("*.xlsx"):
    # Can't grep xlsx directly — check by filename
    log(f"  Case file: {f.name}")

# Check INDEX.md
idx_md = Path(r"D:\Data back test\whale_data\docs\INDEX.md")
if idx_md.exists():
    with open(idx_md, encoding="utf-8") as f:
        content = f.read()
    if "BANANA" in content.upper():
        lines = [l for l in content.split("\n") if "BANANA" in l.upper()]
        log(f"  INDEX.md BANANA lines: {lines}")
    else:
        log(f"  INDEX.md: BANANAS31 not registered yet (expected)")

# agent_log.md
alog = Path(r"D:\Data back test\whale_data\agent_log.md")
if alog.exists():
    with open(alog, encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "BANANA" in content.upper():
        lines = [l for l in content.split("\n") if "BANANA" in l.upper()]
        log(f"  agent_log.md BANANA lines: {len(lines)}")
    else:
        log(f"  agent_log.md: BANANAS31 not mentioned (new case)")

# ── 5. BscScan 0-credit: top holders ──────────────────────────────────────────
log(f"\n--- BscScan top holders (0-credit) ---")
log(f"  Contract: {CONTRACT}")
# BscScan public endpoint (no API key) — try tokenholderchart
bsc_url = (f"https://api.bscscan.com/api?module=token&action=tokenholderlist"
           f"&contractaddress={CONTRACT}&page=1&offset=20")
bsc_raw = fetch_json(bsc_url, timeout=20)
if isinstance(bsc_raw, dict) and bsc_raw.get("status") == "1":
    holders = bsc_raw.get("result", [])
    log(f"  Top holders ({len(holders)}):")
    total_supply = 10_000_000_000
    for h in holders[:10]:
        bal = float(h.get("TokenHolderQuantity", 0) or 0) / 1e18
        pct = bal / total_supply * 100
        log(f"    {h.get('TokenHolderAddress','')} — {bal:,.0f} ({pct:.2f}%)")
else:
    log(f"  BscScan tokenholderlist: {bsc_raw.get('message','?')} (may need API key)")
    # Try alternative: tokenbalance for known exchange addresses
    # Binance hot wallet BSC: check if known
    log(f"  Trying tokenbalance for known BSC exchange addresses...")
    known_addrs = {
        "Binance-peg hot1": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",
        "Binance-peg hot2": "0xe2fc31f816a9b94326492132018c3aecc4a93ae1",
        "Binance cold":     "0xf977814e90da44bfa03b6295a0616a897441acec",
    }
    for name, addr in known_addrs.items():
        url = (f"https://api.bscscan.com/api?module=account&action=tokenbalance"
               f"&contractaddress={CONTRACT}&address={addr}&tag=latest")
        r = fetch_json(url, timeout=10)
        if isinstance(r, dict) and r.get("status") == "1":
            bal = float(r.get("result", 0)) / 1e18
            pct = bal / total_supply * 100
            log(f"    {name} ({addr}): {bal:,.0f} tokens ({pct:.2f}%)")
        else:
            log(f"    {name}: {r.get('message','?') if isinstance(r,dict) else r}")

# ── 6. Alpha ID resolver — check if ALPHA_21 has numeric ID ──────────────────
log(f"\n--- Alpha store path check ---")
# Check where the alpha store actually is
for candidate in [
    Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d"),
    Path(r"D:\Data back test\whale_data\data\raw"),
    Path(r"D:\Data back test\whale_data\data"),
]:
    if candidate.exists():
        dirs = [d.name for d in candidate.iterdir() if d.is_dir()]
        log(f"  {candidate}: {dirs[:10]}")
        break

# Check if there's alpha data under a different path
for d in Path(r"D:\Data back test\whale_data\data").rglob("venue=binance_alpha"):
    log(f"  Found alpha venue dir: {d}")

log(f"\n[B-6 DONE]")
