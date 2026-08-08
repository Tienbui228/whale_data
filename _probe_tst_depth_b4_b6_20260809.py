"""
_probe_tst_depth_b4_b6_20260809.py
T-4: Depth snap #1 + Alpha confirm + BscScan + freshwatch cross-ref.
"""
import sys, io, json, csv, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

SYMBOL   = "TSTUSDT"
CONTRACT = "0x86bb94ddd16efc8bc58e6b056e8df71d9e666429"
SUPPLY   = 939_124_852.9
SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
ROOT     = Path(r"D:\Data back test\whale_data")

def log(s=""): print(s)
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TST DEPTH/B4/B6  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

FAPI = "https://fapi.binance.com"

# ── T-4 DEPTH SNAP #1 ─────────────────────────────────────────────────────────
log("\n--- T-4: Depth snap #1 ---")
depth = fetch_json(f"{FAPI}/fapi/v1/depth?symbol={SYMBOL}&limit=500")
snap_ts = datetime.now(timezone.utc)
if isinstance(depth, dict) and "bids" in depth:
    bids = [(float(p), float(q)) for p, q in depth["bids"]]
    asks = [(float(p), float(q)) for p, q in depth["asks"]]
    mid  = (bids[0][0] + asks[0][0]) / 2 if bids and asks else 0
    # ±2%
    bid2 = sum(p*q for p,q in bids if p >= mid*0.98)
    ask2 = sum(p*q for p,q in asks if p <= mid*1.02)
    log(f"  Timestamp: {snap_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"  px_mid: {mid:.6f}")
    log(f"  Bid±2%: ${bid2:,.0f}")
    log(f"  Ask±2%: ${ask2:,.0f}")
    log(f"  Bid/Ask ratio: {bid2/ask2:.3f}" if ask2 else "  Ask side empty")
    log(f"  Best bid: {bids[0]} | Best ask: {asks[0]}")
    snap = {"ts": snap_ts.isoformat(), "mid": mid, "bid2pct": bid2, "ask2pct": ask2,
            "bids_500": depth["bids"][:10], "asks_500": depth["asks"][:10]}
    out_d = SCRATCH / "tst_depth_snap1_20260809.json"
    out_d.write_text(json.dumps(snap), encoding="utf-8")
    log(f"  Saved: {out_d}")
    log(f"  NOTE: Need snap #2 >= {snap_ts.strftime('%H:%M')} + 4h = {(snap_ts.hour+4)%24:02d}:{snap_ts.minute:02d} UTC")
else:
    log(f"  ERROR: {depth}")

time.sleep(0.3)

# ── T-4 ALPHA CONFIRM (fullyDelisted=True → ABSTAIN) ─────────────────────────
log("\n--- T-4: Alpha confirm (ALPHA_87) ---")
log(f"  Symbol: TST | alphaId: ALPHA_87 | chainId: 56 (BSC)")
log(f"  Contract: {CONTRACT}")
log(f"  fullyDelisted=True → Alpha klines: ABSTAIN (klines[9]==klines[5], L-48)")
log(f"  offline=True, offsell=True")

# Check local alpha store for TST
alpha_store = ROOT / "data" / "raw" / "spot_klines_1d"
tst_alpha_found = False
if alpha_store.exists():
    for d in alpha_store.rglob("venue=binance_alpha"):
        for subd in d.iterdir():
            if "TST" in subd.name.upper():
                log(f"  Alpha local store: {subd}")
                tst_alpha_found = True
if not tst_alpha_found:
    log(f"  Alpha local store: TST not found (fullyDelisted=True, no collect)")

# Try fetch Alpha klines (expect 400 or similar)
log(f"\n  Testing Alpha klines endpoint (expect fail)...")
alpha_map = ROOT / "data" / "config" / "alpha_id_map.json"
if alpha_map.exists():
    amap = json.loads(alpha_map.read_text(encoding="utf-8"))
    tst_info = amap.get("TST") or amap.get("TSTUSDT")
    if tst_info:
        alpha_id = tst_info if isinstance(tst_info, str) else tst_info.get("alphaId", "ALPHA_87")
        log(f"  alpha_id_map: TST → {tst_info}")
    else:
        log(f"  TST not in alpha_id_map (id from BAPI: ALPHA_87)")
        alpha_id = "ALPHA_87"
else:
    alpha_id = "ALPHA_87"

time.sleep(0.3)

# ── T-5 BscScan top holders (0-credit) ───────────────────────────────────────
log("\n--- T-5: BscScan top holders ---")
bsc_url = (f"https://api.bscscan.com/api?module=token&action=tokenholderlist"
           f"&contractaddress={CONTRACT}&page=1&offset=20")
bsc_raw = fetch_json(bsc_url, timeout=20)
if isinstance(bsc_raw, dict) and bsc_raw.get("status") == "1":
    holders = bsc_raw.get("result", [])
    log(f"  Top holders ({len(holders)}):")
    for h in holders[:15]:
        bal = float(h.get("TokenHolderQuantity", 0) or 0)
        try:
            bal_adj = bal / (10**18)
        except:
            bal_adj = bal
        pct = bal_adj / SUPPLY * 100
        log(f"    {h.get('TokenHolderAddress','')} — {bal_adj:,.0f} ({pct:.2f}%)")
else:
    log(f"  BscScan tokenholderlist: {bsc_raw.get('message','?') if isinstance(bsc_raw,dict) else bsc_raw}")
    log(f"  Status: {bsc_raw.get('status','?') if isinstance(bsc_raw,dict) else '?'}")
    log(f"  → CẦN OPERATOR: BscScan API key")

    # Try known exchange addresses
    log(f"\n  Checking known BSC exchange addresses...")
    known_addrs = {
        "Binance-peg hot1": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",
        "Binance-peg hot2": "0xe2fc31f816a9b94326492132018c3aecc4a93ae1",
        "Binance cold":     "0xf977814e90da44bfa03b6295a0616a897441acec",
        "Binance cex2":     "0x3c783c21a0383057d128bae431894a5c19f9cf06",
    }
    for name, addr in known_addrs.items():
        url2 = (f"https://api.bscscan.com/api?module=account&action=tokenbalance"
                f"&contractaddress={CONTRACT}&address={addr}&tag=latest")
        r2 = fetch_json(url2, timeout=10)
        if isinstance(r2, dict) and r2.get("status") == "1":
            try:
                bal = float(r2.get("result", 0)) / 1e18
                pct = bal / SUPPLY * 100
                log(f"    {name}: {bal:,.0f} tokens ({pct:.2f}%)")
            except:
                log(f"    {name}: {r2.get('result','?')}")
        else:
            log(f"    {name}: {r2.get('message','?') if isinstance(r2,dict) else r2}")
        time.sleep(0.2)

log(f"  Contract L-28: BAPI (official source) — need 2nd source")
log(f"  Nansen: LOCKED — CẦN OPERATOR")

time.sleep(0.3)

# ── T-6 freshwatch merge + cross-ref ─────────────────────────────────────────
log("\n--- T-6: freshwatch TST data detail ---")
fw_rows_all = []
for tag in ["2026-06", "2026-07"]:
    fw_csv = SCRATCH / f"freshwatch_daily_{tag}.csv"
    if fw_csv.exists():
        with open(fw_csv, encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f)
                    if "TST" in (r.get("symbol","") or r.get("Symbol","")).upper()
                    and "TSTUSDT" in (r.get("symbol","") or r.get("Symbol","")).upper()]
        fw_rows_all.extend(rows)
        log(f"  {tag}: {len(rows)} rows TSTUSDT")

