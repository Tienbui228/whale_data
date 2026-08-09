"""
_probe_xpin_lsr_diag_20260808.py
Diagnose XPIN LSR source — check FAPI endpoints, freshwatch Aug,
and scratch files for existing data.
"""
import sys, io, json, urllib.request, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"

def log(s=""): print(s)
log("=== XPIN LSR DIAGNOSTIC ===")

# ── Check scratch for existing Aug LSR data ───────────────────────────────────
log("\n--- Scratch files XPIN ---")
for f in sorted(SCRATCH.glob("*xpin*")):
    log(f"  {f.name} ({f.stat().st_size} bytes)")

# ── Check freshwatch files for Aug data ──────────────────────────────────────
log("\n--- Freshwatch CSV files in scratch ---")
fw_files = list(SCRATCH.glob("freshwatch_daily_*.csv"))
for fw in sorted(fw_files):
    log(f"  {fw.name}")
    with open(fw, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        xpin_rows = [r for r in reader if r.get("symbol","").upper()=="XPINUSDT"]
    if xpin_rows:
        dates = sorted(r.get("date","") for r in xpin_rows)
        log(f"    XPIN rows: {len(xpin_rows)}, range: {dates[0]}→{dates[-1]}")
        # Show last 3
        for r in xpin_rows[-3:]:
            log(f"    {r.get('date')}: lsr_pos={r.get('lsr_pos_r','?')} lsr_acc={r.get('lsr_acc_r','?')} glsr={r.get('lsr_global_r','?')}")
    else:
        log(f"    No XPIN rows")

# ── Also check VPS freshwatch path ───────────────────────────────────────────
log("\n--- Check VPS freshwatch Aug files ---")
VPS_FW = Path(r"D:\Check onchain fresh wallets")
if VPS_FW.exists():
    for f in sorted(VPS_FW.rglob("freshwatch_daily_2026-08*")):
        log(f"  {f}")
else:
    log("  VPS local path not found")

# ── Try FAPI exchange info for XPINUSDT ──────────────────────────────────────
log("\n--- FAPI exchange info for XPINUSDT ---")
try:
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    with urllib.request.urlopen(url, timeout=15) as r:
        info = json.loads(r.read())
    xpin_sym = [s for s in info.get("symbols", []) if s.get("symbol") == "XPINUSDT"]
    if xpin_sym:
        s = xpin_sym[0]
        log(f"  XPINUSDT found: status={s.get('status')}, contractType={s.get('contractType')}")
        log(f"  onboardDate: {s.get('onboardDate')}")
    else:
        log("  XPINUSDT NOT FOUND in FAPI exchange info")
        # List similar
        pins = [s["symbol"] for s in info["symbols"] if "XPIN" in s["symbol"]]
        log(f"  XPIN* symbols: {pins}")
except Exception as e:
    log(f"  ERROR: {e}")

# ── Try LSR endpoints with different period ────────────────────────────────────
log("\n--- Try LSR endpoint directly ---")
BASE = "https://fapi.binance.com"
test_urls = [
    f"{BASE}/fapi/v1/topLongShortPositionRatio?symbol=XPINUSDT&period=1d&limit=5",
    f"{BASE}/fapi/v1/globalLongShortAccountRatio?symbol=XPINUSDT&period=1d&limit=5",
]
for url in test_urls:
    short = url.split("?")[0].split("/")[-1] + "?..."
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        log(f"  {short}: OK, {len(data)} records")
        if data:
            log(f"    First: {data[0]}")
    except Exception as e:
        log(f"  {short}: {e}")

log("\n[DIAG DONE]")
