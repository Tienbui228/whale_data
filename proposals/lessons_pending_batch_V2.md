---
type: lessons-pending-batch
version: V2 (21/08/2026)
predecessor: proposals/lessons_pending_batch_20260818.md (V1 — L-52/L-53/L-54 + L-60/L-61 renumbered)
status: **[MERGED → sheet 21/08]** — L-55/L-56/L-57/L-58/L-59 đã insert vào LESSONS sheet CASE_INDEX.xlsx (rows 62-66) và regen lessons_learned.md
signed: L-55/L-56/L-57/L-58/L-59 operator ký chat 21/08/2026
merged_commit: sẽ commit sau paste evidence
---

# LESSONS PENDING BATCH V2 — 21/08/2026 [MERGED → sheet 21/08]

## §L-55 — Go-live ≠ verify

**Nguyên văn ANALYSIS (operator ký chat 21/08):**

> Deploy xong chưa phải xong — go-live chỉ đóng khi verify OUTPUT THẬT trên production (file sinh, đúng schema, đúng giờ cron).
>
> Evidence: phase_tag CSV F1 code-đúng-file-không-sinh 3 ngày · save_snapshot fail-câm · 🎓 sống lần đầu chỉ sau verify 20/08.

## §L-56 — Merge-before-gate

**Nguyên văn ANALYSIS (operator ký chat 21/08):**

> Amendment ký chat phải merge canonical + paste diff TRƯỚC gate/backfill; mọi run gate in `spec_version` + `amendments_applied`; dòng "ĐÃ KÝ" trong sổ phải trỏ được về chat-ký, không trỏ được = CHỜ-KÝ.
>
> Evidence: 6 relay-loss/tuần — L-48 số hiệu · GUA contract · E-R4b ≥-drift · handover ký-không-tồn-tại · lib đổi-nghĩa · va số 49/50.

## §L-57 — Schema-change-append

**Nguyên văn ANALYSIS (operator ký chat 21/08):**

> Thay đổi schema = append-only + changelog + không đè cột cũ; cột đổi nghĩa phải ĐỔI TÊN.
>
> Evidence: cols 51-52 v2.1 · ep_len/struct_n · vol_spot/vol_alpha.

## §L-59 — Ký-không-bằng-chứng = chưa-xong

**Nguyên văn bản P0-audit (operator ký chat 21/08):**

> Lệnh ghi-sổ đã ký đóng bằng paste bằng-chứng-sau-ghi CÙNG chuyến; không bằng chứng = việc chưa tồn tại, CHẶN bước phụ thuộc; sổ hai nhà khai nguồn/view, view chết >3d khi nguồn sống = alert.
>
> Evidence #1: batch V1 ký 20/08, 3 lần đòi không bằng chứng, operator tự phát hiện md chết từ 07/08.
>
> Evidence #2: root-cause "hiểu-nhầm-nhà" 21/08.

## Ghi chú ánh xạ

- spot-collect + watchlist-timing (đề xuất DEV 20/08) — **nuốt bởi L-52 và §5.11+L-59, không cấp ID riêng**.

---

## §A.1 — L-58: Conformance fixture — pin output MỌI consumer, không-pass-không-merge

**Title:** L-58 Conformance fixture doctrine — spec drift là bug, silent semantic change là án cứng

**Nguyên văn (bản ANALYSIS viết, operator ký chat 21/08):**

> Conformance fixture pin output MỌI consumer, không-pass-không-merge, đổi ngữ nghĩa = amendment ký riêng, fixture chạy trong mọi gate run.

**Diễn giải operational:**

1. **Fixture pin output MỌI consumer:** Mỗi consumer (watchlist, registry, phase_tag, gom_scan, downstream analyzers) phải có fixture file (`tests/fixtures/<consumer>_conformance_<YYYYMMDD>.json`) pin OUTPUT actual (events / episodes / labels / metric values) trên một data snapshot cụ thể (freshwatch csv với md5 lock).

2. **Không-pass-không-merge:** CI/pre-commit hook check fixture — bất kỳ commit đụng lib/scanner/probe/scripts consumer path mà fixture FAIL → block merge/push. Không có exception.

3. **Đổi ngữ nghĩa = amendment ký riêng:** Nếu spec logic thực sự cần đổi (e.g., struct_n definition, drift threshold), phải:
   - Ký amendment spec file (§E-R hoặc equivalent) — nguyên văn text
   - Regenerate fixture với semantics mới
   - Update fixture file trong cùng commit với code change
   - Bump fixture version

