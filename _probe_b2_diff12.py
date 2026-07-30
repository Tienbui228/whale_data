#!/usr/bin/env python3
"""Diff 12 calib files: loose (Check onchain) vs repo (docs/case study/).
Output: 12-line table identical/different, field+date delta for different files."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import difflib

REPO_DIR  = Path(r"D:\Data back test\binance-bot-signals\docs\case study")
LOOSE_DIR = Path(r"D:\Check onchain fresh wallets\u50_data")

# Map token names to canonical filenames in repo
TOKENS = ["BANK", "AKE", "TAG", "BAS", "POWER", "BASED", "CLO", "BTW", "TUT", "BULLA", "ESPORTS", "IDOL"]

def find_in_repo(token: str) -> Path | None:
    for p in REPO_DIR.glob("*_result.txt"):
        if p.stem.upper().startswith(token.upper()) or p.stem.lower() == token.lower() + "_result":
            return p
    # fuzzy
    token_low = token.lower()
    for p in REPO_DIR.glob("*_result.txt"):
        if token_low in p.stem.lower():
            return p
    return None

def find_in_loose(token: str) -> Path | None:
    token_low = token.lower()
    # Exclude ARCHIVED/RETIRED files
    for p in LOOSE_DIR.glob("*_result*.txt"):
        if "ARCHIVED" in p.stem or "RETIRED" in p.stem or "LOOSE" in p.stem:
            continue
        if token_low in p.stem.lower():
            return p
    return None

print("=== Loose dir contents (u50_data) ===")
all_loose = sorted(LOOSE_DIR.glob("*_result*.txt"))
for f in all_loose:
    print(f"  {f.name}")

print(f"\n=== Repo dir contents (docs/case study) ===")
all_repo = sorted(REPO_DIR.glob("*_result.txt"))
for f in all_repo:
    print(f"  {f.name}")

print(f"\n=== 12-token diff table ===")
print(f"{'Token':<10} {'Repo file':<25} {'Loose file':<45} {'Result'}")
print("-" * 115)

results = {}
for token in TOKENS:
    rp = find_in_repo(token)
    lp = find_in_loose(token)

    if rp is None:
        results[token] = ("REPO_MISSING", rp, lp)
        print(f"{token:<10} {'(NOT FOUND)':<25} {lp.name if lp else '(not found)':<45} REPO_MISSING")
        continue
    if lp is None:
        results[token] = ("LOOSE_MISSING", rp, lp)
        print(f"{token:<10} {rp.name:<25} {'(NOT FOUND)':<45} LOOSE_MISSING")
        continue

    # Read both (handle encoding)
    def read_file(p: Path) -> str:
        raw = p.read_bytes()
        if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
            return raw.decode("utf-16", errors="replace")
        return raw.decode("utf-8", errors="replace")

    rc = read_file(rp)
    lc = read_file(lp)

    if rc == lc:
        results[token] = ("IDENTICAL", rp, lp)
        print(f"{token:<10} {rp.name:<25} {lp.name:<45} IDENTICAL")
    else:
        results[token] = ("DIFFERENT", rp, lp)
        print(f"{token:<10} {rp.name:<25} {lp.name:<45} DIFFERENT")

# Detail: for each DIFFERENT, show which lines differ
print(f"\n=== Detail for DIFFERENT files ===")
for token, (status, rp, lp) in results.items():
    if status != "DIFFERENT":
        continue
    print(f"\n[{token}] {rp.name} vs {lp.name}")

    def read_file(p: Path) -> list[str]:
        raw = p.read_bytes()
        if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
            return raw.decode("utf-16", errors="replace").splitlines()
        return raw.decode("utf-8", errors="replace").splitlines()

    rlines = read_file(rp)
    llines = read_file(lp)

    # Find differing lines — show first 20 hunks
    diff = list(difflib.unified_diff(llines, rlines, lineterm="", n=0))
    # Summarize: count added/removed, show key value differences
    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]
    print(f"  Lines: repo={len(rlines)}, loose={len(llines)}, +{len(added)}/-{len(removed)}")

    # Show first meaningful diff lines (skip whitespace-only)
    shown = 0
    for line in diff[:80]:
        if line.startswith("@@") or (line.startswith(("+", "-")) and not line.startswith(("+++", "---"))):
            stripped = line[1:].strip()
            if stripped:
                print(f"  {line[:100]}")
                shown += 1
                if shown >= 20:
                    print("  ... (truncated)")
                    break
