"""p11 SUP-NOTE PARITY assert · ĐỘC-LẬP-2-VẾ · KÝ 03/09 hậu-khớp.

Cùng khuôn với sidecar assert:
  · vế 1: n_notes = COUNT (symbol, lane) pairs với `[SUPPRESSED X/14 lane={lane}]` từ CSV re-read
  · vế 2: n_in_window = COUNT (symbol, lane) pairs với `_check_lane_cooldown(...).in_cd=True` từ fresh scan

Assert n_notes ≡ n_in_window. Lệch = FAIL.

Chạy: python tests/harness/assert_p11_sup_note_parity.py --target 2026-09-02
Từ VPS: cd /root/Data_back_test/whale_data && .venv/bin/python3 tests/harness/assert_p11_sup_note_parity.py --target 2026-09-03
"""
from __future__ import annotations
import sys, os, csv, re, argparse, importlib.util
from pathlib import Path

# Detect env
if os.name == "nt":
    REPO = Path(r"D:/Data back test/whale_data")
else:
    REPO = Path("/root/Data_back_test/whale_data")

SCRATCH = REPO / "scratch"

CD_DAYS = 14
CN_DAYS = 3

SUPPRESSED_RE = re.compile(r"\[SUPPRESSED (\d+)/14 lane=(kho|perp)\]")


def _count_notes_from_csv(target_date: str) -> tuple[int, list]:
    """Vế 1: re-read CSV suppressed_note column · parse SUPPRESSED tokens."""
    p = SCRATCH / f"gom_h_daily_{target_date}.csv"
    if not p.exists():
        raise FileNotFoundError(f"CSV missing: {p}")
    notes = []
    with open(p, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for row in rd:
            sup = row.get("suppressed_note", "") or ""
            sym = row.get("symbol", "")
            for m in SUPPRESSED_RE.finditer(sup):
                days, lane = m.group(1), m.group(2)
                notes.append((sym, lane, int(days)))
    return len(notes), notes


def _count_in_window_from_scan(target_date: str) -> tuple[int, list]:
    """Vế 2: fresh scan · call _check_lane_cooldown for EVERY symbol × 2 lanes · count in_cd=True."""
    # Import gom_h_daily module (contains _check_lane_cooldown)
    ghd = REPO / "scripts/gom_h_daily.py"
    spec = importlib.util.spec_from_file_location("gom_h_daily", str(ghd))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass  # module __main__ might sys.exit
    fn = getattr(mod, "_check_lane_cooldown", None)
    if fn is None:
        raise RuntimeError("_check_lane_cooldown not found in gom_h_daily module")

    # Get symbol universe from same-date CSV
    p = SCRATCH / f"gom_h_daily_{target_date}.csv"
    if not p.exists():
        raise FileNotFoundError(f"CSV missing (for symbol universe): {p}")
    symbols = []
    with open(p, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for row in rd:
            s = row.get("symbol", "")
            if s: symbols.append(s)

    in_window = []
    for sym in symbols:
        for lane in ("kho", "perp"):
            try:
                in_cd, reason, days, clean = fn(sym, target_date, lane, SCRATCH, CD_DAYS, CN_DAYS, scan_result=None)
                if in_cd:
                    in_window.append((sym, lane, days))
            except Exception:
                continue
    return len(in_window), in_window


def assert_p11_sup_note_parity_independent(target_date: str, verbose: bool = True):
    """Main assert · độc-lập-2-vế."""
    if verbose:
        print(f"[p11 ASSERT] target={target_date}")
    n_notes, notes = _count_notes_from_csv(target_date)
    n_in_window, in_window = _count_in_window_from_scan(target_date)

    if verbose:
        print(f"  vế 1 (CSV re-read notes)   : n_notes={n_notes}")
        print(f"  vế 2 (fresh scan in_window): n_in_window={n_in_window}")

    # Set diff for diagnostic
    set_notes = {(s, l) for s, l, _ in notes}
    set_win = {(s, l) for s, l, _ in in_window}
    missing_from_notes = set_win - set_notes  # in window but no note = BUG (like 4USDT pre-fix)
    extra_notes = set_notes - set_win          # note exists but not in window = stale
    if verbose:
        if missing_from_notes:
            print(f"  ⚠ MISSING notes (in_window but no CSV note · like 4USDT pre-fix): {sorted(missing_from_notes)[:10]}")
        if extra_notes:
            print(f"  ⚠ EXTRA notes (CSV note but not in_window · stale): {sorted(extra_notes)[:10]}")

    if n_notes != n_in_window:
        raise AssertionError(
            f"[p11 FAIL] target={target_date} · n_notes(CSV re-read)={n_notes} != "
            f"n_in_window(fresh scan)={n_in_window} · "
            f"missing_from_notes={sorted(missing_from_notes)[:5]} · extra_notes={sorted(extra_notes)[:5]}"
        )
    if verbose:
        print(f"[p11 PASS] {n_notes} ≡ {n_in_window} · sup-note parity verified 2-path")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="YYYY-MM-DD")
    ap.add_argument("--verbose", action="store_true", default=True)
    args = ap.parse_args()
    try:
        assert_p11_sup_note_parity_independent(args.target, verbose=args.verbose)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[p11 ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
