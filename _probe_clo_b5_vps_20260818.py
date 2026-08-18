"""_probe_clo_b5_vps_20260818.py — run on VPS to check spot + phase-tag CSV."""
import json, urllib.request, os, glob

# 1. spot api/v3
print("=== spot api/v3 ===")
try:
    r = urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo", timeout=15)
    info = json.loads(r.read().decode())
    total = len(info.get("symbols", []))
    print(f"total_spot_symbols={total}")
    clo = [s for s in info["symbols"]
           if s.get("baseAsset")=="CLO" or "CLO" in s.get("symbol","")]
    print(f"CLO matches: {len(clo)}")
    for s in clo[:8]:
        print(f"  {s.get('symbol')} base={s.get('baseAsset')} quote={s.get('quoteAsset')} status={s.get('status')}")
    yei = [s for s in info["symbols"]
           if "YEI" in s.get("baseAsset","").upper()]
    print(f"YEI base matches: {len(yei)}")
    for s in yei[:5]:
        print(f"  {s.get('symbol')} status={s.get('status')}")
except Exception as e:
    print(f"ERR: {e}")

# 2. phase_tag_daily.csv on VPS
print("\n=== phase_tag_daily.csv search on VPS ===")
paths = []
for root in ["/root/Data_back_test", "/root/data", "/root/whale", "/tmp"]:
    if os.path.exists(root):
        for f in glob.glob(f"{root}/**/phase_tag_daily*", recursive=True):
            paths.append(f)
print(f"found: {len(paths)}")
for p in paths[:10]:
    st = os.stat(p)
    print(f"  {p}  size={st.st_size} mtime={st.st_mtime}")

# Read latest one if any
if paths:
    latest = sorted(paths, key=lambda p: os.stat(p).st_mtime)[-1]
    print(f"\nLatest: {latest}")
    with open(latest, encoding="utf-8") as f:
        lines = f.readlines()
    print(f"  lines: {len(lines)}")
    print(f"  header: {lines[0].strip()}")
    clo_lines = [ln for ln in lines[1:] if "CLO" in ln]
    print(f"\n  CLO lines: {len(clo_lines)}")
    for ln in clo_lines[-5:]:
        print(f"    {ln.strip()}")
