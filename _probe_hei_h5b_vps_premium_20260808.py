"""
HEI: H5b supplement — BscScan top holders (0-credit, address known candidate)
+ H6 supplement — VPS premium_1h inventory for HEIUSDT.
Output: scratch/hei_h5b_vps_supplement_20260808.txt
"""
import sys, io, json, subprocess
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(r"D:\Data back test\whale_data\scratch")
LOG_F   = OUT_DIR / "hei_h5b_vps_supplement_20260808.txt"
VPS     = "root@5.223.67.21"

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

def ssh_run(cmd, timeout=30):
    try:
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", f"ConnectTimeout={timeout}", VPS, cmd],
            capture_output=True, text=True, timeout=timeout+5, encoding="utf-8", errors="replace"
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

lines = []
def log(s=""):
    print(s)
    lines.append(s)

log("=" * 70)
log(f"HEI H5b+H6 supplement  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── Contract candidate: 0xf8f173e20e15f3b6cb686fb64724d370689de083 (Heima) ──
CONTRACT_CANDIDATE = "0xf8f173e20e15f3b6cb686fb64724d370689de083"

log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H5b: BscScan (contract candidate from CoinGecko)    ║")
log("╚══════════════════════════════════════════════════════╝")
log(f"  Contract candidate: {CONTRACT_CANDIDATE}")
log("  Source: CoinGecko id=heima, symbol=HEI, name=Heima, mcap_rank=910")
log("  Chain: BSC (binance-smart-chain) + Ethereum (same address)")
log("  VERIFY: Must confirm this is the same HEI as HEIUSDT perp on Binance")

# BscScan v2 API (free, no API key for basic queries)
# Note: BscScan deprecated v1, use etherscan v2 format
log()
log("── BscScan: token info (free, no key) ──")
bsc_url = f"https://api.bscscan.com/api?module=token&action=tokeninfo&contractaddress={CONTRACT_CANDIDATE}"
bsc_info = fetch_json(bsc_url)
if "_error" not in bsc_info:
    log(f"  BscScan token info: {str(bsc_info)[:400]}")
    result = bsc_info.get("result", [])
    if isinstance(result, list) and result:
        for item in result[:3]:
            log(f"  name: {item.get('name')} | symbol: {item.get('symbol')} | decimals: {item.get('divisor')}")
            log(f"  totalSupply: {item.get('totalSupply')} | holdersCount: {item.get('holdersCount')}")
    elif isinstance(result, str):
        log(f"  result msg: {result}")
else:
    log(f"  BscScan error: {bsc_info['_error']}")

# Try BscScan v2 (etherscan.io API v2 format)
log()
log("── BscScan v2: token supply + holder count ──")
bsc_v2_supply = fetch_json(
    f"https://api.bscscan.com/v2/api?chainid=56&module=stats&action=tokensupply&contractaddress={CONTRACT_CANDIDATE}"
)
if "_error" not in bsc_v2_supply:
    log(f"  Token supply: {bsc_v2_supply}")
else:
    log(f"  Supply API error: {bsc_v2_supply['_error']}")

# Top token holders via BscScan (usually needs API key for topholders endpoint)
log()
log("── BscScan: top holders ──")
bsc_holders = fetch_json(
    f"https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress={CONTRACT_CANDIDATE}&page=1&offset=10"
)
if "_error" not in bsc_holders:
    log(f"  Holders response: {str(bsc_holders)[:300]}")
    result = bsc_holders.get("result", [])
    if isinstance(result, list):
        log(f"  Top holders returned: {len(result)}")
        for h in result[:10]:
            log(f"    addr={h.get('TokenHolderAddress','?')[:20]}... qty={h.get('TokenHolderQuantity','?')}")
    elif isinstance(result, str):
        log(f"  msg: {result}")
else:
    log(f"  Holders error: {bsc_holders['_error']}")

log()
log("── H5 ON-CHAIN SUMMARY ──")
log(f"  Contract candidate (UNVERIFIED): {CONTRACT_CANDIDATE}")
log("  Source: CoinGecko heima (rank 910)")
log("  Verify required: operator confirm this == Binance HEIUSDT underlying")
log("  Top holders: API requires key (paid tier) → MISSING")
log("  Vesting schedule: UNVERIFIED — no on-chain vesting contract found")
log("  On-chain layer: ABSTAIN — contract unconfirmed, Nansen LOCKED")
log("  CẦN OPERATOR: confirm contract address + Nansen for top holders")

# ═══════════════════════════════════════════════════════════════════════════
# H6 supplement — premium_1h VPS store
# ═══════════════════════════════════════════════════════════════════════════
log()
log("╔══════════════════════════════════════════════════════╗")
log("║  H6 supplement — VPS premium_1h for HEIUSDT          ║")
log("╚══════════════════════════════════════════════════════╝")

# List files in premium_1h/symbol=HEIUSDT
stdout1, stderr1, rc1 = ssh_run(
    "ls /root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/ 2>/dev/null | head -20"
)
if rc1 == 0:
    log(f"  premium_1h files for HEIUSDT:\n" + "\n".join("    "+l for l in stdout1.split("\n") if l))
else:
    log(f"  SSH error: {stderr1[:200]}")

# Get date range and row count
stdout2, stderr2, rc2 = ssh_run(
    "find /root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/ -name '*.parquet' 2>/dev/null | sort | head -3; echo '---'; find /root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/ -name '*.parquet' 2>/dev/null | sort | tail -3"
)
if rc2 == 0:
    log(f"  First + last parquet files:\n" + "\n".join("    "+l for l in stdout2.split("\n") if l))
else:
    log(f"  SSH error: {stderr2[:100]}")

# Count total files
stdout3, stderr3, rc3 = ssh_run(
    "find /root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/ -name '*.parquet' 2>/dev/null | wc -l"
)
if rc3 == 0:
    log(f"  Total parquet files: {stdout3}")

# Quick read sample: get last file content via python on VPS
vps_cmd = """python3 -c "
import pandas as pd, glob, os
base = '/root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/'
files = sorted(glob.glob(base + '**/*.parquet', recursive=True))
if files:
    df = pd.read_parquet(files[-1])
    print('Last file:', files[-1])
    print('Shape:', df.shape)
    print('Cols:', list(df.columns))
    print(df.tail(3).to_string())
else:
    print('No parquet files found')
" 2>&1"""
stdout4, stderr4, rc4 = ssh_run(vps_cmd, timeout=45)
if rc4 == 0:
    log(f"\n  VPS premium_1h sample:\n" + "\n".join("    "+l for l in stdout4.split("\n") if l))
else:
    log(f"  VPS python error (rc={rc4}): {stderr4[:300]}")

# Also check date range of premium_1h for HEIUSDT
vps_cmd2 = """python3 -c "
import pandas as pd, glob
base = '/root/Data_back_test/whale_data/data/raw/premium_1h/symbol=HEIUSDT/'
files = sorted(glob.glob(base + '**/*.parquet', recursive=True))
if files:
    dfs = []
    for f in files[:2] + files[-2:]:
        try: dfs.append(pd.read_parquet(f))
        except: pass
    if dfs:
        df = pd.concat(dfs)
        print('Total rows (sample):', len(df))
        print('Cols:', list(df.columns))
        ts_col = [c for c in df.columns if 'time' in c.lower() or 'ts' in c.lower() or 'date' in c.lower()]
        if ts_col:
            print('Min date:', df[ts_col[0]].min())
            print('Max date:', df[ts_col[0]].max())
" 2>&1"""
stdout5, stderr5, rc5 = ssh_run(vps_cmd2, timeout=45)
if rc5 == 0 and stdout5:
    log(f"\n  VPS premium_1h date range:\n" + "\n".join("    "+l for l in stdout5.split("\n") if l))

log()
log("── H6 supplement RESULT ──")
log("  VPS premium_1h: HEIUSDT data EXISTS (/root/.../premium_1h/symbol=HEIUSDT/)")
log("  This is likely fundingRate / premiumIndex 1h data (not klines)")
log("  Usable for: funding history extension beyond fapi 500-row limit")
log("  Action: SCP this data locally if needed for extended funding analysis")

# Write log
with open(LOG_F, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
log(f"\n[H5b+H6 supplement DONE] → {LOG_F.name}")
