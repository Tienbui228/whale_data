# ★ ANNOTATION · verdict phát hành không chữ ký · KÝ 2026-09-11

**File `.flag` GIỮ NGUYÊN** (không đụng · tránh side-effect renderer). Note này song song.

## Trạng thái cờ hiện hành

`data/state/tripwire_e2_v2_TRIPPED.flag`:
- `tripped_at`: 2026-09-01T06:54:21 UTC
- `rate`: 0.4277188328912467
- `threshold`: 0.4
- `grades_md5`: 8fdd0a74f0a615023209519996a96402
- `context`: n_FP=43/n_TP=7/n_PEND=35 · exposure=58d declared

## Lý do án quản trị

Spec [docs/proposals/gom_h_gate_defs_20260828.md](../../docs/proposals/gom_h_gate_defs_20260828.md) dòng 31:

> **E2**: trần FP-rate **CHƯA đăng ký** — [CẦN KÝ]: ANALYSIS trình phân bố FP từ census + control-set, operator đặt số. **DEV không chạy verdict E2 trước chữ ký**; chỉ render số liệu.

⇒ Ngưỡng 0.4 (commit `6366150` · `a62e194` · 2026-08-27) vào code TRƯỚC chữ ký ANALYSIS · docs cùng ngày `gom_h_gate_defs_20260828.md` dòng 24 khai rõ 0.4 = ×2.5 của số đang đo (0.16 · headroom-based, không harm-based).

⇒ Cờ TRIP dựng 0.4277 = verdict cổng phát hành **không có chữ ký hiệu chỉnh**.

## Trạng thái hoạt động

- **REPORT-ONLY**: giữ nguyên (đằng nào cũng đúng vì lý do khác — xem handover mục 4-5).
- **Cờ**: không gỡ, không đóng · chờ ANALYSIS ký ngưỡng mới.
- **Renderer**: vẫn đọc cờ và in `⛔ REPORT-ONLY (tripwire 0.4277 > 0.4 [TRIP])` — hành vi đúng vì cờ tồn tại.
- **Diễn giải phía người đọc**: đây là verdict **placeholder trước ký**, không phải verdict calibrated.

## Handover chi tiết

[docs/handover/tripwire_e2_calibration_20260911.md](../../docs/handover/tripwire_e2_calibration_20260911.md)

## Cửa-thi guard

File này chỉ là annotation (không đọc bởi bất kỳ script sống nào) · không SCP · không wire · không thay đổi cờ · không đụng ngưỡng yaml.
