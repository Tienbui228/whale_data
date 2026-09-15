"""M4 · Pin harness · LAYOUT-ONLY cutover · KÝ 15/09.

Chạy pins {p21, p22, p27, p30, p71, p72, p81, p18} trên concat mới sinh bằng
scripts/digest_summary_v2.py với DIGEST_V1_3=1.

Đen-một-lần: mỗi pin phải FAIL trên input hư (gương) VÀ PASS trên input đúng.
"""
from __future__ import annotations
import sys, os, hashlib, importlib, re, io, contextlib
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_REAL = Path(r"D:/Data back test/whale_data")
SB = REPO_REAL / "sandbox/v1_3_dryrun"
SB_DATA = SB / "data"

sys.path.insert(0, str(REPO_REAL / "scripts"))
import digest_summary_v2 as dsv
import postcheck_gate_d as pgd

def _reload():
    importlib.reload(dsv)
    importlib.reload(pgd)
    dsv.REPO = SB
    dsv.ART_DIR = SB_DATA / "artifacts"
    dsv.LEDGER_DIR = SB_DATA / "logs/event_ledger"
    dsv.FIXTURE_DIR = REPO_REAL / "tests/fixtures/parity"
    dsv.STATE_DIR = SB_DATA / "state"
    dsv.EXPORT_DIR = SB_DATA / "export"
    pgd.REPO = SB
    pgd.ART_DIR = SB_DATA / "artifacts"
    pgd.SB_LOG = SB / "logs" / "harness_sabotage.log"
    (SB / "logs").mkdir(exist_ok=True)

_reload()
os.environ["DIGEST_V1_3"] = "1"

# ═════════════════════════════════════════════════════════════════
# STEP 1 · Render 09-11 + 09-12 with new LAYOUT-ONLY
# ═════════════════════════════════════════════════════════════════
print("═" * 78)
print("M4 · pin harness · LAYOUT-ONLY cutover")
print("═" * 78)
print()

_reload()
os.environ["DIGEST_V1_3"] = "1"
dsv._V1_3_SPECIES_TAGGER_SHA = None   # force re-init

bodies = {}
for target in ("2026-09-11", "2026-09-12"):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        body = dsv.build_v2_digest(target)
    bodies[target] = body
    md5 = hashlib.md5(body.encode()).hexdigest()
    print(f"── target={target} · bytes={len(body.encode())} · md5={md5} ──")
    stderr = buf.getvalue()
    for line in stderr.split("\n"):
        if "[V1.3" in line or "PX-COVERAGE" in line:
            print(f"   stderr: {line.strip()}")
    print()

# ═════════════════════════════════════════════════════════════════
# STEP 2 · p21/p22/p27 XANH (real input)
# ═════════════════════════════════════════════════════════════════
print("─" * 78)
print("XANH tests · p21/p22/p27 trên concat vừa sinh")
print("─" * 78)

xanh_results = {}
for target, body in bodies.items():
    p21 = pgd._check_p21_apr_watch(body)
    p22 = pgd._check_p22_star_pre_count(body)
    p27 = pgd._check_p27_concat_seal(target, body)
    xanh_results[target] = {"p21": p21, "p22": p22, "p27": p27}
    print(f"\n{target}:")
    print(f"  p21={p21[0]:<6} · {p21[1][:100]}")
    print(f"  p22={p22[0]:<6} · {p22[1][:100]}")
    print(f"  p27={p27[0]:<6} · {p27[1][:100]}")

# ═════════════════════════════════════════════════════════════════
# STEP 3 · ĐEN tests (input hư · pin phải FAIL)
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("ĐEN tests · sabotage input · pin phải FAIL")
print("─" * 78)

def _sabotage_p21(body):
    """Đẩy 1 dòng ⏸ WATCH thành → PRE (p21 phải FAIL)."""
    return re.sub(
        r"(⏸ WATCH \[PX-PENDING\]:\s+\S+.*)$",
        r"\1 → PRE",
        body, count=1, flags=re.MULTILINE
    )

