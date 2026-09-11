# DEV → ANALYSIS · TRIPWIRE E2 · ba đường đều tắc + một án quản trị

**Ngày**: 2026-09-11 · **Nguồn số**: Z-round (Z2..Z6) · ZZ-round (ZZ1..ZZ5) · ZA (ZA1..ZA4) · ZB (ZB1..ZB4) · ZC (ZC1..ZC4) · ZD (ZD1..ZD5). Tất cả read-only, không SCP, không đụng VPS, không đụng ngưỡng yaml.

---

## 1. ÁN QUẢN TRỊ — verdict phát hành không chữ ký

Spec [docs/proposals/gom_h_gate_defs_20260828.md](docs/proposals/gom_h_gate_defs_20260828.md) dòng 31:

> **E2**: trần FP-rate **CHƯA đăng ký** — [CẦN KÝ]: ANALYSIS trình phân bố FP từ census (§5) + control-set, operator đặt số. **DEV không chạy verdict E2 trước chữ ký**; chỉ render số liệu.

Nhưng thực trạng:
- Commit `6366150` (2026-08-27 22:37) đưa `MAX_RATE_DEFAULT=0.4` vào `lib/tripwire_e2_v2.py`.
- Commit `a62e194` (2026-08-27 07:43) đưa `max_alert_per_token: 0.4` vào `screen_thresholds.yaml`.
- Cờ `data/state/tripwire_e2_v2_TRIPPED.flag` dựng 2026-09-01 06:54 UTC · rate=0.4277 · grades_md5=8fdd0a74.

⇒ **Cổng đã phán trong khi spec của nó cấm phán.**

**Đề nghị**: đánh dấu cờ hiện hành = `verdict phát hành không chữ ký` · giữ REPORT-ONLY (đằng nào cũng đúng vì lý do khác — xem mục 4-5) · ghi án riêng.

**Đã làm**: tạo annotation file [data/state/tripwire_e2_v2_TRIPPED_unsigned_note.md](data/state/tripwire_e2_v2_TRIPPED_unsigned_note.md) song song `.flag` (**KHÔNG chạm** file `.flag` để tránh side-effect renderer).

---

## 2. 0.4 KHÔNG CÓ GỐC HIỆU CHỈNH

Docs `gom_h_gate_defs_20260828.md` dòng 24:

> E2-trần = **0.4** alert/token/30d hậu-cooldown, đo trên control-universe mỗi 30d; vượt → compose tự về report-only chờ operator. (**Máy hiện đo 0.16 — headroom ×2.5.**)

**0.4 = 0.16 × 2.5** = trần đặt so với mức đang chạy, KHÔNG so với mức gây hại. Không có phân bố FP, không có dataset trích, không có analysis-side-scoring commit kèm.

---

## 3. Mức tăng 0.16 → 0.4277 KHÔNG phải drift

`graded_at` trong census v4 chỉ có 2 mốc:

| graded_at | n_rows | FP | TP | PENDING |
|-----------|--------|-----|-----|---------|
| 2026-08-29 | 41 | 6 | 0 | 35 |
| 2026-08-31 | 44 | 37 | 7 | 0 |

- 0.16 ứng n_FP≈16 (giai đoạn chấm sơ khởi 08-27 khi docs viết).
- 0.4277 ứng n_FP=43 (sau khi chấm xong batch 08-31).

**Tăng do CHẤM XONG, không do hệ xấu đi.** Cả số tuyệt đối lẫn mức tăng đều không diễn giải được như tín hiệu. Muốn có chuỗi theo đêm phải re-grade rolling data_through 58 lần (cur không tồn tại).

---

## 4. Mẫu thực nghiệm 58 đêm (ZD3)

Roster đích danh mỗi ngày (`fw139 ∩ VPS-store ∧ ∉ EXCL`), 58 file trong [sandbox/backfill_09/output/roster_daily/](sandbox/backfill_09/output/roster_daily/):

```
n_roster dao động:  min=1  max=121  median=121
- 06-26        : 65   (store partial)
- 06-27 → 07-03: 120  (1 token thiếu)
- 07-04 → 07-23: 121  (full)
- 07-24/25/26  : 1    ★ OUTAGE 99.2% collapse
- 07-27 → 08-22: 121  (phục hồi)
```

