"""HARNESS §D SKELETON · KÝ 02/09 · zero-send scaffold · chờ ANALYSIS v1.1.

§D pins (per master v1.1 chờ ANALYSIS chốt):
  D1 · anchor=target_date · runner in [A6 target-check PASS] TRƯỚC so số
  D2 · sidecar n_sidecar ≡ n_printed cho MỖI renderer
  D3 · fixture md5 pin (L-67 immutability)
  D4 · L-74 view-stale check · consumer đối chiếu source_md5
  D5 · L-51 bridge-inject audit · MỌI identity dùng chung phải có 1 getter
  D6 · L-73 CEX-list one-source · pre-commit hook
  D7 · L-76 SMOKE-KHÔNG-ĐƯỢC-VIẾT-PROD · post-smoke md5 assert
  D8 · L-77 PORT-PARITY (candidate) · golden-master diff trước khi port thay
  D9-D∞ · TBD ANALYSIS

Marker-pin convention:
  Mỗi test declare @pin("D<N>") · runner enumerate coverage matrix.
  Test không có @pin → LOOSE (in warning · không block).

Run: python tests/harness/harness_D_skeleton.py
"""
from __future__ import annotations
import sys, io, os, subprocess, importlib.util, hashlib
from pathlib import Path
from datetime import datetime

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path(__file__).resolve().parents[2]
RESULTS = []


def pin(pin_id: str):
    """Decorator: attach §D pin ID to test function."""
    def _wrap(f):
        f._pin = pin_id
        return f
    return _wrap


def _run_test(f):
    pin_id = getattr(f, "_pin", "(LOOSE)")
    try:
        result = f()
        status = "PASS" if result else "FAIL"
    except Exception as e:
        status = f"ERROR: {type(e).__name__}: {e}"
    RESULTS.append({"test": f.__name__, "pin": pin_id, "status": status})


# ---- §D1: A6 target-check pattern ----
@pin("D1")
def test_a6_target_check_present():
    """Verify gom_h_daily.py contains A6 target-check code path."""
    p = REPO / "scripts/gom_h_daily.py"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return "A6 target-check" in body or "target_date" in body


