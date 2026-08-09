"""Append COOKIE session to agent_log.md"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"D:\Data back test\whale_data")
log_path = ROOT / "agent_log.md"

entry = """
---

## SESSION COOKIE — audit-collect COOKIEUSDT (2026-08-09)

### Câu hỏi case
gom_scan đã fire COOKIE — fire hợp lệ theo spec v1.5 không? Có ai gom thật không, gom từ bao giờ, bao nhiêu (§3 ba phương pháp), và đang ở pha nào vòng đời?

### Pipeline thực hiện

| Bước | Script | Kết quả |
|------|--------|---------|
| C-0 Truy alert | `_probe_cookie_c0_20260809.py` | GOM-C chain start=08-03, n=1, Q1=$0, VWAP=$0.00774[vw-vol], ALPHA_33 |
| C-1 LSR collect | `_probe_cookie_c1_20260809.py` | 4 endpoints PASS, 44 dates, lsr_raw CSV 44 rows |
| C-2 Collect | `_probe_cookie_c2_collect_20260809.py` | perp=579r, fund=500rec, OI=30d, spot=576r, BAPI, perpInfo |
| C-2 Build | `_task_cookie_c2_build_20260809.py` | CASE_COOKIE.xlsx 7 sheets 138KB; fix funding CSV (raw→aggregated bug) |
| C-3 §3 | `_probe_cookie_c3_q123_20260809.py` | Q1_chain=$0, Q1_win=$754K, Q2_net=+$238K, Q3=$993K-$2.98M, VWAP khớp +0.04% |
| C-4 Phase | `_probe_cookie_c4_phase_20260809.py` | ATH-97.9%, nền 66d, GOM-C rechấm: C2✓C3✓ d_pos FAIL, hedge_struct=90% |
| C-5 On-chain | `_probe_cookie_c5_onchain_20260809.py` | BAPI live OK, depth snap#1 01:50 UTC bid/ask=$590K/$397K ratio=1.49 |
| C-6 Crossref | `_probe_cookie_c6_crossref_20260809.py` | agent_log 17 mentions, FW consistent, CASE_INDEX pending |
| C-7 Sanity | `_probe_cookie_c7_sanity_20260809.py` | S1-S5 all PASS |
| C-8 Register | `_task_cookie_c8_register_20260809.py` | CASE_INDEX row 17, INDEX.md regen, status=OPEN |

### Số chốt

| Metric | Giá trị |
|--------|---------|
| Fire date | 2026-08-03 (GOM-C, n=1) |
| Q1_chain | $0 (OI declining on fire day) |
| Q1_audit (08-01→08-08) | $754,118 |
| Q2_net | +$237,798 |
| Q2_ceiling | $972,614 |
| Q3 low/high | $993K / $2.98M |
| VWAP bot | $0.00774 [vw-vol] ✓ (khớp manual +0.04%) |
| px 08-08 | $0.01304 (+68.4% vs VWAP) |
| ATH | $0.6287 (listing day 2025-01-07) — px vs ATH: -97.9% |
| ATL | $0.00749 (2026-07-30) |
| OI (08-08) | $1,557,750 |
| oi_cycle_pos (08-08) | 0.289 |
| flag_hedge_struct | 90% (dominant) |
| Depth snap#1 ratio | 1.4858 (bid-heavy full book; ask-heavy ±1%) |
| SNAP#2 gate | ≥05:50 UTC 2026-08-09 |

### GOM-C rechấm 08-03

| Condition | Result |
|-----------|--------|
| C1 stealth_grind | CẦN SPEC — gLSR=3.2391 >> typical bound |
| C2_quiet (f_avg≤2×neutral) | PASS — f_avg=-6.1e-7 |
| C3_lax (taker∈[40%,55%]) | PASS — taker=44.39% |
| d_pos≥0 | FAIL — d_pos=-0.1056 |

### CẦN OPERATOR

| Item | Lý do |
|------|-------|
| Depth snap #2 | ≥05:50 UTC 08-09 (4h sau snap#1) |
| BscScan top holders | API V1 NOTOK |
| Nansen | LOCKED |
| C1 exact spec | gom_scan.py không ở root (check scripts/) |
| Alpha delisting date | Không có delistTime field |
| Unlock schedule | Không có vesting contract |
| Verdict | Operator fills CASE + INDEX |

### Trạng thái

| Item | Status |
|------|--------|
| CASE_COOKIE.xlsx | OPEN — audit-collect complete |
| _collect_cookie_20260809.md | DONE — chờ operator đọc |
| Depth snap #2 | PENDING (≥05:50 UTC) |
| FF snap #2 | PENDING (≥16:07 UTC 08-08 — check if done in prior session) |
| Verdict | PENDING OPERATOR |
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)

print(f"Appended COOKIE session to agent_log.md")
with open(log_path, encoding="utf-8", errors="replace") as f:
    total = sum(1 for _ in f)
print(f"New total lines: {total}")