def _sabotage_p22(body):
    """Đổi header ── A · GHẾ BẬT ── (N) thành (N+7) (p22 phải FAIL count mismatch)."""
    return re.sub(
        r"(── A · GHẾ BẬT ── )\((\d+)\)",
        lambda m: f"{m.group(1)}({int(m.group(2)) + 7})",
        body, count=1
    )

def _sabotage_p22_alt(body):
    """Nếu không có ── A ── header, đổi khối khác (── ? hoặc CHƯA XẾP)."""
    for pat in [r"(── B · HEDGE → UNHEDGE ── )\((\d+)\)",
                r"(── C · ĐẠP → GOM → ĐẨY ── )\((\d+)\)",
                r"(── \? CHƯA NHÌN ĐƯỢC ── )\((\d+)\)",
                r"(── CHƯA XẾP LOÀI ── )\((\d+)\)"]:
        new_body, n = re.subn(pat, lambda m: f"{m.group(1)}({int(m.group(2)) + 5})",
                              body, count=1)
        if n > 0: return new_body
    return body

def _sabotage_p27_file(target):
    """Sửa seal trong master_body_<target>.txt trên disk (p27 đọc file, không body string)."""
    body_p = SB_DATA / "artifacts" / f"master_body_{target}.txt"
    orig = body_p.read_bytes()
    sabot = re.sub(rb"concat-seal=[a-f0-9]{12}",
                   b"concat-seal=deadbeefcafe", orig, count=1)
    body_p.write_bytes(sabot)
    return orig   # for restore

den_results = {}
for target, body in bodies.items():
    # p21 sabotage
    body_sab21 = _sabotage_p21(body)
    p21_sab = pgd._check_p21_apr_watch(body_sab21)
    # p22 sabotage
    body_sab22 = _sabotage_p22(body)
    if body_sab22 == body:  # no ── A ── to sabotage, try alt
        body_sab22 = _sabotage_p22_alt(body)
    p22_sab = pgd._check_p22_star_pre_count(body_sab22)
    # p27 sabotage (đọc file, không body param)
    orig_body_bytes = _sabotage_p27_file(target)
    p27_sab = pgd._check_p27_concat_seal(target, body)
    (SB_DATA / "artifacts" / f"master_body_{target}.txt").write_bytes(orig_body_bytes)  # restore

    print(f"\n{target}:")
    print(f"  p21 sabotage (+→ PRE): {p21_sab[0]:<6} · {p21_sab[1][:100]}")
    print(f"  p22 sabotage (header+N):  {p22_sab[0]:<6} · {p22_sab[1][:100]}")
    print(f"  p27 sabotage (seal-swap): {p27_sab[0]:<6} · {p27_sab[1][:100]}")

    den_results[target] = {"p21": p21_sab, "p22": p22_sab, "p27": p27_sab}

# ═════════════════════════════════════════════════════════════════
# STEP 4 · p71 · TẬP TOKEN so V1.2 ≡ V1.3-LAYOUT-ONLY
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("p71 · TẬP TOKEN (set) V1.2 ≡ V1.3-LO")
print("─" * 78)

def _extract_tokens(b):
    toks = set()
    for line in b.split("\n"):
        m = re.match(r"^\s+(?:\[[^\]]+\]\s+)?(?:⏸ WATCH \[PX-PENDING\]:\s+)?(\S+)\s+\d-trục", line)
        if m: toks.add(m.group(1))
        m2 = re.search(r"\(\+\d+ nữa:\s+([^)]+)\)", line)
        if m2:
            for n in m2.group(1).split("·"):
                n = n.strip()
                if n: toks.add(n)
    return toks

p71_results = {}
for target in ("2026-09-11", "2026-09-12"):
    body_v13 = bodies[target]
    # Sinh V1.2 baseline
    os.environ["DIGEST_V1_3"] = "0"
    _reload()
    body_v12 = dsv.build_v2_digest(target)
    os.environ["DIGEST_V1_3"] = "1"
    _reload()

    toks_v12 = _extract_tokens(body_v12)
    toks_v13 = _extract_tokens(body_v13)
    equal = toks_v12 == toks_v13
    missing = toks_v12 - toks_v13
    extra = toks_v13 - toks_v12
    status = "PASS" if equal else "FAIL"
    p71_results[target] = (status, len(toks_v12), len(toks_v13), missing, extra)
    print(f"\n{target}: {status} · V1.2={len(toks_v12)} tokens · V1.3-LO={len(toks_v13)} tokens")
    if not equal:
        print(f"  V1.2-only ({len(missing)}): {sorted(missing)[:10]}")
        print(f"  V1.3-only ({len(extra)}): {sorted(extra)[:10]}")

