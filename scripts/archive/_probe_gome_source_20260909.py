"""V3.5l S5 probe: verify GOM-E source == watchlist rows for div + freshwatch_daily for gLSR."""
import json, csv, os
from pathlib import Path

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")

# Watchlist rows
d = json.load(open(REPO / "data/state/hedge_watchlist_2026-09-08.json"))
la = d.get("list_a_tokens", {})
lb = d.get("list_b_tokens", {})
print(f"list_a type={type(la).__name__} · list_b type={type(lb).__name__}")

la_syms = list(la.keys()) if isinstance(la, dict) else [t for t in la if isinstance(t, str)]
lb_data = lb if isinstance(lb, dict) else {}
la_data = la if isinstance(la, dict) else {}

print(f"list_a: n={len(la_syms)} sample: {la_syms[:3]}")
print(f"list_b: n={len(lb_data)} sample: {list(lb_data.keys())[:3]}")

# Freshwatch daily gLSR lookup
glsr_map = {}
p = REPO / "data/export/freshwatch_daily_2026-09.csv"
if p.exists():
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date") == "2026-09-08":
                sym = row.get("symbol", "")
                try:
                    glsr_map[sym] = float(row.get("lsr_global_r", "nan"))
                except:
                    pass

# For each expected token, print status
for tok in ["ESPORTS", "AIO", "AIA", "XAN", "GIGGLE", "HANA", "AGT", "AIOT", "B2", "TRADOOR"]:
    hit_a = [k for k in la_syms if k.startswith(tok)]
    hit_b = [k for k in lb_data if k.startswith(tok)]
    in_a = bool(hit_a); in_b = bool(hit_b)
    if in_a and la_data:
        div = la_data[hit_a[0]].get("div_ratio") if isinstance(la_data.get(hit_a[0]), dict) else None
        loc = "LIST-A"
        key = hit_a[0]
    elif in_a:
        div = None; loc = "LIST-A (dict-less)"; key = hit_a[0]
    elif in_b:
        div = lb_data[hit_b[0]].get("div_ratio")
        loc = "LIST-B"; key = hit_b[0]
    else:
        div, loc, key = None, "-", tok + "USDT"
    glsr = glsr_map.get(key)
    verdict = "?"
    if in_a and div is not None and div <= 0.5:
        verdict = f"CAGED[div={div:.3f}·gLSR={glsr:.2f}]" if glsr is not None else f"CAGED[div={div:.3f}·gLSR=N/A]"
    elif in_a and div is not None:
        verdict = f"OPEN(div={div:.3f}>0.5)"
    else:
        verdict = "OPEN (not-in-LIST-A · no registry)"
    print(f"  {tok:<10} loc={loc:<8} div={div} gLSR={glsr} → {verdict}")
