"""
_task_register_bananas31_20260808.py
Register CASE_BANANAS31 in CASE_INDEX + INDEX.md + write _collect_bananas31_20260807.md.
"""
import sys, io
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from openpyxl.styles import Font

CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
DOCS     = Path(r"D:\Data back test\whale_data\docs")
ROOT     = Path(r"D:\Data back test\whale_data")

def log(s=""): print(s)

NOW = datetime.now(timezone.utc)
log(f"REGISTER BANANAS31  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

# ── 1. CASE_INDEX.xlsx ────────────────────────────────────────────────────────
idx_xlsx = CASE_DIR / "CASE_INDEX.xlsx"
wb = openpyxl.load_workbook(idx_xlsx)
ws = wb.active if "CASE" not in wb.sheetnames else wb["CASE"]
# Find first empty row after header
max_r = ws.max_row
new_row = max_r + 1
for ri in range(2, max_r+2):
    if ws.cell(ri, 1).value in (None, ""):
        new_row = ri; break

# Read headers from row 1 to know column positions
hdrs = {str(ws.cell(1, ci).value).lower().strip(): ci
        for ci in range(1, ws.max_column+2) if ws.cell(1, ci).value}
log(f"  CASE_INDEX headers: {list(hdrs.keys())}")

entry = {
    "symbol":   "BANANAS31USDT",
    "status":   "COLD_START — PENDING",
    "ngay_mo":  "2026-08-07",
    "ngay_dong":"",
    "verdict":  "",
    "archetype":"",
    "note":     "ALPHA_21 fullyDelisted | cold-start 07/08/2026",
}
# Write using header mapping, fallback to sequential
if len(hdrs) > 0:
    for key, val in entry.items():
        # Try to find matching column
        col = None
        for hk, hc in hdrs.items():
            if key.replace("_","") in hk.replace("_","").replace(" ","") or key in hk:
                col = hc; break
        if col:
            ws.cell(new_row, col).value = val
            ws.cell(new_row, col).font  = Font(size=9)
    # Fill remaining fields sequentially if headers don't match
    # At minimum write symbol + status
    if not any(ws.cell(new_row, ci).value for ci in range(1, 5)):
        for ci, val in enumerate(entry.values(), 1):
            ws.cell(new_row, ci).value = val
            ws.cell(new_row, ci).font  = Font(size=9)
else:
    for ci, val in enumerate(entry.values(), 1):
        ws.cell(new_row, ci).value = val
        ws.cell(new_row, ci).font  = Font(size=9)

log(f"  CASE_INDEX: row {new_row} written")
wb.save(idx_xlsx)
log(f"  CASE_INDEX saved")

# ── 2. INDEX.md ───────────────────────────────────────────────────────────────
idx_md = DOCS / "INDEX.md"
if idx_md.exists():
    content = idx_md.read_text(encoding="utf-8")
    # Find CASE_HEI.xlsx line and insert BANANAS31 after it (or at end of Tầng 3)
    insert_after = "CASE_HEI.xlsx"
    new_line = "- [CASE_BANANAS31.xlsx](case_files/CASE_BANANAS31.xlsx) — COLD_START PENDING (Alpha fullyDelisted, dump 91 ngày ret<-5%)"
    if "BANANAS31" in content:
        log(f"  INDEX.md: BANANAS31 already present")
    else:
        if insert_after in content:
            content = content.replace(
                insert_after,
                insert_after + "\n" + new_line.replace("- [", "  - [")
            )
        else:
            content += f"\n{new_line}\n"
        idx_md.write_text(content, encoding="utf-8")
        log(f"  INDEX.md: BANANAS31 added")
else:
    log(f"  INDEX.md: not found at {idx_md}")

# ── 3. _collect_bananas31_20260807.md ─────────────────────────────────────────
collect_md = ROOT / "_collect_bananas31_20260807.md"
report = f"""# Collect Report: CASE_BANANAS31 (BANANAS31USDT)
**Ngày collect:** 2026-08-07
**Model:** claude-sonnet-4-6
**Status:** COLD_START — PENDING
**Câu hỏi mở:** "Hồ sơ đẹp nhưng giá dump liên tục — build-into-weakness hay bẫy (BTW/phân phối/short-side)?"

---

## LAYER COVERAGE

| Layer | Status | Nguồn | Boundary | Ghi chú |
|---|---|---|---|---|
| PERP klines | ✓ FULL | fapi klines 1d | 2025-03-23 → 2026-08-07 | 503 ngày |
| FUNDING | ✓ PARTIAL | fapi fundingRate | 2026-05-16 → 2026-08-07 | 84 ngày (fn=6/ngày) |
| OI hist | ✓ PARTIAL | fapi openInterestHist | 2026-07-09 → 2026-08-07 | 30 ngày |
| LSR fresh | ✓ PARTIAL | fapi 4 endpoints | 2026-07-08 → 2026-08-07 | 31 ngày (30d retention) |
| LSR freshwatch | ✓ EXT | freshwatch CSV 06-07/2026 | 2026-06-01 → 2026-07-31 | 37 ngày BANANAS31USDT |
| LSR total | ✓ | merged | 2026-06-01 → 2026-08-07 | 68 ngày |
| SPOT klines | ✓ FULL | api/v3 klines 1d | 2025-03-23 → 2026-08-07 | 499 ngày |
| ALPHA klines | ✗ ABSTAIN | fullyDelisted | — | ALPHA_21, offline=True, offsell=True |
| ON-CHAIN | ✗ ABSTAIN | Nansen LOCKED | — | Contract 0x3d4f0513...a760 (BSC) |
| BscScan holders | ✗ CẦN OP | API NOTOK 0-credit | — | Cần API key hoặc manual |
| Depth | ✓ PARTIAL | fapi depth | 2026-08-07 13:09 UTC | Snap #1 only — snap #2 cần >=17:09 UTC |

---

## B-1: PERP DAILY

**Symbol:** BANANAS31USDT (perp) | **Listing perp:** 2025-03-22 | **Alpha listing:** 2024-12-20
**Source fn:** boundary=fn (4h=6/ngày) · OI boundary=00:00 UTC ngày D (L-21) · LSR boundary=00:00 UTC ngày D (L-38)

| Metric | Giá trị |
|---|---|
| Klines | 503 ngày (2025-03-23 → 2026-08-07) |
| px_listing_close | 0.005298 |
| px_ATH_close | 0.037270 (2025-07-10) |
| px_ATH_high (intraday) | 0.082783 |
| px_current_close | 0.007143 |
| Drawdown từ ATH close | -80.83% |
| Total red days (full history) | 91+ ngày ret_1d ≤ -5% |
| LSR pos_r (07/08) | 6.7083 |
| LSR acc_r (07/08) | 1.4588 |
| gLSR (07/08) | 1.1997 |
| div_raw (07/08) | 6.7083 / 1.4588 = 4.598 |
| div_avg3 (07/08) | ~4.9-5.x |
| OI hiện tại | ~50,978,074 tokens / ~$5.13M |
| Funding last | 07/08: fn=3 (partial), f_avg=8.38e-6 |
| GOM-A fires | 25 ngày (tập trung Jun-Aug 2026) |
| GOM-B fires | 0 |

**GOM-A fires (25 ngày):**
2026-06-06→08, 06-16→18, 06-20→22, 06-28→30, 07-01→02, 07-07, 07-14, 07-16→17, 07-28→31, 08-01→03
→ Chủ yếu khi avg5(gLSR) ≤ 1.1 (crowd tạm net short) + slope ≤ 1.15 (gLSR chưa bùng)
→ A1 luôn TRUE (div_avg3 >> 1.5) — nhien lieu dồi dào suốt window

---

## B-2: CỜ CHẨN ĐOÁN (diagnostic flags)

**Định nghĩa:**
- `flag_neg_div`: f_avg ≤ -2e-4 AND range3d(px) ≤ ±7% [neg funding flat market]
- `flag_dist_wall_day`: taker ≥ 50% AND ret_1d < 0 [distribution wall]
- `dist_wall_streak`: consecutive dist_wall_day count
- `flag_decay_day`: taker < 45% [seller decay / buyer thoái lui]
- `flag_hedge_struct`: div_avg3 ≤ 0.5 [hedge structure — 0 ngày trong window vì div_avg3 quá cao]
- `flag_knife_crowd`: gLSR(t) > gLSR(t-1) AND ret_1d < -3% [crowd nạp long vào chiều rơi]

| Flag | Count (503 ngày) | Ghi chú |
|---|---|---|
| flag_neg_div | — | ít (f mostly pin hoặc gần 0) |
| flag_dist_wall_day | 57 ngày | 11.3% tổng ngày — cao bất thường |
| flag_decay_day | — | — |
| flag_hedge_struct | 0 ngày | div_avg3 luôn >> 0.5 |
| flag_knife_crowd | 9 ngày | nguy hiểm nhất — crowd nạp vào dump |

**Build-check (OLS 30d):**
- pos_r slope 30d: +0.0363 ↑ RISING — top traders tiếp tục tích lũy long dù giá dump
- sign(Δpos_r) vs sign(ret_1d): same=52.3%, opposite=47.7% — gần 50/50 (pos_r không synchronize với giá)
- **Kết luận số thô:** pos_r tăng trong khi giá xu hướng giảm → NGUYÊN LIỆU BUILD-INTO-WEAKNESS HỘP ĐEN; cần phân biệt với phân phối (ANALYSIS)

---

## B-3: GIẢI PHẪU CHUỖI DUMP

**ATH close:** 0.037270 (2025-07-10) — intraday high 0.082783
**Hiện tại:** 0.007143 = -80.83% từ ATH close

**Dump days (ret_1d ≤ -5%): 91 ngày tổng**

Các dump lớn có flag_knife_crowd=TRUE (crowd long vào dump):
| Date | ret_1d | vol_vs_m | taker% | ghi chú |
|---|---|---|---|---|
| 2026-06-09 | -7.55% | 1.73x | 47.0% | knife_crowd |
| 2026-06-10 | -6.45% | 0.79x | 45.2% | knife_crowd |
| 2026-06-18 | -7.63% | 0.77x | 48.5% | knife_crowd |
| 2026-06-20 | -9.80% | 0.61x | 44.4% | knife_crowd |
| 2026-06-23 | -9.60% | 0.56x | 45.3% | knife_crowd |
| 2026-06-27 | -5.61% | 0.52x | 48.1% | knife_crowd |
| 2026-07-08 | -12.47% | 1.25x | 44.6% | — |
| 2026-07-10 | -8.63% | 1.46x | 49.4% | knife_crowd |

**Vol >= 8x med14 (L-15 bait candidates): 31 ngày**
Clusters: Jun-Jul 2025 (launch pump), Nov 2025 (second pump), Mar 2026 (third pump)
→ Mỗi vol spike cluster thường sau đó là dump kéo dài

**Last 30 days:** Total red=17/30 (57%), dump streak hiện tại = 0 (không liên tục)

---

## B-4: SPOT + ALPHA

**Spot:** BANANAS31USDT spot TRADING, isSpotTradingAllowed=True
**Spot klines:** 499 ngày, l29_flag: cần check ngày cụ thể

**Alpha:** ALPHA_21
- `fullyDelisted=True` · `offsell=True` · `offline=True`
- Alpha klines: ABSTAIN (fullyDelisted — BAPI returns 400)
- Alpha local store: venue=binance_alpha KHÔNG TỒN TẠI trong store (có thể chưa collected hoặc đã expired)
- `taker_alpha`: BANNED (k[9]==k[5] — confirmed từ bài ALPHA_435/IDOL)

**Depth snapshot #1 (2026-08-07 13:09:34 UTC):**
- Bid±2%: $70,718 | Ask±2%: $48,709 | px_mid: 0.007143
- **CẦN OPERATOR:** Depth snap #2 sau 17:09 UTC 07/08 (L-23)

---

## B-5: ON-CHAIN / KHO

**Contract (BSC):** 0x3d4f0513e8a29669b960f9dbca61861548a9a760 — chainId=56
Nguồn: alpha token list (Binance BAPI) — VERIFIED (official source)

| Metric | Giá trị | Nguồn |
|---|---|---|
| Total supply | 10,000,000,000 tokens | alpha token list |
| Circulating supply | 10,000,000,000 (= total) | alpha token list |
| Holders | 158,024 | alpha token list |
| Market cap | $71,522,027 ($0.00715) | alpha token list 07/08 |

**BscScan top holders:** NOTOK (0-credit API) — **CẦN OPERATOR:** API key hoặc manual check
**Nansen:** LOCKED — **CẦN OPERATOR**
**L-28:** Nguồn xác minh chéo CHƯA CÓ — contract chưa verify qua source thứ 2

---

## B-6: VPS + SỔ CHÉO

**freshwatch 2026-07:** BANANAS31USDT FOUND — 28 ngày trong tháng 7 (kèm BANANAUSDT cùng file)
- Cuối July: pos_r=5.97-6.00, gLSR=0.96-1.05, f_avg=5e-5 (PIN_HI cứng)
- data_ok=True (fn=6)

**freshwatch 2026-06:** 17 ngày BANANAS31USDT

**gom_scan (gom_gate6_full_20260808.txt):** BANANAS31 không xuất hiện (kiểm, sạch)
**gom_diag_20260808.txt:** BANANAS31 không xuất hiện
**screen_thresholds.yaml:** BANANAS31 không có trong thresholds
**CASE files hiện tại:** 10 file — không file nào có BANANAS31 trong tên
**agent_log.md:** BANANAS31 chưa đề cập (case mới)
**MM_BOOK fingerprint:** chưa match với case nào đang mở

---

## MISSING

1. **Depth snapshot #2** (cần ≥ 17:09 UTC 07/08/2026) — L-23 compliance
2. **BscScan top holders** — CẦN OPERATOR (API key hoặc manual)
3. **Nansen top holders** — CẦN OPERATOR (LOCKED)
4. **Contract verify cross-source** — chỉ có BAPI, cần nguồn 2 (L-28)
5. **Alpha klines lịch sử** — fullyDelisted, BAPI 400, local store không có
6. **Venue ngoài Binance** — chưa check (L-30: Bitget, OKX flag)
7. **VPS freshwatch từ 05/2026** — có thể có data từ tháng 5 nếu listing vào freshwatch sớm
8. **T0, B_ref OI, Archetype** — việc ANALYSIS + operator (L-42)

---

*Script chain: _probe_bananas31_b0_prep_20260808.py → _probe_bananas31_b4_alpha_20260808.py → _probe_bananas31_b6_crossref_20260808.py → build_case.py → _task_register_bananas31_20260808.py*
"""

collect_md.write_text(report, encoding="utf-8")
log(f"  Collect report written: {collect_md}")

log(f"\n[REGISTER DONE]")
