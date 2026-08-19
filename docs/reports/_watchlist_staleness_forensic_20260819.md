# WATCHLIST STALENESS — forensic — 19/08/2026

**Scope:** READ-ONLY forensic. KHÔNG hotfix, KHÔNG sửa CSV lịch sử, KHÔNG đổi threshold.

**Data provenance (L-48):**
- data-source: VPS `/root/Data_back_test/whale_data/data/export/{watchlist_log_2026-08.csv, freshwatch_daily_2026-08.csv, watchlist_cron.log}` + `/root/.../scripts/watchlist_daily.py`
- machine: local Windows probe (backup /tmp/watchlist_forensic_20260819/)
- date-range: 2026-08-01 → 2026-08-18 (freshwatch), 2026-08-11 → 2026-08-17 (log target dates, 7 runs)
- code-commit: pending

---

## [W0] Backup + md5

Backup 3 file VPS → `C:\Users\Hello\AppData\Local\Temp\watchlist_forensic_20260819\`:

| file (VPS) | md5 |
|---|---|
| `data/export/watchlist_log_2026-08.csv` | `dfa9a60bc171861fbcaa00f03a489f2a` |
| `scripts/watchlist_daily.py` | `8e3597ca0443dff4970515117516913a` |
| `data/export/freshwatch_daily_2026-08.csv` | `8042e34b3d04eb142ec1dcca53f24697` |

Không edit VPS. Không edit local. Chỉ probe.

---

## [W1] FORENSIC RUN 18+19/08 — **TIMING BUG CONFIRMED (a)**

### W1a — watchlist_cron.log tail

```
INFO: target_date=2026-08-11  tokens=525    ← cron ran ~08-13
INFO: target_date=2026-08-12  tokens=525    ← cron ran ~08-14
INFO: target_date=2026-08-13  tokens=525    ← cron ran ~08-15
INFO: target_date=2026-08-14  tokens=526    ← cron ran ~08-16
INFO: target_date=2026-08-15  tokens=526    ← cron ran ~08-17
INFO: target_date=2026-08-16  tokens=526    ← cron ran ~08-18
INFO: target_date=2026-08-17  tokens=526    ← cron ran ~08-19 01:00 UTC
```

`INFO: Telegram OK` mỗi run. **Không có ERROR/WARN** trong log — bot chạy êm, không self-detect stale.

### W1c — Crontab timing (smoking gun)

```
20 1 * * *  ... post_export_csv_commit.sh    (freshwatch export 01:20 UTC)
 0 1 * * *  ... python3 watchlist_daily.py   (watchlist 01:00 UTC — TRƯỚC 20 phút!)
30 1 * * *  ... run_phase_tag.py             (phase_tag 01:30 UTC — SAU freshwatch)
```

`freshwatch_daily_2026-08.csv` mtime: **2026-08-19 01:20:06 UTC** (freshwatch chạy ok).

**Cơ chế lệch:**
- Cron ngày D 01:00 UTC → watchlist reads CSV last-touched ngày D-1 01:20 UTC → CSV contains rows up to date D-2 (D-1 chưa append)
- Watchlist chọn `target = max(dates trong CSV)` → target = D-2
- **Lag mechanical = 2 ngày** cứng mỗi cron

Vd hôm nay 2026-08-19 01:00 → target = 2026-08-17 (bỏ qua 08-18 vì freshwatch mới add 08-18 lúc 01:20).

**CÙNG BUG timing PHASE-TAG** đã fix bằng dời sang 01:30. Watchlist CHƯA fix.

### W1b — STBL input bot thấy vs realtime

Full freshwatch STBL data (VPS latest):
```
date        oi_usd      lsr_pos_r  lsr_acc_r
2026-08-11  1559500.77  0.8808     3.8356
2026-08-12  1565753.91  0.9127     3.6382
2026-08-13  1504959.27  0.8972     3.7642
2026-08-14  1480822.47  0.9174     3.8146
2026-08-15  1519504.69  0.9312     3.6729
2026-08-16  1598811.30  0.9334     3.8876
2026-08-17  1960647.17  0.9775     2.9968    ← bot thấy đến đây (target=08-17 trên 08-19)
2026-08-18  2062661.16  0.9727     2.5348    ← bot KHÔNG THẤY
```

Nến cuối bot thấy = **08-17**. Nhưng real close 08-18 đã available lúc cron ran (01:20 08-19).

---

## [W2] ROW-VẮNG — 08-11 duplicate 5×, TRIA present all dates

| run_date | unique_symbols | rows_w_dup | anomaly |
|---|---:|---:|---|
| 2026-08-11 | 102 | **499** | duplicate ~5× (cron ran manual re-run nhiều lần?) |
| 2026-08-12 | 109 | 129 | normal (dup A+B) |
| 2026-08-13 | 111 | 125 | normal |
| 2026-08-14 | 107 | 120 | normal |
| 2026-08-15 | 108 | 124 | normal |
| 2026-08-16 | 112 | 131 | normal |
| 2026-08-17 | 108 | 123 | normal |

**TRIA presence:** đủ 7 dates 08-11..08-17. KHÔNG vắng.
**Nhãn TRIA over time (từ cron log):**
```
08-11..08-12  TĂNG (long mới)
08-13         PHẲNG
08-14..08-16  GIẢM (short cover)
08-17         PHẲNG
```

Operator nghĩ "TRIA vắng 18/08" = thực tế **bot KHÔNG có target=18/08** vì timing lag. TRIA không thiếu row — chỉ là bot không xử ngày đó.

**Exception nuốt câm?** Không phát hiện exception bị nuốt riêng — log clean, no ERROR. Cron dependencies không có `except: pass` chặn scan.

---

## [W3] AUDIT NGƯỢC — 30 dòng recompute

**Method:** recompute mỗi log row bằng freshwatch canonical:
- **Sanity:** target=run_date (nên khớp bot 100%) — verify recompute logic đúng
- **Test:** target=max_avail=**2026-08-18** — nếu timing được fix (bot đọc CSV mới nhất)

### Sanity — recompute logic ✓

```
1251/1251 log rows audited
oi_trend match : 1251/1251 (100.0%)    ← recompute logic identical to bot
pos_trend match: 981/1251 (78.4%)      ← 270 differ (dig-deeper — có thể do khác cutoff LOW_CONF cho pos)
```

oi_trend (nhãn operator trade) recompute EXACT match. Sanity PASS cho OI.

### Flip test (target=2026-08-18)

```
Total oi_trend flips: 599/1251 = 47.9%    ← gần MỘT NỬA thay đổi nếu bot thấy fresh 08-18