Tổng exposure empirical = **6595 token-days** (không phải 52×58=3016 · không phải 121×58=7018).

Rate empirical: `43 × 30 / 6595 = 0.1956` — dưới 0.4 dù chưa loại nhiễm.

**★ Ba ngày OUTAGE phải trừ khỏi mẫu** (không quan sát được). Mẫu "58 ngày × X token" là ảo — chốt phải dùng empirical.

---

## 5. FP/fire theo họ × 3 quy ước PENDING (ZD4)

| họ | exclude PEND | as_FP | as_TP |
|----|--------------|-------|-------|
| **H1** | 13/17 = **0.7647** | 36/40 = 0.9000 | 13/40 = 0.3250 |
| **H2/H3** | 30/33 = **0.9091** | 42/45 = 0.9333 | 30/45 = 0.6667 |
| **GỘP** | 43/50 = **0.8600** | 78/85 = 0.9176 | 43/85 = 0.5059 |

**H2/H3 xấu hơn H1 ở MỌI quy ước PENDING** — kết luận bền, không phụ thuộc chọn semantic.

---

## 6. FP-lines/ngày · CHẶN BỞI C3

Không tìm được nguồn CANONICAL 'C3 as-SENT' trên local. Sandbox tg_final 4 files (không canonical) · sidecar_snapshots 12 files (sidecar chứ không phải in-Telegram).

**Không thay bằng fire/ngày** — fire là compose-time, chưa phải in-Telegram (còn cooldown/dedup/DQ-SERIAL/tripwire filter). Chờ C3 archive SCP về sau cửa-thi.

---

## ĐỀ NGHỊ ĐƯỜNG ĐI

**Bỏ hẳn ý "chuyển ngưỡng cũ sang thang mới"** — không có gì để chuyển (0.4 là placeholder, không phải calibrated baseline).

**Thay bằng workflow calibration LẦN ĐẦU**:

1. **ANALYSIS trình PHÂN PHỐI FP/fire theo họ** (số đã có ở mục 5).
2. **Tiên đặt ngưỡng lần đầu trên số THẬT**, không phải ×2.5 của số đang chạy.
3. **Khai rõ quy ước PENDING trước khi nhìn kết quả** — chọn exclude / as_FP / as_TP là **quyết định method-first**, không phải fit-post-hoc.
4. **Chọn semantic mẫu**:
   - (a) 52 kept (silent-truncate hiện hành · KHÔNG khuyến nghị)
   - (b) 121 clean (control_set đầy đủ)
   - (c) empirical roster-day-sum (6595 token-days · trừ outage · KHUYẾN NGHỊ)
5. **Sau khi ANALYSIS ký ngưỡng mới + semantic mẫu**:
   - DEV wire re-compute rate `data/state/tripwire_e2_v2_TRIPPED.flag` với công thức mới
   - Add SELF-CHECK: mọi n_FP row có token ∈ roster · lệch → sentinel N/A-ERROR
   - Wire re-grade rolling snapshot n_FP theo ngày (58-day series thay vì 2-mốc batch)
6. **Cờ hiện hành**: giữ REPORT-ONLY (không gỡ, không đóng · chờ ANALYSIS ký). Annotation "unsigned verdict" đã đặt.

---

## Kèm chốt số

- Ngưỡng 0.4 origin: commits `6366150` + `a62e194` (2026-08-27 · không kèm phân bố).
- Cờ TRIP hiện: `rate=0.4277188 · n_FP=43 · exposure=58d · grades_md5=8fdd0a74`.
- Store canonical VPS: 08 md5=463fd476 · 09 md5=f33330e0.
- fw-139 config mtime Aug 24 (source thứ tự [:52] truncate).

## Nợ (ticket)

- **CONTROL-52-ROSTER** (ZB4) · UPGRADE priority per ZC4.
- **TRIPWIRE-CALIBRATION-LẦN-ĐẦU** (mới, thay ZB4 goal): ngưỡng + semantic mẫu + PENDING convention.
- **TAGGER-BLIND-CONSISTENCY** (ZA1 nợ): silent-FALSE trong tagger đã sửa local, chưa land tests/fixture.
- **DEAD-MAN**: alert gap_report chưa wire (ZA4).

## Cửa-thi guard

Không SCP · không wire · không đụng cron · không đụng yaml. Cửa-thi 13/09 vẫn frozen.
