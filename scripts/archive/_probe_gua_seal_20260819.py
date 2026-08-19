#!/usr/bin/env python3
"""[A0] SEAL bit-equal full 40-hex — operator contract vs 3 nơi config."""
import sys, io, json, urllib.request, urllib.parse, csv
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OPERATOR_CT = "0xa5c8e1513b6a08334b479fe4d71f1253259469be"

REPO = Path(r"D:\Data back test\whale_data")
U50 = Path(r"D:\Check onchain fresh wallets\u50_universe.csv")
ALPHA_MAP = REPO / "data" / "config" / "alpha_id_map.json"

UA = {"User-Agent": "Mozilla/5.0"}

def chareq(a, b):
    """Bit-equal char-by-char."""
    if len(a) != len(b): return False, f"length: {len(a)} vs {len(b)}"
    diffs = [(i, ca, cb) for i, (ca, cb) in enumerate(zip(a, b)) if ca != cb]
    if diffs: return False, f"diffs at pos: {diffs}"
    return True, "PASS"

def norm(s):
    return (s or "").lower().strip()

print("═" * 78)
print(f"[A0] SEAL bit-equal full 40-hex compare")
print("═" * 78)
op = norm(OPERATOR_CT)
print(f"\nOperator contract (canonical, niêm phong):")
print(f"  {OPERATOR_CT}  (len={len(OPERATOR_CT)}, prefix=0x + 40 hex)")
print(f"  normalized: {op}")

# ─── ① u50_universe.csv
print(f"\n─── ① u50_universe.csv row 138 (futures_base=GUA) ─── ")
gua_row = None
for r in csv.DictReader(open(U50, encoding="utf-8-sig")):
    if r["futures_base"] == "GUA":
        gua_row = r
        break
u50_ct = norm(gua_row.get("bsc_address"))
print(f"  raw       : {gua_row.get('bsc_address')!r}")
print(f"  normalized: {u50_ct}")
ok, msg = chareq(op, u50_ct)
print(f"  vs operator: {msg}  → {'PASS' if ok else 'FAIL'}")

# ─── ② Alpha bapi ALPHA_483 contractAddress
print(f"\n─── ② Alpha bapi wallet-direct alphaId=ALPHA_483 contractAddress ─── ")
req = urllib.request.Request(
    "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list",
    headers=UA)
with urllib.request.urlopen(req, timeout=15) as r:
    raw = json.loads(r.read().decode())
tokens = raw if isinstance(raw, list) else raw.get("data", [])
if isinstance(tokens, dict):
    tokens = tokens.get("list") or tokens.get("tokens") or []
alpha_rec = next((t for t in tokens if str(t.get("alphaId")) == "ALPHA_483"), None)
if alpha_rec:
    alpha_ct = norm(alpha_rec.get("contractAddress"))
    print(f"  raw       : {alpha_rec.get('contractAddress')!r}")
    print(f"  normalized: {alpha_ct}")
    ok2, msg2 = chareq(op, alpha_ct)
    print(f"  vs operator: {msg2}  → {'PASS' if ok2 else 'FAIL'}")
else:
    ok2 = False; msg2 = "ALPHA_483 not found in bapi list"
    print(f"  {msg2}")

# ─── ③ Gate GUA_USDT metadata chains[0].addr
print(f"\n─── ③ Gate /api/v4/spot/currencies/GUA chains[0].addr ─── ")
try:
    with urllib.request.urlopen(
        "https://api.gateio.ws/api/v4/spot/currencies/GUA", timeout=15) as r:
        raw = json.loads(r.read().decode())
    chains = raw.get("chains", [])
    bsc_chain = next((c for c in chains if c.get("name") == "BSC"), None)
    if bsc_chain:
        gate_ct = norm(bsc_chain.get("addr"))
        print(f"  raw       : {bsc_chain.get('addr')!r}")
        print(f"  normalized: {gate_ct}")
        ok3, msg3 = chareq(op, gate_ct)
        print(f"  vs operator: {msg3}  → {'PASS' if ok3 else 'FAIL'}")
    else:
        ok3 = False; msg3 = "no BSC chain entry"
        print(f"  {msg3}")
except Exception as e:
    ok3 = False; msg3 = f"fetch error: {e}"
    print(f"  {msg3}")

# ─── SEAL verdict
print(f"\n" + "═" * 78)
print(f"SEAL VERDICT")
print("═" * 78)
all_pass = ok and ok2 and ok3
if all_pass:
    print(f"  ① u50           : PASS")
    print(f"  ② Alpha bapi    : PASS")
    print(f"  ③ Gate metadata : PASS")
    print(f"  → SEAL PASS. Path A cleared to execute (A1-A3).")
else:
    print(f"  ① u50           : {'PASS' if ok  else 'FAIL — ' + msg}")
    print(f"  ② Alpha bapi    : {'PASS' if ok2 else 'FAIL — ' + msg2}")
    print(f"  ③ Gate metadata : {'PASS' if ok3 else 'FAIL — ' + msg3}")
    print(f"  → SEAL FAIL. DỪNG. Chuyển Path B.")
