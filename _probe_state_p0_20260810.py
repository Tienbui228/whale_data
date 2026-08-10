"""P0 state integrity check — backup bc3f8c35 vs current gom_state.json."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Data back test\whale_data")

def load(p): return json.loads(p.read_text(encoding="utf-8"))

bak = load(ROOT / "data" / "gom_state_v9_vps.json")
cur = load(ROOT / "data" / "gom_state.json")

bak_open = {t for t,c in bak.items() if c.get("chain_open")}
cur_open  = {t for t,c in cur.items() if c.get("chain_open")}

print("=== P0 STATE INTEGRITY ===")
print(f"Backup bc3f8c35 (gom_state_v9_vps.json): {len(bak)} tokens, {len(bak_open)} open")
print(f"Current gom_state.json (1e65eb1b):        {len(cur)} tokens, {len(cur_open)} open")
print()
print(f"Open in backup: {sorted(bak_open)}")
print(f"Open in current: {sorted(cur_open)}")
print()
missing_from_cur  = bak_open - cur_open
extra_in_cur      = cur_open - bak_open
print(f"Chains OPEN in backup but MISSING/CLOSED in current ({len(missing_from_cur)}): {sorted(missing_from_cur)}")
print(f"Chains OPEN in current but NOT in backup ({len(extra_in_cur)}): {sorted(extra_in_cur)}")
print()

# Check FF, BTW, PARTI specifically
print("=== SPECIFIC TOKENS ===")
for sym in ["FF", "BTW", "PARTI"]:
    b = bak.get(sym, {})
    c = cur.get(sym, {})
    print(f"\n{sym}:")
    print(f"  BACKUP: in_state={sym in bak}  chain_open={b.get('chain_open')}  close_date={b.get('close_date','N/A')}  close_reason={b.get('close_reason','N/A')[:40] if b.get('close_reason') else 'N/A'}  Q1={b.get('Q1_cum_usd',0):,.0f}")
    print(f"  CURRENT: in_state={sym in cur}  chain_open={c.get('chain_open')}  close_date={c.get('close_date','N/A')}  close_reason={c.get('close_reason','N/A')[:40] if c.get('close_reason') else 'N/A'}")

# Check tokens missing entirely from current state
missing_entirely = {t for t in bak if t not in cur}
print(f"\n=== Tokens in backup but NOT in current state at all ({len(missing_entirely)}): ===")
print(sorted(missing_entirely)[:30])

# Tokens closed in current that were open in backup
closed_wrongly = {t for t in bak_open if t in cur and not cur[t].get("chain_open")}
print(f"\n=== Tokens OPEN in backup, CLOSED in current ({len(closed_wrongly)}): ===")
for t in sorted(closed_wrongly):
    c = cur[t]
    print(f"  {t}: close_date={c.get('close_date','?')} reason={str(c.get('close_reason','?'))[:50]}")