4. **Fixture chạy trong mọi gate run:** Backfill/gate scripts (`_probe_registry_backfill_*.py`, `_probe_watchlist_forensic_*.py`, gate acceptance runs) phải load + verify fixture md5+content TRƯỚC compute — mismatch = STOP, không chạy gate.

**Rationale (L-53/L-54/L-58 chain):**

- L-53: điểm mù structural (registry vá) — nếu ngữ nghĩa metric drift silent, cả tầng vá bị lệch, blind spot resurfaces bằng dạng khác.
- L-54: signal quality = signal × confirmation-chain. Silent drift = confirmation chain gãy → intel → entry mapping sai.
- L-58: chống drift bằng compile-time contract (fixture) chứ không rely runtime alert. Prior incidents:
  - E-R7 turn 1-4 (20/08-21/08): struct_n dual-definition lệch (count vs ep_len) — 4 ca (HEMI+2 · ON+2 · GUA+2 · CARV+3) khi episode có gap-days. Baseline 25.9% ae5f2a0 dùng semantics khác lib 5c2f22d → 5 tokens REMOVED / 10 ADDED unexplained cho đến khi regress-3 mapping A-G.
  - E-R7c cutover 1.10 → 1.15 r2 (17/08 relay): text ký nhưng code chưa update → mâu thuẫn 3 lần tuần.
  - P0 watchlist SAFE (2ba669f): bit-equal đảm bảo nhờ chưa refactor watchlist inline; nếu refactor mà không fixture → drift silent immediately.

**Ref case studies:**
- E-R7e regress-3 A-G mapping (`_probe_e_r7e_regress3_20260821.py`) — 5 tokens dispatch to code drift causes
- P0 CHECK watchlist inline vs lib (`_probe_e_r7e_regress2_20260821.py`) — verify pattern
- Struct_n dual-def HEMI/ON/GUA/CARV (regress-3 §2) — count vs ep_len discrepancy

**Deliverables L-58 kickoff (phase-2 acceptance):**

1. **Fixture file schema (draft):**
   ```json
   {
     "consumer": "registry|watchlist|phase_tag|...",
     "spec_version": "<canonical version string>",
     "spec_commit": "<sha short>",
     "data_snapshot_md5": {"freshwatch_daily_2026-06.csv": "<md5>", ...},
     "config": {<all thresholds>},
     "tokens": {"HEMIUSDT": {"episodes": [...], "events": [...], "sn_ae5": ..., "sn_lib": ..., ...}}
   }
   ```

2. **Fixture test runner:** `tests/test_<consumer>_conformance.py`
   - Load fixture
   - Verify data snapshot md5 (fail if data drift)
   - Run current consumer code on pinned data
   - Assert output matches pinned
   - FAIL → block CI

3. **Fixture initial batch (L-58 kickoff, chờ ANALYSIS chốt semantics per Q1-Q3 regress-3):**
   - Registry: HEMI / ON / GUA / CARV / ARIA (5 tokens covering all A-G cases)
   - Watchlist: same 5 + STBL + TRIA (validation coverage)
   - Phase_tag: fw-139 pinned stage per token (from `phase_tag_daily.csv` 08-19 first canonical)

4. **Fixture governance:**
   - Fixture file COMMITTED (not scratch) trong `tests/fixtures/`
   - Update = separate commit ký amendment
   - Diff must show fixture change + spec amendment cùng commit
   - Pre-commit hook block if fixture updated without spec amendment ref

**Timeline:**
- **21/08 (nay):** L-58 append lessons_pending_batch_V2 — ky.
- **After ANALYSIS Q1-Q3 chốt struct_n/luật tiền-extract semantics:**
  - Agent generate fixture initial values
  - Operator ký fixture
  - Add pre-commit hook + CI script
- **Before phase-2 cron 08:25:** fixture PASS mandatory.

**Ref:**
- `proposals/unhedge_registry_spec.md` v1.2-FINAL+doctrine-pack+conformance-pack (§E-R1 canonical struct_n)
- `proposals/hedge_watchlist_spec.md` §3 (consumer split canonical)
- `_probe_e_r7e_regress3_20260821.py` (evidence code-drift explains 4/5 tokens)
- E-R7d/E-R7e turn series (17-21/08) — drift incidents that motivated L-58

---

## Deliver

**Sync `CASE_INDEX.xlsx` LESSONS sheet:** operator apply per CLAUDE.md workflow — thêm row L-58 với title + one-liner + ref. Sau apply → `_task_gen_case_state_map_20260818.py` regen `case_state_map.md` + SCP VPS (per PHASE-TAG workflow).

**File này (V2) tiếp tục sử ký cho lessons L-59+ sau.**
