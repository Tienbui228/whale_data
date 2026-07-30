# Tape Daemon Spec — Gate.io Spot Trades

**Status:** DRAFT — chờ operator approve trước khi implement  
**Date:** 2026-07-30  
**Based on:** probe `scripts/_probe_tape_br_rate.py` + `_probe_br_fullday_jul29.py` (run 2026-07-30)

---

## 1. Kết quả probe BR@Gate

### Probe 1 — Rate estimate (rate probe từ 100 trades mẫu)
| Metric | Giá trị |
|--------|---------|
| Rate estimate (từ sample 112 min) | ~1 282 trades/day *(underestimate)* |
| Gate `from`/`to` filter | CONFIRMED working |

### Probe 2 — Full-day Jul29 VERIFIED (L-09: chỉ tin bảng điều kiện)
| Metric | Giá trị |
|--------|---------|
| Trades Jul29 thực tế | **2 401 trades** |
| Timestamp phủ | 00:00:13 → 23:59:09 UTC (gap <1 phút hai đầu) |
| Pages cần (limit=1000) | **3 pages** |
| Tape vol (sum size×price) | **$24 025.34 USDT** |
| Kline vol Gate Jul29 | **$24 025.34 USDT** |
| Sai lệch | **0.0%** |
| Verdict | **PASS ≤ 5%** |

---

## 2. Kết luận kiến trúc

### BR@Gate — One-shot đủ (VERIFIED bằng số)
BR có **2 401 trades/ngày** thực tế, cần 3 lần gọi API (page=1/2/3, limit=1000).  
`collect_tape.py` dùng pagination đúng (last_id hoặc page); one-shot daily **phủ 100%** ngày Jul29.  
Tape vol khớp kline **0.0%** — xác nhận không mất trade.

**Giới hạn áp dụng:** one-shot valid chỉ cho token ≤ ~5 000 trades/ngày (≤ 5 pages limit=1000, margin 2×). Tokens > 5 000 trades/ngày → cần daemon incremental.

Cron daily cho BR: **APPROVED (by probe)**. Implement sau khi operator confirm mục 5.

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
| LOW | BR_USDT | **2 401/day** (verified Jul29) | one-shot daily | **giữ one-shot + cron** |
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
