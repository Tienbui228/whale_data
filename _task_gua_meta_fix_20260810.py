"""
_task_gua_meta_fix_20260810.py
Fix gua_perp_info (onboardDate = int ms) + create gua_bapi JSON for build_case.py.
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM_LOWER = "gua"
START_MS = 1766312100000  # 2025-12-21 10:15 UTC

# ── Fix perp_info: onboardDate must be int ms ────────────────────────────────
pinfo_path = SCRATCH / f"{SYM_LOWER}_perp_info_{DATE_TAG}.json"
with open(pinfo_path, encoding="utf-8") as f:
    pinfo = json.load(f)
pinfo["onboardDate"] = START_MS  # overwrite string with int
with open(pinfo_path, "w", encoding="utf-8") as f:
    json.dump(pinfo, f, ensure_ascii=False, indent=2)
print(f"Fixed {pinfo_path.name}: onboardDate={START_MS}")

# ── Create gua_bapi JSON (from alpha token list data captured in G-0) ─────────
bapi_data = {
    "symbol": "GUA",
    "name": "SUPERFORTUNE",
    "contractAddress": "0xa5c8e1513b6a08334b479fe4d71f1253259469be",
    "chainId": "56",
    "totalSupply": "1000000000",
    "circulatingSupply": "UNKNOWN — CAN OPERATOR",
    "holders": "UNKNOWN — CAN OPERATOR",
    "fullyDelisted": False,
    "offsell": False,
    "offline": False,
    "listingTime": START_MS,
    "alphaId": "ALPHA_483",
    "_note": "built from bapi alpha token list G-0 2026-08-10",
}
bapi_path = SCRATCH / f"{SYM_LOWER}_bapi_{DATE_TAG}.json"
with open(bapi_path, "w", encoding="utf-8") as f:
    json.dump(bapi_data, f, ensure_ascii=False, indent=2)
print(f"Created {bapi_path.name}")
print(f"  contract: {bapi_data['contractAddress']}")
print(f"  totalSupply: {bapi_data['totalSupply']}")
