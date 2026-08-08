"""BUOC 2 prep: check gate-relevant tokens from gom_state_v8.json"""
import json, sys
from pathlib import Path

STATE = Path("data/gom_state_v8.json")
state = json.loads(STATE.read_text(encoding="utf-8"))

gate_toks = ["PARTI","TAG","ZBT","BAS","BTW","AKE","BULLA","POWER","CLO","BANK","TUT","BANANAS31","IDOL"]
print(f"{'TOKEN':<12} {'open':>5} {'ch':>3} {'start':>12} {'close':>12} {'reason':<45} {'dq_ep':>12} {'dq_end':>12}")
print("-"*120)
for tok in gate_toks:
    s = state.get(tok, {})
    if not s:
        print(f"{tok:<12} {'--':>5} {'--':>3} {'--':>12} {'--':>12} {'(no state)':45} {'':>12} {'':>12}")
        continue
    chain_open = s.get("chain_open", False)
    open_date  = s.get("start_date","?")[:10]
    close_date = s.get("close_date","?")[:10]
    close_rsn  = (s.get("close_reason","") or "")[:44]
    chapter    = s.get("chapter",1)
    dq_ep      = (s.get("dq_episode_start","") or "")[:10]
    dq_end     = (s.get("dq_cooldown_end","") or "")[:10]
    hist       = s.get("chapter_hist",[])
    print(f"{tok:<12} {str(chain_open):>5} {chapter:>3} {open_date:>12} {close_date:>12} {close_rsn:<45} {dq_ep:>12} {dq_end:>12}")
    for h in hist:
        print(f"  hist ch{h.get('chapter','?')}: {h.get('start','?')[:10]}->{h.get('end','?')[:10]}  vwap={h.get('vwap','?')}  Q1=${h.get('Q1_cum',0):,.0f}")

print()
# Also show OPEN count and list
open_toks = [k for k,v in state.items() if not k.startswith("_") and isinstance(v,dict) and v.get("chain_open")]
print(f"OPEN chains ({len(open_toks)}): {', '.join(sorted(open_toks))}")
print(f"Total tokens in state: {sum(1 for k in state if not k.startswith('_'))}")
