# ERRATA · master 09-21 SKIP · sentinel window lỗi thiết kế (AY4)

**date-range:** 2026-09-22
**target:** 2026-09-21 (cron master 22/09 01:46:01 UTC)
**operator:** whale-data-operator · Tiên
**code-commit:** master_preview_send V3.5s
**gửi tay:** msg_id=8852 (AY1 · 22/09 06:xx UTC · full_md5=704ee140c134 · state md5 SAME)

## Sự việc

Cron master 22/09 01:46 UTC (target=09-21):
- **6/6 chân SENT ok** (bell_journal + native-marker + leg-sent-marker · missing_legs=[])
- **verdict = KÍCH** vì `unknown_sentinels=["N/A-ERROR:LINT"]`
- STUCK-BELL alert msg_id=40 gửi · **standing bell KHÔNG gửi** (SKIP · standing not met)

## Nguyên nhân · LỖI THIẾT KẾ compute_night_verdict

**Vị trí:** `scripts/master_preview_send.py:462` — `_cutoff = _now_utc - timedelta(hours=26)`

**Sentinel scan neo vào `now_utc`** (giờ chấm verdict), KHÔNG neo vào `cron_close` (giờ khép đêm). Kết quả:
- Cron 22/09 01:46 chấm target=09-21 · cutoff = **20/09 23:46 UTC**
- Log entry `[N/A-ERROR:LINT]` từ **21/09 01:46:04** (X1 lint fail cho target 09-20 · đã fix trước AW) VẪN trong cửa sổ 26h
- LINT không nằm trong `declared_sentinels={DUMP-HALF-FAIL, DUMP-FAIL, STANDING, VETO}` → `unk_sent=1` → **KÍCH**

**Đây KHÔNG PHẢI lỗi dữ liệu.** Dữ liệu đêm 09-21 sạch: 6/6 chân SENT, artifact đủ, no lint issue in 09-21 cron. Chỉ do sentinel scan window dính vào log entry cũ 22h trước.

**Đối chiếu artifact scan:** `_has_recent_artifact` (line 306) neo vào `cron_close = target+1d 01:46` — **anchor khác nhau giữa 2 phần** của cùng function. Inconsistency.

## Không sửa cái gì đã stamp

- `EPOCH-STAMP target=2026-09-21 · verdict=KÍCH` giữ nguyên (immutable per §KỶ-LUẬT #11)
- `dem0_lan2_verdict.json` giữ verdict KÍCH · KHÔNG re-compute
- bell_journal + master_preview.log · KHÔNG chỉnh sửa

## Đã làm

- **AY1 (22/09 06:xx UTC · commit sau):** gửi tay master body cho Tiên xem
  - prefix `[GỬI TAY · target=2026-09-21]`
  - msg_id=8852 · full_md5=704ee140c134
  - state md5 SAME (5/5 file) · không journal · không epoch · không counter

## Sẽ làm (AY3 · SAU đêm đầu HEDGE v2)

**Commit riêng · fix cửa sổ sentinel:**
- Đổi anchor sentinel scan từ `now_utc` → `cron_close = target+1d 01:46 UTC`
- Chỉ đếm sentinel có ts trong `[cron_close(T-1), cron_close(T))` (window = ngày T, không tràn ngày trước)
- Pin p115 đen-một-lần:
  - Sentinel phát lúc cron đêm T-1 → KHÔNG tính cho T
  - Sentinel phát trong đêm T → tính
  - Chấm cùng target ở hai giờ khác nhau → cùng kết quả (deterministic)
- Dry verdict 7 đêm 09-15..09-21 với logic mới · in verdict từng đêm
- Qua dry master (luật #12) → SCP

## Impact hiện tại

- **Không** — kỳ vọng cron 23/09 01:46 UTC (target=09-22) sẽ tự sạch: cutoff = 21/09 23:46 UTC > LINT 21/09 01:46:04 → clean → nếu 6/6 chân SENT thì verdict = KHÔNG-KÍCH bình thường.
- **Nếu vẫn KÍCH 23/09** → lỗi mới (không phải residual LINT) → điều tra riêng.

Tiên có bản tin master 09-21 tay msg_id=8852. Đêm 23/09 kỳ vọng master gửi standing bell target=09-22 tự động qua cron.
