# WATCHLIST STALENESS — proposal fix (chờ ký) — 19/08/2026

**Status:** DRAFT — chờ operator ký. KHÔNG apply tới ký.

**Bối cảnh:** forensic 19/08 xác nhận watchlist_daily.py có 2-day stale MECHANICAL do timing cron. Ảnh hưởng: **226 dòng nhãn B1↔B2 đảo nghĩa** (18.1% của 1251 log rows, 30-day window). Operator trade theo nhãn đó → **fix GỐC = dời cron + guard**.

**Forensics ref:** `docs/reports/_watchlist_staleness_forensic_20260819.md`

---

## Fix hai tầng — CẦN CẢ HAI

### [1] TIMING — fix GỐC (dời cron)

**Vấn đề:** cron `0 1 * * *` (01:00 UTC) chạy TRƯỚC freshwatch export `20 1 * * *` (01:20 UTC) → bot đọc CSV thiếu ngày cuối → target = D-2 relative to cron day (2-day lag mechanical).

**Đề xuất:** dời cron watchlist về **`35 1 * * *`** (01:35 UTC) — SAU freshwatch 01:20 + buffer 15 phút. Cùng chuẩn PHASE-TAG (01:30, có buffer 10 phút — đề xuất buffer 15 để đủ leeway).

**Diff crontab (VPS `crontab -e`):**
```diff
- 0 1 * * * cd /root/Data_back_test/whale_data && python3 scripts/watchlist_daily.py >> /root/Data_back_test/whale_data/data/export/watchlist_cron.log 2>&1
+ 35 1 * * * cd /root/Data_back_test/whale_data && python3 scripts/watchlist_daily.py >> /root/Data_back_test/whale_data/data/export/watchlist_cron.log 2>&1
```

**Bonus:** đổi `python3` → `.venv/bin/python3` (nhất quán với `run_gom_daily.py` cron) để tránh module-mismatch:
```diff
- 35 1 * * * cd /root/Data_back_test/whale_data && python3 scripts/watchlist_daily.py ...
+ 35 1 * * * cd /root/Data_back_test/whale_data && /root/Data_back_test/whale_data/.venv/bin/python3 scripts/watchlist_daily.py ...
```

---

### [2] GUARD — freshness-check trong code (chống stale + missing)

Dời cron chỉ fix **stale cơ học** (bot chạy sau freshwatch xong). Nhưng nếu freshwatch fail (endpoint down), bot vẫn có thể chạy trên CSV cũ và không alert. → cần **guard §5.11 block-nếu-thiếu** + per-symbol skip-stale.

#### 2.1 Guard block-nếu-thiếu — global freshness

Thêm sau `load_token_data` trong `main()`:

```python
# Guard §5.11: bảo đảm freshwatch có data đến D-1 (yesterday close)
from datetime import date, timedelta
expected_max = (date.today() - timedelta(days=1)).isoformat()
actual_max = max(r["date"] for arr in td.values() for r in arr)
if actual_max < expected_max:
    stale_days = (date.fromisoformat(expected_max) - date.fromisoformat(actual_max)).days
    _msg = (f"⚠ WATCHLIST STALE: freshwatch latest={actual_max} vs "
            f"expected D-1={expected_max} (stale {stale_days}d). "
            f"BLOCK scan — chờ freshwatch export xong.")
    print(f"ERROR {_msg}", file=sys.stderr)
    # Telegram alert BẮT BUỘC — operator PHẢI biết
    try:
        from scripts.fw_loader_utils import taker_scale_check  # dummy import to ensure sys.path ok
        # tg_send từ scripts (nếu chưa có, chép pattern run_phase_tag.py)
        send_telegram(f"⚠ WATCHLIST BLOCKED — freshwatch stale {stale_days}d "
                      f"(latest={actual_max}). Bỏ chuyến hôm nay. "
                      f"Check freshwatch export log.")
    except Exception:
        pass
    sys.exit(1)   # exit ≠ 0 → cron log ERROR (L-44)
```

#### 2.2 as_of per-symbol — track ngày close mỗi symbol

Thêm cột `as_of` (ngày close latest cho symbol đó) vào output CSV:

```python
# Trong snapshot() thêm:
"as_of": arr[i]["date"],   # actual latest date processed for this symbol

# Trong append_csv() thêm cột as_of vào fieldnames
```

Giúp operator kiểm tra thủ công: mỗi dòng CSV có ghi rõ "data đến ngày nào" — không giả định uniform.

#### 2.3 Skip-stale per-symbol

Nếu 1 symbol thiếu row cho D-1 (nhưng phần lớn khác có) → skip symbol đó (không auto-fill):

