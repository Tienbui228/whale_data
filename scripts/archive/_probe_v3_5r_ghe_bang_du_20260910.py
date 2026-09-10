"""V3.5r item 4 · GHẾ 27/09 · BẢNG ĐỦ TRƯỚC RENDER.

Per-date {08-31·09-04·09-05·09-06·09-07} × per-token {DOS·BEAT·ONE·B} search:
  · as-sent artifact: /data/artifacts/tg_final_{fresh_digest|gom_daily|watchlist|exch_digest}_<d>.txt
  · raw-save sidecar: /data/logs/sidecar/{fresh_digest|exch_digest|gom_daily|watchlist}_<d>.jsonl

Cite ⇒ path + TRÍCH DÒNG · MISS ⇒ path grepped (0 hit).
Search-space bao gồm raw-save từ 01/09 (V3.5o sidecar wire).

Run via SSH · aggregate results locally.
"""
from __future__ import annotations
import sys, os, subprocess, json
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
VPS_HOST = "root@5.223.67.21"
VPS_REPO = "/root/Data_back_test/whale_data"

DATES = ["2026-08-31", "2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07"]
TOKENS = ["DOS", "BEAT", "ONE", "B"]
# For B: 'B' is a symbol prefix — must anchor as $B\s or "$B "
TOKEN_PATTERNS = {
    "DOS": r"\$DOS\b",
    "BEAT": r"\$BEAT\b",
    "ONE": r"\$ONE\b",
    "B": r"\$B\b",
}


def ssh_run(cmd: str, timeout: int = 20) -> tuple[int, str, str]:
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", VPS_HOST, cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def grep_token_in_files(date: str, token: str) -> list[tuple[str, str]]:
    """Return list of (path, matched_line) tuples for token in date's files."""
    pattern = TOKEN_PATTERNS[token]
    # Search 4 file types × 2 locations (artifact + sidecar)
    candidates = [
        f"{VPS_REPO}/data/artifacts/tg_final_fresh_digest_{date}.txt",
        f"{VPS_REPO}/data/artifacts/tg_final_gom_daily_{date}.txt",
        f"{VPS_REPO}/data/artifacts/tg_final_watchlist_{date}.txt",
        f"{VPS_REPO}/data/artifacts/tg_final_exch_digest_{date}.txt",
        f"{VPS_REPO}/data/logs/sidecar/fresh_digest_{date}.jsonl",
        f"{VPS_REPO}/data/logs/sidecar/exch_digest_{date}.jsonl",
        f"{VPS_REPO}/data/logs/sidecar/gom_daily_{date}.jsonl",
        f"{VPS_REPO}/data/logs/sidecar/watchlist_{date}.jsonl",
    ]
    hits = []
    for f in candidates:
        # Use grep -P for word boundary
        cmd = f"[ -f {f} ] && grep -nP '{pattern}' {f} 2>/dev/null | head -3 || true"
        rc, out, err = ssh_run(cmd)
        if not out.strip(): continue
        for line in out.strip().splitlines():
            hits.append((f, line))
    return hits


def check_file_exists(date: str) -> dict:
    """Report which files exist for date (search-space visibility)."""
    files = [
        ("tg_final_fresh_digest", f"{VPS_REPO}/data/artifacts/tg_final_fresh_digest_{date}.txt"),
        ("tg_final_gom_daily", f"{VPS_REPO}/data/artifacts/tg_final_gom_daily_{date}.txt"),
        ("tg_final_watchlist", f"{VPS_REPO}/data/artifacts/tg_final_watchlist_{date}.txt"),
        ("sidecar_fresh_digest", f"{VPS_REPO}/data/logs/sidecar/fresh_digest_{date}.jsonl"),
        ("sidecar_exch_digest", f"{VPS_REPO}/data/logs/sidecar/exch_digest_{date}.jsonl"),
        ("sidecar_gom_daily", f"{VPS_REPO}/data/logs/sidecar/gom_daily_{date}.jsonl"),
    ]
    result = {}
    ls_cmd = "; ".join([f"[ -f {p} ] && echo {n}=1 || echo {n}=0" for n, p in files])
    rc, out, _ = ssh_run(ls_cmd)
    for line in out.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip() == "1"
    return result


def main():
    print("═" * 66)
    print(f"V3.5r item 4 · GHẾ 27/09 · BẢNG ĐỦ · TRƯỚC RENDER · {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print("═" * 66)

    grand_table = {}
    file_map = {}
    for d in DATES:
        print(f"\n─── {d} · file map ───")
        file_map[d] = check_file_exists(d)
        for k, v in file_map[d].items():
            mark = "✓" if v else "·"
            print(f"    {mark} {k}")

        print(f"\n─── {d} · token grep ───")
        grand_table[d] = {}
        for tok in TOKENS:
            hits = grep_token_in_files(d, tok)
            grand_table[d][tok] = hits
            n = len(hits)
            if n == 0:
                print(f"    · {tok}: MISS · 0 hit across {sum(file_map[d].values())} files present")
            else:
                for path, line in hits[:2]:
                    fname = path.split("/")[-1]
                    print(f"    · {tok}: HIT · {fname} · {line[:120]}")

    # Aggregate counters per-token
    print("\n" + "═" * 66)
    print("AGGREGATE COUNTER · per-token · as-sent hits (any file)")
    print("═" * 66)
    counters = {}
    for tok in TOKENS:
        dates_with_hit = [d for d in DATES if grand_table[d][tok]]
        counters[tok] = len(dates_with_hit)
        print(f"  · {tok}: {counters[tok]}× · dates: {dates_with_hit}")

    print("\n" + "─" * 66)
    print("LỆNH-3× GATE (V3.5q · < 3× ⇒ NOMINATION RÚT)")
    print("─" * 66)
    for tok, n in counters.items():
        verdict = "ĐỦ 3×" if n >= 3 else f"RÚT ({n} < 3)"
        print(f"  · {tok}: {n}× ⇒ {verdict}")

    total_hits = sum(counters.values())
    seat_status = "ĐỦ để đề cử" if any(n >= 3 for n in counters.values()) else "TRỐNG"
    print(f"\n[GHẾ 27/09] status: {seat_status} · total-hits-across-tokens={total_hits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
