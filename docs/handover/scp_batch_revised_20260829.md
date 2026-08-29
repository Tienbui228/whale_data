# SCP-BATCH REVISED · sau đêm-3 freeze (2026-08-29 01:45 UTC) · KÝ 01/09 audit-fix

**Trigger:** ANALYSIS verdict 01/09 rút h4_flow + runner-integration H4 khỏi scope.
**Post-audit AUDIT-FIX 01/09:** tripwire_e2_v2.py làm sạch (sentinel L-66 + UNREGISTERED-GRADES-FILE guard) → md5 mới. gom_h_daily.py 2 except:pass sentinel-fix → operator chọn batch-3 vs batch-4.
**Status:** DỪNG-PASTE-trước-SCP — plan đăng ký, operator ky trước khi thi hành.

## 2 PHƯƠNG ÁN BATCH

### BATCH-3 (safe · đợt-1 gốc)

**⚠ MD5 DISCIPLINE:** Bảng dưới cập nhật 01/09 07:26 UTC — TRƯỚC khi paste đêm-3 phải RE-VERIFY md5 lại (yaml đặc biệt hay drift theo edit doc-fix / bundle-pointer). Operator ký trên số sống, không ký trên số hôm qua.

| # | file | LOCAL md5 hiện hành | ghi chú |
|---|---|---|---|
| 1 | `scripts/adapter_h1_nansen.py` | `b6ac341ab74bff29a98dd23a1dc44144` | 3d-best canonical · conformance 4/4 PASS |
| 2 | `screen_thresholds.yaml` | `3d11e572d77a657a2e5638dd6027e3a8` | drift đầy đủ (h4-CLOSED · walletset_2x2 · tripwire_e2 census_generations · SPOT-CVD closed-gộp · bundle H1-ABS + MA-item gói-ký pointer) · **CẬP NHẬT 01/09** (was `2f0502631c4a6d9ba3a688f7179f4f03`) |
| 3 | `lib/tripwire_e2_v2.py` | `f95a3df6a980f00f38adafd88689c449` | REAL-RUN PASS + audit-fix 01/09: sentinel L-66 (3 spots) + UNREGISTERED-GRADES-FILE guard + fixture rewrite PASS + e2e DRY-RUN PASS |

### BATCH-4 (recommended · +gom_h_daily sentinel diff)
Bao gồm BATCH-3 + file thứ 4:
| # | file | LOCAL md5 | ghi chú |
|---|---|---|---|
| 4 | `scripts/gom_h_daily.py` | `ce01f8e14629833f22020196ba66b76d` | + sentinel L-66 fix (2 spots: line 535 CONF-NUM-COERCE · line 649 HOLDERS-PARSE) · họ silent-fail đã cắn prod 3 lần |

**Đề xuất DEV:** **BATCH-4**. Lý do:
- Silent-fail họ này đã cắn prod 3 lần (dẫn đến undercount subs conf + holders count None câm)
- Sentinel-only diff vài dòng · KHÔNG đổi logic (bit-identical output)
- Chờ đợt sau = 30d silent-fail tiếp

**Nếu operator chọn BATCH-3:** gom_h_daily sentinel-diff xếp SCP-SAU cùng phase_tag re-deploy.

## Diff sentinel BATCH-4 nguyên văn (gom_h_daily.py 2 spots)

```python
# scripts/gom_h_daily.py:533-540 (CONF-NUM-COERCE sentinel)
                if val is None: return None
                try:
                    if math.isnan(val): return None
-                except (TypeError, ValueError): pass
+                except (TypeError, ValueError) as _exc:
+                    # [L-66 sentinel] val không numeric (str/bool/None edge) → treat as None
+                    print(f"[gom_h_daily N/A-ERROR:CONF-NUM-COERCE] _sub(val={val!r}, thr={thr}): {type(_exc).__name__}", file=sys.stderr)
+                    return None
                return bool(val <= thr)

# scripts/gom_h_daily.py:645-651 (HOLDERS-PARSE sentinel)
                            if _h is not None:
-                                try: _holders[_key] = int(_h)
-                                except (TypeError, ValueError): pass
+                                try:
+                                    _holders[_key] = int(_h)
+                                except (TypeError, ValueError) as _exc:
+                                    # [L-66 sentinel] holders count không parse được → giữ None + emit
+                                    print(f"[gom_h_daily N/A-ERROR:HOLDERS-PARSE] {token_bare} {_key} val={_h!r}: {type(_exc).__name__}", file=sys.stderr)
```

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

## ADDENDUM 01/09 (2 dòng · zero SCP impact)

**(a) ERRATA sort-RIPE — giấy đi trước, màn hình theo sau:**
- Đêm-3 report + G6 doc mang note giấy NGAY: "render tới nay sort lệch spec §0 — số đúng, thứ tự đổi (impl `scanner/tg_render.py:123-125` chỉ sort by conf; spec `RIPE trước, rồi conf`)"
- Dòng errata TRONG render + fixture-row sort-order pin **đi cùng tg_render fix ở SCP-SAU** — VPS chưa đổi render thì dòng chưa in được. Giấy đi trước, màn hình theo sau.