```python
# Trong run_date(), thay:
idx = next((i for i, r in enumerate(arr) if r["date"] == target_date), None)
if idx is None: continue

# Thêm log để phân biệt "not in data" vs "data cũ":
if idx is None:
    max_dt = arr[-1]["date"] if arr else "?"
    print(f"WARN skip {sym}: no row for target={target_date} (latest={max_dt})",
          file=sys.stderr)
    continue
```

#### 2.4 CORRECTIONS append log (không sửa lén)

Nếu operator/ANALYSIS muốn ghi correction sau (ví dụ retroactive verify nhãn STBL 08-13 = actually TĂNG), append vào file riêng:

```
data/export/watchlist_corrections_YYYY-MM.md
```

Ghi tay theo template:
```
- run_date 2026-08-13 STBLUSDT list=A · oi_trend logged=GIẢM · verified=TĂNG · reason: freshwatch stale 2d timing bug → target=08-11 vs actual close 08-13 available. Ref: _watchlist_staleness_forensic_20260819.md
```

**CẤM sửa watchlist_log_2026-08.csv lịch sử** (append-only, provenance). Correction ĐI RIÊNG file corrections.

---

### [3] BONUS BUG — 🎓 graduation broken on VPS

**Finding:** `/root/Data_back_test/whale_data/data/state/` **RỖNG** trên VPS. `save_snapshot()` chưa từng chạy thành công trên VPS (hoặc dir bị xóa). Cron log không có "INFO: snapshot committed for {target}".

**Hậu quả:** `load_prev_snapshot()` luôn trả None → `format_output_tg` chạy without prev_snap → **🎓 classifier RỜI-list không hoạt động trên VPS**. Local Windows có 2 snapshot 08-16/08-17 (từ chạy tay operator?).

**Nghi ngờ:** cron VPS chạy `python3` (system, không phải .venv), có thể save_snapshot() fail silently do exception KHÔNG bị catch (nhưng đâu không có log ERROR). Cần probe log ERROR/stderr riêng.

**Fix đề xuất:** thêm log RÕ ràng cho save_snapshot success/fail:
```python
try:
    save_snapshot(snaps_a, snaps_b, target)
    print(f"INFO: snapshot SAVED to {STATE_DIR}/hedge_watchlist_{target}.json",
          file=sys.stderr)
except Exception as _exc:
    print(f"ERROR: save_snapshot FAIL: {_exc}", file=sys.stderr)
    raise    # fail-loud
```

---

## Regression 3 case (bắt buộc trước ký)

Trước khi apply, chạy regression trên 3 date + so nhãn kỳ vọng:

| # | run_date | mode | expected oi_trend | ghi chú |
|---|---|---|---|---|
| 1 | 2026-08-17 (target hiện tại) | pre-fix (target=08-15, no guard) | STBL=GIẢM (đã logged) | baseline |
| 2 | 2026-08-19 (target D-1=08-18) | post-fix (dời cron + guard) | STBL=TĂNG (recompute@08-18) | fix on |
| 3 | 2026-08-19 (guard test) | mock freshwatch stale 3d | BLOCK + telegram alert | guard active |

Regression PASS = cả 3 case output khớp expected.

---

## Deploy plan (chờ ký cả 3)

1. **Backup:** `cp watchlist_daily.py scratch/watchlist_daily_bak_pre_W_20260819.py`; VPS `crontab -l > /root/crontab_bak_20260819.txt`
2. **Apply code:** patch guard §5.11 + as_of + skip-stale log + 🎓 save log
3. **Regression:** chạy 3 case, verify PASS
4. **SCP:** `scp watchlist_daily.py root@5.223.67.21:/root/Data_back_test/whale_data/scripts/`
5. **VPS crontab:** `crontab -e` dời `0 1` → `35 1` + `.venv/bin/python3`
6. **Verify tomorrow (2026-08-20 01:35 UTC):** cron chạy, log có target_date=D-1, telegram push clean
7. **Commit `[WATCHLIST-STALENESS-FIX-YYYYMMDD]`**

Sau deploy: KHÔNG được backfill sửa `watchlist_log_2026-08.csv` (lịch sử provenance giữ nguyên). Correction file riêng nếu operator cần.

---

## Chờ operator ký

- [ ] **A. Timing fix** — dời cron 01:00 → 01:35 + đổi `python3` → `.venv/bin/python3`
- [ ] **B. Guard code** — §5.11 block-nếu-thiếu + as_of + skip-stale + 🎓 save log
- [ ] **C. CORRECTIONS log convention** — chấp thuận file corrections.md riêng, cấm sửa lịch sử CSV
- [ ] **D. Regression 3 case** — approve list + expected values
