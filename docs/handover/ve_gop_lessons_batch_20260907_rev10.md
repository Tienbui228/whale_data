# VÉ GỘP LESSONS · REV10 · KÝ 08/09 GATE-4 V3.5g · sanitize gloss-sort

**Trạng thái:** REV10 · bản REV9 `4e222a6a055591b5203548c937a0de56` **SUPERSEDED** vì grep còn DÍNH cụm "mới nhất" (line 45) + "sorted ... DESC" (line 51) — cả hai là gloss-sort. REV10 = sanitized · verbatim "top-3 đóng góp" + impl-note.

**Updates so với REV9:**
- **SANITIZE gloss-sort:** thay "top-3 PRE mới-nhất-trước" → **"top-3 đóng góp"** verbatim
- **IMPL-NOTE inline:** `[dải-a = star_birth DESC · dải-b = last-signal ASC · per p14-run]` gán trực tiếp chỗ output pin p14
- **STAR_BIRTH DEFINITION chính xác** vào code-comment + harness-doc (fixture-example bảng 7 dòng)
- **SWEEP-SANDBOX L-76 one-line confirm**
- **MORNING 08/09 verdict đích danh** (đêm-0 · 6/6 · ledger · DEMO-5)

---

## 1-3. L-78/L-79/án-lệ-✓-suy · không đổi

## 4. §B AMENDMENT v1.8 (REV10)

Cộng dồn V3.1-V3.5f + V3.5g:

- (v1.7 giữ nguyên · tất cả rules)
- **V3.5g SANITIZE (REV10):** language "top-3 mới nhất" thay = "top-3 đóng góp" + impl-note verbatim. Gloss-sort ("sorted X DESC" as bare claim) → replaced by impl-note bracket citing sort key.
- **STAR_BIRTH def formal (V3.5g):**
  > **star_birth(token) := min{ d : |{ trục có event ≤ d }| ≥ 2 }**
  Ngày trục-thứ-hai tới. Different from first-seed (earliest event of any axis).

## 5. Pin p14 DẢI-KÉP (V3.5g sanitized)

**Chân-a:** `n_PRE ∈ [4,6]` · vi phạm → in `[STAR-ANOMALY dải-a n=X] top-3 đóng góp [dải-a=star_birth DESC · per p14-run]: [...]`
**Chân-b:** `n_treo ≤ 15 ∧ coverage-sạch` · vi phạm → in `[STAR-ANOMALY dải-b n_treo=Y] top-3 đóng góp [dải-b=last-signal ASC · per p14-run]: [...]`
**Caveat:** coverage thủng → CAVEAT "án-ở-ống" (không phải án-chợ)

## 6. ⭐-01 COLLECT · unchanged (POST-DUMP · ret-40.0%)

## 7. §E ROUTING · unchanged

---

## STAR_BIRTH DEFINITION (V3.5g · code-comment + harness-doc verbatim)

```
star_birth(token) := min{ d : |{ trục có event ≤ d }| ≥ 2 }
→ Ngày trục-thứ-hai tới · KHÔNG dùng first-seed
```

**Wired vào:**
- `tests/harness/harness_digest_summary.py` docstring (V3.5g)
- `tests/harness/harness_digest_summary.py` `_p14_dai_kep()` inline comment

**FIXTURE-EXAMPLE (giữ · target=2026-09-06):**

| # | sym | first_seed (fs) | star_birth (sb) |
|:-:|---|---|---|
| 1 | GIGGLE | 08-31 | **09-06** |
| 2 | AIOT | 08-30 | **09-06** |
| 3 | 龙虾 | 09-02 | 09-05 |
| 4 | ESPORTS | 09-02 | 09-03 |
| 5 | AIA | 08-29 | 09-03 |
| 6 | AGT | 08-30 | 09-03 |
| 7 | B2 | 08-31 | 09-02 |

**p14-run V3.5g output (verbatim after sanitize):**
```
top-3 đóng góp [dải-a=star_birth DESC · per p14-run]:
  [('GIGGLE','2026-08-31','2026-09-06'), ('AIOT','2026-08-30','2026-09-06'), ('龙虾','2026-09-02','2026-09-05')]
top-3 đóng góp [dải-b=last-signal ASC · per p14-run]:
  [('TRIA','2026-08-31'), ('B2','2026-09-02'), ('AIA','2026-09-03')]
```

