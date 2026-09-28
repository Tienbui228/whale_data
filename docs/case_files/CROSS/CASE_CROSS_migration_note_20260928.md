# CASE_CROSS · migration note · 2026-09-28

**Ghi chú (v28d)**:

- Whales_config có 2 entries CÙNG contract `0x6bf62ca91e397b5a7d1d6bce97d9092065d7a510`:
  - `symbol=CROSS name='CROSS Protocol'` (cap_source=alpha) → match perp CROSSUSDT ratio 1.00× ✓
  - `symbol=ONE name='ONEchain' cg_id='cross-2'` (cap_source=cg) → MISMATCH perp ONEUSDT ratio 64× (perp là Harmony ONE, khác project)
- **Kho CROSS lấy từ dòng whales CROSS** (không phải dòng ONE) — Nansen snapshot key theo symbol='CROSS' (per N1 verify · grep 09-07..09-27 · ONE=0 fires · CROSS có kho fire 2026-09-11).
- Hành động migration v27: BỎ ONE entry duplicate · save 2 credits/night.
