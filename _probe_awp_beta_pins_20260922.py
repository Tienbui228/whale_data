"""AW-β · pins mới: p105 (U7 gate cấm slice), p113 (luật-nền có event vẫn hiện),
β-fix4 csv-md5 (thay ô fund → md5 đổi), + rerun p100..p112 6 đêm.

p105 · U7 gate: body vượt 4096 → send blocked · body có tag ngoài whitelist → blocked
p113 · CROSS 09-20 event L1 + luật nền → SỰ KIỆN có dòng CROSS kèm [hậu-D0]
β-fix4 · registry_md5 tính từ CSV bytes · sửa ô fund → md5 khác trước
"""
from __future__ import annotations
import os, sys, hashlib, csv, tempfile, shutil
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

import hedge_v2 as hv

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

fails = 0

# ── p105 · U7 gate ─────────────────────────────────────────────────────────
print("═══ p105 · U7 gate ═══")
# case 1 · body OK
body_ok = "Hello world"
ok, reason = hv.u7_gate(body_ok)
c1 = ok
print(f"  case1 body OK: {ok} ({reason})")

# case 2 · body length overflow
body_over = "x" * 5000
ok, reason = hv.u7_gate(body_over)
c2 = (not ok) and "LEN" in reason
print(f"  case2 body over 4096: blocked={not ok} reason={reason}")

# case 3 · body has bad HTML tag
body_bad_html = "Test <script>alert(1)</script>"
ok, reason = hv.u7_gate(body_bad_html)
c3 = (not ok) and "HTML" in reason
print(f"  case3 body bad HTML: blocked={not ok} reason={reason}")

# case 4 · body has ok whitelist tag <b>
body_ok_tag = "Test <b>bold</b>"
ok, reason = hv.u7_gate(body_ok_tag)
c4 = ok
print(f"  case4 body <b> tag: {ok} ({reason})")

p105_ok = c1 and c2 and c3 and c4
print(f"  p105: {'PASS' if p105_ok else 'FAIL'}")
if not p105_ok: fails += 1
print()

# ── p113 · token luật-nền có event → SỰ KIỆN có [hậu-D0] · dynamic 6 đêm ─────
print("═══ p113 · luật-nền có event → SỰ KIỆN kèm [hậu-D0] · dynamic ═══")
TARGETS_113 = ["2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18",
               "2026-09-19", "2026-09-20"]
p113_pass_count = 0
p113_total = 0
for tgt in TARGETS_113:
    body, meta = hv.compose_body(tgt, report_only=True)
    events, _, _ = hv.read_events(tgt)
    price_map = hv.load_daily_rows(tgt)
    # Tìm event tokens (bell/class/u1) có luật nền
    luat_event_toks = []
    for e in events or []:
        t = e.get("type")
        if t not in ("bell", "class", "u1"): continue
        tok = e.get("tok")
        if not tok: continue
        for c in (f"{tok}USDT", tok):
            if c in price_map:
                over, kd = hv.luat_nen_2x_min60d(c, tgt, price_map)
                if over:
                    luat_event_toks.append((tok, kd))
                    break
    if not luat_event_toks:
        continue    # no test case tonight
    # Verify SỰ KIỆN block có dòng cho token có [hậu-D0]
    su_kien_lines = []
    in_su_kien = False
    for ln in body.split("\n"):
        if ln.startswith("── SỰ KIỆN"): in_su_kien = True; continue
        if ln.startswith("── ") and in_su_kien: break
        if in_su_kien: su_kien_lines.append(ln)
    for tok, kd in luat_event_toks:
        p113_total += 1
        found = False
        for ln in su_kien_lines:
            if f" {tok} " in ln or ln.endswith(f" {tok}") or ln.endswith(f"{tok}"):
                if "[hậu-D0" in ln:
                    found = True
                break
        mark = "PASS" if found else "FAIL"
        if found: p113_pass_count += 1
        print(f"  {tgt} {tok:10s} kd={kd:2d} → {mark}")

p113_ok = (p113_total > 0) and (p113_pass_count == p113_total)
print(f"  p113: {'PASS' if p113_ok else 'FAIL'} · {p113_pass_count}/{p113_total} cases")
if not p113_ok: fails += 1
print()

# ── β-fix4 · CSV md5 changes when content changes ────────────────────────────
print("═══ β-fix4 · CSV md5 sensitivity ═══")
# Save baseline md5 via re-compose (writes CSV)
_body1, meta1 = hv.compose_body("2026-09-20", report_only=True)
csv_p = hv.ART_DIR / "hedge_registry_2026-09-20.csv"
md5_1 = hashlib.md5(csv_p.read_bytes()).hexdigest()[:12]
print(f"  baseline registry_md5 in meta:     {meta1['registry_md5']}")
print(f"  baseline md5 from CSV bytes:       {md5_1}")
b1_ok = meta1['registry_md5'] == md5_1

# Now mutate CSV manually (change one fund cell), re-read md5
tmp_p = Path(tempfile.mkdtemp()) / "hedge_reg_mut.csv"
shutil.copy2(csv_p, tmp_p)
lines = tmp_p.read_text(encoding="utf-8").splitlines()
if len(lines) > 3:
    # Change fund_state column in row 2
    parts = lines[2].split(",")
    if len(parts) >= 9:
        parts[8] = "MUTATED"
        lines[2] = ",".join(parts)
tmp_p.write_text("\n".join(lines) + "\n", encoding="utf-8")
md5_mut = hashlib.md5(tmp_p.read_bytes()).hexdigest()[:12]
b2_ok = md5_mut != md5_1
print(f"  mutated CSV md5:                    {md5_mut}")
print(f"  md5 changed after mutation:         {b2_ok}")
try: tmp_p.parent.rmdir()
except OSError: pass  # L-66-OK

fix4_ok = b1_ok and b2_ok
print(f"  β-fix4: {'PASS' if fix4_ok else 'FAIL'}")
if not fix4_ok: fails += 1
print()

# ── β-fix2 · GOM-E divergence check on EVAA/POWER/SHELL ─────────────────────
print("═══ β-fix2 · GOM-E divergence EVAA/POWER/SHELL ═══")
# ANALYSIS ref: EVAA 0.531 · POWER 0.579 · SHELL 0.526 (GOM-E cùng đêm)
# Compute cả HEDGE canonical + GOM-E direct để đối chiếu
TARGET_DIV = "2026-09-18"   # đêm ANALYSIS chỉ đích
fw_extra = hv.load_fw_extra(TARGET_DIV)
CHECK = {"EVAAUSDT": 0.531, "POWERUSDT": 0.579, "SHELLUSDT": 0.526}
for sym, expected in CHECK.items():
    canon = hv._compute_registry_fields(sym, TARGET_DIV, fw_extra)
    div = canon.get("div_avg3")
    div_s = f"{div:.3f}" if isinstance(div, float) else "N/A"
    lech = ""
    if isinstance(div, float) and abs(div - expected) > 0.01:
        lech = " · LỆCH"
    print(f"  {sym:16s} HEDGE={div_s} (GOM-E ref={expected:.3f}){lech}")
print()

# ── Rerun main 9 pins (α' pins) ─────────────────────────────────────────────
print("═══ Rerun α' 9 pins (p100..p112) ═══")
import subprocess
r = subprocess.run(["python3", str(_REPO / "_probe_awp_pins_20260922.py")],
                    capture_output=True, encoding="utf-8", errors="replace")
print(r.stdout.split("\n")[-3] if r.stdout else "(no output)")
print()

print(f"═══ TỔNG β pins mới · {3 - fails}/3 PASS ═══")
sys.exit(0 if fails == 0 else 1)
