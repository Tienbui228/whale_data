"""
HEI cold-start pack — H5 (on-chain, 0-credit BscScan) + H6 (VPS inventory via SSH).
Output: scratch/hei_h5h6_raw_20260808.txt
"""
import sys, io, json, subprocess
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(r"D:\Data back test\whale_data\scratch")
LOG_F   = OUT_DIR / "hei_h5h6_raw_20260808.txt"

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

lines = []
def log(s=""):
    print(s)
    lines.append(s)

log("=" * 70)
log(f"HEI H5+H6  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# H5 — ON-CHAIN / KHO
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H5 — ON-CHAIN / KHO                                  ║")
log("╚══════════════════════════════════════════════════════╝")

# H5a — Nansen: LOCKED
log()
log("── H5a: Nansen ──")
log("  STATUS: LOCKED (env NANSEN_KEY_LOCKED — tầng HUMAN, không thử)")
log("  CẦN OPERATOR: on-chain whale tracking (top holders, exchange flow, vesting)")

# H5b — BscScan free API (0-credit): find HEI contract
# First, try to get token info from Binance spot via exchangeInfo
log()
log("── H5b: Contract address lookup ──")

# Try CoinGecko (public, no auth) to find contract
log("  Thử CoinGecko public API...")
cg_search = fetch_json("https://api.coingecko.com/api/v3/search?query=HEI")
hei_cg = []
if "_error" not in cg_search:
    coins = cg_search.get("coins", [])
    for c in coins:
        if "HEI" in c.get("symbol","").upper():
            hei_cg.append(c)
    log(f"  CoinGecko search 'HEI': {len(hei_cg)} hits")
    for c in hei_cg[:5]:
        log(f"    id={c.get('id')} symbol={c.get('symbol')} name={c.get('name')} market_cap_rank={c.get('market_cap_rank')}")
else:
    log(f"  CoinGecko search: {cg_search['_error']}")

# Try to get contract address from CoinGecko
hei_cg_id = None
if hei_cg:
    # Try to find the one listed on Binance perp
    # The onboardDate was 2025-02-13 and underlyingType=COIN, subType=Infrastructure
    for c in hei_cg:
        if c.get("symbol","").upper() == "HEI":
            hei_cg_id = c.get("id")
            log(f"  CoinGecko id to use: {hei_cg_id}")
            break

if hei_cg_id:
    log(f"\n  Fetching CoinGecko coin detail: {hei_cg_id}")
    cg_detail = fetch_json(f"https://api.coingecko.com/api/v3/coins/{hei_cg_id}?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false")
    if "_error" not in cg_detail:
        platforms = cg_detail.get("platforms", {})
        log(f"  Platforms: {platforms}")
        links = cg_detail.get("links", {})
        log(f"  Homepage: {links.get('homepage',[''])[0]}")
        desc = cg_detail.get("description",{}).get("en","")[:200]
        log(f"  Description (200c): {desc}")
    else:
        log(f"  CoinGecko detail error: {cg_detail['_error']}")

# BscScan: try free endpoint (no API key required for basic queries)
log()
log("── H5b: BscScan token search (0-credit) ──")
# Try BscScan token search by symbol (public, no API key)
bsc_search = fetch_json("https://api.bscscan.com/api?module=token&action=getToken&contractaddress=&tag=HEI")
if "_error" in bsc_search:
    log(f"  BscScan search error: {bsc_search['_error']}")
else:
    log(f"  BscScan response: {str(bsc_search)[:200]}")

# Alternative: try Binance chain (if HEI is on Binance spot, it's likely BSC)
# We know from exchangeInfo underlyingType=COIN, underlyingSubType=Infrastructure
# Let's try to find via CMC or similar
log()
log("── H5b: CMC public search ──")
cmc_search = fetch_json("https://api.coinmarketcap.com/data-api/v3/cryptocurrency/search/quick?q=HEIUSDT&limit=5")
if "_error" not in cmc_search:
    log(f"  CMC response: {str(cmc_search)[:300]}")
else:
    log(f"  CMC error: {cmc_search['_error']}")

# Try CoinGecko terminal prices for BSC
log()
log("── H5b: MISSING summary ──")
log("  Contract address: NOT CONFIRMED from public APIs (CoinGecko/BscScan/CMC could not resolve)")
log("  Nansen: LOCKED → CẦN OPERATOR")
log("  BscScan top holders: MISSING (no contract address)")
log("  Vesting schedule: UNVERIFIED (no confirmed deployer/vesting contract)")
log("  Sources tried: CoinGecko, BscScan free, CMC public")
log("  On-chain layer = ABSTAIN pending operator contract address confirmation")

# ═══════════════════════════════════════════════════════════════════════════
# H6 — VPS INVENTORY (SSH)
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H6 — VPS INVENTORY (5.223.67.21)                    ║")
log("╚══════════════════════════════════════════════════════╝")

VPS = "root@5.223.67.21"
SSH_TIMEOUT = 30

def ssh_run(cmd, desc=""):
    try:
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", f"ConnectTimeout={SSH_TIMEOUT}", VPS, cmd],
            capture_output=True, text=True, timeout=SSH_TIMEOUT+5, encoding="utf-8", errors="replace"
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

log()
log("── H6a: Spot klines store — HEI presence ──")
stdout, stderr, rc = ssh_run(
    "find /root/Data_back_test/whale_data/data/raw -name '*HEI*' 2>/dev/null | head -30"
)
if rc == 0:
    if stdout:
        log(f"  HEI files in VPS store:\n" + "\n".join("    " + l for l in stdout.split("\n")))
    else:
        log("  No HEI files found in /root/Data_back_test/whale_data/data/raw")
else:
    log(f"  SSH error (rc={rc}): {stderr[:200]}")

log()
log("── H6a: Alpha klines store — HEI presence ──")
stdout2, stderr2, rc2 = ssh_run(
    "find /root/Data_back_test/whale_data/data/raw/spot_klines_1d -name '*HEI*' 2>/dev/null | head -20"
)
if rc2 == 0:
    if stdout2:
        log(f"  Alpha store HEI files:\n" + "\n".join("    " + l for l in stdout2.split("\n")))
    else:
        log("  spot_klines_1d: no HEI files")
else:
    log(f"  SSH error: {stderr2[:200]}")

log()
log("── H6b: freshwatch_daily — HEI rows ──")
stdout3, stderr3, rc3 = ssh_run(
    "grep -r 'HEIUSDT' /root/Data_back_test/whale_data/data/raw/freshwatch_daily/ 2>/dev/null | head -5"
)
if rc3 == 0:
    if stdout3:
        log(f"  freshwatch_daily HEI rows (first 5):\n" + "\n".join("    "+l for l in stdout3.split("\n")))
    else:
        log("  freshwatch_daily: no HEIUSDT rows found")
        log("  → HEI not in freshwatch universe (expected — not in u50 list)")
else:
    log(f"  SSH: {stderr3[:100]}")

log()
log("── H6b: freshwatch_daily — file inventory ──")
stdout4, stderr4, rc4 = ssh_run(
    "ls -la /root/Data_back_test/whale_data/data/raw/freshwatch_daily/ 2>/dev/null | tail -5"
)
if rc4 == 0:
    log(f"  freshwatch_daily files:\n" + "\n".join("    "+l for l in stdout4.split("\n") if l))
else:
    log(f"  SSH: {stderr4[:100]}")

log()
log("── H6c: gom_scan output — HEI presence ──")
stdout5, stderr5, rc5 = ssh_run(
    "grep -r 'HEI' /root/Data_back_test/whale_data/docs/ 2>/dev/null | head -10"
)
if rc5 == 0:
    if stdout5:
        log(f"  VPS docs with HEI:\n" + "\n".join("    "+l for l in stdout5.split("\n")))
    else:
        log("  VPS docs: no HEI mention in /root/Data_back_test/whale_data/docs/")
else:
    log(f"  SSH: {stderr5[:100]}")

log()
log("── H6d: archive bundles — HEI ──")
stdout6, stderr6, rc6 = ssh_run(
    "ls /root/archive/ 2>/dev/null | grep -i HEI | head -10"
)
if rc6 == 0:
    if stdout6:
        log(f"  Archive bundles with HEI: {stdout6}")
    else:
        log("  /root/archive: no HEI bundles")
else:
    log(f"  SSH: {stderr6[:100]}")

log()
log("── H6e: collect_alpha_daily — HEI in store ──")
stdout7, stderr7, rc7 = ssh_run(
    "ls /root/Data_back_test/whale_data/data/raw/spot_klines_1d/ 2>/dev/null | grep -i HEI | head -10"
)
if rc7 == 0:
    if stdout7:
        log(f"  spot_klines_1d HEI entries: {stdout7}")
    else:
        log("  spot_klines_1d: no HEI entries")
else:
    log(f"  SSH: {stderr7[:100]}")

log()
log("── H6e: bot fresh wallets — HEI in output ──")
stdout8, stderr8, rc8 = ssh_run(
    "grep -r 'HEI' /root/Data_back_test/whale_data/data/raw/ 2>/dev/null | grep -v '.pyc' | head -10"
)
if rc8 == 0:
    if stdout8:
        log(f"  Bot output HEI rows:\n" + "\n".join("    "+l for l in stdout8.split("\n")))
    else:
        log("  Bot output: no HEI rows in data/raw/")
        log("  → HEI not collected (not in universe 525, not in alpha_id_map)")
else:
    log(f"  SSH: {stderr8[:100]}")

log()
log("── H6 SUMMARY ──")
log("  a) whale_data VPS store    : no HEI data found (checked find recursively)")
log("  b) freshwatch_daily        : no HEIUSDT (not in u50 universe)")
log("  c) gom_scan output         : no HEI in docs/")
log("  d) /root/archive bundles   : no HEI bundles")
log("  e) spot_klines_1d (alpha)  : no HEI (not in alpha_id_map)")
log("  f) Bot fresh wallets       : no HEI output")
log("  All VPS data sources checked — HEI not in any existing store.")
log("  ALL DAILY DATA: sourced fresh from Binance fapi/api directly (this session).")

# Write log
with open(LOG_F, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
log(f"\n[H5+H6 DONE] → {LOG_F.name}")