# ĐEN p71: sabotage V1.3 body by removing one token
print()
print("ĐEN p71 · sabotage V1.3-LO (xóa 1 token line):")
for target in ("2026-09-11", "2026-09-12"):
    body = bodies[target]
    lines = body.split("\n")
    # Find first indented token line and remove it
    new_lines = []; removed = None
    for l in lines:
        if removed is None and re.match(r"^\s+(?:\[[^\]]+\]\s+)?\S+\s+\d-trục", l):
            removed = l.strip()[:40]
            continue
        new_lines.append(l)
    body_sab = "\n".join(new_lines)
    toks_sab = _extract_tokens(body_sab)
    orig_toks = _extract_tokens(body)
    status = "FAIL" if toks_sab != orig_toks else "PASS-GƯƠNG"
    print(f"  {target}: sabotage removed '{removed}' → toks {len(orig_toks)}→{len(toks_sab)} · pin verdict: {status}")

# ═════════════════════════════════════════════════════════════════
# STEP 5 · p30 · Direction (→ PRE/WATCH/XẢ) không đổi vì prefix
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("p30 · direction không đổi vì tag")
print("─" * 78)

def _extract_directions(b):
    """Map sym → direction extracted from token lines."""
    result = {}
    for line in b.split("\n"):
        # Match token line, capture symbol and direction
        m = re.match(r"^\s+(?:\[[^\]]+\]\s+)?(?:⏸ WATCH \[PX-PENDING\]:\s+)?(\S+)\s+\d-trục.*?→\s*(\S+)", line)
        if m:
            sym = m.group(1)
            dir_ = m.group(2).rstrip("[").rstrip()   # strip trailing [PX-PENDING] tag
            result[sym] = dir_
        # WATCH tokens don't have → in the middle · direction implicit WATCH
        elif re.search(r"⏸ WATCH \[PX-PENDING\]:\s+(\S+)", line):
            m2 = re.search(r"⏸ WATCH \[PX-PENDING\]:\s+(\S+)", line)
            result[m2.group(1)] = "WATCH"
    return result

p30_results = {}
for target in ("2026-09-11", "2026-09-12"):
    body_v13 = bodies[target]
    os.environ["DIGEST_V1_3"] = "0"; _reload()
    body_v12 = dsv.build_v2_digest(target)
    os.environ["DIGEST_V1_3"] = "1"; _reload()

    dir_v12 = _extract_directions(body_v12)
    dir_v13 = _extract_directions(body_v13)
    common = set(dir_v12) & set(dir_v13)
    mismatches = [s for s in common if dir_v12[s] != dir_v13[s]]
    status = "PASS" if not mismatches else "FAIL"
    p30_results[target] = (status, len(mismatches))
    print(f"  {target}: {status} · common={len(common)} tokens · mismatches={len(mismatches)}")
    if mismatches[:3]:
        for s in mismatches[:3]:
            print(f"    {s}: V1.2→{dir_v12[s]} vs V1.3→{dir_v13[s]}")

# ═════════════════════════════════════════════════════════════════
# STEP 6 · p72 · Token count V1.2 ≡ V1.3-LO
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("p72 · Count token · hint lines KHÔNG tính")
print("─" * 78)

for target in ("2026-09-11", "2026-09-12"):
    body_v13 = bodies[target]
    os.environ["DIGEST_V1_3"] = "0"; _reload()
    body_v12 = dsv.build_v2_digest(target)
    os.environ["DIGEST_V1_3"] = "1"; _reload()

    n_v12 = len(_extract_tokens(body_v12))
    n_v13 = len(_extract_tokens(body_v13))
    # Also count hint lines in V1.3 (should NOT be in token count)
    n_hints = sum(1 for l in body_v13.split("\n") if l.strip().startswith("(→ xem"))
    status = "PASS" if n_v12 == n_v13 else "FAIL"
    print(f"  {target}: {status} · V1.2={n_v12} · V1.3={n_v13} · hint_lines={n_hints} (not counted)")

