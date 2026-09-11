# AMENDMENT GATE-D · KÝ 2026-09-11 · V3.5s draft (chờ Tiên ký)

## Bối cảnh

Đêm 10/09 (cron 01:46 UTC 11/09) verdict `target=2026-09-10` = **KÍCH** ĐÓNG DẤU BẤT-BIẾN vào `verdict_epoch_2026-09-10.json`. Cơ chế đóng dấu:
- 6/6 full-pair ✅ · 6/6 sent ✅ · unknown_sentinels=[] ✅
- **pin_scan_p1_p22_bo_niem = FAIL**
- verdict gate: `n_full==6 ∧ n_sent==6 ∧ pin_result=="PASS" ∧ not unknown_sentinels` — sai vì pin_result="FAIL" → rơi else → KÍCH.

**Bằng chứng từ `data/logs/harness_sabotage.log` (ts=2026-09-11T01:46:01+00:00):**
- p20 · PASS (unit test empty-sidecar renders N/A-ERROR)
- **p21 · FAIL** · `target=2026-09-10 APR px_now=None → WATCH` · `APR-in-WATCH-block=False · APR-still-PRE=False`
- **p22 · N/A** · `target=2026-09-10 ⭐-PRE header ≡ printed + tail names` · `no ⭐-PRE block found`

## Phân loại: **GRADER-BUG** (không phải PERFORMER)

### Gãy #1: pin-scan chạy pre-ledger

**Chuỗi thứ tự main()** (`scripts/master_preview_send.py:390-475`):
```
① compute_night_verdict(target)   ← pin-scan subprocess (harness gọi build_v2_digest LIVE)
② check_standing()
③ IF standing OK → step_rebuild_ledger(target)   ← ghi events_<target>.jsonl
④ step_render_digest → build_v2_digest(target)   ← đọc events file
⑤-⑦ lint · seal · send
```

**Pin-scan tại ① đọc body live-build khi events file CHƯA CÓ**. Cùng function `build_v2_digest` gọi lần ① vs ④ cho ra 2 output khác:
- Lần ① (pre-ledger): body chứa `[LEDGER-WARMUP · events file missing]` · **không có ⭐-PRE block** · APR không có star routing → APR chỉ xuất hiện trong khối `KHO` (không phải `⏸ WATCH-PX-PENDING`).
- Lần ④ (post-ledger): body đầy đủ ⭐-PRE + WATCH-PX-PENDING routing.

**p21/p22 dựng body lần ① thay lần ④** → chấm bằng chứng chưa có → FAIL/N/A → GRADER trả điểm sai.

### Gãy #2: verdict gate không phân biệt FAIL vs N/A

`master_preview_send.py:322-325`:
```python
if chưa_thi:    verdict = "CHƯA-THI"
elif n_full == 6 and n_sent == 6 and pin_result == "PASS" and not unknown_sentinels:
                verdict = "KHÔNG-KÍCH"
else:           verdict = "KÍCH"
```

- `pin_result` chỉ có 3 giá trị: `"PASS"` · `"FAIL"` · `"ERR:..."`. Không có `"N/A"`.
- Pin N/A (thiếu chủ thể để chấm) rơi cùng nhánh với pin FAIL (chủ thể có nhưng sai) → cả 2 → KÍCH. Sai về semantic: N/A nghĩa "chưa đủ dữ kiện để chấm", phải trả `CHƯA-THI` chờ tự-fix.

### Gãy #3: exit-code nuốt lý do

L286-296 subprocess `capture_output=True` · `stdout/stderr` không được `_log()` vào `master_preview.log`. Chỉ `pin_result` (3-value) vào verdict-file. Detail per-pin lưu duy nhất `data/logs/harness_sabotage.log` (append). Điều tra pin nào rớt = phải grep file khác — mất nửa ngày đêm 11/09.

### Gãy #4: LEDGER_DIR ghim REPO/data/logs/event_ledger

`digest_summary_v2.py:27` `LEDGER_DIR = REPO / "data/logs/event_ledger"` const.
`build_v2_digest(target: str)` KHÔNG nhận `ledger_dir` param.
`ledger_backfill_30d_v3_5.py` argparse chỉ có `--target` và `--window` — KHÔNG có `--out/--dir`.
Kết quả: pin-scan không thể tách sandbox/prod ledger để test pre-run.

## Cổng mới (GATE-D)

### D1 · Pin-scan chỉ chạy tập PRE-LEDGER trong compute_verdict

Thay `subprocess.run([harness_p20_p22, --target target])` bằng:
```python
subprocess.run([harness_p20_p22, --target target, --only pre-ledger])
```
- Pre-ledger pins hiện tại: **p20** (test pure `_hedge_line("")` unit · không depend body/ledger)
- Post-ledger pins: **p21 · p22** (cần ⭐-PRE block + WATCH routing từ events)

Harness thêm arg `--only {pre-ledger|post-ledger|all}` (default `all` cho di-sản offline).

### D2 · Enum verdict thêm nhánh N/A

