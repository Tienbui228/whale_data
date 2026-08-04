#!/usr/bin/env python3
"""TASK: Generate data/config/alpha_id_map.json — resolver cho toàn u50_universe.

Gọi token-list endpoint → join bsc_address → ghi JSON.
Output: data/config/alpha_id_map.json
"""
import csv, json, sys, time, urllib.request, urllib.parse
from pathlib import Path

sys.stdout = __import__("io").TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)

WHALE = Path(r"D:\Data back test\whale_data")
U50   = Path(r"D:\Check onchain fresh wallets\u50_universe.csv")
OUT   = WHALE / "data" / "config" / "alpha_id_map.json"
BASE  = "https://www.binance.com"
UA    = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def bget(path, params=None):
    qs  = f"?{urllib.parse.urlencode(params)}" if params else ""
    req = urllib.request.Request(f"{BASE}{path}{qs}", headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def flatten(raw):
    if isinstance(raw, list): return raw
    if isinstance(raw, dict):
        d = raw.get("data", raw)
        if isinstance(d, list): return d
        if isinstance(d, dict): return d.get("list") or d.get("tokens") or []
    return []

print("Fetching Alpha token list...", flush=True)
raw = bget("/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list")
tokens_all = flatten(raw)
print(f"  total tokens: {len(tokens_all)}")

alpha_by_addr = {}
for t in tokens_all:
    if str(t.get("chainId")) == "56":
        addr = (t.get("contractAddress") or "").lower().strip()
        if addr:
            alpha_by_addr[addr] = t
print(f"  BSC indexed: {len(alpha_by_addr)}")

rows = list(csv.DictReader(open(U50, encoding="utf-8-sig")))
mapping = {}
fail = []
for r in rows:
    sym = r["futures_base"]
    bsc = (r.get("bsc_address") or "").lower().strip()
    t   = alpha_by_addr.get(bsc)
    if t:
        alpha_id = t.get("alphaId") or ""
        if alpha_id:
            mapping[sym] = alpha_id
        else:
            fail.append(f"{sym}:NO_ALPHAID")
    else:
        fail.append(f"{sym}:NO_MATCH")

print(f"  resolved: {len(mapping)}/{len(rows)}")
if fail:
    print(f"  FAIL: {fail}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(mapping, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
print(f"\nWrote {len(mapping)} entries → {OUT}")