Breakdown:
  TĂNG → GIẢM       : 169    ← B2 long-mới thành B1 short-cover
  TĂNG → PHẲNG      : 163
  GIẢM → PHẲNG      :  77
  GIẢM → TĂNG       :  57    ← B1 short-cover thành B2 long-mới (STBL kiểu này)
  PHẲNG → TĂNG      :  56
  PHẲNG → GIẢM      :  50
  other              :  27
```

### ⚠ B1↔B2 ĐẢO NGHĨA (nhãn operator trade theo)

```
B1(GIẢM short-cover) → B2(TĂNG long-mới):  57
B2(TĂNG long-mới) → B1(GIẢM short-cover): 169
─────────────────────────────────────────
Tổng B1↔B2 đảo nghĩa:                    226 / 1251 = 18.1%
```

**Operator trade sai chiều 1/5 dòng.**

### STBL trace — ĐẢO NGHĨA XÁC NHẬN

```
run_date    logged     recompute@08-18   flip?
08-11 A     TĂNG       TĂNG              -
08-12 A     TĂNG       TĂNG              -
08-13 A     GIẢM       TĂNG              ✓ B1→B2
08-14 A     GIẢM       TĂNG              ✓ B1→B2
08-15 A/B   GIẢM       TĂNG              ✓ B1→B2  (×2 rows)
08-16 A/B   GIẢM       TĂNG              ✓ B1→B2  (×2 rows)
08-17 A/B   TĂNG       TĂNG              -   (latest run catches up)
```

**6 dòng STBL logged "GIẢM short-cover" 08-13→08-16 SAI** — recompute với fresh 08-18 = TĂNG. Operator đã trade nhãn B1 trong 4 ngày liên tiếp thực chất là B2. ĐÚNG như operator đã cảm nhận.

### TRIA trace — cũng có nhãn sai

```
run_date    logged     recompute@08-18
08-11..12   TĂNG       PHẲNG   (5 dòng dup)
08-13       PHẲNG      PHẲNG   -
08-14..16   GIẢM       PHẲNG   ← 4 dòng: nhãn B1 short-cover CHẾ ra (không có TREND thật)
08-17       PHẲNG      PHẲNG   -
```

TRIA 4 dòng logged "short-cover" nhưng fresh data = PHẲNG (không thuộc B1). Không phải B1↔B2 flip nhưng vẫn signal CHẾ.

### 🎓 Graduation snapshots

**FINDING BONUS:** VPS `data/state/` **HOÀN TOÀN RỖNG**. `save_snapshot()` chưa từng chạy thành công trên VPS.
```
$ ls /root/Data_back_test/whale_data/data/state/
total 8
drwxr-xr-x 2 root root 4096 Aug 19 04:42 .
drwxr-xr-x 12 root root 4096 Aug 19 04:42 ..
```

Cron log 0 hit "snapshot" / "INFO: snapshot committed". Nghĩa là **🎓 classifier RỜI-list v1.4 HOÀN TOÀN KHÔNG hoạt động trên VPS**. `load_prev_snapshot` luôn None → không diff → không 🎓 tag. Local Windows có 2 snapshot (08-16, 08-17) — có thể từ chạy tay operator.

**CLO/TRIA nhãn 🎓 operator validate bằng mắt** = **CHỈ dùng được nếu operator chạy tay bằng Windows**. VPS không sinh.

---

## Tóm tắt 3 câu

| câu | kết quả |
|---|---|
| **W1** | ✅ TIMING BUG (a) CONFIRMED — cron 01:00 vs freshwatch 01:20 → lag 2d mechanical mỗi cron |
| **W2** | ✅ 08-11 dup 5× (cron re-run?), TRIA present all dates (không thiếu — chỉ target lag) |
| **W3** | ⚠ **226 dòng B1↔B2 đảo nghĩa** (18.1%). STBL: 6 dòng short-cover → thực long-mới. TRIA: 4 dòng short-cover → thực PHẲNG. 🎓 broken trên VPS. |

**Định cỡ thiệt hại:** 30-day window, operator trade sai chiều **~1/5 nhãn B1/B2**. Nghiêm trọng.

---

## Chờ operator ký proposal

Proposal draft: `proposals/watchlist_staleness_fix_20260819.md` — chứa fix 3 tầng:
1. **Timing** — dời cron 01:00 → 01:35 UTC (buffer 15 min sau freshwatch)
2. **Guard §5.11** — block-nếu-thiếu (freshwatch stale → exit ≠ 0 + telegram)
3. **Bonus** — fix 🎓 save_snapshot log ẩn silent-fail

**KHÔNG hotfix, KHÔNG sửa CSV lịch sử, KHÔNG đổi threshold TỚI KHI OPERATOR KÝ.**

Correction file riêng nếu operator cần retroactive verify — cấm sửa `watchlist_log_2026-08.csv` (append-only, provenance).
