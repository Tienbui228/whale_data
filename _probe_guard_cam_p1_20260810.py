#!/usr/bin/env python3
"""ÁN GUARD-CÂM P1 · 2026-08-10 — Findings report.

Phạm vi: (0) R5 verify + negative test + ACX 60/60;
         (1a) BROCCOLIF3B root cause; (1b) guard hiện tại; (1c) TST persist.

data-source: collect_daily_metrics.py + freshwatch_daily_2026-0*.csv (VPS)
machine: VPS canonical + local scripts
date-range: 2026-06-10 → 2026-08-10
code-commit: (this session, pending commit)
"""
from __future__ import annotations
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent


def sep(title=""):
    print()
    print("=" * 70)
    if title:
        print(title)
        print("=" * 70)


# ══════════════════════════════════════════════════════════════════════════════
# (0) R5 VERIFY — count=0/thiếu → RAISE thật?
# ══════════════════════════════════════════════════════════════════════════════
sep("(0) R5 VERIFY — collect_daily_metrics count=0 behavior")

print("""
Câu hỏi: khi endpoint trả 0 rows, hệ có RAISE + exit≠0 không?

Negative test evidence — nguyên văn code (collect_daily_metrics.py):

  [Line 298-299] _collect_symbol_daily():
    if not data:
        return symbol, 0, None          ← FAIL-OPEN: 0 rows, NO error

  [Line 306-307] _collect_symbol_daily():
    if df.empty:
        return symbol, 0, None          ← FAIL-OPEN: parse OK, 0 rows, NO error

  [Line 88-91] _write_daily_partition():
    async def _write_daily_partition(...):
        if df.empty:
            return                      ← FAIL-OPEN: silent skip write

  [Line 412-428] run_collect_daily_metrics():
    total_rows = 0
    for res in results:
        sym_r, rows_r, err_r = res
        total_rows += rows_r
        if err_r:
            errors.append(...)          ← only logs if err_r is not None
                                        ← rows_r=0, err_r=None → silent
    # [NO check: if total_rows == 0: alert/raise]
    return 0                            ← ALWAYS returns 0, no raise

Kết luận (0): R5 FAIL-OPEN confirmed.
  - count=0/thiếu → returns (sym, 0, None) → không error, không ping
  - Caller (main loop) không check total_rows == 0
  - exit code = 0 (success) ngay cả khi 0 rows collected
  - Vi phạm L-44: missing-dependency → cấm no-op êm

Negative test result:
  Thao tác: block endpoint (metrics_override=['nonexistent_metric'])
  Kỳ vọng: exit=1 + ping
  Thực tế: exit=0, no ping, no log warning
  → NEGATIVE TEST FAIL (system không raise khi cần — đây là bug, không phải test failure)
""")

# ── ACX 60/60 status ──────────────────────────────────────────────────────────
sep("(0) ACX 60/60 status")
print("""
ACX oi_hist_1d sau patch (--days-back 29, 2026-08-10 01:27 UTC):
  - oi_hist_1d:       27 rows (2026-07-12 → 2026-08-10) — API cap 29d
  - top_pos_1d:       27 rows
  - top_acct_1d:      27 rows
  - retail_global_1d: 27 rows
  - taker_ratio_1d:   28 rows (including today's partial)
  errors = 0

ACX freshwatch daily CSV:
  - 2026-08-07: 526 symbols, ACX ✓
  - 2026-08-08: 522 symbols, ACX MISSING (cùng với HFTUSDT, VANRYUSDT, VICUSDT)
  - 2026-08-09: 522 symbols, ACX MISSING
  Nguyên nhân: 4 symbols bị loại khỏi freshwatch export sau 08-07
  (likely: delisted từ FAPI futures — không thể patch từ phía này)

Kết luận ACX: oi_hist_1d = patched (07-12→08-10). Freshwatch 08-08/09 gap
= systemic (4 symbols), không phải 1-off → cần check freshwatch export
script hoặc FAPI status cho 4 symbols này. Án riêng nếu operator xác nhận.
""")


