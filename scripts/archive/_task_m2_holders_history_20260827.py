"""(M2) HOLDERS-HISTORY CHECK · quyết D3 · local snapshots

Per-token: first_date · last_date · n_days của exchange_holders (non-null)
TUT + BTW: coverage trọn window 06-26..08-22 · per-day gap list
Count tokens đủ ≥30d · api_failed days (họ SOPH 08-23/24)
Verdict 1 dòng: H4-replay khả thi TUT/BTW hay không.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
from gom_h_daily import _load_universe

SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
WINDOW_START = _date(2026, 6, 26)
WINDOW_END = _date(2026, 8, 22)

symbols = _load_universe()
tokens = [s[:-4] if s.endswith("USDT") else s for s in symbols]

# Scan all snapshots for exchange_holders
HOLDERS = {}      # {tok: {ingest_date: holders_count}}
API_FAILED = {}   # {tok: [ingest_dates where exchange_api_failed=True]}
snap_dates = []
for p in sorted(SNAPS.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    ingest = p.stem
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    snap_dates.append(ingest)
    for r in d.get("rows", []):
        if not r: continue
        sym_u = (r.get("symbol") or "").upper()
        if not sym_u: continue
        h = r.get("exchange_holders")
        if h is not None:
            try: HOLDERS.setdefault(sym_u, {})[ingest] = int(h)
            except: pass
        # API-failed track
        if r.get("api_failed") is True or r.get("exchange_api_failed") is True:
            API_FAILED.setdefault(sym_u, []).append(ingest)

print("═" * 100)
print("[M2 HOLDERS-HISTORY CHECK · quyết D3 · local snapshots]")
print("═" * 100)
print(f"snapshot files scanned: {len(snap_dates)} · date range: {min(snap_dates)}..{max(snap_dates)}")
print(f"tokens với exchange_holders history: {len(HOLDERS)} / {len(tokens)}")
print()

# Per-token coverage stats
print("[Per-token exchange_holders coverage]")
coverage = []
for tok in tokens:
    if tok not in HOLDERS:
        coverage.append((tok, None, None, 0))
        continue
    hist = HOLDERS[tok]
    dates_sorted = sorted(hist.keys())
    first = dates_sorted[0]
    last = dates_sorted[-1]
    # Count days in window
    n_days_in_window = sum(1 for d in dates_sorted
                            if WINDOW_START <= _date.fromisoformat(d) <= WINDOW_END + _td(days=1))
    coverage.append((tok, first, last, n_days_in_window))

# Print summary
n_ge30 = sum(1 for c in coverage if c[3] >= 30)
n_ge14 = sum(1 for c in coverage if c[3] >= 14)
n_zero = sum(1 for c in coverage if c[3] == 0)
n_total = len(coverage)
print(f"  ≥30d in window: {n_ge30}/{n_total} · ≥14d: {n_ge14}/{n_total} · 0d: {n_zero}/{n_total}")
print()

# Focus TUT + BTW
print("[TUT coverage trọn window 06-26..08-22]")
for tok in ["TUT", "BTW"]:
    print(f"\n  {tok}:")
    if tok not in HOLDERS:
        print(f"    NO EXCHANGE_HOLDERS DATA")
        continue
    hist = HOLDERS[tok]
    dates_sorted = sorted(hist.keys())
    # ingest_date = bal_date + 1, so bal_date = ingest - 1
    # window is bal_date 06-26..08-22 → ingest 06-27..08-23
    win_ingest_start = WINDOW_START + _td(days=1)
    win_ingest_end = WINDOW_END + _td(days=1)
    all_ingests = [(win_ingest_start + _td(days=i)).isoformat()
                   for i in range((win_ingest_end - win_ingest_start).days + 1)]
    present = [d for d in all_ingests if d in hist]
    missing = [d for d in all_ingests if d not in hist]
    api_fail_in_window = [d for d in API_FAILED.get(tok, [])
                          if win_ingest_start.isoformat() <= d <= win_ingest_end.isoformat()]
    print(f"    ingest date range wanted: {win_ingest_start}..{win_ingest_end} ({len(all_ingests)} days)")
    print(f"    holders present: {len(present)}/{len(all_ingests)} · missing: {len(missing)} · api_failed: {len(api_fail_in_window)}")
    if missing:
        print(f"    missing ingest dates: {', '.join(missing[:20])}")
        if len(missing) > 20: print(f"      ... +{len(missing)-20} more")
    if api_fail_in_window:
        print(f"    api_failed dates: {', '.join(api_fail_in_window[:10])}")
    # Show holders values (first + last + Δ)
    if present:
        first_val = hist[present[0]]
        last_val = hist[present[-1]]
        print(f"    holders series first={first_val}@{present[0]} · last={last_val}@{present[-1]} · Δ={last_val-first_val:+d}")

# SOPH api_failed check (họ example 08-23/24)
print(f"\n[SOPH api_failed sample (họ example)]")
soph_af = API_FAILED.get("SOPH", [])
print(f"  SOPH api_failed ingest dates: {soph_af}")

# Full universe: count valid ≥30d
tokens_ge30 = [c[0] for c in coverage if c[3] >= 30]
tokens_ge14 = [c[0] for c in coverage if c[3] >= 14]
print(f"\n[Full universe]")
print(f"  Tokens ≥30d holders history in window: {len(tokens_ge30)}/{len(tokens)}")
print(f"  Tokens ≥14d: {len(tokens_ge14)}/{len(tokens)}")

# Verdict
print(f"\n[VERDICT H4-replay TUT/BTW feasibility]")
for tok in ["TUT", "BTW"]:
    if tok not in HOLDERS:
        print(f"  {tok}: KHÔNG khả thi (no holders data)")
        continue
    hist = HOLDERS[tok]
    win_ingest_start = WINDOW_START + _td(days=1)
    win_ingest_end = WINDOW_END + _td(days=1)
    all_ingests = [(win_ingest_start + _td(days=i)).isoformat()
                   for i in range((win_ingest_end - win_ingest_start).days + 1)]
    n_present = sum(1 for d in all_ingests if d in hist)
    n_missing = len(all_ingests) - n_present
    coverage_pct = n_present / len(all_ingests) * 100
    verdict = "KHẢ THI" if coverage_pct >= 90 else ("BÌNH THƯỜNG (có gaps)" if coverage_pct >= 70 else "KHÓ (nhiều gaps)")
    print(f"  {tok}: {n_present}/{len(all_ingests)} = {coverage_pct:.1f}% coverage → {verdict}")