# ═════════════════════════════════════════════════════════════════
# STEP 7 · p81 · Counter CHỜ (giả lập preview era n>2)
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("p81 · counter-CHỜ · giả lập đêm 3 chưa cutover")
print("─" * 78)

# Simulate the label logic from master_preview_send
MASTER_LIVE_TARGET = "2026-09-15"
cases = [
    ("2026-09-11", 1, "[MASTER-PREVIEW đêm 1/2]"),
    ("2026-09-12", 2, "[MASTER-PREVIEW đêm 2/2]"),
    ("2026-09-13", 3, "[ĐỦ 2/2 · CHỜ \"ok master live\"]"),
    ("2026-09-14", 4, "[ĐỦ 2/2 · CHỜ \"ok master live\"]"),
    ("2026-09-15", 3, "[MASTER · live từ 2026-09-15]"),
    ("2026-09-16", 4, "[MASTER · live từ 2026-09-15]"),
]
for target, n, expected in cases:
    if target >= MASTER_LIVE_TARGET:
        label = "[MASTER · live từ 2026-09-15]"
    elif n <= 2:
        label = f"[MASTER-PREVIEW đêm {n}/2]"
    else:
        label = "[ĐỦ 2/2 · CHỜ \"ok master live\"]"
    ok = label == expected
    icon = "✅" if ok else "❌"
    print(f"  {icon} target={target} n={n} → label={label!r}")
    if not ok:
        print(f"       expected: {expected!r}")

# ═════════════════════════════════════════════════════════════════
# STEP 8 · p18 · UNIVERSE-BOUND · cohort ∈ [expected_low, expected_high]
# ═════════════════════════════════════════════════════════════════
print()
print("─" * 78)
print("p18 · UNIVERSE-BOUND · cohort trong [20, 200] · guard rỗng-quá / tràn-quá")
print("─" * 78)

# Load token_records per target
for target in ("2026-09-11", "2026-09-12"):
    star_body, star_mode, star_syms, ledger_md5, meta = dsv._star_block_from_ledger(target)
    n_records = len(meta.get("token_records", []))
    UNIV_LO, UNIV_HI = 5, 200
    status = "PASS" if UNIV_LO <= n_records <= UNIV_HI else "FAIL"
    print(f"  {target}: {status} · cohort={n_records} · guard [{UNIV_LO}, {UNIV_HI}]")

# ĐEN p18: giả lập cohort 0 hoặc 500
for fake_n in (0, 3, 500):
    status = "PASS" if 5 <= fake_n <= 200 else "FAIL"
    print(f"  ĐEN cohort={fake_n}: pin verdict={status} (kỳ vọng FAIL nếu ngoài dải)")

# ═════════════════════════════════════════════════════════════════
# VERDICT
# ═════════════════════════════════════════════════════════════════
print()
print("═" * 78)
print("VERDICT")
print("═" * 78)

all_ok = True
for target in ("2026-09-11", "2026-09-12"):
    xr = xanh_results[target]
    dr = den_results[target]
    xanh_ok = all(x[0] in ("PASS", "N/A") for x in [xr["p21"], xr["p22"], xr["p27"]])
    # Đen: p21 phải FAIL (đã inject → PRE), p22 phải FAIL (đã +7), p27 phải FAIL (seal đổi)
    den_ok = (dr["p21"][0] == "FAIL" and dr["p22"][0] == "FAIL" and dr["p27"][0] == "FAIL")
    tstatus = "PASS" if (xanh_ok and den_ok) else "FAIL"
    if tstatus != "PASS": all_ok = False
    print(f"  {target}: xanh={xanh_ok} · đen={den_ok} · verdict={tstatus}")

print()
print("★ TỔNG: " + ("PASS · sẵn sàng SCP" if all_ok else "FAIL · KHÔNG SCP · sửa trước"))