# ══════════════════════════════════════════════════════════════════════════════
# (1a) ROOT CAUSE BROCCOLIF3B — px_avg/ret None, vol/taker CÓ
# ══════════════════════════════════════════════════════════════════════════════
sep("(1a) BROCCOLIF3B #4 root cause — column key mismatch")

print("""
Pattern: vol/taker CÓ nhưng px_avg/ret = None trong BR3-4 analytics.

COLLECT phase (_probe_br3_2_collect_20260810.py, line 76-77):
  rows.append({
      "date": dt,
      "open": o,      ← key = "open"
      "high": h,      ← key = "high"
      "low":  l,      ← key = "low"
      "close": c,     ← key = "close"
      "vol_quote_usd": vol_q,   ← key = "vol_quote_usd"
      "taker_pct":    taker_pct ← key = "taker_pct"
  })
  CSV columns: ["date","open","high","low","close","vol_quote_usd","taker_pct"]

ANALYTICS/DERIVE-PX phase (_probe_br3_345_analytics_20260810.py, line 372-379):
  pr = perp_by_d.get(dt, {})
  o  = safe_float(pr.get("o"))     ← expects "o"    → NONE (key="open")
  h  = safe_float(pr.get("h"))     ← expects "h"    → NONE (key="high")
  l  = safe_float(pr.get("l"))     ← expects "l"    → NONE (key="low")
  c  = safe_float(pr.get("c"))     ← expects "c"    → NONE (key="close")
  px_avg = (h+l+c)/3 if (h and l and c) else None  ← → NONE (always)
  vol_p  = safe_float(pr.get("vol_quote_usd"))      ← "vol_quote_usd" MATCH ✓
  taker  = safe_float(pr.get("taker_pct"))          ← "taker_pct" MATCH ✓
  ret_1d = safe_float(pr.get("ret_1d"))             ← "ret_1d" NOT IN CSV → NONE

Key values tại điểm lệch (example row 2026-08-07):
  Collect-side write:  {"high": 0.006886, "close": 0.006886, "vol_quote_usd": 1020719, ...}
  Analytics-side read: pr.get("h") = None  (column "h" không tồn tại)

ROOT CAUSE: column name mismatch (schema-level, không phải dtype/tz):
  Write side: "open", "high", "low", "close"
  Read side:  "o",    "h",    "l",   "c"
  derive-px chạy TRONG analytics loop, SAU khi load CSV vào dict.
  Derive-px không sai thứ tự (không phải "chạy trước merge") — sai vì key lệch.

FIX: đồng nhất tên cột. Một trong hai:
  a) Collect viết "o","h","l","c" (ngắn, match analytics)
  b) Analytics đọc "open","high","low","close" (dài, match collect)
  Chọn (b) vì "open","high","low","close" = convention chuẩn hơn.
""")


# ══════════════════════════════════════════════════════════════════════════════
# (1b) GUARD HIỆN TẠI — check sai tầng ở đâu
# ══════════════════════════════════════════════════════════════════════════════
sep("(1b) Guard hiện tại — paste nguyên văn + kết luận tầng")

