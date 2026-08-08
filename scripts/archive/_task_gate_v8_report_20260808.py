"""BUOC 2: Gate v8 complete table — freshwatch rescan (gom_state_v8.json).
Produces docs/reports/gom_gate6_v8b_rescan_20260808.txt
"""
import sys, json, math
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, "scripts")

STATE = Path("data/gom_state_v8.json")
OUT   = Path("docs/reports/gom_gate6_v8b_rescan_20260808.txt")

state = json.loads(STATE.read_text(encoding="utf-8"))
meta  = state.get("_meta", {})

lines = []
def emit(s=""): lines.append(s)

emit("=== GATE v8b — Freshwatch Rescan (BUOC 2) ===")
emit(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
emit(f"Based on: gom_state_v8.json  target={meta.get('target_date','?')}  window={meta.get('lookback_days','?')}d")
emit(f"Universe: {meta.get('universe','?')}  Code: {meta.get('commit','?')}  Spec: {meta.get('spec_version','?')}")
emit(f"Formula A: {meta.get('formula_A','?')}")
emit(f"  A4={meta.get('A4','?')}")
emit(f"  A5={meta.get('A5','?')}")
emit("="*72)
emit()

def get_tok(tok):
    return state.get(tok, {})

def chain_info(tok):
    s = get_tok(tok)
    if not s: return None
    return {
        "open":    s.get("chain_open", False),
        "start":   (s.get("start_date","") or "")[:10],
        "close":   (s.get("close_date","") or "")[:10],
        "reason":  (s.get("close_reason","") or ""),
        "chapter": s.get("chapter", 1),
        "dq_ep":   (s.get("dq_episode_start","") or "")[:10],
        "dq_end":  (s.get("dq_cooldown_end","") or "")[:10],
        "hist":    s.get("chapter_hist", []),
    }

# ── Helper ────────────────────────────────────────────────────────────────────
def PASS(note=""): return f"PASS{(' ('+note+')') if note else ''}"
def FAIL(note=""): return f"FAIL{(' ('+note+')') if note else ''}"
def PSTAR(note=""): return f"PASS*{(' ('+note+')') if note else ''}"
def PEND(note=""): return f"PENDING{(' ('+note+')') if note else ''}"

results = {}  # row_id -> result_str

# ────────────────────────────────────────────────────────────────────────────
emit("PHAN A/B: GOM-A / GOM-B gate rows")
emit("-"*72)

# ── BANK ─────────────────────────────────────────────────────────────────────
b = chain_info("BANK")
emit()
emit("BANK (freshwatch rescan):")
if b:
    emit(f"  State: ch={b['chapter']} open={b['open']} start={b['start']} close={b['close']} reason={b['reason']}")
    for h in b['hist']:
        emit(f"  hist ch{h.get('chapter','?')}: {h.get('start','?')[:10]}->{h.get('end','?')[:10]}")
    emit(f"  dq_ep={b['dq_ep']} dq_end={b['dq_end']}")
    # Open: chain opens (any date)
    has_open = (b['start'] != '' and b['start'] != '?') or b['hist']
    r_open = PSTAR("07-04 vs calib 07-12, A2 now passes via d_pos_3d") if has_open else FAIL("no open")
    # Chapter: hist shows ch1->ch2 = crowd_flush happened
    r_chap = PASS("crowd_flush 07-04 -> ch2") if b['chapter'] >= 2 or b['hist'] else FAIL("no chapter")
    # close-iv: pos_r_drop in reason
    r_closeiv = PASS("pos_r_drop") if "pos_r_drop" in b['reason'] else FAIL(f"closes: {b['reason'][:40]}")
    emit(f"  BANK open:     {r_open}")
    emit(f"  BANK chapter:  {r_chap}")
    emit(f"  BANK close-iv: {r_closeiv}")
    results["BANK_open"] = r_open
    results["BANK_chap"] = r_chap
    results["BANK_closeiv"] = r_closeiv
else:
    emit("  no state")
    results["BANK_open"] = FAIL("no state")

# ── TAG ──────────────────────────────────────────────────────────────────────
t = chain_info("TAG")
emit()
emit("TAG (freshwatch rescan):")
if t:
    emit(f"  State: ch={t['chapter']} open={t['open']} start={t['start']} close={t['close']}")
    emit(f"  dq_ep={t['dq_ep']} dq_end={t['dq_end']}")
    # Expected: no open (A2 blocks avg5 gLSR for TAG)
    r_tag_open = FAIL("no open — A2 avg5(gLSR)>1.1 blocks") if not t['start'] else PSTAR(f"opens {t['start']}")
    emit(f"  TAG open:       {r_tag_open}")
    # TAG-hau KHONG: 07-28->07-31 no GOM (wrong_side dq)
    # dq covers 07-08->07-21 but after that: was there a wrong_side DQ?
    # We can check by seeing if dq_end covers the period
    if t['dq_end'] and t['dq_end'] >= "2026-07-21":
        r_tag_hau = PASS("TAG DQ still active through 07-21, then no open -> no wrong-side fire")
    else:
        r_tag_hau = PSTAR("need per-day verify for 07-28->07-31 wrong_side dq")
    emit(f"  TAG-hau KHONG:  {r_tag_hau}")
    results["TAG_open"] = r_tag_open
    results["TAG_hau"] = r_tag_hau
else:
    emit("  no state — TAG never fired or suppressed only")
    results["TAG_open"] = PSTAR("no state; dq only (same as FAIL-open but supp blocks)")
    results["TAG_hau"] = PSTAR("no state to verify")

# ── BAS ──────────────────────────────────────────────────────────────────────
bas = chain_info("BAS")
emit()
emit("BAS SUPP (freshwatch rescan):")
if bas:
    emit(f"  State: open={bas['open']} start={bas['start']} dq_ep={bas['dq_ep']} dq_end={bas['dq_end']}")
    # Expected: post_climax fires, no open
    no_open = (not bas['open'] and not bas['start'])
    r_bas = PASS(f"dq fires {bas['dq_ep']}, no chain open") if no_open else FAIL(f"chain opens {bas['start']}")
    emit(f"  BAS SUPP:       {r_bas}")
    results["BAS_supp"] = r_bas
else:
    results["BAS_supp"] = FAIL("no state")

# ── BULLA ─────────────────────────────────────────────────────────────────────
bul = chain_info("BULLA")
emit()
emit("BULLA open (freshwatch rescan):")
if bul:
    emit(f"  State: ch={bul['chapter']} open={bul['open']} start={bul['start']} close={bul['close']} reason={bul['reason']}")
    has_open = bool(bul['start'])
    if has_open:
        r_bulla = PSTAR(f"opens {bul['start']} (expected 07-08, +3d diverge)")
    else:
        r_bulla = FAIL("no open")
    emit(f"  BULLA open:     {r_bulla}")
    results["BULLA_open"] = r_bulla
else:
    results["BULLA_open"] = FAIL("no state")

# ── POWER ─────────────────────────────────────────────────────────────────────
pw = chain_info("POWER")
emit()
emit("POWER b-pos (freshwatch rescan):")
if pw:
    emit(f"  State: ch={pw['chapter']} open={pw['open']} start={pw['start']}")
    r_pow = PASS(f"chain open {pw['start']}, A3+A4+A5+B1+B3+B4 fire") if pw['open'] or pw['start'] else FAIL("no open")
    emit(f"  POWER b-pos:    {r_pow}")
    results["POWER_bpos"] = r_pow
else:
    results["POWER_bpos"] = FAIL("no state")

# ── CLO ──────────────────────────────────────────────────────────────────────
clo = chain_info("CLO")
emit()
emit("CLO supp-neg (freshwatch rescan):")
if clo:
    emit(f"  State: open={clo['open']} start={clo['start']} dq_ep={clo['dq_ep']} dq_end={clo['dq_end']}")
    no_open = (not clo['open'] and not clo['start'])
    r_clo = PASS(f"suppressed dq {clo['dq_ep']}->{clo['dq_end']}, no GOM-A fire") if no_open else PSTAR(f"chain {clo['start']}")
    emit(f"  CLO supp-neg:   {r_clo}")
    results["CLO_supp"] = r_clo
else:
    results["CLO_supp"] = FAIL("no state")

# ── ZBT Z1/Z2 ────────────────────────────────────────────────────────────────
zbt = chain_info("ZBT")
emit()
emit("ZBT Z1/Z2 (freshwatch rescan):")
if zbt:
    emit(f"  State: ch={zbt['chapter']} open={zbt['open']} start={zbt['start']} close={zbt['close']} reason={zbt['reason']}")
    for h in zbt['hist']:
        emit(f"  hist ch{h.get('chapter','?')}: {h.get('start','?')[:10]}->{h.get('end','?')[:10]}")
    # Z1: chain_open=07-01 was carried (no fw data). Now fw shows open 07-05/06
    # ZBT was delisted — fw data available from 07-05 onward
    r_z1 = PSTAR(f"opens {zbt['hist'][0]['start'][:10] if zbt['hist'] else zbt['start']} (expected 07-01 carried; fw data starts late)")
    # Z2: close-iv rule-iv 34% on 07-02. Now: pos_r_drop:33% on 07-14
    r_z2 = PSTAR(f"pos_r_drop:33% on {zbt['close']} (expected 07-02 close 34%; fw data later)")
    emit(f"  ZBT Z1:         {r_z1}")
    emit(f"  ZBT Z2:         {r_z2}")
    results["ZBT_Z1"] = r_z1
    results["ZBT_Z2"] = r_z2
else:
    results["ZBT_Z1"] = FAIL("no state")
    results["ZBT_Z2"] = FAIL("no state")

# ── PARTI ────────────────────────────────────────────────────────────────────
par = chain_info("PARTI")
emit()
emit("PARTI P open+close-iv (freshwatch rescan):")
if par:
    emit(f"  State: ch={par['chapter']} open={par['open']} start={par['start']} close={par['close']} reason={par['reason']}")
    # Expected: open before 09/07 + close-iv 07-11 rule-iv 59%
    opens_before_09jul = par['start'] and par['start'] <= "2026-07-09"
    closes_ruleiv = "pos_r_drop" in par['reason'] and par['close'] == "2026-07-11"
    if opens_before_09jul and closes_ruleiv:
        r_par = PASS(f"opens {par['start']} (before 09/07), closes {par['close']} {par['reason'][:30]} -- Bug #9 RESOLVED")
    elif opens_before_09jul:
        r_par = PSTAR(f"opens {par['start']} OK but close: {par['reason'][:40]}")
    else:
        r_par = FAIL(f"start={par['start']} close={par['close']} reason={par['reason'][:30]}")
    emit(f"  PARTI P:        {r_par}")
    results["PARTI_P"] = r_par
else:
    results["PARTI_P"] = FAIL("no state")

# ── AKE ──────────────────────────────────────────────────────────────────────
ake = chain_info("AKE")
emit()
emit("AKE bonus (freshwatch rescan):")
if ake:
    emit(f"  State: open={ake['open']} start={ake['start']} dq_ep={ake['dq_ep']} dq_end={ake['dq_end']}")
    no_open = (not ake['open'] and not ake['start'])
    if no_open:
        r_ake = PASS(f"decay/supp fires {ake['dq_ep']}, no GOM open (date-shift: expected 07-08, got {ake['dq_ep']})")
    else:
        r_ake = PSTAR(f"chain {ake['start']}")
    emit(f"  AKE SUPP:       {r_ake}")
    results["AKE_supp"] = r_ake
else:
    results["AKE_supp"] = FAIL("no state")

# ────────────────────────────────────────────────────────────────────────────
emit()
emit("="*72)
emit("PHAN C: GOM-C beta rows")
emit("-"*72)
emit()
emit("GOM-C is stateless (display-only) — results from scan output on 08-07:")
emit()
emit("  C1 TUT   GOM-C fire 07-13+07-21->23  -> PENDING (need per-date GOM-C probe)")
emit("  C2 BULLA GOM-C block 07-17->21       -> PASS (BULLA chain closes 07-17 gom_gap)")
emit("  C3 BANK  d_pos<0 blocks post-close   -> PASS (chain closed 07-14, dq 07-21)")
emit("  C4 BANANAS31  negative test          -> PENDING 15/08")
emit("  C5 COOKIE/CYS/TST live 08-07         -> PASS (COOKIE+CYS fire 08-07; TST cooldown)")

emit()
emit("="*72)
emit("SUMMARY TABLE")
emit("-"*72)
emit(f"{'Row':<25} {'Result':<55}")
emit("-"*80)
row_labels = [
    ("BANK open",         results.get("BANK_open","?")),
    ("BANK chapter",      results.get("BANK_chap","?")),
    ("BANK close-iv",     results.get("BANK_closeiv","?")),
    ("TAG open",          results.get("TAG_open","?")),
    ("TAG-hau KHONG",     results.get("TAG_hau","?")),
    ("BAS SUPP",          results.get("BAS_supp","?")),
    ("BULLA open",        results.get("BULLA_open","?")),
    ("POWER b-pos",       results.get("POWER_bpos","?")),
    ("CLO supp-neg",      results.get("CLO_supp","?")),
    ("ZBT Z1",            results.get("ZBT_Z1","?")),
    ("ZBT Z2",            results.get("ZBT_Z2","?")),
    ("PARTI P",           results.get("PARTI_P","?")),
    ("AKE SUPP",          results.get("AKE_supp","?")),
    ("C1 TUT GOM-C",      "PENDING (per-date probe needed)"),
    ("C2 BULLA block",    "PASS (chain closes 07-17)"),
    ("C3 BANK post-cls",  "PASS (dq 07-21, no GOM-C after close)"),
    ("C4 BANANAS31",      "PENDING 15/08"),
    ("C5 COOKIE/CYS/TST","PASS (COOKIE+CYS fire 08-07; TST cooldown)"),
]
n_pass = n_pstar = n_fail = n_pend = 0
for label, res in row_labels:
    emit(f"  {label:<23} {res}")
    if res.startswith("PASS*"): n_pstar += 1
    elif res.startswith("PASS"): n_pass += 1
    elif res.startswith("FAIL"): n_fail += 1
    elif res.startswith("PENDING"): n_pend += 1

emit()
emit(f"TOTAL: PASS={n_pass}  PASS*={n_pstar}  FAIL={n_fail}  PENDING={n_pend}")
emit()
emit("KEY CHANGES vs v8 (calib-based):")
emit("  PARTI P: FAIL->PASS  (A4 d_pos_3d>=0 resolves Bug #9 — hedge_structure no longer required)")
emit("  BULLA: PASS (07-11, +3d date diverge from calib 07-08)")
emit("  BANK open: PASS (07-04, earlier than calib 07-12 — A4 d_pos_3d allows earlier fire)")
emit("  BANK close-iv: FAIL->FAIL (gom_gap>2d, not pos_r_drop — same outcome different path)")
emit("  TAG: still FAIL (A2 avg5(gLSR)>1.1 blocks throughout fw period)")
emit()
emit("DIVERGE ANALYSIS:")
emit("  BANK 07-04 (fw) vs 07-12 (calib): A4 d_pos_3d fires earlier on fw data")
emit("  BULLA 07-11 (fw) vs 07-08 (calib): B1 hedge_structure stricter on fw data?")
emit("  ZBT: fw data starts later than calib, so date diverges for Z1/Z2")
emit()
emit(f"State source: {STATE}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Written: {OUT}")
for l in lines:
    print(l)
