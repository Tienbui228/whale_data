"""AL2 · pin · u1 event CHỈ khi class=L1.

Verify:
  · SOPH 09-08 (D_cross) → target=09-13 (D_cross+5) → class SOPH = L2_OR_L3 · KHÔNG có u1 row
  · BULLA 08-25 (D_cross) → target=08-30 (D_cross+5) → class BULLA = L1 · CÓ u1 row (đúng 1)
"""
import sys, os
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

from events_build import build_events

# ── p_al2-a · SOPH ──
# SOPH D_cross detected in earlier check = 2026-09-08 (per AI1 fires 09-09, close to fire day).
# Actually SOPH fires 09-09 (fire=cross day D_cross). D_cross+5 = 09-14.
# But b_state_tracker uses episode-based cross. Let me check actual.
# Fires from AK preview: SOPH kêu 09-09 → D_cross likely 09-08 or 09-09.
# Test with target = 09-14 (D_cross+5 if D_cross=09-09) and 09-13 (if D_cross=09-08).

for target in ["2026-09-13", "2026-09-14"]:
    rows, _ = build_events(target)
    u1_soph = [r for r in rows if r["type"] == "u1" and r["tok"] == "SOPH"]
    class_soph = [r for r in rows if r["type"] == "class" and r["tok"] == "SOPH"]
    print(f"  target={target} · SOPH u1_rows={len(u1_soph)} · SOPH class_rows={len(class_soph)}")
    for r in class_soph:
        print(f"    class SOPH: d_cross={r['d_cross']} tier={r['tier']}")

# ── p_al2-b · BULLA ──
# BULLA fires 09-14. Test target=09-19 (D_cross+5 if D_cross=09-14).
# BULLA is proven-13. Check L1 pass at D_cross → should have u1.
print()
for target in ["2026-09-19", "2026-09-20"]:
    rows, _ = build_events(target)
    u1_bulla = [r for r in rows if r["type"] == "u1" and r["tok"] == "BULLA"]
    class_bulla = [r for r in rows if r["type"] == "class" and r["tok"] == "BULLA"]
    print(f"  target={target} · BULLA u1_rows={len(u1_bulla)} · BULLA class_rows={len(class_bulla)}")
    for r in u1_bulla:
        print(f"    u1 BULLA: d_cross={r['d_cross']} v1={r['v1']:.3f} v2={r['v2']:.3f} verdict={r['verdict']}")

# ── p_al2-c · TỔNG: mọi u1 phải có class=L1 cùng d_cross ──
print()
print(f"═══ p_al2-c · verify mọi u1 event có class=L1 tương ứng (bất kỳ target) ═══")
from datetime import datetime, timedelta
d_start = datetime(2026, 9, 10).date()
d_end = datetime(2026, 9, 20).date()

# Build global set: (tok, d_cross) → tier
class_tiers = {}
u1_seen = []
for k in range((d_end - d_start).days + 1):
    tgt = (d_start + timedelta(days=k)).isoformat()
    rows, _ = build_events(tgt)
    for r in rows:
        if r["type"] == "class":
            class_tiers[(r["tok"], r["d_cross"])] = r["tier"]
        elif r["type"] == "u1":
            u1_seen.append((r["tok"], r["d_cross"]))

# Verify each u1 has class=L1 for same (tok, d_cross)
violations = []
for tok, dc in u1_seen:
    tier = class_tiers.get((tok, dc))
    if tier != "L1":
        violations.append(f"{tok}@{dc}: class={tier} (missing L1) but u1 emitted")

print(f"  Total u1 events: {len(u1_seen)}")
print(f"  Total class events: {len(class_tiers)}")
print(f"  Violations (u1 without class=L1): {len(violations)}")
for v in violations[:10]:
    print(f"    {v}")

p_al2 = len(violations) == 0
print(f"\n═══ p_al2 · TỔNG {'PASS' if p_al2 else 'FAIL'} ═══")
sys.exit(0 if p_al2 else 1)
