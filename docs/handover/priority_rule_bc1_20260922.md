# Luật ưu tiên BC1 — nhiều bộ phân loại cùng token → một khối thắng

**date-ký:** 2026-09-22 (ANALYSIS)
**wire:** 27/09/2026 (theo lịch BC3)
**pin:** p117 (viết khi wire · rule-check)
**scope:** rendering pipeline · digest_summary_v2 (khối loài) + b_state_tracker (B-tier)

## Vấn đề

Ngày 22/09 target 09-21 · lint p115 (report-only DAY 1/5) báo 4 tokens trong ≥2 khối loài:

| token | blocks (loài) |
|-------|---------------|
| BTR   | A · B |
| BULLA | A · B |
| CROSS | A · B |
| IDOL  | B · CHƯA XẾP LOÀI |

Nguyên nhân: nhiều bộ phân loại (gom_e species classifier · b_state_tracker U0-CLASS · CHƯA XẾP fallback) cùng nhận một token nhưng KHÔNG có luật ưu tiên rõ ràng → token in nhiều lần.

## Luật ưu tiên (ANALYSIS 22/09)

**Priority DESC:** `B-tier (CONFIRMED/CROSS) > C > D > B(loài S1) > A`

Cụ thể:
1. **B-tier** = từ b_state_tracker · tier ∈ {CONFIRMED, CROSS} — HIGHEST
2. **C** = species C (ĐẠP → GOM → ĐẨY)
3. **D** = species D
4. **B(loài S1)** = loài B từ species classifier · S1 sub-tier (lai với D)
5. **A** = species A (base·chưa đủ evidence) — LOWEST

**Rule áp dụng:**
- Token in **MỘT LẦN** ở khối thắng (priority cao nhất)
- Kèm tag phụ: `(cũng khớp <loài> k/n)` với k = số bộ phụ, n = tổng số bộ khớp
- Lai **[B·D]** giữ nguyên như S1 (không bị luật này ảnh hưởng · đã có convention riêng)

## Ví dụ áp dụng cho 09-21

| token | classifiers | winner | tag phụ |
|-------|-------------|--------|---------|
| BTR   | A + B-tier=CROSS | **B** | `(cũng khớp A 1/1)` |
| BULLA | A + B-tier=CROSS | **B** | `(cũng khớp A 1/1)` |
| CROSS | A + B-tier=CROSS | **B** | `(cũng khớp A 1/1)` |
| IDOL  | B-tier=CROSS + CHƯA XẾP | **B** | `(cũng khớp CHƯA-XẾP 1/1)` |

Sau khi wire: cả 4 chỉ in một dòng ở B, có tag phụ · lint p115/BB1 sẽ báo 0 ca.

## Pin p117 (rule-check · viết khi wire 27/09)

Test cases:
- **p117-a** · Token có B-tier CROSS + species A → chỉ dòng B · tag `(cũng khớp A 1/1)`
- **p117-b** · Token có B-tier CONFIRMED + C + D → chỉ dòng B · tag `(cũng khớp C 1/2 · D 1/2)`
- **p117-c** · Token có C + D · KHÔNG B-tier → dòng C · tag `(cũng khớp D 1/1)`
- **p117-d** · Token có A only → dòng A · KHÔNG tag phụ
- **p117-e** · Token lai [B·D] S1 → giữ như hiện tại · KHÔNG áp luật BC1
- **p117-f** · Token có event hôm nay (BELL/CLASS/U1) → vẫn hiện ở khối thắng · không giấu (§14)

## Impact lên lint p115/BB1

- **Trước BC1** (nay): 4 tokens ≥2 loài blocks (BTR/BULLA/CROSS/IDOL)
- **Sau BC1 wire** (27/09+): kỳ vọng 0 ca · lint p115 báo sạch
- **Nâng lint p115 → CHẶN**: sớm nhất 02/10 nếu 27/09-01/10 báo 0 ca liên tiếp (BC2 · doctrine #15 amendment)

## Không làm hôm nay

BC1 defer wire 27/09 theo lịch BC3 (một đêm một thay đổi). Doc này = spec để implement khi tới ngày.
