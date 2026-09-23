"""roster_daily.py · R2 · ghi roster_<date>.txt cho mỗi target.

Roster = fw_universe ∩ (symbols with data at target).
Match cách U0-BELL/events_build.py scan trong đêm.

Usage:
  python3 scripts/roster_daily.py --target 2026-09-22
  → data/state/roster_2026-09-22.txt (một token/dòng)
  → data/state/roster_2026-09-22.md5

Tính:
  · fw_universe từ data/config/freshwatch_symbols.txt
  · data_at_target từ data/export/freshwatch_daily_<YYYY-MM>.csv (unique symbols có date==target)
  · roster = sorted(fw ∩ data)

KHÔNG chạm code U0-BELL · KHÔNG mutate state · pure readonly + write output.

Ranh giới hold-out: script này CHỈ ghi roster · KHÔNG động vào code U0 hay events_build.
"""
from __future__ import annotations
import argparse, os, sys, csv, hashlib
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

FW_SYM_P  = _REPO / "data/config/freshwatch_symbols.txt"
EXPORT_D  = _REPO / "data/export"
STATE_D   = _REPO / "data/state"


def build_roster(target: str) -> tuple[list[str], dict]:
    """Trả (roster_sorted, provenance_dict).
    provenance: source paths + counts."""
    if not FW_SYM_P.exists():
        raise FileNotFoundError(f"fw_universe missing: {FW_SYM_P}")
    fw_syms = {ln.strip() for ln in FW_SYM_P.read_text(encoding="utf-8").splitlines() if ln.strip()}

    ym = target[:7]
    csv_p = EXPORT_D / f"freshwatch_daily_{ym}.csv"
    if not csv_p.exists():
        raise FileNotFoundError(f"daily csv missing: {csv_p}")

    data_syms = set()
    with csv_p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("date") == target:
                s = r.get("symbol", "").strip()
                if s: data_syms.add(s)

    roster = sorted(fw_syms & data_syms)
    prov = {
        "fw_universe_file": str(FW_SYM_P),
        "fw_universe_n":    len(fw_syms),
        "data_csv":         str(csv_p),
        "data_at_target_n": len(data_syms),
        "roster_n":         len(roster),
        "target":           target,
    }
    return roster, prov


def write_roster(roster: list[str], target: str, out_dir: Path = None) -> tuple[Path, str]:
    """Ghi roster + .md5 sidecar · trả (path, md5_hex[12])."""
    if out_dir is None: out_dir = STATE_D
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"roster_{target}.txt"
    md5_p = out_dir / f"roster_{target}.md5"
    body = "\n".join(roster) + "\n"
    p.write_text(body, encoding="utf-8")
    md5_hex = hashlib.md5(body.encode("utf-8")).hexdigest()
    md5_p.write_text(md5_hex + "\n", encoding="utf-8")
    return p, md5_hex[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    roster, prov = build_roster(args.target)
    out_dir = Path(args.out_dir) if args.out_dir else STATE_D
    p, md5_short = write_roster(roster, args.target, out_dir)

    # Report · NGUỒN column (doctrine #16)
    print(f"═══ roster_daily · target={prov['target']} ═══")
    print(f"NGUỒN fw_universe:   {prov['fw_universe_file']} · n={prov['fw_universe_n']}")
    print(f"NGUỒN data_at_target: {prov['data_csv']} · n_unique_syms={prov['data_at_target_n']}")
    print(f"OUTPUT roster:       {p} · n={prov['roster_n']} · md5={md5_short}")
    print(f"     (roster = fw_universe ∩ data_at_target)")

if __name__ == "__main__":
    main()
