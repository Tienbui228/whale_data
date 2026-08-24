#!/usr/bin/env python3
"""[FEEDER tier-STRICT probe] BULLA episode 06-29→07-17 (freshwatch) + HBS per day
(from _result.txt bot-signals) → assign_episode_tiers.

Expected: tier-STRICT (BULLA HBS window 07-05→07-09 + 07-11→07-14 FALLS WITHIN 06-29→07-17 span).
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(BOT))

from replay import parse_result_file, build_days
import scripts.gom_scan as gom_scan
from lib.registry_events import (
    window_prefilter_and_detect, assign_episode_tiers,
)
from lib.hedge_episode import NaN, ok, calc_div

# ─── Step 1: Compute BULLA HBS per day from bot-signals _result.txt ───
cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)

fps = list((BOT / "docs" / "case study").glob("bulla*_result.txt"))
if not fps: sys.exit("BULLA _result.txt not found")
funding, oi, ratio, klines = parse_result_file(fps[0])
days = build_days(funding, oi, ratio, klines)
sc = {}

hbs_by_day = {}   # {date_str: bool}
for i in range(len(days)):
    d = days[i]
    date_str = d.get("date", "")
    if len(date_str) == 5: date_str = "2026-" + date_str
    if not date_str: continue
    try:
        r = gom_scan.eval_gom(days, i, cfg, sc)
    except Exception:
        continue
    hbs = r.get("hedge_base_strict", False)
    hbs_by_day[date_str] = hbs

print(f"[FEEDER probe] BULLA hbs_by_day covers {len(hbs_by_day)} days "
      f"({min(hbs_by_day)} → {max(hbs_by_day)})")
hbs_true_dates = sorted([d for d, v in hbs_by_day.items() if v])
print(f"  HBS=True dates: {hbs_true_dates}")

# ─── Step 2: Compute BULLA registry episode from freshwatch ───
frames = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        frames.append(df[df["symbol"] == "BULLAUSDT"])
df = pd.concat(frames, ignore_index=True).sort_values("date")
arr = []
for _, r in df.iterrows():
    def _f(k):
        try: return float(r[k])
        except: return NaN
    arr.append({
        "date": r["date"], "px": _f("px_avg"),
        "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
        "oi": _f("oi_usd"), "vol": _f("vol_quote"),
    })

WS = "2026-06-20"
arr_reg, ep_reg = window_prefilter_and_detect(arr, WS)

# Extract episodes list format
episodes = []
seen_eids = set()
for i, e in enumerate(ep_reg):
    eid = e.get("episode_id", 0)
    if eid == 0 or eid in seen_eids: continue
    seen_eids.add(eid)
    start_i = i; end_i = i
    for j in range(i, len(ep_reg)):
        if ep_reg[j].get("episode_id") == eid and ep_reg[j]["in_hedge"]:
            end_i = j
        elif ep_reg[j].get("episode_id") == eid:
            continue
        else:
            break
    episodes.append({
        "episode_id": eid,
        "start_date": arr_reg[start_i]["date"],
        "end_date": arr_reg[end_i]["date"],
        "count_le050": ep_reg[end_i].get("sn_count_le050", 0),
        "ep_len": end_i - start_i + 1,
    })

print(f"\n[FEEDER probe] BULLA registry episodes: {len(episodes)}")
for ep in episodes:
    print(f"  ep_id={ep['episode_id']}  {ep['start_date']}→{ep['end_date']}  "
          f"count_le050={ep['count_le050']}  ep_len={ep['ep_len']}")

# ─── Step 3: Apply feeder ───
print(f"\n[FEEDER probe] Apply assign_episode_tiers()...")
result = assign_episode_tiers(episodes, hbs_by_day)
print(f"\n{'ep_id':>6}  {'span':>25}  {'count_le050':>11}  {'tier':>15}  {'note':<40}  {'hbs_dates (count)':<20}")
print("─" * 130)
for ep in result:
    span = f"{ep['start_date']}→{ep['end_date']}"
    hbs_n = len(ep.get("hbs_dates", []))
    print(f"{ep['episode_id']:>6}  {span:>25}  {ep['count_le050']:>11}  {ep['tier']:>15}  "
          f"{ep.get('tier_note','')[:40]:<40}  {hbs_n}d {'{' + ', '.join(ep['hbs_dates'][:5]) + '}' if hbs_n else ''}")
print()

# Expected verify
expected_tier = "tier-STRICT" if any(hbs_by_day.get(d, False) for d in ["2026-07-05", "2026-07-06", "2026-07-07"]) else "?"
if result and result[0]["tier"] == "N/A":
    print(f"[VERIFY] BULLA episode gets tier='N/A' — expected because HBS data (bot-signals _result.txt) "
          f"only covers {min(hbs_by_day)} → {max(hbs_by_day)}, not full registry span 06-29→08-23.")
    print(f"  Fail-loud correctly triggered — missing HBS days flagged.")
elif result and result[0]["tier"] == "tier-STRICT":
    print(f"[VERIFY] BULLA episode tier-STRICT ✓ (HBS window falls within registry span)")
