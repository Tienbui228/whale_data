# Tape Daemon Spec — Gate.io Spot Trades

**Status:** DRAFT — chờ operator approve trước khi implement  
**Date:** 2026-07-30  
**Based on:** probe `scripts/_probe_tape_br_rate.py` (run 2026-07-30)

---

## 1. Kết quả probe BR@Gate

| Metric | Giá trị |
|--------|---------|
| Trades returned | 100 (API limit) |
| Time span | 6 738 s ≈ 112 min |
| Rate estimate | ~0.9 trades/min |
| Rate estimate | ~53 trades/hour |
| Rate estimate | **~1 282 trades/day** |
| Pages needed (limit=1000) | **~2 pages/day** |
| Gate `from`/`to` filter | **CONFIRMED working** (test: yesterday 00:00–03:00 UTC, 100 trades, all in window) |

---

## 2. Kết luận kiến trúc

### BR@Gate — One-shot đủ
Volume cực thấp (~1 282 trades/day). `collect_tape.py` hiện tại (one-shot, từ `from`/`to` ngày hôm qua) là **đủ** cho BR:
- 2 lần gọi API limit=1000 phủ 1 ngày hoàn chỉnh
- Không cần daemon liên tục; cron daily là phù hợp

### Tokens volume cao — Cần daemon
Với tokens như TAG (perp, khối lượng lớn hơn), một-shot có thể bỏ sót nếu:
- Volume > 10 000 trades/day (10 pages)
- Khoảng trống giữa các lần chạy dài hơn window `last_id` API cho phép

---

## 3. Thiết kế daemon (cho tokens volume cao)

### Trigger
```
Cron: */15 * * * *  (mỗi 15 phút)
Script: scripts/collect_tape.py --mode=incremental --symbol=<TOKEN>_USDT
```

### Incremental mode logic
```
1. Đọc last_id đã lưu từ state file: data/tape_state/<TOKEN>.json
2. Gọi GET /spot/trades?currency_pair=<TOKEN>_USDT&limit=1000&last_id=<saved_last_id>
   (backward pagination từ last_id — Gate trả trades CŨ HƠN last_id)
   → đây là pagination đúng cho Gate spot trades
3. Nếu len(trades) == 1000 → có thể còn thêm, lặp với last_id mới
4. Append vào parquet partition: data/tape/<TOKEN>/<YYYY-MM-DD>.parquet
5. Cập nhật state file với last_id mới nhất (trades[0]["id"])
```

### State file format
```json
{
  "symbol": "TAG_USDT",
  "last_id": "12345678",
  "last_trade_time": "2026-07-30T01:23:45Z",
  "updated_at": "2026-07-30T01:30:01Z"
}
```

### Gap recovery
Nếu daemon bị dừng > 24h:
```
Chạy: python scripts/collect_tape.py --mode=backfill --symbol=<TOKEN>_USDT --from=<date> --to=<date>
```
Dùng `from`/`to` (epoch seconds) thay vì `last_id` — đã xác nhận hoạt động.

---

## 4. Ưu tiên triển khai

| Priority | Symbol | Ước lượng volume | Mode hiện tại | Mode đề xuất |
|----------|--------|-----------------|---------------|--------------|
| LOW | BR_USDT | ~1 282/day | one-shot daily | **giữ one-shot** |
| MEDIUM | TAG_USDT | chưa đo | one-shot daily | daemon 15min |
| MEDIUM | BANK_USDT | chưa đo | chưa collect | daemon 15min |

---

## 5. Items cần operator approve

1. **Approve kiến trúc** daemon vs one-shot cho TAG/BANK  
2. **Đo volume** TAG và BANK trước khi quyết định (`_probe_tape_*_rate.py`)  
3. **Chọn cron interval**: 15min (khuyến nghị) hay 5min?  
4. **VPS cron** hay Windows Task Scheduler cho daemon?  

---

## 6. Không thay đổi gì hiện tại

Spec này là **đề xuất, chưa implement**. `collect_tape.py` hiện hành (one-shot) giữ nguyên.  
Implement sau khi operator ký off mục 5.
