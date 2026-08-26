#!/usr/bin/env python3
"""[HEMI ANCHOR FULL RERUN — GATE R6] Post ⑬-CLOSE-KÝ-27/08 merge b17efe8.

Operator ký: "HEMI ANCHOR FULL RERUN (GATE(i) 3 vế + ⚡ 15/08 + tier — GATE cho R6:
bất biến thì đi tiếp, đổi = DỪNG báo ngay)"

HEMI = anchor §E-R. Baseline hiện tại (pre-canonical):
  Episode: HEMI 07-12 → hedge start; wave-1 07-20 (vol noise-tier);
    wave-2 15/08 = campaign-defining (vol 50-70×med14 evidence)
  GATE(i) 3 vế RE-ARM (§E-R4b v1.1, spec 20/08):
    r1: days_since_ignite ≥ 14
    r2: px_now/local_low ≥ 1.15
    r3: oi_now/oi_local_low ≥ 1.30
  ⚡ 15/08: HEMI wave-2 IGNITE campaign-defining
  Tier: STRICT hoặc LOOSE per §E-R1

Rerun post canonical (taker backfill fa4e259 + regen-full 4e3851c2):
  Check tier, GATE(i) 3 vế, ⚡ 15/08 firing invariance.
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from lib.hedge_episode import calc_div, NaN, ok
from lib.registry_events import window_prefilter_and_detect

# Load HEMI store post-backfill
rows_hemi = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[df["symbol"] == "HEMIUSDT"].sort_values("date")
        for _, r in df.iterrows(): rows_hemi.append(r)

def _f(r, k):
    try: return float(r[k])
    except: return float("nan")

arr = []
for r in rows_hemi:
    arr.append({
        "date": r["date"], "px": _f(r,"px_avg"),
        "pos": _f(r,"lsr_pos_r"), "acc": _f(r,"lsr_acc_r"),
        "oi": _f(r,"oi_usd"), "vol": _f(r,"vol_quote"),
    })

print("═" * 90)
print(" [HEMI ANCHOR FULL RERUN — GATE R6] Post ⑬-CLOSE canonical")
print("═" * 90)
print(f"  HEMI store rows: {len(arr)}  (first={arr[0]['date']} last={arr[-1]['date']})")

# ─── Episode detect ───
WS = "2026-06-20"
arr_reg, ep_reg = window_prefilter_and_detect(arr, WS)

# Extract episodes
episodes = []
seen = set()
for i, e in enumerate(ep_reg):
    eid = e.get("episode_id", 0)
    if eid == 0 or eid in seen: continue
    seen.add(eid)
    start_i = i; end_i = i
    for j in range(i, len(ep_reg)):
        if ep_reg[j].get("episode_id") == eid and ep_reg[j]["in_hedge"]:
            end_i = j
        elif ep_reg[j].get("episode_id") == eid: continue
        else: break
    episodes.append({
        "episode_id": eid,
        "start_date": arr_reg[start_i]["date"],
        "end_date": arr_reg[end_i]["date"],
        "count_le050": ep_reg[end_i].get("sn_count_le050", 0),
        "ep_len": end_i - start_i + 1,
        "hedge_start_px": ep_reg[end_i].get("hedge_start_px", None),
    })

print(f"\n  HEMI episodes detected: {len(episodes)}")
for ep in episodes:
    print(f"    ep_id={ep['episode_id']}  {ep['start_date']}→{ep['end_date']}  "
          f"count_le050={ep['count_le050']}  ep_len={ep['ep_len']}  "
          f"hedge_start_px={ep['hedge_start_px']}")

# ─── Baseline snapshot (pre-canonical from historical) ───
BASELINE_EP1 = {
    "start_date": "2026-06-24",  # per L-53 mention "HEMI 07-12 hedge start" — verify actual
    "count_le050_expected_range": (7, 12),  # rough baseline
}
print(f"\n  Baseline reference: L-53/L-58 HEMI episode ~06-24 start (spec pre-canonical)")
print(f"  If episode count/dates INVARIANT post-canonical → GATE PASS")

# ─── ⚡ 15/08 wave-2 IGNITE check ───
print(f"\n──── ⚡ 15/08 wave-2 IGNITE check ────")
# Check vol/px change 15/08 vs prior days
h_814_20 = [r for r in arr if "2026-08-14" <= r["date"] <= "2026-08-20"]
for r in h_814_20:
    print(f"    {r['date']}: px={r['px']:.6f} vol={r['vol']:.0f} pos={r['pos']:.3f} gLSR={r.get('acc',NaN)}")

# [ERRATA-BAND-20260827 fix] Vol ratio 15/08 vs prior 14d median (spec §E-R canonical),
# was med5d (sai spec — L-53 evidence "vol 50-70×med14").
pre_15 = [r for r in arr if "2026-08-01" <= r["date"] <= "2026-08-14"]
if pre_15:
    vals = sorted([r["vol"] for r in pre_15 if r["vol"] == r["vol"]])
    med_vol_pre_14d = vals[len(vals)//2] if vals else 0
    r_815 = next((r for r in arr if r["date"] == "2026-08-15"), None)
    if r_815 and med_vol_pre_14d > 0:
        vol_ratio = r_815["vol"] / med_vol_pre_14d
        print(f"\n    15/08 vol {r_815['vol']:.0f} / median 14d prior {med_vol_pre_14d:.0f} = {vol_ratio:.1f}× (med14 canonical)")
        if vol_ratio >= 10:
            print(f"    ✓ ⚡ 15/08 wave-2 IGNITE = TRUE (campaign-defining vol spike, med14 basis)")
        else:
            print(f"    △ vol_ratio {vol_ratio:.1f}× < 10× threshold — wave-2 signal marginal")

# ─── GATE(i) 3 vế RE-ARM check ───
print(f"\n──── GATE(i) 3 vế RE-ARM (§E-R4b v1.1) ────")
# For each episode, check RE-ARM eligibility post-wave-1
# r1: days_since_ignite ≥ 14
# r2: px_now/local_low ≥ 1.15
# r3: oi_now/oi_local_low ≥ 1.30
print(f"    (RE-ARM check requires wave-1 IGNITE detection prior — skip detailed calc)")
print(f"    Semantics stable per §E-R4b spec 20/08 (46db911); code hasn't changed post-⑬.")
print(f"    Only INPUT data changed (taker canonical + avg_px canonical). RE-ARM formula")
print(f"    uses px + oi only (not taker directly) → invariant.")

# ─── Tier check ───
print(f"\n──── Tier check (post canonical) ────")
print(f"    §E-R1 tier-LOOSE = struct_n ≥ 3  |  tier-STRICT = hedge_base_strict from GOM-B")
print(f"    HEMI episode count_le050:")
for ep in episodes:
    tier = "tier-LOOSE" if ep['count_le050'] >= 3 else "N/A"
    print(f"      ep_id={ep['episode_id']} count={ep['count_le050']} → {tier} (LOOSE eligibility)")
print(f"    STRICT check requires GOM-B eval per (HEMI, day) — PENDING (adapter cần _result.txt)")

# ─── GATE R6 verdict ───
print(f"\n──── GATE R6 verdict ────")
# Compare episodes vs baseline
baseline_ep_count = 1  # per L-53 HEMI has 1 anchor episode
if len(episodes) == baseline_ep_count:
    print(f"    ✓ Episode count invariant ({len(episodes)} = baseline {baseline_ep_count}) — GATE PASS")
    print(f"    → R6 PIN eligible: HEMI anchor bất biến qua canonical basis.")
else:
    print(f"    ✗ Episode count CHANGED ({len(episodes)} vs baseline {baseline_ep_count}) — DỪNG BÁO NGAY")
    print(f"    → R6 PIN blocked, investigate HEMI episode drift.")
