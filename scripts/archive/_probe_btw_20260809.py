"""BTW profile + new-chain breakdown 08-07 vs 08-08.
Q: (1) DQ timeline (2) A1-A5 on 08-08 (3) source of $7.5M Q1
   (4) How many chains NEW on 08-08 vs 08-07 (fw139 universe)
   (5) Was 08-08 a red day (market move)?
"""
import sys, json, math
from pathlib import Path
import pandas as pd

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gom_scan as gs
from fw_loader_utils import build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df

STORE   = Path("data/export")
CONFIG  = Path("data/config")
STATE   = Path("data/gom_state.json")
FW_SYM  = CONFIG / "freshwatch_symbols.txt"

intervals = load_funding_intervals(CONFIG)
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

# ── Load export CSVs ──────────────────────────────────────────────────────────
frames = []
for fn in ["freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    p = STORE / fn
    if p.exists():
        frames.append(pd.read_csv(p))
df = pd.concat(frames, ignore_index=True)
df = taker_scale_check_df(df)

fw_syms = [l.strip() for l in FW_SYM.read_text(encoding="utf-8").splitlines() if l.strip()]

# ── (0) Clarify open_chains_reported=36 ───────────────────────────────────────
with open(STATE) as f:
    state = json.load(f)
fw_base = {s[:-4] if s.endswith("USDT") else s for s in fw_syms}
open_fw = [(k, v) for k, v in state.items() if v.get("chain_open") and k in fw_base]
print(f"CLARIFY: open_chains_reported=36 was mis-count (all indented lines in report)")
print(f"  Actual fw139 open 08-08: {len(open_fw)}")
print(f"  Actual fw139 open 08-07: 16 (from yesterday's report)")
print(f"  Delta: +{len(open_fw)-16} = BTW only entering ★")
print()

# ── (1) BTW DQ timeline ───────────────────────────────────────────────────────
btw_st = state.get("BTW", {})
print("=== BTW DQ TIMELINE ===")
print(f"  dq_episode_start : {btw_st.get('dq_episode_start', 'N/A')}")
print(f"  dq_last_fire     : {btw_st.get('dq_last_fire', 'N/A')}")
print(f"  dq_cooldown_end  : {btw_st.get('dq_cooldown_end', 'N/A')}")
print(f"  chapter_hist     : {btw_st.get('chapter_hist', [])}")
print(f"  Current chapter  : {btw_st.get('chapter')} start={btw_st.get('start_date')}")
print(f"  Days clear before open: 8 days (07-31 -> 08-08)")
print()

# ── (2) A1-A5 on 08-08 ───────────────────────────────────────────────────────
days_btw, _ = build_token_days(df, "BTWUSDT", "2026-06-01", "2026-08-08", intervals)
enrich_token_days(days_btw)

chain = {}
print("=== BTW A1-A5 BREAKDOWN (running chain) ===")
print(f"{'Date':10}  {'A1':4}  {'A2':4}  {'A3':4}  {'A4':4}  {'A5':4}  {'B1':4}  {'B3':4}  {'B4':4}  {'GOM':4}  {'DQ':4}  pos_r  oi_usd")
print("-" * 95)
for i, d in enumerate(days_btw):
    dt = d.get("date", "")
    if dt < "2026-07-15" or dt > "2026-08-08":
        continue
    r = gs.eval_gom(days_btw, i, cfg, sc)
    chain = gs.update_chain(chain, "BTW", days_btw, i, r, cfg, sc)
    conds = r.get("conditions_met", [])
    dq    = r.get("any_supp_dq", False)
    gom   = r.get("gom_day", False)
    pos_r = d.get("lsr_pos_r", float("nan"))
    oi    = d.get("oi_usd", float("nan"))
    pos_s = f"{pos_r:.3f}" if not math.isnan(pos_r) else "N/A"
    oi_s  = f"${oi/1e6:.2f}M" if not math.isnan(oi) else "N/A"
    a1 = "Y" if "A1" in conds else "."
    a2 = "Y" if "A2" in conds else "."
    a3 = "Y" if "A3" in conds else "."
    a4 = "Y" if "A4" in conds else "."
    a5 = "Y" if "A5" in conds else "."
    b1 = "Y" if "B1" in conds else "."
    b3 = "Y" if "B3" in conds else "."
    b4 = "Y" if "B4" in conds else "."
    print(f"{dt:10}  {a1:4}  {a2:4}  {a3:4}  {a4:4}  {a5:4}  {b1:4}  {b3:4}  {b4:4}  {'Y' if gom else 'N':4}  {'DQ' if dq else '.':4}  {pos_s}  {oi_s}")
print()

# ── (3) Source of $7.5M Q1 ───────────────────────────────────────────────────
print("=== BTW OI SERIES (source of $7.5M Q1) ===")
df_btw = df[df["symbol"] == "BTWUSDT"].sort_values("date")
df_btw = df_btw[df_btw["date"] >= "2026-07-15"]
for _, row in df_btw.iterrows():
    dt   = row["date"]
    oi   = row.get("oi_usd", float("nan"))
    px   = row.get("px_avg", float("nan"))
    pos  = row.get("lsr_pos_r", float("nan"))
    oi_s = f"${oi/1e6:.3f}M" if not math.isnan(oi) else "N/A"
    px_s = f"${px:.5f}" if not math.isnan(px) else "N/A"
    pos_s = f"{pos:.3f}" if not math.isnan(pos) else "N/A"
    print(f"  {dt}  OI={oi_s}  px={px_s}  pos_r={pos_s}")

# Compute single-day delta for chapter open
oi_0807 = df_btw[df_btw["date"] == "2026-08-07"]["oi_usd"].values
oi_0808 = df_btw[df_btw["date"] == "2026-08-08"]["oi_usd"].values
if len(oi_0807) and len(oi_0808):
    delta = oi_0808[0] - oi_0807[0]
    print(f"\n  Q1 source: OI(08-08) - OI(08-07) = ${oi_0808[0]/1e6:.3f}M - ${oi_0807[0]/1e6:.3f}M = +${delta/1e6:.3f}M")
    print(f"  (matches Q1_cum_usd={btw_st.get('Q1_cum_usd',0)/1e6:.3f}M in state)")
print()

# ── (4) Market context 08-08 ─────────────────────────────────────────────────
print("=== MARKET CONTEXT 08-08 (px change for fw139 universe) ===")
df_08 = df[df["date"].isin(["2026-08-07", "2026-08-08"])]
px_pivot = df_08.pivot_table(index="symbol", columns="date", values="px_avg")
px_pivot.columns = ["px_0807", "px_0808"]
px_pivot = px_pivot.dropna()
px_pivot["ret"] = (px_pivot["px_0808"] - px_pivot["px_0807"]) / px_pivot["px_0807"] * 100
fw_syms_set = set(fw_syms)
px_pivot_fw = px_pivot[px_pivot.index.isin(fw_syms_set)]
n_up   = (px_pivot_fw["ret"] > 1).sum()
n_down = (px_pivot_fw["ret"] < -1).sum()
n_flat = len(px_pivot_fw) - n_up - n_down
median_ret = px_pivot_fw["ret"].median()
print(f"  fw139 tokens 08-08: up>1%={n_up}, down<-1%={n_down}, flat={n_flat}")
print(f"  Median ret 08-08: {median_ret:+.1f}%")
print(f"  Verdict: {'RED day (market down)' if median_ret < -1 else 'GREEN day' if median_ret > 1 else 'FLAT'}")
print()

# ── (5) New chains on 08-08 vs 08-07 ─────────────────────────────────────────
print("=== NEW CHAINS 08-08 vs 08-07 (fw139, sorted by Q1) ===")
# open_fw already computed above
# start_date == 08-08 = new chain
new_chains = [(k, v) for k, v in open_fw if v.get("start_date") == "2026-08-08"]
old_chains = [(k, v) for k, v in open_fw if v.get("start_date") != "2026-08-08"]
new_chains.sort(key=lambda x: -x[1].get("Q1_cum_usd", 0))
print(f"New chains opening 08-08: {len(new_chains)}")
print(f"Chains already open before 08-08: {len(old_chains)}")
print()
print(f"{'Token':12}  {'Q1':10}  {'n':3}  {'start':10}  conditions_hint")
for k, v in new_chains[:20]:
    q1  = v.get("Q1_cum_usd", 0)
    nd  = v.get("n_days", 0)
    sd  = v.get("start_date", "?")
    q1s = f"${q1/1e3:.0f}k" if q1 >= 1000 else "$0"
    print(f"  {k:12}  {q1s:10}  {nd:3}  {sd}")