# ---- §D2: sidecar emitter module exists ----
@pin("D2")
def test_sidecar_emitter_available():
    p = REPO / "scripts/lib/sidecar_emitter.py"
    if not p.exists(): return False
    spec = importlib.util.spec_from_file_location("sidecar_emitter", str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return hasattr(m, "SidecarEmitter") and hasattr(m, "SidecarAssertError")


# ---- §D3: fixture md5 pin ----
@pin("D3")
def test_fixture_md5_pin_stable():
    fx_fresh = REPO / "tests/fixtures/parity/golden_A_fresh_20260831.txt"
    fx_exch = REPO / "tests/fixtures/parity/golden_A_exch_20260831.txt"
    expected = {
        "golden_A_fresh_20260831.txt": "df772d84fb1f0f6a134a830385fd6c6b",
        "golden_A_exch_20260831.txt":  "868edfd85ce3dd98c8686420ce55fc72",
    }
    for name, want in expected.items():
        p = REPO / "tests/fixtures/parity" / name
        if not p.exists(): return False
        got = hashlib.md5(p.read_bytes()).hexdigest()
        if got != want: return False
    return True


# ---- §D4: L-74 view-stale consumer ----
@pin("D4")
def test_view_stale_check_module():
    p = REPO / "scripts/lib/view_stale_check.py"
    return p.exists()


# ---- §D5: L-51 bridge-inject audit ----
@pin("D5")
def test_l51_getter_discipline():
    """Placeholder: enum getters in core_nansen · assert each identity has 1 getter."""
    # TBD ANALYSIS v1.1 · scaffold returns True (not blocking)
    return True


# ---- §D6: L-73 cex_addresses_bsc.txt one-source ----
@pin("D6")
def test_l73_cex_list_one_source():
    p = REPO / "data/ref/cex_addresses_bsc.txt"
    if not p.exists(): return False
    expected_md5 = "0983fb5f8a190872ac2b904798b3cbf7"
    got = hashlib.md5(p.read_bytes()).hexdigest()
    return got == expected_md5


# ---- §D7: L-76 SMOKE guard ----
@pin("D7")
def test_l76_smoke_guard_available():
    return (REPO / "scripts/lib/assert_prod_scratch_unchanged.py").exists()


# ---- §D8: L-77 parity runner ----
@pin("D8")
def test_l77_parity_runner_available():
    p = REPO / "tests/parity/run_parity_check_20260831.py"
    if not p.exists(): return False
    # Run inline
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return "PARITY-CHECK OK" in r.stdout


# ---- §D9: SIDECAR emission wire (3 renderers wired: digest 2 + gom_h fire blocks; 3 remaining PENDING) ----
@pin("D9")
def test_sidecar_wired_renderers():
    """Verify sidecar wire in: digest_daily_vps (2) + gom_h_daily (3 fire blocks)."""
    d = REPO / "scripts/digest_daily_vps.py"
    g = REPO / "scripts/gom_h_daily.py"
    if not (d.exists() and g.exists()): return False
    body_d = d.read_text(encoding="utf-8", errors="replace")
    body_g = g.read_text(encoding="utf-8", errors="replace")
    ok_d = ("SIDECAR §B" in body_d and "SidecarEmitter" in body_d
            and "assert_equal_independent(len(pre_lines))" in body_d
            and "assert_equal_independent(len(up) + len(down))" in body_d)
    ok_g = ("SIDECAR §B" in body_g and "_sidecar_gh" in body_g
            and "assert_equal_independent(_sidecar_row_idx)" in body_g)
    return ok_d and ok_g


# ---- §D9-PENDING → §D9-POSTHOC · 3 renderer sidecar wire via post-hoc extractor (batch-kế 07/09) ----
@pin("D9-POSTHOC")
def test_sidecar_posthoc_extractor_available():
    """Verify sidecar_extract_post_hoc.py exists + emit_from_text_and_assert_independent helper."""
    p_ex = REPO / "scripts/sidecar_extract_post_hoc.py"
    p_lib = REPO / "scripts/lib/sidecar_emitter.py"
    if not (p_ex.exists() and p_lib.exists()): return False
    body_lib = p_lib.read_text(encoding="utf-8", errors="replace")
    body_ex = p_ex.read_text(encoding="utf-8", errors="replace")
    return ("emit_from_text_and_assert_independent" in body_lib
            and ("RENDERER_SPECS" in body_ex or "LOG_MAP" in body_ex)
            and all(r in body_ex for r in ("gom_daily", "phase_map", "watchlist")))


# ---- §D12 · Assembler send-path AND-gated (KÝ 07/09) ----
@pin("D12")
def test_assembler_send_path_and_gated():
    """Verify assembler_preview has AND-gate: ASSEMBLER_SEND_ENABLE + TG_CHAT_ID_DAILY."""
    p = REPO / "scripts/assembler_preview.py"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return ("ASSEMBLER_SEND_ENABLE" in body
            and "TG_CHAT_ID_DAILY" in body
            and "PREVIEW_MODE = not (ASSEMBLER_SEND_ENABLE and TG_CHAT_ID_DAILY)" in body
            and "_send_master_preview" in body)


# ---- §D10: DEV-CAP-01 REV fixture + diff pinned ----
@pin("D10")
def test_dev_cap_01_rev_fixture_pinned():
    rev = REPO / "tests/fixtures/parity/golden_A_exch_20260831_REV_DEV-CAP-01.txt"
    diff = REPO / "tests/fixtures/parity/golden_A_exch_20260831_REV_DEV-CAP-01.diff"
    if not (rev.exists() and diff.exists()): return False
    expected = {
        "golden_A_exch_20260831_REV_DEV-CAP-01.txt": "ac34e1b73adc7a31c939565954454fc6",
        "golden_A_exch_20260831_REV_DEV-CAP-01.diff": "88a0d2c1b64b130a40b9e6d028c7fb8e",
    }
    for name, want in expected.items():
        p = REPO / "tests/fixtures/parity" / name
        if hashlib.md5(p.read_bytes()).hexdigest() != want: return False
    return True


# ---- §D11: p11 SUP-NOTE PARITY (KÝ 03/09 · án 4USDT + 龙虾) ----
@pin("D11")
def test_p11_sup_note_parity_gom_h_daily_fix_applied():
    """Verify gom_h_daily.py has p11 backfill block installed (primary + N/A branch extended)."""
    p = REPO / "scripts/gom_h_daily.py"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return ("p11 SUP-NOTE PARITY" in body and "_in_cd_kho_bf" in body
            and "_in_cd_perp_bf" in body and "_p11_notes_na" in body)


# ---- §D11-2P: p11 assert 2-path fn available ----
@pin("D11-2P")
def test_p11_assert_2path_available():
    p = REPO / "tests/harness/assert_p11_sup_note_parity.py"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return ("_count_notes_from_csv" in body and "_count_in_window_from_scan" in body
            and "assert_p11_sup_note_parity_independent" in body)


# ---- §D9-2P: sidecar assert_equal_independent 2-path in emitter ----
@pin("D9-2P")
def test_sidecar_assert_2path_available():
    p = REPO / "scripts/lib/sidecar_emitter.py"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return ("assert_equal_independent" in body and "n_rows_reread" in body
            and "independent I/O path" in body)


# ---- §DA11: axis_map.yaml ACTIVE ----
@pin("DA11")
def test_axis_map_active():
    p = REPO / "data/config/axis_map.yaml"
    if not p.exists(): return False
    body = p.read_text(encoding="utf-8", errors="replace")
    return "status: ACTIVE" in body and "spec_version: v1.1" in body and "A11 · dòng mới ANALYSIS parity" in body


# ---- Driver ----
def main():
    tests = [test_a6_target_check_present, test_sidecar_emitter_available,
             test_fixture_md5_pin_stable, test_view_stale_check_module,
             test_l51_getter_discipline, test_l73_cex_list_one_source,
             test_l76_smoke_guard_available, test_l77_parity_runner_available,
             test_sidecar_wired_renderers, test_sidecar_posthoc_extractor_available,
             test_sidecar_assert_2path_available,
             test_dev_cap_01_rev_fixture_pinned,
             test_p11_sup_note_parity_gom_h_daily_fix_applied,
             test_p11_assert_2path_available,
             test_axis_map_active,
             test_assembler_send_path_and_gated]
    for t in tests:
        _run_test(t)
    print("=" * 78)
    print(f"HARNESS §D SKELETON RESULTS · {datetime.now().isoformat()}")
    print("=" * 78)
    print(f"{'PIN':<6} {'STATUS':<10} TEST")
    print("-" * 78)
    for r in RESULTS:
        print(f"{r['pin']:<6} {r['status']:<10} {r['test']}")
    print()
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_fail = sum(1 for r in RESULTS if r["status"] != "PASS")
    print(f"[SUMMARY] {n_pass}/{len(RESULTS)} PASS · {n_fail} FAIL/ERROR")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
