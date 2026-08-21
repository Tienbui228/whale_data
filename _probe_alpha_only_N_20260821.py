"""_probe_alpha_only_N_20260821.py
Cross fw-139 × Binance spot api/v3 exchangeInfo → count N Alpha-only tokens.
Alpha-only definition: fw-139 symbol KHÔNG có Binance spot base match.
Nợ từ án SUPERFORTUNE 18/08 — chưa export bảng bao giờ.
"""
import sys, io, json, urllib.request, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")
FW139 = ROOT / "scratch" / "freshwatch_symbols.txt"

# Load fw-139
with open(FW139, encoding="utf-8", errors="ignore") as f:
    fw139 = [l.strip().upper() for l in f if l.strip()]
print(f"fw-139: {len(fw139)} tokens")

# base = strip USDT suffix
fw139_bases = set()
for s in fw139:
    b = s[:-4] if s.endswith("USDT") else s
    fw139_bases.add(b)
print(f"fw-139 unique bases: {len(fw139_bases)}")

# Get Binance spot symbols via VPS (api.binance.com blocked local)
print("\n=== Fetch api.binance.com/api/v3/exchangeInfo via VPS ===")
vps_cmd = "curl -s https://api.binance.com/api/v3/exchangeInfo | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d[\"symbols\"])); [print(s[\"baseAsset\"]+\"|\"+s[\"quoteAsset\"]+\"|\"+s[\"status\"]) for s in d[\"symbols\"]]'"
r = subprocess.run(["ssh","root@5.223.67.21", vps_cmd], capture_output=True, timeout=60)
r.stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
r.stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
lines = r.stdout.strip().split("\n")
print(f"Response lines: {len(lines)}")
if not lines:
    print(f"ERR: {r.stderr[:200]}")
    sys.exit(1)

n_total = int(lines[0])
print(f"Binance spot symbols total: {n_total}")

spot_bases = set()
spot_trading_bases = set()  # only TRADING (không BREAK/HALT)
for line in lines[1:]:
    parts = line.split("|")
    if len(parts) == 3:
        base, quote, status = parts
        spot_bases.add(base.upper())
        if status == "TRADING":
            spot_trading_bases.add(base.upper())

print(f"Binance spot unique bases: {len(spot_bases)}")
print(f"Binance spot TRADING bases: {len(spot_trading_bases)}")

# Cross-check
print("\n=== CROSS fw-139 × Binance spot ===")
has_spot = fw139_bases & spot_bases
has_spot_trading = fw139_bases & spot_trading_bases
alpha_only = fw139_bases - spot_bases  # no Binance spot at all
alpha_only_status = fw139_bases - spot_trading_bases  # no TRADING spot (may have BREAK)

print(f"fw-139 với Binance spot pair (any status): {len(has_spot)}")
print(f"fw-139 với Binance spot TRADING: {len(has_spot_trading)}")
print(f"\n★ N Alpha-only (no Binance spot base):       {len(alpha_only)}")
print(f"★ Alpha-only-strict (no TRADING spot):        {len(alpha_only_status)}")

# List Alpha-only sorted
print(f"\n=== ALPHA-ONLY LIST (N = {len(alpha_only)}, sorted) ===")
alpha_sorted = sorted(alpha_only)
for i, sym in enumerate(alpha_sorted, 1):
    print(f"  {i:3d}. {sym}USDT")

# Also list tokens có Binance spot pair (for completeness, reversed)
print(f"\n=== Có Binance spot pair ({len(has_spot)}) ===")
for sym in sorted(has_spot):
    print(f"  · {sym}USDT")

# Save
out = ROOT / "scratch" / "alpha_only_fw139_20260821.csv"
with open(out, "w", encoding="utf-8") as f:
    f.write("rank,symbol,alpha_only,has_binance_spot\n")
    all_bases = sorted(fw139_bases)
    for i, b in enumerate(all_bases, 1):
        is_alpha_only = b in alpha_only
        has_bnc = b in spot_bases
        f.write(f"{i},{b}USDT,{is_alpha_only},{has_bnc}\n")
print(f"\nWritten: {out}")

print(f"\n[SUMMARY] N Alpha-only = {len(alpha_only)} / fw-139 = {len(fw139_bases)} bases")
