"""AV3/22-09 · So Bảng A (GOM-E, 121) vs List A (HEDGE v2 spec, 73).

Đo:
 · |A ∩ B| · |A \\ B| · |B \\ A|
 · Sample 5 token đầu mỗi tập
 · Xác định BTR/MIRA/F: nằm Bảng A? nằm List A? div_avg3 = ?

Chạy trên VPS · dùng file live.
"""
import sys, os, json, csv, math
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

REPO = Path("/root/Data_back_test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

# ── Load GOM-E Bảng A (in_registry from state.json) ─────────────────────────
state_path = REPO / "data" / "gom_e_state.json"
with open(state_path, encoding="utf-8") as f:
    state = json.load(f)
BANG_A = {sym for sym, v in state.items() if v.get("in_registry")}
print(f"Bảng A (GOM-E in_registry, thres=0.85 · H1∧H2): {len(BANG_A)} tokens")

# ── Compute List A (watchlist_daily gate: div_avg3 ≤ 0.5 + sn_count_le050 ≥ 5) ─
import watchlist_daily as wl
cfg = wl.load_config()
print(f"List A gate cfg: div_ratio_max={cfg['hedge']['div_ratio_max']} · "
      f"sn_min={cfg['hedge'].get('sn_count_min', cfg['hedge'].get('struct_n_min'))}")

TARGET = "2026-09-20"
td = wl.load_token_data(min_rows=cfg["data"]["min_history_rows"])
LIST_A = set()
list_a_details = {}
for sym, arr in td.items():
    ep = wl.detect_episodes(arr, cfg)
    idx = next((i for i, r in enumerate(arr) if r["date"] == TARGET), None)
    if idx is None: continue
    s = wl.snapshot(sym, arr, ep, idx, cfg)
    if wl.in_list_a(s, cfg):
        LIST_A.add(sym)
        list_a_details[sym] = (s["div_ratio"], s.get("sn_count_le050"))

print(f"List A (watchlist_daily gate 09-20): {len(LIST_A)} tokens")

# ── Overlap ─────────────────────────────────────────────────────────────────
common = BANG_A & LIST_A
only_A = BANG_A - LIST_A
only_L = LIST_A - BANG_A

print()
print(f"CHUNG (A ∩ L)             : {len(common):3d}")
print(f"Chỉ Bảng A (A \\ L)        : {len(only_A):3d}")
print(f"Chỉ List A (L \\ A)        : {len(only_L):3d}")
print()

# ── Sample 8 token đầu each set ─────────────────────────────────────────────
def _sample(sset, n=8):
    return sorted(sset)[:n]

print(f"Sample CHUNG (A∩L) [{len(common)}]:")
for s in _sample(common):
    d, sn = list_a_details.get(s, (float("nan"), 0))
    print(f"  {s:20s} div={d:.3f} sn={sn}")

print()
print(f"Sample CHỈ Bảng A (A\\L) [{len(only_A)}]:")
for s in _sample(only_A):
    dv = state.get(s, {}).get("f_avg_mean")
    print(f"  {s:20s} (in gom_e registry · KHÔNG qua List A)")

print()
print(f"Sample CHỈ List A (L\\A) [{len(only_L)}]:")
for s in _sample(only_L):
    d, sn = list_a_details.get(s, (float("nan"), 0))
    print(f"  {s:20s} div={d:.3f} sn={sn} (qua List A · KHÔNG in gom_e registry)")

# ── BTR/MIRA/F kiểm tra riêng ───────────────────────────────────────────────
print()
print(f"═══ BTR/MIRA/F đối chiếu ═══")
for tok in ["BTRUSDT", "MIRAUSDT", "FUSDT"]:
    in_A = tok in BANG_A
    in_L = tok in LIST_A
    d, sn = list_a_details.get(tok, (float("nan"), 0))
    st_ent = state.get(tok, {}).get("entry_date", "?")
    print(f"  {tok:12s}: BảngA={in_A} · ListA={in_L} · "
          f"div_ratio(smoothed)={d:.3f} · sn_count_le050={sn} · "
          f"BảngA entry_date={st_ent}")

sys.exit(0)