Verdict gate mới:
```python
if chưa_thi:                            verdict = "CHƯA-THI"
elif pin_result == "N/A":               verdict = "CHƯA-THI"   ← MỚI
elif n_full == 6 and n_sent == 6 and pin_result == "PASS" and not unknown_sentinels:
                                        verdict = "KHÔNG-KÍCH"
else:                                   verdict = "KÍCH"
```

Pin-scan subprocess:
```python
pin_result = "PASS" if rc == 0 else ("N/A" if rc == 2 else "FAIL")
```
Harness convention: exit 0=PASS · exit 1=FAIL · exit 2=N/A (thiếu chủ thể).

### D3 · Hậu-kiểm module (post-send)

Module mới `scripts/postcheck_gate_d.py`:
- Trigger: sau `send_telegram` success (step ⑦).
- Đọc: artifact ĐÃ GỬI trên đĩa (`master_concat_<target>.txt` · `tg_final_*.jsonl` sidecars).
- Chạy: p21 + p22 (post-ledger pins) trên body ĐÃ SEND (không rebuild).
- Kết quả:
  - PASS → ghi `postcheck_ok=true` vào `preview_journal.jsonl` entry cùng target.
  - FAIL → ghi `postcheck_ok=false` + cờ `[POSTCHECK-FAIL <pin_id>]` trong journal + log.

### D4 · standing_ok thêm vế postcheck_ok

`check_standing()` cập nhật:
```python
def check_standing() -> tuple[bool, str]:
    ...
    v = json.loads(VERDICT.read_text())
    if v.get("verdict") != "KHÔNG-KÍCH": return False, ...
    # ... existing checks ...
    # D4 · NEW: check postcheck_ok từ preview_journal (đêm trước target)
    if not _postcheck_ok_for_previous_target(target): return False, "[N/A-ERROR:POSTCHECK-FAIL]"
    return True, ...
```

### D5 · NIGHT-COUNTER chỉ tăng khi postcheck_ok=true

`main()` L436-446 counter logic thêm filter:
```python
distinct_targets = set()
for line in PREVIEW_JOURNAL.read_text().splitlines():
    e = json.loads(line)
    if e.get("standing_ok") and e.get("postcheck_ok") and e.get("target_date", "") >= PREVIEW_EPOCH:
        distinct_targets.add(e["target_date"])
```

### D6 · Header run in

`_log()` line đầu mỗi run:
```
─── master_preview_send V3.5s pipeline start · spec_version=V3.5s · amendments_applied=[GATE-D] ───
```

### D7 · Sửa nhãn p20

Disan text `09-08 watchlist artifact missing (V3.5i Path bug)` → `pre-ledger sidecar-missing unit (V3.5i Path bug fix, no target)`. Assertion KHÔNG đổi.

### D8 · Log stdout+stderr harness

`compute_night_verdict` L286-296:
```python
r = subprocess.run([...], capture_output=True, text=True, timeout=60)
_log(f"[PIN-SCAN stdout]\n{r.stdout}")
_log(f"[PIN-SCAN stderr]\n{r.stderr}") if r.stderr else None
pin_result = "PASS" if r.returncode == 0 else ("N/A" if r.returncode == 2 else "FAIL")
```

## Pin p59-p63 (đen-một-lần local)

- **p59**: xoá events file trước cổng → p20 vẫn chấm PASS, log KHÔNG có dòng p21/p22 (compute_verdict pre-ledger chỉ chạy p20). Log có dòng p21/p22 = FAIL.
- **p60**: mutate 1 byte artifact ĐÃ GỬI (`master_concat_<target>.txt`) → p21/p22 postcheck đổi kết quả; mutate body pre-send (trước send) → KHÔNG đổi (postcheck đọc file trên đĩa).
- **p61**: ép 1 pin cổng trả N/A (rc=2) → verdict CHƯA-THI + chân đỏ đích danh `[PIN-N/A <pin_id>]`; ra KHÔNG-KÍCH = FAIL.
- **p62**: postcheck FAIL → journal có cờ `[POSTCHECK-FAIL <pin>]` · NIGHT-COUNTER KHÔNG tăng; tăng = FAIL.
- **p63**: ledger events file exists mà artifact ĐÃ GỬI thiếu khối ⭐-PRE = FAIL.

## md5 amendment file
_(computed at write time · in in báo cáo)_

## Rollback

Nếu GATE-D deploy fail:
- Restore `master_preview_send.py.bak_pre_gated_20260911` từ VPS backup (kỳ vọng md5=`576409bc772d17db290185858cf1245f`)
- SCP verify md5 khớp
- Test cú pháp: `python3 -c "import ast; ast.parse(open('scripts/master_preview_send.py').read())"`
- Cron 01:46 UTC 12/09 sẽ chạy bản pre-GATE-D (KÍCH nhiều đêm nữa nhưng an toàn)

## Nợ theo dõi sau master-live

- Re-pin fixture_master gộp p28/p38-p50/p59-p63 (deferred sau 13/09 · quyết định DEV lùi được)
- Ledger_backfill_30d_v3_5.py cần `--out` arg cho sandbox test (proposal riêng)
- Digest_summary_v2.py `build_v2_digest` nên nhận `ledger_dir` param cho isolation (proposal riêng)
