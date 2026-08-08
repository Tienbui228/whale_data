"""3d cross-check: BR, XPIN, HEI — inline signal readings for gate v8d table.

Pull last 3 days of GOM-A signals + suppressor state for each token.
Also pull full chain state from gom_state_v8.json.
"""
import sys, math, json
from pathlib import Path
sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE    = Path("D:/Check onchain fresh wallets/data/export")
CONFIG   = Path("data/config")
STATE_V8 = Path("data/gom_state_v8.json")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-08-07", lookback_days=75)
df = taker_scale_check_df(df)

state_all = json.loads(STATE_V8.read_text(encoding="utf-8"))

TOKENS = ["BR", "XPIN", "HEI"]

for sym in TOKENS:
    build_sym = sym + "USDT"
    st = state_all.get(sym, {})
    print(f"\n{'='*60}")
    print(f"TOKEN: {sym}  ({build_sym})")
    print(f"State: chain_open={st.get('chain_open')}  dq_ep={st.get('dq_episode_start','')}  "
          f"dq_end={st.get('dq_cooldown_end','')}  close_reason={st.get('close_reason','')}  "
          f"close_date={st.get('close_date','')}")

    try:
        days_tok, _ = build_token_days(df, build_sym, "2026-07-01", "2026-08-07", intervals)
        enrich_token_days(days_tok)
    except Exception as e:
        print(f"  BUILD ERROR: {e}")
        continue

    if not days_tok:
        print("  NO DAYS in fw")
        continue

    print(f"  fw range: {days_tok[0].get('date')} → {days_tok[-1].get('date')}  ({len(days_tok)} days)")
    print()

    # Run scan loop and print last 5 days
    chain = {}
    all_results = []
    for i, d in enumerate(days_tok):
        result = gs.eval_gom(days_tok, i, cfg, sc)
        chain  = gs.update_chain(chain, build_sym, days_tok, i, result, cfg, sc)
        all_results.append((d.get("date",""), result, dict(chain), dict(d)))

    # Print last 5 days
    print(f"  {'date':<12} {'A1':>4} {'A2':>4} {'A3':>4} {'A4':>4} {'A5':>4} {'FIRE':>6} {'supp':>6} {'chain_open':>11} {'dq_ep':<12}")
    print("  " + "-"*80)
    for dt, result, ch, d in all_results[-5:]:
        ga   = result.get("gom_a", {})
        fire = ga.get("A1") and ga.get("A2") and ga.get("A3") and (ga.get("A4") or ga.get("A5"))
        supp = result.get("any_supp_dq", False)
        a1   = "T" if ga.get("A1") else "F"
        a2   = "T" if ga.get("A2") else "F"
        a3   = "T" if ga.get("A3") else "F"
        a4   = "T" if ga.get("A4") else "F"
        a5   = "T" if ga.get("A5") else "F"
        fire_s = "FIRE" if fire else ""
        supp_s = "SUPP" if supp else ""
        co   = "open" if ch.get("chain_open") else ""
        dq   = ch.get("dq_episode_start","")
        avg_px = d.get("avg_px", float("nan"))
        lsr    = d.get("lsr_pos", float("nan"))
        print(f"  {dt:<12} {a1:>4} {a2:>4} {a3:>4} {a4:>4} {a5:>4} {fire_s:>6} {supp_s:>6} {co:>11} {dq:<12}  px={avg_px:.6g}  lsr={lsr:.4g}")

    # Final chain state
    final_chain = all_results[-1][2]
    print()
    print(f"  Final chain state:")
    for k in ["chain_open","dq_episode_start","dq_cooldown_end","close_date","close_reason","retro_tag","peak_pos_r","n_days"]:
        if k in final_chain:
            print(f"    {k}: {final_chain[k]}")