---

## WL-ÁN-LỆ VERBATIM (giữ từ REV9)

> **"18≡18 đối-chứng-hai-nguồn · 44-unique · List-B[23,44]avg34.6 · thác 157→16 · thay vĩnh viễn mọi trích tiền-REV4"**

---

## SWEEP-SANDBOX L-76 CONFIRM (V3.5g one-line)

`tests/harness/harness_full_sabotage_sweep.py` · 17 mutate functions operate on **in-memory Python copies** (list-comprehension `[f for f in flags if not ...]`, dict cloning via `json.loads(json.dumps(sr))`) · **zero write to prod files**. Chỉ append vào audit log `data/logs/harness_sabotage.log` (L-76 sandbox-compliant · cửa cron 01:02 không chạm prod).

Grep verify: chỉ 1 write call `LOG.open("a")` (audit log append) · KHÔNG `write_text`, `write_bytes`, `os.replace`, `shutil.copy`, `subprocess` chạm prod.

---

## LABEL-CLAIMS-LINT (giữ từ REV9 · V3.5f wire)

Script `label_claims_lint.py` md5 `ca45943794a677179ab377963f1ccd15` · tuyển-dụng PASS · text vé tuần sau.

---

## DOS-PACKAGE (giữ từ REV9)

Doc md5 `e5816b17f6880857169cf6193d144919` · ghế 27/09. BEAT/ONE/B đếm tiếp.

---

## HARNESS-LOG (giữ từ REV9)

17 dòng canonical 4-field · 16 FAIL-PIN + 1 VÔ-HẠI intended.

---

## MORNING 08/09 · THỨ TỰ THIÊNG · VERDICT ĐÍCH DANH

**Timestamp verdict:** 2026-09-08T01:22 UTC (còn quá sớm cho toàn bộ chain).

**(a) ĐÊM-0 KÍCH/KHÔNG-KÍCH đích danh:**
- ✅ **PARTIAL-KÍCH:** `tg_relay_gom_h` fired for target 2026-09-07 · sender-dump ghi `data/artifacts/tg_final_tg_relay_gom_h_2026-09-07.txt` size 4249B, `.jsonl` 3229B (mtime 08/09 01:20 UTC)
- ⏳ **CHỜ:** `fresh_digest`, `exch_digest`, `watchlist_cron` chưa fire cho 09-07 (không tìm thấy 2026-09-07 marker trong digest_daily_vps.log / watchlist_cron.log tại 01:22 UTC)
- Nhánh (a) 3-vế (thước-sạch ∧ số-cũ-re-measure ∧ MỘT-ĐÊM-không-kích): 
  - ✅ thước-sạch (V3.5b/c/d/e/f/g layered)
  - ✅ số-cũ-re-measure (ledger md5 dd9e83f0 preserved)
  - ⏳ MỘT-ĐÊM-không-kích: **chưa đủ đêm** (đêm-0 mới partial-kích) → **nhánh (a) chưa closed**

**(b) 6/6 tg_final as-sent 09-07 [PROVENANCE=as-sent] → posthoc RETIRE verdict:**
- **1/6 hiện có** tại 01:22 UTC:
  - ✓ `tg_relay_gom_h_2026-09-07` (mtime 01:20)
  - ✗ `fresh_digest_2026-09-07` (chưa fire · cron thường sau 01:30)
  - ✗ `exch_digest_2026-09-07` (chưa fire)
  - ✗ `watchlist_2026-09-07` (chưa fire)
  - ✗ `gom_daily_2026-09-07` (chưa fire)
  - ✗ `phase_map_2026-09-07` (chưa fire)
- **Posthoc RETIRE verdict:** **CHỜ** (cần 6/6 · hiện 1/6). Sau khi cron rest fire → tự động RETIRE candidate qualified.

**(c) Ledger rebuild 09-07 + harness full trên 09-07:**
- **CHỜ:** cần fresh/exch digest 09-07 (chưa có) + watchlist 09-07 (chưa có) trước khi rebuild ledger 09-07 có nghĩa
- Placeholder rebuild target=09-06 vẫn stable (dd9e83f0)

