# SCP-BATCH REVISED · sau đêm-3 freeze (2026-08-29 01:45 UTC)

**Trigger:** ANALYSIS verdict 01/09 rút h4_flow + runner-integration H4 khỏi scope. Scope còn 3 file.
**Status:** DỪNG-PASTE-trước-SCP — plan đăng ký, operator ky trước khi thi hành.

## Rút khỏi scope (per H4-CLOSED verdict 01/09)

- ~~`lib/h4_flow.py`~~ → giữ LOCAL dormant (header note "no consumer — H4 closed; N2-interface reusable")
- ~~`scripts/gom_h_daily.py` runner-integration H4 lane render~~ → CANCELLED (chưa từng wire)
- ~~`h4_bot_cycle.py` (bot repo)~~ → CANCELLED (chưa từng tạo)

## Scope còn lại: 3 file

| # | file | mô tả | LOCAL sha ref |
|---|---|---|---|
| 1 | `scripts/adapter_h1_nansen.py` | 3d-best canonical `_kho_step_3d_best()` · conformance 4/4 PASS (XAN 10.10% · BTR 12.02% · TUT 4.58% · CAP 29.24%) | commit đã sẵn LOCAL |
| 2 | `screen_thresholds.yaml` | drift đầy đủ: h4-CLOSED (status/close_reason/evidence_md5) · walletset_2x2 · tripwire_e2 v2 census_generations block · review_bundle_20260927 reshape (5+3+1) | commit `26d0ab9` + H4-CLOSED commit này |
| 3 | `lib/tripwire_e2_v2.py` | REAL-RUN PASS (Resolution b): rate=0.4277 ≈ 0.428 [TRIP] · exposure_days_declared từ yaml single-source · grades-v4 md5 8fdd0a74 · SELF-CHECK KÉP | commit LOCAL đã sẵn |

## Thứ tự SCP (DỪNG-PASTE-trước-SCP mỗi bước)

1. **Chuẩn bị VPS-side:** SSH root@5.223.67.21 → `mkdir -p /root/Data_back_test/whale_data/lib` (nếu chưa có) → xác nhận `data/logs/gom_h_daily.log` bằng md5 pre-SCP.
2. **SCP file 1** `scripts/adapter_h1_nansen.py` → verify md5 khớp local · restart chạy dry cron test 1 lần → so sánh output vs pre-SCP.
3. **SCP file 2** `screen_thresholds.yaml` → verify md5 · cron test 1 lần → coverage/fire count không lệch phi tự nhiên.
4. **SCP file 3** `lib/tripwire_e2_v2.py` → verify md5 · smoke test đọc grades-v4 8fdd0a74 → in trailing dòng `tripwire FP-rate=0.428 [TRIP]` cạnh Telegram block.
5. **SCP kèm** `docs/case_files/census_63_grades/census_grades_v4_FULL85_20260831.csv` → md5 KHỚP 8fdd0a74.

## Verification checklist sau SCP

- [ ] md5 3 file khớp local vs VPS
- [ ] Cron 01:45 UTC 30/08 target=08-29 fires clean → coverage OK, ramp lane hoạt động
- [ ] Tripwire trailing dòng emit từ chính cron (không LOCAL-simulated)
- [ ] `yaml goi_nhe.h4.status="CLOSED-BY-PRINCIPLE-20260901"` VPS load → không có `dom` / `dom_rise_pp` / etc.
- [ ] `phase_tag` cron 01:30 UTC không lỗi (yaml đọc được)

## Rollback plan (nếu 1 trong 3 file gây lỗi)

- Backup VPS-side pre-SCP: `cp scripts/adapter_h1_nansen.py{,.bak_20260829}`; `cp screen_thresholds.yaml{,.bak_20260829}`; `cp lib/tripwire_e2_v2.py{,.bak_20260829}` (nếu tồn tại).
- Rollback = `mv .bak_20260829 → gốc`, restart cron manually.

## Không SCP (giữ LOCAL)

- `lib/h4_flow.py` [DORMANT — H4 closed, no consumer, N2-interface reusable]
- `scripts/archive/_task_survey_v2_reparse_20260827.py` (probe archived, evidence sống trong CSV)
- `docs/reports/survey_dom_level_nansen_v2_20260827.csv` (LOCAL evidence exhibit)
- `data/ref/cex_addresses_bsc.txt` (gitignored runtime — canonical đã ở docs/reference/)
- `data/state/nansen_raw_survey/*.json` (33 raw · evidence exhibit)

## Ref

- ANALYSIS verdict: [DEV → AGENT · H4-CLOSED merge 01/09]
- Đêm-2 C report: [dem2_c_report_20260828.md](dem2_c_report_20260828.md)
- gom_detect_spec changelog: H4V1-CLOSED-20260901 · V3-CLOSED-20260831 · E2-METRIC-B-20260831
