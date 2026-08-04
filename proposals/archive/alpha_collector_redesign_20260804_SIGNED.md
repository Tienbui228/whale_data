# DESIGN MEMO: Alpha Collector Redesign — NHÁNH B
**Ngày:** 2026-08-04  
**Trạng thái:** CHỜ OPERATOR KÝ — KHÔNG tự áp dụng  
**Bối cảnh:** Điều tra 04/08 xác nhận `collect_alpha_spot.py` gọi standard spot API (nhánh B), không phải bapi/alpha. Mọi thay đổi thiết kế cần operator phê duyệt trước khi thực thi.

---

## BỐI CẢNH — Kết quả điều tra 04/08

| Mục | Thực tế |
|-----|---------|
| `collect_alpha_spot.py` gọi | `api.binance.com/api/v3/klines` (standard spot) |
| Đường alpha thật | `binance.com/bapi/defi/v1/public/alpha-trade/klines` (chưa dùng) |
| BSC_BROKEN trong u50 (137 symbols) | **0** — không symbol nào có taker hỏng |
| NO_SPOT trong u50 (không có Binance spot listing) | **84 / 137 (61%)** |
| OK spot (collect_spot_daily đã phủ) | **51 / 137 (37%)** |
| EMPTY/ZERO_VOL | 2 |
| alpha_bsc_symbols.txt | MISSING — collector no-op từ 31/07 |
| token-list endpoint | 404 tất cả 10 path thử — CẦN OPERATOR DevTools |
| CALIB_ALPHA resolver | 12 entries tay trong `_calib_alpha_daily.py` |

**Hệ quả:** 84 tokens BSC không có Binance spot listing đang MÙ hoàn toàn (không có price/vol từ bất kỳ automated source nào trong pipeline hiện tại).

---

## OPTION B1 — Chuyển collector sang bapi/alpha

**Mô tả:** Viết lại `collect_alpha_spot.py` để gọi `bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_NNNUSDT`. Phủ các token BSC không có Binance spot listing nhưng có trên Binance Alpha program.

**Được:**
- Phủ được ~84 NO_SPOT tokens (nếu đều có alpha_id) — lấp chỗ trống lớn nhất
- Tách bạch rõ ràng: collect_spot_daily → tokens có spot; collect_alpha → tokens chỉ có Alpha
- Alpha vol có lịch sử từ khi token listing (không bị giới hạn 30/07 như spot store)
- Taker data: cũng ABSTAIN (klines[9]==klines[5] trên bapi/alpha — đã xác nhận với IDOL response)
- Venue label chính xác: `binance_alpha` thay vì `binance_spot_bsc` (misleading)

**Mất / Cần làm:**
- **BLOCKING: token-list endpoint = 404** — không có cách tự động map 84 contract → alpha_id
  - Cần operator: mở DevTools trên binance.com/alpha → bắt API call sinh danh sách token
  - Hoặc: extend CALIB_ALPHA dict tay từ 12 → 84 (labor-intensive, không scalable)
- Cần viết resolver: contract_address → alpha_id (join u50_universe.bsc_address + token-list)
- Cần test alpha endpoint rate limit (undocumented public API — có thể WAF block không báo)
- Schedule: cron PHẢI chạy riêng (bapi endpoint, không share client với spot)

**Số phủ được / không:**
- Phủ được: ~84 NO_SPOT (ước tính — một số có thể không có alpha_id nếu không tham gia Alpha program)
- Không phủ: 51 OK-spot (đã có collect_spot_daily) + 2 EMPTY
- Cần resolver để biết con số chính xác

---

## OPTION B2 — Giữ spot-thường + đổi tên venue

**Mô tả:** Giữ nguyên logic collect_alpha_spot.py (gọi api.binance.com/api/v3/klines), chỉ đổi venue label từ `binance_spot_bsc` → `binance_spot` (hoặc xóa hẳn script này vì redundant với collect_spot_daily).

**Được:**
- Không cần thêm resolver hay endpoint mới
- Sạch hơn: nếu script không làm gì mới, xóa nó → giảm dead code

**Mất / Cần kiểm tra:**
- Không giải quyết coverage gap: 84 NO_SPOT vẫn MÙ
- collect_spot_daily đã bao phủ toàn bộ universe symbols với guard BSC_BROKEN tích hợp sẵn
  - `_BSC_TAKER_RATIO_THRESHOLD = 0.9985` đã có trong collect_spot_daily.py
  - → collect_alpha_spot.py là REDUNDANT hoàn toàn
- **Kết luận Option B2: xóa collect_alpha_spot.py + cron của nó** (không có giá trị so với B1)

---

## KHUYẾN NGHỊ ĐIỀU TRA

| | B1 | B2 |
|--|----|----|
| Coverage gap 84 tokens | **Giải quyết** | Không giải quyết |
| Resolver cần | 84 alpha_id + token-list | Không |
| Code cần viết | Viết lại collector + resolver | Xóa script |
| Blocking | DevTools operator (token-list) | Không |
| Kết luận | **Đúng mục đích gốc** | Dead code cleanup |

**Khuyến nghị:** B1 nếu 84 NO_SPOT tokens là ưu tiên phân tích; B2 (cleanup) có thể làm song song độc lập với B1 vì collect_spot_daily đã phủ 51 OK tokens.

---

## VIỆC TẬP PHẢI LÀM (theo thứ tự nếu chọn B1)

1. **OPERATOR [5 phút]:** Vào binance.com/alpha → mở DevTools → bắt API call sinh danh sách alpha tokens → paste response vào agent
2. **DEV [agent]:** Viết resolver: u50_universe.bsc_address → token-list → alpha_id → mapping file
3. **DEV [agent]:** Verify mapping: đối chiếu 12 CALIB_ALPHA entries với mapping mới (12/12 phải khớp trước khi retire CALIB_ALPHA)
4. **DEV [agent]:** Viết lại collect_alpha_spot.py → bapi/alpha endpoint + mới config file
5. **OPERATOR:** Ký trước khi deploy cron

---

## RÀNG BUỘC

- KHÔNG tự áp dụng bất kỳ option nào — chờ operator ký
- KHÔNG backfill trong session này
- KHÔNG sinh alpha_bsc_symbols.txt (file này sẽ rỗng và vô dụng)
- Report điều tra: `docs/reports/_probe_alpha_deadcode_20260803.md`
