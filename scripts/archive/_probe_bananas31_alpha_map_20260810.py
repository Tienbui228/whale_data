"""Check BANANAS31 in alpha_id_map.json."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"D:\Data back test\whale_data")
m = json.loads((ROOT / "data" / "config" / "alpha_id_map.json").read_text(encoding="utf-8"))
has = "BANANAS31" in m
print(f"BANANAS31 in map: {has}")
keys_b = [k for k in m if "BANANA" in k.upper()]
print(f"Keys with BANANA: {keys_b}")
if has:
    print(f"alpha_id: {m['BANANAS31']}")
