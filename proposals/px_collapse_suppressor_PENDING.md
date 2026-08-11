---
title: px_collapse suppressor — veto NUM-DRIVEN trên dead-cat
status: PENDING — chờ ANALYSIS + operator chọn threshold
date: 2026-08-11
origin: GUA dead-cat discovery (P3 backtest 11/08/2026)
---

## PHÁT HIỆN GỐC

GOM-E bắn NUM-DRIVEN cho GUAUSDT ngày 2026-08-10:
- switch_date 2026-06-20: px_avg = 1.0482
- fire_date   2026-08-10: px_avg = 0.0582  → drawdown từ switch = **−94.4%**
- px sập liên tục từ 06-20 → 08-09 (bottom 0.0360), bounced một ngày → fire trigger

E3 (d_oitok_2d ≤ 0 = short cover) đúng về mặt kỹ thuật — short đang cover.
Nhưng context: cover-vì-thoát-xác, không phải cover-để-kéo.

## LESSON E3-HAI-NGHĨA (đề xuất vào CASE_INDEX.xlsx sheet LESSONS)

**Rule:** E3-cover không immune với dead-cat. Khi token đã sập >X% từ đỉnh gần,
E3 không đọc bullish — short cover có thể là bán tháo cuối (stop-loss chain) hoặc
market-maker đóng hedge trên token đã chết thực tế.

**Analog:** pos_r có hai nghĩa (L-48): số cao = "crowd long mạnh" HOẶC "crowd long
lỗ nặng giữ không bán." E3 tương tự: cover = "hedge-farm đóng SHORT (bullish)" HOẶC
"short-seller take profit trên token đang sụp (bearish continuation)."

**Implication:** GOM-E cần suppressor phân biệt context trước khi đọc E3 là bullish.
GUA là bằng chứng đầu tiên. Cần quét toàn 22 NUM + 11 OI-EXPAND xem có dead-cat khác.

## ĐỀ XUẤT SUPPRESSOR px_collapse

**Tên:** `suppress_px_collapse`
**Trigger:** `drawdown_90d := (px_fire − max_px_90d_before_fire) / max_px_90d_before_fire`
            nếu drawdown_90d < −THRESHOLD → veto fire, tag `[DEAD-CAT-SUSPECT]`, log.

**Spec nguyên bản (chưa implement):**
```
suppress_px_collapse:
  px_fire     = px_avg tại ngày fire (canonical 00:00 UTC)
  max_px_90d  = max(px_avg) trong 90 ngày TRƯỚC fire_date (window đóng kín)
  drawdown_90d = (px_fire − max_px_90d) / max_px_90d
  nếu drawdown_90d < −THRESHOLD:
    → veto NUM-DRIVEN fire
    → tag thay thế: [DEAD-CAT-SUSPECT]
    → log verdict: suppress_px_collapse
    → KHÔNG tắt OI-EXPAND (dead-cat vẫn có OI signature riêng)
```

**Threshold chưa chốt — options:**
| Threshold | GUA bị loại | Cần ANALYSIS scan n dead-cat |
|---|---|---|
| −50%  | YES | TBD |
| −70%  | YES | TBD |
| −80%  | YES | TBD |
| −90%  | YES | TBD |
| −95%  | NO  | TBD |

→ Chạy scan P3 22+11 fires với drawdown_90d từng con, paste list.
→ Nếu dead-cat ≥ 5 con → suppressor là CONFIRM-tier (vào spec §1).
→ Nếu dead-cat = 1-2 (chỉ GUA) → lesson-tier (không thêm điều kiện, ghi chú review).

**Nguồn data:** px_avg từ freshwatch_daily export (canonical 00:00 UTC).
**Không dùng:** alpha spot px hoặc klines intraday (C-2 không join — đã chốt).

## TRẠNG THÁI

- [ ] ANALYSIS xác nhận threshold và scan kết quả
- [ ] Operator ký threshold → implement trong gom_e.py eval_mode_switch()
- [ ] Gate re-run với threshold mới
- [ ] Nếu ≥5 dead-cat: thêm suppress_px_collapse vào §1 spec + verdict enum T2

## LIÊN QUAN

- GUA dead-cat: docs/reports/ hoặc agent_log.md 11/08/2026
- E3 dual-meaning: CASE_INDEX.xlsx sheet LESSONS (ghi mới, pending operator enter)
- P3 backtest: scratch/probe_p3_event_scan.py
- P3 classify: scratch/probe_p3_classify_untagged.py