**(d) DEMO-5 SEND Daily channel:**
- **CHỜ (c) xong** · không SEND với ledger 09-06 stale (day-old)
- Khi 6/6 as-sent + ledger 09-07 rebuild + harness full pass → SEND với format:
  ```
  [STAR-ANOMALY dải-a n=<N>] top-3 đóng góp [dải-a=star_birth DESC · per p14-run]: ...
  🔻 XẢ-WATCH+XẢ (<n>) [câu-soi bộ XẢ]: ... [STICKY-XẢ vì 🔴-<DD/MM>] ...
  ⭐-PRE (<n>): ...
  POST-DUMP+🌊 (<n>): ...
  [NGOÀI-SỔ: 09-07: <tokens>] + DOS counter update
  coverage MỘT vector {fresh X · kho Y · perp Z}/31
  ━━ footer ━━ concat-seal=<hex>
  ```

**(e) "ok preview" xin:** **CHỜ (a)-(d) xong**. Hiện tại: 1/6 dumps · cron 5 slot còn chờ · không thể trình DEMO-5 với data half-fired.

**Recommendation:** kiểm tra lại sau ~02:00-03:00 UTC khi digest/watchlist cron thường fire cho target 09-07.

---

## V3.5g NUMBERS (target=09-06 · unchanged from V3.5f)

**COVERAGE:** PERP=19/31 · KHO=9/31 · FRESH=6/31 (MỘT vector).

**BỘ-BA:** treo=20 · mới=5⊆treo.

**Direction 3-tầng:**
- ⭐-PRE (7): AGT · AIA · AIOT · B2 · ESPORTS · GIGGLE · 龙虾 · **top-3 đóng góp [dải-a=star_birth DESC]: GIGGLE·AIOT·龙虾**
- 🔻 XẢ-WATCH (2): MITO · CYS [STICKY-XẢ vì 🔴-02/09]
- POST-DUMP+🌊 (11): BULLA · 4 · UAI · AKE · BTR · CLO · COLLECT · HANA · RIVER · TRIA · TUT

**NGOÀI-SỔ counter (30d window):** DOS 3× → ĐỀ-CỬ-UNIVERSE 27/09 · ONE 2× · BEAT 1× · B 1×.

---

## md5 chuỗi (V3.5g · REV10)

| File | md5 |
|---|---|
| `scripts/ledger_backfill_30d_v3_5.py` | a0b8132e86ad9e86639a033bfb24d716 |
| `scripts/watchlist_daily.py` (L-66 sentinel) | 6f7189c618f85fbd7a04c3392eebefb2 |
| `scripts/digest_summary_v2.py` | b79300462c540c70269ea34a15479340 |
| `tests/harness/harness_full_sabotage_sweep.py` | a30fc5e8a89a3fbb4500044124e8a9dd |
| `tests/harness/harness_digest_summary.py` (V3.5g sanitize · star_birth def) | **bef708081c198dbe5a9748dafbb43641** |
| `tests/harness/harness_p16_p17_direction.py` | 630d73d898abfe44fc8b34926337e5ae |
| `tests/harness/label_claims_lint.py` | ca45943794a677179ab377963f1ccd15 |
| `data/config/axis_map.yaml` | 0597734a111641915d4eccb642fc8348 |
| `events_2026-09-06.jsonl` | **dd9e83f0b9af5d475aa6dc043f3b6e98** (L-59) |
| `stars_2026-09-06.jsonl` | ade90907ec2e0e840e148d54e747cf92 |
| `star_grades.jsonl` | 421c8430342aea37bf35edab651708b1 |
| `docs/handover/dos_package_20260907.md` | e5816b17f6880857169cf6193d144919 |
| `ve_gop_lessons_batch_20260907_rev10.md` | (this file · md5 sau write) |

## Chờ chữ Tiên

REV10 = SANITIZED · REV9 `4e222a6a` **SUPERSEDED** vì grep còn DÍNH gloss-sort.

**Sạch language check REV10:**
- Không còn "top-3 PRE mới nhất" (thay = "top-3 đóng góp")
- Không còn "sorted X DESC" as bare claim (thay = impl-note bracket `[dải-a=star_birth DESC · per p14-run]`)
- Star_birth def formal wired code-comment + doc + fixture-example

**Morning 08/09 verdict:** 1/6 as-sent hiện có · 5 slot chờ cron · DEMO-5 SEND & ok-preview đều CHỜ 6/6 hoàn tất.

**Chờ Tiên "khớp REV10 <md5>".** Bổ nhật kiểm lại morning tasks sau 02:00-03:00 UTC.