print("""
build_case.py A-0b guard (lines 832-853) — nguyên văn:

  # ── A-0b: LSR + spot coverage guard ─────────────────────────────────
  lsr_null = sum(1 for i,d in enumerate(all_dates)
                 if i >= last30_start and pos_r_all[i] is None)
  lsr_null_pct = lsr_null / len(last30_dates) * 100 if last30_dates else 100
  if lsr_null_pct > 50:
      log(f"!!!! LSR COVERAGE FAIL: pos_r null {lsr_null_pct:.1f}% !!!!")
      log(f"!!!! ABORT: Check A-1 LSR persist — do not ship !!!!")
      raise ValueError(f"A-0b guard: LSR pos_r null {lsr_null_pct:.1f}% > 50%")

build_case.py L-32 guard (lines 824-830) — nguyên văn:

  wb2 = openpyxl.load_workbook(XLSX, data_only=True)
  ws2 = wb2["DAILY"]
  cnt = sum(1 for ri in range(3, ws2.max_row+100)
            if ws2.cell(ri,1).value not in (None,""))
  assert cnt == len(daily_data), f"ROW COUNT MISMATCH: {len(daily_data)} vs {cnt}"

Kết luận:
  - A-0b check: LSR pos_r null % (schema-level) — tầng đúng cho LSR
  - L-32 check: row count total — tầng đúng cho completeness
  - THIẾU: không check px_avg null %, vol null %, taker null % trong 30d
  - Tầng bị bỏ qua: "pre-merge frame" = sau khi perp_by_d merge vào daily_data,
    trước khi ghi XLSX. Nếu perp klines có gap, px_avg=None ngay cả khi
    LSR OK và row count OK. Guard A-0b không detect được.

FF-1c nợ từ 08/08 (câu trả lời):
  CASE_FF.xlsx: 313 rows all px_avg=None — lý do: PERP klines FFUSDT
  không được collect vào klines store trên VPS (chỉ có freshwatch CSV,
  không có 1h parquet). build_case.py gọi _build_klines_agg() → empty
  → px_avg = None. A-0b pass vì LSR OK. L-32 pass vì count OK.
  Guard V2 sẽ catch: px_avg 0/30 = 0% < 50% → FAIL → block ship.
""")


# ══════════════════════════════════════════════════════════════════════════════
# (1c) TST PERSIST — silent failure code branch
# ══════════════════════════════════════════════════════════════════════════════
sep("(1c) TST persist — except-pass hay ghi-rỗng-không-kiểm?")

print("""
Loại: "ghi-rỗng-không-lỗi" (write-empty-without-raise).
Không phải except: pass. Là silent return None với rows=0.

Code branch (collect_daily_metrics.py):

  async def _collect_symbol_daily(...) -> tuple[str, int, Optional[str]]:
      ...
      data = await _paginate_daily(client, mc, symbol, start_ms, end_ms)
      if not data:
          return symbol, 0, None     ← #1 SILENT: no data, err=None
      df = mc["parser"](data, symbol, fetched_at_ms)
      if df.empty:
          return symbol, 0, None     ← #2 SILENT: parse OK, empty, err=None

  # Main loop:
      sym_r, rows_r, err_r = res
      total_rows += rows_r
      if err_r:
          errors.append(...)
          log.warning(...)
      # ← khi rows_r=0 AND err_r=None: không log warning, không append error

R4 đã chỉ: TST MISSING = universe-timing (TST delisted trước window start).
Phần CÂM (code line): line 298-299 AND 306-307 collect_daily_metrics.py.
Cụ thể với TST: Binance API trả [] cho TSTUSDT (delisted) → hit branch #1
→ return (TSTUSDT, 0, None) → main loop: rows_r=0, err_r=None → silent.
Exit code = 0. Không ping. Log: chỉ có "daily_symbol_error" khi err_r≠None.

Fix (Guard V2 sẽ giải quyết ở cấp CASE pack, không ở cấp collect):
  Cấp collect: nếu total_rows == 0 cho một metric → exit 1 + alert.
  Cấp pack: validate_written_pack() reload + check columns ≥50% non-null.
""")


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
sep("SUMMARY")
print("""
(0) R5 FAIL-OPEN: CONFIRMED. collect_daily_metrics exits 0 on count=0.
    ACX oi_hist_1d: patched 27 rows (07-12→08-10). Freshwatch 08-08/09
    gap: systemic 4 symbols, cần investigation riêng.

(1a) BROCCOLIF3B: column key mismatch (collect writes "high", analytics
     reads "h") → px_avg=None, ret_1d=None. vol/taker CÓ vì key khớp.
     Fix: đồng nhất sang "open","high","low","close".

(1b) Guard hiện tại: schema-level (LSR null %) + row count. Không check
     px_avg null % trong 30d. FF-1c debt: FFUSDT có 313 px_avg=None do
     PERP klines không collect → guard A-0b không detect.

(1c) TST persist: line 298-299 collect_daily_metrics.py — "if not data:
     return symbol, 0, None" — silent 0 rows, no error, no ping.

Guard V2 next: validate_written_pack() — see scripts/case_guard.py.
""")
