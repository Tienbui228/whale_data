---
type: proposal-rejected
name: §E-R4b RE-ARM v1.2 WAVE-END
version: 1.2-DRAFT-REJECTED
status: REJECTED (21/08/2026)
canonical_replacement: proposals/unhedge_registry_spec.md §E-R4b v1.2-FINAL
---

# [REJECTED 21/08 — falsified by HEMI anchor, thay bằng Version A]

Đề xuất WAVE-END (ANALYSIS relay 20/08): 3 close-condition thêm cho row IGNITED nếu markup-giữ:
- **w1** `gLSR return ≥ 0.80 pre-flush peak` (herd return)
- **w2** `vol-nguội 5d` (median 5d < 0.5× med14)
- **w3** `fizzle: OI ↓ ≥20% từ ignite trong 7d liên tiếp`

Nếu bất kỳ w1/w2/w3 fires → row đóng WAVE-END outcome.

## Lý do REJECT

**HEMI anchor falsify:** loài captive-kho dàn trận NGAY TRONG markup (deposit +100M đến giữa lúc giá giữ 1.15-1.48× local_low, RỒI mới nổ mega-wave 15/08). WAVE-END close-condition sẽ:
- w1 (herd return): sập nếu crowd chưa vào (HEMI 07-30..08-14 gLSR flat, không herd return)
- w2 (vol-nguội 5d): sập nếu volume dry lại giữa 2 wave (HEMI 08-01..08-14 vol nguội — sẽ trigger đóng)
- w3 (fizzle OI ↓): sập nếu OI dip tạm (HEMI có OI dip 08-10..08-14)

→ Cả 3 điều kiện WAVE-END sẽ ĐÓNG HEMI row NGAY TRƯỚC 15/08 mega-wave (miss ×2 second time).

## Verdict operator (chat 21/08)

Version A (r2 1.15 / r3 1.30 / cooldown 3d, BỎ close-condition MARKUP-GIỮ) chống-miss tốt hơn. Wave-end doctrine hồi sinh xác chết có giấy tờ (relay-loss #6 — được ghi handover 20/08 nhưng operator chưa bao giờ ký thật).

**Chốt:** Wave-end BỎ. Version A canonical.

## Ref

- Canonical: `proposals/unhedge_registry_spec.md` §E-R4b v1.2-FINAL
- Handover 20/08 (relay-loss #6): "wave-end đã ký" — SAI, chưa ký.
- HEMI L-53 case study — anchor n=1 falsifier.
