# Y1 · Sentinel window verify · TRƯỚC khi bật HEDGE_V2 · IN SỐ

Doctrine áp: #16 mọi bảng NGUỒN · #18 mọi số mang gốc.
KHÔNG chạy compute_night_verdict không --dry (§KỶ-LUẬT #11).

## 1 · Định nghĩa cron_close (file:dòng)

**NGUỒN:** `scripts/master_preview_send.py:463-474` (AZ2 commit 997985b)

```python
# Line 464
_CRON_HOUR = 1; _CRON_MIN = 46; _CRON_BUFFER_MIN = 5

# Line 467-469
_cron_close_T = _dt2.combine(_tgt_d_snt + _td2(days=1),
                              _dt2.strptime(f"{_CRON_HOUR:02d}:{_CRON_MIN:02d}", "%H:%M").time(),
                              tzinfo=_tz2.utc)

# Line 470
_cron_close_T_minus_1 = _cron_close_T - _td2(days=1)

# Line 473-474
_window_start = _cron_close_T_minus_1 + _td2(minutes=_CRON_BUFFER_MIN)
_window_end   = _cron_close_T + _td2(minutes=_CRON_BUFFER_MIN)
```

Formula:
- `cron_close(D) = combine(D + 1day, 01:46:00) UTC`
- `window(T) = [cron_close(T-1) + 5min, cron_close(T) + 5min)`

## 2 · "23:51 21/09" trong X1 báo cáo · CORRECTION

**Nguồn gốc "23:51 21/09":** **KHÔNG có file gốc** · đây là **LỖI ARITHMETIC** của agent trong X1 report `ops/holdout_u0bell_20260920/X1_postcheck_20260922_report.md`.

**Đúng cho verdict compute cho T=09-22 tại 23/09 01:46 UTC:**

| item | value |
|------|------:|
| target T | 2026-09-22 |
| cron_close(T) = target+1d 01:46 UTC | **2026-09-23 01:46:00 UTC** |
| cron_close(T-1) = cron_close(09-21) | **2026-09-22 01:46:00 UTC** |
| _window_start = cron_close(T-1) + 5min | **2026-09-22 01:51:00 UTC** |
| _window_end = cron_close(T) + 5min | **2026-09-23 01:51:00 UTC** |

**KHÔNG PHẢI 21/09 23:51.** X1 báo cáo agent typo · in trước "cutoff" mà không tính đúng.

**Correction hiệu quả:** LINT 21/09 01:46:04 < window_start=09-22 01:51:00 → **OUT** (correct outcome, wrong arithmetic label).

## 3 · Mọi dòng log trong [window_start=09-22 01:51:00, 23/09 01:46:00]

**NGUỒN grep:** `data/logs/master_preview.log` · pattern `[YYYY-MM-DD ...]` prefix line.

Trong khoảng `[2026-09-22T01:51:00, 2026-09-23T01:46:00]`:

| ts_gốc | line content | in window? |
|--------|--------------|:---:|
| 2026-09-22T01:46:01+00:00 | `standing: ok=False · [N/A-ERROR:STANDING-VERDICT] verdict='KÍCH'` | **OUT** (< 09-22 01:51:00) |
| 2026-09-22T01:46:02+00:00 | `[STUCK-BELL] streak=2 reason='N/A-ERROR:STANDING-VERDICT' sent=True det=HTTP 200 · message_id=40` | **OUT** (< 09-22 01:51:00) |
| — | (không có log entry nào khác trong khoảng [09-22 01:51, 09-23 01:46]) | — |

**Kết quả:** window `[09-22 01:51:00, 09-23 01:51:00)` cho T=09-22 verdict compute = **0 N/A-ERROR entries** → unk_sent=0 ✓ (khớp log COMPUTE-VERDICT).

**Lưu ý:** "empty-sidecar result=..." lines trong log là PIN-SCAN stdout · không match `_line_ts_re` regex `^\[YYYY-MM-DD...\]` → **KHÔNG được scan sentinel** (bypass tự động).

## 4 · Master run 22/09 01:46 (target 09-21) TRONG hay NGOÀI window T=09-22

**NGUỒN grep:** `grep -E '^\[2026-09-22T01:4' master_preview.log`

Log entries tại 22/09 01:46:xx UTC (7 dòng liên tiếp, all ts=01:46:01 và 01:46:02):
- `[EPOCH-STAMP] target=2026-09-21 · first-compute stored · verdict=KÍCH`
- `[COMPUTE-VERDICT] target=2026-09-21 · KÍCH · full=6/6 · sent=6/6 · pin-PASS · missing_legs=[] · unk_sent=1`
- `standing: ok=False · [N/A-ERROR:STANDING-VERDICT] verdict='KÍCH' · cần KHÔNG-KÍCH`
- `SKIP · standing not met`
- `[STUCK-BELL] streak=2 reason='N/A-ERROR:STANDING-VERDICT' sent=True det=HTTP 200 · message_id=40`

Windows T=09-22 = `[09-22 01:51:00, 09-23 01:51:00)`.

**Master run 22/09 01:46 timestamps** (01:46:01 và 01:46:02) `< 09-22 01:51:00` → **NGOÀI window T=09-22.**

**Semantic:** Master run 22/09 01:46 chấm target=09-21 (T-1 relative to 09-22). Log entries của run đó thuộc window T=09-21 chứ không phải T=09-22 · buffer 5min đúng loại chúng ra khỏi T=09-22 window.

## 5 · Kịch bản đêm 24/09 · nếu HEDGE fail ghi N/A-ERROR:SEND

**Giả định:** HEDGE cron 24/09 01:40:xx UTC fires · fail send · ghi `[N/A-ERROR:SEND] ...` (hypothetical format) vào master_preview.log HOẶC bell_journal.jsonl.

**Note nguồn writer thực tế:**
- `scripts/master_preview_send.py:252` `_log(f"[N/A-ERROR:SEND] missing TG_BOT_TOKEN or TG_CHAT_ID_DAILY env")`
- `scripts/master_preview_send.py:265` `_log(f"[N/A-ERROR:SEND] {type(e).__name__}: {e}")`
- Chỉ MASTER's send emits N/A-ERROR:SEND. HEDGE fail writes `fail_reason="TG-SEND-FAIL"` vào `hedge_v2_journal.jsonl` (line 985) · KHÔNG format N/A-ERROR:SEND.
- Nếu operator setup wrapper khác để HEDGE echo N/A-ERROR:SEND vào master log, kịch bản DEV áp.

**Window analysis:**

**Verdict compute cho target=09-24 tại 25/09 01:46:**
- `_window_start = 09-24 01:51:00 UTC`
- `_window_end = 09-25 01:51:00 UTC`

**HEDGE fail sentinel timestamps:**

| ts | so với window T=09-24 | trong/ngoài |
|----|:---:|:---:|
| 24/09 01:40:xx (HEDGE cron time) | `< 09-24 01:51:00` | **NGOÀI** (in buffer đầu · thuộc T=09-23) |
| 24/09 01:46:xx (nếu HEDGE ghi sau master start) | `< 09-24 01:51:00` | **NGOÀI** (in buffer đầu) |
| 24/09 12:00:00 (giả sử HEDGE ghi mid-day) | `> 09-24 01:51:00` AND `< 09-25 01:51:00` | **TRONG** ✓ |
| 25/09 01:40:xx (next cron for target 09-24) | `< 09-25 01:51:00` | **TRONG** (in buffer cuối · thuộc T=09-24) |
| 25/09 01:52:00 | `≥ 09-25 01:51:00` | **NGOÀI** (thuộc T=09-25) |

**Kết luận đo (không kết luận suy diễn):**
- HEDGE cron 24/09 01:40:xx sentinel: **KHÔNG** rơi vào window T=09-24 (bị buffer 5min loại · thuộc T=09-23 verdict compute chạy 24/09 01:46).
- Nếu HEDGE emit sentinel sau 24/09 01:51:00 (VD mid-day) và trước 25/09 01:51:00: **CÓ** rơi vào window T=09-24 → tính vào unk_sent.
- Nếu HEDGE emit lại tại 25/09 01:40:xx (cron re-run của target 09-24): **CÓ** rơi vào window T=09-24 (buffer cuối) → tính vào unk_sent → verdict T=09-24 → KÍCH.

Agent IN SỐ · KHÔNG kết luận · DEV chấm.
