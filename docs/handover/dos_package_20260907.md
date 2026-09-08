# DOS-PACKAGE · KHUÔN ANALYSIS · KÝ 07/09 · ghế 27/09

## Câu kiến trúc mới (V3.5f · directive verbatim)

> **"exposure-declared-theo-thế-hệ tầng universe — đổi mẫu số tại ranh thế hệ"**

Universe không phải hằng số. Mỗi thế hệ (generation) có universe riêng · exposure declared per-generation · đổi mẫu số (denominator) tại ranh giới thế hệ.

## DOS observation V3.5e (target=2026-09-06 · window=30d)

**Fresh Δ≥50k fires:**
- 2026-08-31: DOS Δ=+254,646
- 2026-09-05: DOS Δ=+69,898
- 2026-09-06: DOS Δ=+192,711

**Counter:** DOS = **3× / 30d window** → đạt ngưỡng ĐỀ-CỬ-UNIVERSE.

**Cite:**
- Ledger events md5: `dd9e83f0b9af5d475aa6dc043f3b6e98`
- File: `data/logs/event_ledger/events_2026-09-06.jsonl`
- Backfill script: `scripts/ledger_backfill_30d_v3_5.py` md5 `a0b8132e86ad9e86639a033bfb24d716`
- Universe current: `data/config/freshwatch_symbols.txt` md5 `e36183036102c52ed586d6c2bdcfc928` n=139 (KHÔNG chứa DOS)

## Trạng thái

**⇒ [ĐỀ-CỬ-UNIVERSE: DOS 3×/30d — chờ chữ 27/09]**

- Không seed vào PERP/FRESH-CHAIN axis (V3.5d/e strict-139 rule)
- Ghi vào `[NGOÀI-SỔ: <date>] DOS Δ=+X` (in cuối khối 📒 digest)
- Counter đếm tiếp trong window rolling
- **Ghế 27/09:** ANALYSIS ký duyệt / bác thêm DOS vào universe thế hệ mới (generation next)

## Câu hỏi kiến trúc cho ANALYSIS

1. **Universe thế hệ:** current = generation-0 (u50 = 139 syms lock 07/2026). Adding DOS = generation-1 (u51 = 140 syms) hay generation-alpha (parallel branch)?
2. **Ranh thế hệ:** effective at target-date T · exposure per-token trong window trước T vs sau T so sánh thế nào?
3. **Denominator switch:** mọi trục (fresh_coverage/n_universe · matrix denominator) đổi tại ranh · làm sao bridge N-day rolling window đi qua điểm đổi?
4. **Backfill semantic:** rerun cũ với universe-0 hay universe-mới? Áp cho ngày trước ranh?

Chờ ANALYSIS bàn 27/09.

## BEAT/ONE/B đếm tiếp

Counter continue in rolling window · KHÔNG đề cử sớm (<3×):
- BEAT: 1× (08-31)
- ONE: 2× (09-04, 09-05)
- B: 1× (09-06)

Nếu tái xuất trong fresh 09-07 → counter +1 · nếu đạt 3× → ĐỀ-CỬ-UNIVERSE mới.

## Prior art (án lệ)

Chưa có DOS-package tiền lệ. Đây là DOS-package #1 · khuôn cho generation-transition policy.

**Related directives:**
- V3.5d strict-139 + [NGOÀI-SỔ]
- V3.5e counter + [ĐỀ-CỬ-UNIVERSE: X n×/30d]
- L-48 per-target-date universe (chưa wire · SOPH-family delist)

## md5

- `docs/handover/dos_package_20260907.md`: (compute post-write)
- Chờ ANALYSIS bàn 27/09 · nếu duyệt → generation-1 universe file drop
