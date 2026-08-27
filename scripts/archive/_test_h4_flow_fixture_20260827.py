"""[H4 FLOW FIXTURE L-58 · SELF-CHECK per PROBE-SUBMIT RULE án lệ #2 · KÝ 27/08]

Test lib/h4_flow.py: trigger check · snapshot IO · lane render · sentinel · cooldown.

IMPORT prod (không tự dựng compose):
  · lib.h4_flow (module under test)
  · gom_h_daily._load_cfg (yaml h4 block)

SELF-CHECK cases:
  (1) trigger fires: token có ≥2 vế T0.1 pass ∧ chưa snap 14d → trigger=True
  (2) trigger skip insufficient-t01: t01_n_pass=1 → False, reason "insufficient-t01"
  (3) trigger skip snap-fresh: token có snap trong <14d → False, reason "snap-fresh"
  (4) render DOM-HIGH: dom=0.83 · thr=0.80 → "H4 DOM-HIGH 83% (snap dd/mm)"
  (5) render N/A-NO-SNAPSHOT: no snap record → "H4 N/A-NO-SNAPSHOT"
  (6) DOM-RISE: 2 snaps liên tiếp delta ≥+3pp → True

FAIL = fixture blocks integration (per PROBE-SUBMIT RULE · CLAUDE.md án lệ #2).
"""
from __future__ import annotations
import sys, io, tempfile, json
from pathlib import Path

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

# IMPORT prod
from lib import h4_flow
from gom_h_daily import _load_cfg

cfg_all = _load_cfg()
cfg_h4 = cfg_all.get("goi_nhe", {}).get("h4", {})

# Use temp files for isolation
_TMP = Path(tempfile.mkdtemp(prefix="h4_fixture_"))
h4_flow.TRIGGER_PATH = _TMP / "trigger.json"
h4_flow.SNAPSHOTS_PATH = _TMP / "snapshots.jsonl"

print("═" * 100)
print("[H4 FLOW FIXTURE · SELF-CHECK L-58 · PROBE-SUBMIT RULE án lệ #2]")
print(f"  temp dir: {_TMP}")
print(f"  yaml goi_nhe.h4: {cfg_h4}")
print("═" * 100)

results = []

# ─── (1) trigger fires ───
h4_flow.SNAPSHOTS_PATH.write_text("", encoding="utf-8")  # empty snapshots
trig, reason = h4_flow.check_trigger("TUT", t01_n_pass=2, target_date="2026-08-27",
                                      t01_min=cfg_h4.get("t01_min", 2),
                                      resnap_days=cfg_h4.get("resnap_days", 14))
sc1 = (trig is True)
results.append(("SELF-CHECK-COMPOSE-1", f"TUT trigger t01=2 no-snap → trigger={trig} reason={reason}",
                sc1, "trigger=True kỳ vọng"))

# ─── (2) insufficient-t01 ───
trig, reason = h4_flow.check_trigger("TUT", t01_n_pass=1, target_date="2026-08-27",
                                      t01_min=2, resnap_days=14)
sc2 = (trig is False and "insufficient-t01" in reason)
results.append(("SELF-CHECK-COMPOSE-2", f"TUT t01=1 → trigger={trig} reason={reason}",
                sc2, "trigger=False kỳ vọng reason='insufficient-t01'"))

# ─── (3) snap-fresh ───
h4_flow.append_snapshot("TUT", "2026-08-20T00:00:00Z", top100_dom_raw=0.83, n_holders_fetched=100)
trig, reason = h4_flow.check_trigger("TUT", t01_n_pass=2, target_date="2026-08-27",
                                      t01_min=2, resnap_days=14)
sc3 = (trig is False and "snap-fresh" in reason)
results.append(("SELF-CHECK-COMPOSE-3", f"TUT t01=2 snap 7d ago → trigger={trig} reason={reason}",
                sc3, "trigger=False kỳ vọng reason='snap-fresh-7d'"))

# ─── (4) render DOM-HIGH ───
# TUT already has snap dom=0.83 from step (3) — reuse
lane_str = h4_flow.render_h4_lane("TUT", "2026-08-27", cfg_h4)
sc4 = ("DOM-HIGH" in lane_str and "83%" in lane_str)
results.append(("SELF-CHECK-COMPOSE-4", f"render TUT dom=0.83 → '{lane_str}'",
                sc4, "kỳ vọng 'H4 DOM-HIGH 83% (snap 20/08)'"))

# ─── (5) render N/A-NO-SNAPSHOT ───
lane_str_none = h4_flow.render_h4_lane("NONEXIST", "2026-08-27", cfg_h4)
sc5 = (lane_str_none == "H4 N/A-NO-SNAPSHOT")
results.append(("SELF-CHECK-COMPOSE-5", f"render NONEXIST no-snap → '{lane_str_none}'",
                sc5, "kỳ vọng 'H4 N/A-NO-SNAPSHOT'"))

# ─── (6) DOM-RISE ───
# Add 2nd snap for BTW to test delta
h4_flow.append_snapshot("BTW", "2026-08-15T00:00:00Z", top100_dom_raw=0.90, n_holders_fetched=100)
h4_flow.append_snapshot("BTW", "2026-08-27T00:00:00Z", top100_dom_raw=0.96, n_holders_fetched=100)
rise, delta = h4_flow.compute_dom_rise("BTW", "2026-08-27", dom_rise_pp=cfg_h4.get("dom_rise_pp", 3))
sc6 = (rise is True and abs(delta - 6.0) < 0.01)
results.append(("SELF-CHECK-COMPOSE-6", f"BTW dom 0.90→0.96 → rise={rise} delta={delta:.2f}pp",
                sc6, "kỳ vọng rise=True delta=6.0pp (≥+3pp)"))

# Print results
print()
all_pass = True
for name, detail, pass_flag, expect in results:
    status = "PASS ✓" if pass_flag else "FAIL ✗"
    if not pass_flag: all_pass = False
    print(f"  {name}: {detail}")
    print(f"    → {status} ({expect})")

print()
print(f"[VERDICT] ALL PASS: {all_pass}")
if not all_pass:
    print(f"[FAIL] H4 flow fixture BROKEN — bảng KHÔNG được nộp (PROBE-SUBMIT RULE án lệ #2).")
    sys.exit(1)
print(f"[OK] H4 flow fixture certified · lib/h4_flow.py ready for integration.")

# Cleanup temp
import shutil
shutil.rmtree(_TMP, ignore_errors=True)