log(f"  Total freshwatch rows: {len(fw_rows_all)}")
if fw_rows_all:
    log(f"  Date range: {fw_rows_all[0].get('date','?')} → {fw_rows_all[-1].get('date','?')}")
    log(f"  Columns: {list(fw_rows_all[0].keys())}")
    log(f"\n  TST freshwatch summary:")
    for r in fw_rows_all:
        log(f"    {r.get('date','?')}: pos_r={r.get('lsr_pos_r','?')} acc_r={r.get('lsr_acc_r','?')} gLSR={r.get('lsr_global_r','?')} fn={r.get('funding_n','?')} data_ok={r.get('data_ok','?')}")

# Save merged LSR freshwatch
out_fw = SCRATCH / "tst_freshwatch_lsr_20260809.csv"
if fw_rows_all:
    with open(out_fw, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fw_rows_all[0].keys()))
        w.writeheader()
        w.writerows(fw_rows_all)
    log(f"\n  Saved merged freshwatch: {out_fw}")

# gom_scan for TST
log("\n--- T-6: gom_scan check ---")
for fname in ["gom_gate6_full_20260808.txt", "gom_diag_20260808.txt"]:
    fpath = ROOT / "docs" / "reports" / fname
    if fpath.exists():
        txt = fpath.read_text(encoding="utf-8", errors="replace")
        if "TST" in txt.upper():
            lines = [l for l in txt.split("\n") if "TST" in l.upper()]
            log(f"  {fname}: {len(lines)} TST lines")
            for l in lines[:5]:
                log(f"    {l}")
        else:
            log(f"  {fname}: TST not found (checked, clean)")
    else:
        log(f"  {fname}: not found")

# CASE files
log("\n--- T-6: CASE files for TST ---")
case_dir = ROOT / "docs" / "case_files"
for f in case_dir.glob("*.xlsx"):
    if "TST" in f.name.upper():
        log(f"  Existing case file: {f.name}")
if not any("TST" in f.name.upper() for f in case_dir.glob("*.xlsx")):
    log(f"  No existing TST case file (expected)")

# screen_thresholds.yaml
thresh_file = ROOT / "screen_thresholds.yaml"
if thresh_file.exists():
    for line in thresh_file.read_text(encoding="utf-8").splitlines():
        if "TST" in line.upper():
            log(f"  screen_thresholds.yaml: {line}")
else:
    log(f"  screen_thresholds.yaml: not found")

log(f"\n[DEPTH/B4/B6 DONE] {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  Snap #2 window: ≥ {(NOW.hour+4)%24:02d}:{NOW.minute:02d} UTC 08/08/2026")