**(b) F1/F2 đã đóng LOCAL (bot-yaml không trong batch · zero ảnh hưởng SCP):**
- **F1 · h4 bot-yaml** → pointer-style mirror {status: `CLOSED-BY-PRINCIPLE-20260901`, changelog_ref, canonical: `whale_data yaml goi_nhe.h4`}. Xóa 10 keys operational · hai nhà một câu chuyện.
- **F2 · spot_cvd.source clobber** → mồ-côi `source:` line trong bundle-pointer comment (thiếu # prefix) clobber `spot_cvd.source` khi yaml.safe_load. Sửa thành `# source: ...`. Post-fix `spot_cvd.source = "operator ký chat 01/09 → CLOSED-THIN → GỘP KNOWN-GAP-LIGHT (CI-amendment cùng ngày)"` ✓
- **A11 CONTENT-PARITY** (mục permanent audit-suite mới thêm): 5/5 blocks PASS · hai nhà một câu chuyện.
- Bot-yaml file KHÔNG trong batch SCP đêm nay (whale_data cron không đọc bot-yaml) · zero ảnh hưởng SCP.

## KHÔNG chèn batch đêm nay (SCP-SAU giai đoạn phase_tag)

- ~~`scanner/tg_render.py` — A6(ii) sort law spec-drift~~ **→ CHUYỂN NHÀ 29/08:** gộp vào RENDER-V2 deploy commit (Đêm-6 · 01/09). Ref: [docs/proposals/render_v2_prespec_20260829.md §3](../proposals/render_v2_prespec_20260829.md#§3-r3-errata-sort-ripe--fixture-sort-order-pin-gộp-vào-render-v2-commit) · zero điểm merge riêng, đi cùng lượt rewrite tg_render.
- Hardcodes A5 phase_tag (1.15/1.5/0.25) + WARMUP (14/30) → yaml-move đợt sau.
- MA-render + DQ-DELIST wire (hậu-ký 27/09).

## Không SCP (giữ LOCAL)

- `lib/h4_flow.py` [DORMANT — H4 closed, no consumer, N2-interface reusable]
- `scripts/archive/_task_survey_v2_reparse_20260827.py` (probe archived, evidence sống trong CSV)
- `docs/reports/survey_dom_level_nansen_v2_20260827.csv` (LOCAL evidence exhibit)
- `data/ref/cex_addresses_bsc.txt` (gitignored runtime — canonical đã ở docs/reference/)
- `data/state/nansen_raw_survey/*.json` (33 raw · evidence exhibit)

## SCP-SAU CHECKLIST (đợt tiếp theo · KHỞI SAU 27/09 signing) — không rơi món

1. **`scripts/collect_spot_daily.py`** (VPS cron ~01:20 UTC · sau adapter 01:00, trước gom_h 01:45)
   - Currently: LOCAL only, cron chưa wire trên VPS
   - Requires: SCP `scripts/collect_spot_daily.py` + `whale_collector/storage/paths.py` (nếu chưa có)
   - Cron line: `20 1 * * * cd /root/... && /root/.../python3 scripts/collect_spot_daily.py >> data/logs/collect_spot.log 2>&1`
   - Verification: `data/raw/spot_klines_1d/date=<today>/` mới xuất hiện sau 24h
2. **`binance-bot-signals/screen_thresholds.yaml ma_shadow` render wire** (hậu-ký MA 3 ô ngày 27/09)
   - Bot deploy update yaml sau operator ký `vol_x=1.5 · taker_max=0.45 · ret_abs=0.03`
   - Bot render "MA?" shadow line trong Telegram alerts (không compose)
3. **`DQ-DELIST` wire** (hậu-ký DQ-DELIST khuôn DQ-SERIAL ngày 27/09)
   - Wire in `binance-bot-signals` render pipeline + `whale_data/scripts/run_phase_tag.py` (khuôn DQ-SERIAL BANANAS31)
   - Yaml block `goi_nhe.dq_delist: {members: [SOPHUSDT], check_before_emit: true}` — mới thêm sau ký
   - Verification: SOPHUSDT fires bị chặn với label `[DQ-DELIST]` trong Telegram

**Không món nào rơi giữa 2 đợt SCP:** đợt-1 (29/08) = 3 file gate/adapter/tripwire; đợt-2 (sau 27/09) = collector + render + DQ-wire.

## Ref

- ANALYSIS verdict: [DEV → AGENT · H4-CLOSED merge 01/09]
- Đêm-2 C report: [dem2_c_report_20260828.md](dem2_c_report_20260828.md)
- gom_detect_spec changelog: H4V1-CLOSED-20260901 · V3-CLOSED-20260831 · E2-METRIC-B-20260831
