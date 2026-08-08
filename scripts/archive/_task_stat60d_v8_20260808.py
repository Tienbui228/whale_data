"""BUOC 3: Statistics tables 60d from gom_state_v8.json.
3a. Closed chapters (sort: rule-iv first)
3b. Open chains
3c. Suppressed (dq episode active, no chain open)
3d. Cross-check with human verdicts (CASE files where known)
Output: docs/reports/gom_stat60d_v8_20260808.txt
"""
import json, sys, math
from pathlib import Path
from datetime import datetime, timezone

STATE  = Path("data/gom_state_v8.json")
CASES  = Path("docs/case_files")
OUT    = Path("docs/reports/gom_stat60d_v8_20260808.txt")

state  = json.loads(STATE.read_text(encoding="utf-8"))
meta   = state.get("_meta", {})

lines = []
def e(s=""): lines.append(s)

e("=== GOM STAT 60d v8 — BUOC 3 ===")
e(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
e(f"State: gom_state_v8.json  target={meta.get('target_date','?')}  60d window")
e(f"Universe: {meta.get('universe','?')}  Code: {meta.get('commit','?')}")
e("="*72)

# ── Categorise tokens ─────────────────────────────────────────────────────────
open_chains   = []   # chain_open=True
closed_chains = []   # chain_open=False and (start_date or chapter_hist)
suppressed    = []   # chain_open=False, no start, dq_ep present

for tok, s in state.items():
    if tok.startswith("_") or not isinstance(s, dict):
        continue
    chain_open  = s.get("chain_open", False)
    start       = s.get("start_date","") or ""
    close       = s.get("close_date","") or ""
    reason      = s.get("close_reason","") or ""
    chapter     = s.get("chapter", 1)
    hist        = s.get("chapter_hist", [])
    dq_ep       = s.get("dq_episode_start","") or ""
    dq_end      = s.get("dq_cooldown_end","") or ""
    peak_pos_r  = s.get("peak_pos_r", float("nan"))
    q1          = s.get("Q1_cum_usd", 0) or 0

    if chain_open:
        open_chains.append({
            "tok": tok, "start": start[:10], "chapter": chapter,
            "q1": q1, "peak": peak_pos_r,
            "dq_ep": dq_ep[:10], "reason": reason
        })
    elif start or hist:
        # Has history — closed chain
        is_ruleiv = "pos_r_drop" in reason
        all_q1 = q1
        for h in hist:
            all_q1 += h.get("Q1_cum", 0) or 0
        closed_chains.append({
            "tok": tok, "start": start[:10], "close": close[:10],
            "reason": reason[:60], "chapter": chapter,
            "is_ruleiv": is_ruleiv, "q1": all_q1, "peak": peak_pos_r,
            "hist": hist, "dq_ep": dq_ep[:10], "dq_end": dq_end[:10]
        })
    elif dq_ep:
        suppressed.append({
            "tok": tok, "dq_ep": dq_ep[:10], "dq_end": dq_end[:10],
        })

# sort closed: rule-iv first, then by close date
closed_chains.sort(key=lambda r: (0 if r["is_ruleiv"] else 1, r["close"]))
open_chains.sort(key=lambda r: r["start"])
suppressed.sort(key=lambda r: r["dq_ep"])

# ── 3a: CLOSED CHAPTERS ───────────────────────────────────────────────────────
e()
e("3a. CHUONG DA DONG 60d — sort: rule-iv truoc, then close date")
e("-"*72)
e(f"{'TOK':<14} {'ch':>3} {'open':>12} {'close':>12} {'reason':<55} {'Q1':>10}")
e("-"*100)
for r in closed_chains:
    q_str = f"${r['q1']:,.0f}" if r['q1'] else "    —"
    e(f"{r['tok']:<14} {r['chapter']:>3} {r['start']:>12} {r['close']:>12} {r['reason']:<55} {q_str:>10}")
    for h in r['hist']:
        e(f"  {'':14} hist ch{h.get('chapter','?')}: {h.get('start','?')[:10]}->{h.get('end','?')[:10]}  Q1=${h.get('Q1_cum',0):,.0f}")

e()
e(f"Subtotal closed chains: {len(closed_chains)}")
rule_iv_count = sum(1 for r in closed_chains if r["is_ruleiv"])
e(f"  rule-iv (pos_r_drop): {rule_iv_count}")
e(f"  gap/supp close:       {len(closed_chains)-rule_iv_count}")

# ── 3b: OPEN CHAINS ───────────────────────────────────────────────────────────
e()
e("3b. CHUOI DANG MO — as of 2026-08-07")
e("-"*72)
e(f"{'TOK':<14} {'ch':>3} {'start':>12} {'Q1':>12} {'peak_pos_r':>12}")
e("-"*60)
for r in open_chains:
    q_str = f"${r['q1']:,.0f}" if r['q1'] else "    —"
    pk = f"{r['peak']:.2f}" if not math.isnan(float(r['peak'])) else "NaN"
    e(f"{r['tok']:<14} {r['chapter']:>3} {r['start']:>12} {q_str:>12} {pk:>12}")

e()
e(f"Subtotal open: {len(open_chains)}")

# ── 3c: SUPPRESSED ────────────────────────────────────────────────────────────
e()
e("3c. SUPPRESSED — dq episode active, no GOM chain opened")
e("-"*72)
e(f"{'TOK':<14} {'dq_ep':>12} {'dq_end':>12}")
e("-"*42)
for r in suppressed:
    e(f"{r['tok']:<14} {r['dq_ep']:>12} {r['dq_end']:>12}")

e()
e(f"Subtotal suppressed-only: {len(suppressed)}")

# ── 3d: CROSS-CHECK ───────────────────────────────────────────────────────────
e()
e("3d. DOI CHIEU — so sanh vs ho so CASE")
e("-"*72)
# Known verdicts from CASE files and session notes
human_verdicts = {
    "BANK":   ("closed",  "chain 06-29 (v7 calib); fw 07-04; close 07-14 gom_gap vs calib close-iv 07-21"),
    "TAG":    ("supp",    "no GOM in fw period — A2 gLSR blocks; dq 07-08->07-21"),
    "BAS":    ("supp",    "post_climax 07-02, no open"),
    "BTW":    ("closed",  "fw opens 07-03, closes 07-08 gom_gap (not in gate spec v8b)"),
    "AKE":    ("supp",    "decay fires 07-24 (calib 07-08), no open"),
    "BULLA":  ("closed",  "opens 07-11 (calib 07-08), closes 07-17 gom_gap"),
    "PARTI":  ("closed",  "PASS — opens 07-07, closes 07-11 pos_r_drop:59% (Bug #9 RESOLVED)"),
    "ZBT":    ("closed",  "ch2 closes 07-14 pos_r_drop:33%"),
    "POWER":  ("open",    "OPEN 08-02, b-positive structure"),
    "CLO":    ("supp",    "dq 07-27->08-09, no open"),
    "TUT":    ("gomc",    "GOM-C fires 08-07; no GOM-A/B chain"),
    "BANANAS31": ("closed","opens 08-01, closes 08-06 gom_gap>2d"),
    "COOKIE": ("gomc",    "GOM-C fires 08-07"),
    "CYS":    ("gomc",    "GOM-C fires 08-07"),
    "TST":    ("gomc",    "GOM-C suppressed cooldown (first 08-04, clear 08-18)"),
}

e(f"{'TOK':<14} {'scan_status':<14} {'note'}")
e("-"*100)
for tok, (status, note) in human_verdicts.items():
    s = state.get(tok, {})
    scan_open  = s.get("chain_open", False) if s else False
    scan_start = (s.get("start_date","") or "")[:10] if s else ""
    scan_close = (s.get("close_date","") or "")[:10] if s else ""
    scan_dq    = (s.get("dq_episode_start","") or "")[:10] if s else ""

    if scan_open:
        scan_s = f"OPEN {scan_start}"
    elif scan_start:
        scan_s = f"closed {scan_close}"
    elif scan_dq:
        scan_s = f"supp {scan_dq}"
    else:
        scan_s = "no state"

    match = "OK" if (
        (status == "open"   and scan_open) or
        (status == "closed" and scan_start and not scan_open) or
        (status == "supp"   and scan_dq and not scan_start) or
        (status == "gomc"   and not scan_open)
    ) else "??"
    e(f"{tok:<14} {scan_s:<14} [{match}] {note}")

e()
e("="*72)
e("TOTALS:")
e(f"  Open chains:      {len(open_chains)}")
e(f"  Closed chains:    {len(closed_chains)}  (rule-iv: {rule_iv_count}  gom_gap/supp: {len(closed_chains)-rule_iv_count})")
e(f"  Suppressed-only:  {len(suppressed)}")
e(f"  Total w/ state:   {len(open_chains)+len(closed_chains)+len(suppressed)}")
e(f"  Total scanned:    {sum(1 for k in state if not k.startswith('_'))}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Written: {OUT}")
for l in lines:
    print(l)
