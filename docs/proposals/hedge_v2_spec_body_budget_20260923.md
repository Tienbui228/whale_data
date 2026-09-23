# Nợ proposal · HEDGE v2 §1 spec body budget update

**date:** 2026-09-23 (đăng ký nợ · KHÔNG apply)
**target-apply:** SAU 24/09 tối HEDGE v2 first-night ổn định · commit riêng qua proposals/ workflow
**why nợ:** Doctrine "một đêm một thay đổi" (BC3) · KHÔNG gộp spec update vào commit chạm cron/wire

## Nội dung nợ

**Sửa spec `docs/HEDGE_report_v2_spec_20260921.md` §1 "Khuôn thân":**

Trước (line 10):
```
## 1. Khuôn thân (≤ [3.200] byte)
```

Sau (proposal):
```
## 1. Khuôn thân (thân ≤ 3.600 ký tự Telegram · UTF-16 sau markup · trần cứng 4.096)
```

**Rationale:**
- Số cũ "3.200" đặt trong `[...]` (chờ chốt) và đo bằng "byte" mơ hồ
- Số thật đã áp trong code từ AW-α' (22/09): `BODY_BUDGET = 3600` với đo bằng `tg_len` (UTF-16 code unit sau strip HTML whitelist)
- Trần cứng 4.096 = Telegram API limit (`TG_LIMIT`)

## Assertion hiện tại của p100 (chưa sửa · chỉ báo)

| item | value | NGUỒN |
|------|------:|-------|
| BODY_BUDGET constant | **3600** | `scripts/hedge_v2.py:32` (`BODY_BUDGET = 3600 # p100 · tg_len pre-cap ≤ 3600 (α' bump từ 3200 · thêm kr/STALE/Nguội)`) |
| p100 assert code | `r["p100"] = meta["tg_len"] <= hv.BODY_BUDGET` | `_probe_awp_pins_20260922.py:40` |
| p100 docstring | "thân ≤ ngân sách 3200 (tg_len) 6 đêm" · **STALE** (còn ghi 3200 thay vì 3600) | `_probe_awp_pins_20260922.py:3` |
| meta over_budget flag | `body_tg_len > BODY_BUDGET` | `scripts/hedge_v2.py:820` |

**Nợ chi tiết:**
1. Docstring p100 stale · nên đồng bộ với BODY_BUDGET=3600 (docstring text · không phải logic)
2. Assertion đo bằng `tg_len` (UTF-16 lib/tg_len.py) · đúng · không sửa
3. TG_LIMIT hardcode nhiều nơi (4096) · nên centralize thành constant chung (nợ lớn hơn · defer)

## Thứ tự apply nợ (sau 24/09)

1. Chờ HEDGE v2 24/09 first-night send OK · postcheck sáng 25/09 PASS
2. Commit riêng qua proposals/ workflow:
   - Sửa spec §1 body budget text
   - Sửa docstring p100 (STALE 3200 → 3600)
   - KHÔNG gộp với cron/wire changes
3. Nếu 24/09 FAIL · defer nợ tới HEDGE v2 lần re-launch OK

## KHÔNG sửa hôm nay

- KHÔNG chạm spec doc (docs/HEDGE_report_v2_spec_20260921.md)
- KHÔNG chạm _probe_awp_pins_20260922.py docstring
- KHÔNG chạm BODY_BUDGET constant hay logic
- Chỉ đăng ký nợ · commit riêng sau 24/09
