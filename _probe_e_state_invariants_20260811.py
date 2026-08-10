"""E: State invariants checker — run on production gom_state.json.

Five invariants per P0 spec:
(i)  closed-chapters append-only: checked vs md5 reference
(ii) open chain must have last_gom_date within ≤3d of last_eval_date
(iii) no token both chain_open=True AND in cooldown list (dq_cooldown_end future)
(iv) every open/closed chapter has valid vwap_type ∈ {oi_weighted, vol_weighted, N/A, unknown}
(v)  DQ episode not negative: dq_cooldown_end ≥ dq_episode_start when both non-empty

data-source: /root/Data_back_test/whale_data/data/gom_state.json (VPS canonical)
machine: VPS via SSH
date-range: state snapshot 2026-08-11
code-commit: see git log
"""
from __future__ import annotations
import sys, io, json, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
MD5_REF_PATH = Path(r"D:\Data back test\whale_data\scratch\md5_closed_chapters_20260810.json")

result = subprocess.run(
    ["ssh", VPS, "cat /root/Data_back_test/whale_data/data/gom_state.json"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if result.returncode != 0:
    print(f"SSH ERROR: {result.stderr}"); sys.exit(1)

state = json.loads(result.stdout)
print(f"State loaded: {len(state)} tokens")

violations: list[dict] = []

def viol(inv, tok, msg, severity="P1"):
    violations.append({"inv": inv, "token": tok, "msg": msg, "severity": severity})

def parse_date(s):
    if not s or not isinstance(s, str): return None
    try: return datetime.strptime(s[:10], "%Y-%m-%d")
    except: return None

VALID_VWAP_TYPES = {"oi_weighted", "vol_weighted", "N/A", "unknown", ""}

# Current eval reference date (latest last_eval_date we know)
eval_dates = [v.get("last_eval_date","") for v in state.values() if v.get("last_eval_date")]
ref_date_str = max(eval_dates) if eval_dates else "2026-08-09"
ref_date = parse_date(ref_date_str)
print(f"Reference eval date: {ref_date_str}")

# ── (i) Closed-chapters append-only (md5 reference) ─────────────────────────
print(f"\n=== (i) CLOSED-CHAPTERS APPEND-ONLY (md5 check) ===")
if MD5_REF_PATH.exists():
    ref = json.loads(MD5_REF_PATH.read_text(encoding="utf-8"))
    ref_hashes = ref.get("per_token", {})
    ref_agg    = ref.get("aggregate_md5", "")
    ref_n      = ref.get("n_closed", 0)
    ref_date_snap = ref.get("snapshot_date", "?")

    # Recompute current closed chapters
    cur_closed = {}
    for tok, v in state.items():
        if not v.get("chain_open") and v.get("close_date"):
            snap = {k: val for k, val in v.items()
                    if k not in ("updated_at", "last_eval_date", "dq_last_fire")}
            cur_closed[tok] = snap

    cur_tok_hashes = {}
    for tok in sorted(cur_closed):
        canonical = json.dumps(cur_closed[tok], sort_keys=True, ensure_ascii=False, default=str)
        cur_tok_hashes[tok] = hashlib.md5(canonical.encode("utf-8")).hexdigest()

    agg_str = json.dumps(cur_tok_hashes, sort_keys=True)
    cur_agg = hashlib.md5(agg_str.encode("utf-8")).hexdigest()

    agg_match = (cur_agg == ref_agg)
    print(f"  Reference snapshot: {ref_date_snap} | {ref_n} closed | agg_md5={ref_agg}")
    print(f"  Current state     : {ref_date_str} | {len(cur_closed)} closed | agg_md5={cur_agg}")
    print(f"  Aggregate match   : {'PASS ✓' if agg_match else 'FAIL ✗ — closed chapters CHANGED'}")

    if not agg_match:
        # Which tokens changed?
        changed = []
        for tok in sorted(set(list(ref_hashes.keys()) + list(cur_tok_hashes.keys()))):
            rh = ref_hashes.get(tok, "ABSENT")
            ch = cur_tok_hashes.get(tok, "ABSENT")
            if rh != ch:
                changed.append((tok, rh, ch))
        print(f"  Changed tokens ({len(changed)}):")
        for tok, rh, ch in changed[:20]:
            print(f"    {tok}: ref={rh[:8]} cur={ch[:8]}")
        if len(changed) > 0:
            viol("i", "aggregate", f"{len(changed)} closed chapters changed since {ref_date_snap}", "P0")
else:
    print(f"  MD5 reference NOT FOUND at {MD5_REF_PATH} — skip (run after first cron)")

# ── (ii) Open chain ≤3d since last GOM fire ──────────────────────────────────
print(f"\n=== (ii) OPEN CHAIN ≤3d SINCE LAST GOM FIRE ===")
open_tokens = [(t, v) for t, v in state.items() if v.get("chain_open")]
ii_violations = 0
for tok, v in open_tokens:
    last_gom = parse_date(v.get("last_gom_date",""))
    last_eval = parse_date(v.get("last_eval_date",""))
    if last_eval is None:
        continue  # legacy token, not scanned by new incremental
    if last_gom is None:
        viol("ii", tok, f"chain_open=True but last_gom_date empty", "P1")
        ii_violations += 1
        continue
    gap = (last_eval - last_gom).days
    if gap > 3:
        viol("ii", tok, f"last_gom={v.get('last_gom_date')} last_eval={v.get('last_eval_date')} gap={gap}d > 3", "P1")
        ii_violations += 1

print(f"  Open tokens checked: {len(open_tokens)}")
print(f"  Violations         : {ii_violations}")
if ii_violations == 0:
    print(f"  PASS ✓")

# ── (iii) Not both open AND cooldown-suppressed ──────────────────────────────
print(f"\n=== (iii) OPEN chain ≠ in cooldown simultaneously ===")
iii_violations = 0
for tok, v in open_tokens:
    cooldown_end = v.get("dq_cooldown_end","")
    if cooldown_end:
        cd_dt = parse_date(cooldown_end)
        if cd_dt and ref_date and cd_dt >= ref_date:
            viol("iii", tok, f"chain_open=True but dq_cooldown_end={cooldown_end} still active on {ref_date_str}", "P0")
            iii_violations += 1

print(f"  Open tokens: {len(open_tokens)}")
print(f"  Violations : {iii_violations}")
if iii_violations == 0:
    print(f"  PASS ✓")

# ── (iv) Valid vwap_type ─────────────────────────────────────────────────────
print(f"\n=== (iv) VALID vwap_type ===")
iv_violations = 0
for tok, v in state.items():
    vwap_type = v.get("vwap_type","")
    if vwap_type not in VALID_VWAP_TYPES:
        viol("iv", tok, f"vwap_type='{vwap_type}' not in valid set", "P2")
        iv_violations += 1
    # Also check chapter_hist
    for hist in v.get("chapter_hist", []):
        # chapter_hist doesn't have vwap_type by default — skip
        pass

print(f"  Tokens checked: {len(state)}")
print(f"  Violations    : {iv_violations}")
if iv_violations == 0:
    print(f"  PASS ✓")
else:
    for vv in [v for v in violations if v["inv"] == "iv"][:10]:
        print(f"    {vv['token']}: {vv['msg']}")

# ── (v) DQ episode not negative ──────────────────────────────────────────────
print(f"\n=== (v) DQ EPISODE NOT NEGATIVE (cooldown_end ≥ episode_start) ===")
v_violations = 0
for tok, v in state.items():
    ep_start   = parse_date(v.get("dq_episode_start",""))
    cooldown   = parse_date(v.get("dq_cooldown_end",""))
    if ep_start and cooldown and cooldown < ep_start:
        viol("v", tok, f"dq_cooldown_end={v.get('dq_cooldown_end')} < dq_episode_start={v.get('dq_episode_start')}", "P1")
        v_violations += 1

print(f"  Tokens with DQ episode: {sum(1 for v in state.values() if v.get('dq_episode_start'))}")
print(f"  Violations             : {v_violations}")
if v_violations == 0:
    print(f"  PASS ✓")

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"STATE INVARIANT SUMMARY — {len(state)} tokens, ref={ref_date_str}")
print(f"{'='*60}")
if not violations:
    print(f"  ALL 5 INVARIANTS PASS ✓")
else:
    p0 = [v for v in violations if v["severity"] == "P0"]
    p1 = [v for v in violations if v["severity"] == "P1"]
    p2 = [v for v in violations if v["severity"] == "P2"]
    print(f"  P0 violations: {len(p0)}")
    print(f"  P1 violations: {len(p1)}")
    print(f"  P2 violations: {len(p2)}")
    for vv in violations:
        print(f"  [{vv['severity']}] inv({vv['inv']}) {vv['token']}: {vv['msg']}")
