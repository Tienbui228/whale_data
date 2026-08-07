# Proposal: Collector Funding Gap Fix (08/08/2026)

**Trạng thái:** Đề xuất — chờ operator ký  
**Liên quan:** FIX-PACK v2 step 4 — Án Collector Polling Gap

---

## Root Cause

### Cơ chế

`collect_funding.py` chạy 3 lần/ngày (00:10, 08:10, 16:10 UTC) với lookback cố định 16h:

```python
start_ms = now - lookback_h * HOUR_MS   # floating window — NOT cursor-based
universe = read_latest_universe()        # snapshot tại thời điểm poll
```

Khi một symbol được thêm vào universe tại ngày D, lần poll đầu tiên bắt đầu fetch từ `now - 16h`. Nếu symbol có settlements trước cửa sổ 16h đó → **bị bỏ sót vĩnh viễn** (cho đến khi có repair).

### Trường hợp BANKUSDT 27/07/2026

- BANKUSDT đã niêm yết Binance Futures từ ~2025-04-17 (onboardDate=1745001000000ms)
- Được thêm vào whale_data universe ~2026-07-26 hoặc 07-27
- Lần poll đầu tiên include BANK: 07-28 00:10 UTC (lookback 16h = từ 07-27 08:10 UTC)
- Settlements 07-27 00:00 và 04:00 nằm ngoài cửa sổ → bỏ sót tại thời điểm export 07-28 00:50
- Store hiện tại COMPLETE (6/6 settlements) nhờ các collector runs sau + manual backfill
- CSV đã force-regen: fn=6 ✓

### Bệnh hiện tại

- Mẫu này tái diễn với **mọi symbol mới vào universe** (không chỉ BANK)
- `repair_gaps.py` đã tồn tại (`scripts/repair_gaps.py`) nhưng **KHÔNG trong crontab**
- Không có periodic safety net nào → CSV born-wrong là mẫu tái diễn, không phải sự cố đơn lẻ

---

## repair_gaps.py — Đánh giá

Tool đã sẵn sàng, proper CLI (typer), idempotent:

```bash
python3 scripts/repair_gaps.py funding_8h \
  --start-date 2026-07-21 \
  --end-date   2026-07-28 \
  [--symbols BANKUSDT,TAGUSDT]   # default: full universe
```

- Appends rows với `fetched_at_ms` mới → dedup tự động trong exporter
- Supports all metrics: `funding_8h`, `klines_1h`, `oi_hist_1d`, etc.
- **Đã tested**: backfill 410 rows Aug-05 ngày 08/08 — zero issue

---

## Đề xuất Fix

### Option A — Weekly repair_gaps cron (KHUYẾN NGHỊ)

Thêm vào crontab VPS:

```cron
# Weekly funding repair: Chủ nhật 02:00 UTC — vá settlements bị sót do universe churn
0 2 * * 0 cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/repair_gaps.py funding_8h --start-date $(date -d '8 days ago' +%%Y-%%m-%%d) --end-date $(date -d '1 day ago' +%%Y-%%m-%%d) >> data/logs/repair_gaps.log 2>&1
```

**Ưu điểm:**
- Zero code change vào hot path (collect_funding.py không đụng)
- Window 8 ngày cover mọi universe-churn case (symbol vào universe trong tuần)
- Idempotent — chạy lại không harm
- Fail → crontab EMAIL / log có exit code ≠ 0 (per L-44 rule)

**Nhược điểm:**
- Vẫn có cửa sổ 7 ngày không có safety net (có thể rút xuống daily nếu cần)

### Option B — Cursor-based fetch (P2 enhancement)

Thay thế floating lookback bằng `since_last_ts` per symbol:

```python
# collect_funding.py
last_ts = get_last_stored_ts(symbol, metric="funding_8h")
start_ms = last_ts + 1 if last_ts else now - 16 * HOUR_MS
```

**Ưu điểm:**
- Catch new universe members từ lần poll đầu tiên
- Không cần repair cron

**Nhược điểm:**
- Code change vào hot path (rủi ro)
- Cursor tracking phức tạp (per-symbol state)
- P2 — implement sau khi Option A đã có safety net

---

## Trạng thái tạm thời (chưa có cron)

- Manual backfill đã thực hiện 08/08/2026 — 410 rows Aug-05 ✓
- Nếu có symbol mới vào universe tuần tới → cần manual backfill tương tự
- Operator confirm ký Option A → agent thêm crontab

---

## Checklist để đóng án

- [ ] Operator ký Option A → agent thêm crontab 1 dòng
- [ ] Test run repair_gaps.py một lần thủ công (kiểm tra exit code + log)
- [ ] Verify funding_intervals.json: BANKUSDT interval đúng (hiện config=1h, store có fn=6 từ 4h era — historical rows đúng cho kỳ đó, không cần fix)
- [ ] Option B: ghi DEV task, không làm ngay
