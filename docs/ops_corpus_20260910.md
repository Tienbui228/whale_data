# OPS-CORPUS · V3.5r · KÝ 2026-09-10

**V3.5r directive item 5+8 · E8 relay-gap close + LINT #6 CITE-TYPE-MATCH wired**

## OPS-CORPUS (án lệ vận hành ANALYSIS)

### E1 · phantom-grep (V3.5j · 07/09)
> Bịa blocker vì grep sai file. Ví dụ: grep `TG_CHAT_ID_DAILY .env = 0` mà không grep `/root/.env_tg` (nơi thật · chmod 600).
Root: sai path/file khi verify claim.
Fix: grep multiple candidate paths trước khi tuyên missing.

### E2 · catchup-no-bell (V3.5m · 09/09)
> CATCH-UP script chạy đúng nhưng output stdout không append log file. `[SENT] phase_map ok=True` sinh ra trong shell mà phase_tag.log không có → verdict grep miss.
Fix: CATCH-UP phải append log target hoặc call log_bell() populate bell_journal.

### E3 · chờ-chữ-người deadlock (V3.5n · 07/09)
> Chờ operator ký spec (registry def) blocks downstream (subtag revive). Deadlock ×N ngày.
Cặp deadlock #1 với E4 (chờ-phiên-máy).
Fix: cite bằng-chứng-tường (E5) → operator xử nhanh hơn văn vô cứ.

### E4 · chờ-phiên-máy deadlock (V3.5n · 09/09)
> Code local wired nhưng chờ cron cycle (24h gap) mới có runtime evidence. Đêm N deploy · đêm N+1 mới verify.
Cặp deadlock #1 với E3.
Fix: post-commit auto-SCP + first-cron mtime-verify + first-cron trigger manual nếu cấp bách.

### E5 · chờ-operator no-cite (V3.5m)
> Blocker-shift "chờ operator" mà không cite bằng-chứng-tường {lệnh/path · hit/miss}.
Ví dụ SAI: "chờ operator xác định 'registry'".
Ví dụ ĐÚNG: "chờ operator · evidence: grep LIST-A hedge_watchlist_09-08.json AIO=miss GIGGLE=miss".
Luật-con: "Mọi mục 'Chờ operator' PHẢI cite bằng-chứng-tường {lệnh/path · hit/miss}"

### E6 · claim-wired-vs-cron (V3.5o · 09/09)
> Code wired local ≠ VPS runtime. Operator hỏi "wired chưa?" · agent "yes" mà cron log vắng runtime evidence.
Bằng chứng V3.5o: gom_daily/phase_map/watchlist log_bell wired 09-09 sáng · bell_journal empty from cron.
Fix: DEPLOY-ORDER PROOF · md5 VPS↔local + first-cron runtime-verify.

### E7 · deploy-lag pair (V3.5o · cặp cùng E6)
> Fix commit local · SCP done · but cron mới chạy sau · gap 24h. Claim "deployed" đêm N là ✓-suy vì runtime evidence chưa có tới đêm N+1.
Fix: chờ cron cycle · KHÔNG tuyên PASS đêm N.

### E8 · relay-gap cite-type (V3.5r · 10/09) — **CLOSED**
> ANALYSIS relay cite `[per pX]` mà không đóng cửa kiểm-loài · mutate cross-loài lọt xuống render:
> ví dụ claim về pointer-integrity cite `[per p22]` (đúng loài) · người relay đổi sang `[per p7]` (seal-integrity)
> mà render không cản → dấu-lạc-loài lọt.
Root: seal-registry chỉ mang id, không mang loài · lint không biết ép match.
Fix (V3.5r item 5):
  1. `data/state/seal_registry.json` MANG LOÀI: seals[pin].loai + loai_index + claim_loai_hints
  2. `tests/harness/label_claims_lint.py` thêm `_check_cite_type_match()` = LINT #6
  3. `tests/harness/harness_cite_type_match_mutate.py` mutate `[per p22]`↔`[per p7]` PHẢI FAIL
Verify PASS 4/4 case (10-09 UTC).

## LINT-CORPUS (tests/harness/label_claims_lint.py · nội bộ lint văn bản)

- #1 pointer-integrity OK mồ côi
- #2 5/5 WIRED ✅ không biên lai
- #2b claim-✅-giả toàn phần (watchlist wire 0 dump_as_sent)
- #3 grep-sai-file phantom-blocker (link OPS E1)
- #4 chờ-operator no-cite blocker-shift (link OPS E5)
- #5 BEAT-sai-loài (V3.5o): counter cite từ nansen_snapshots (SAI LOÀI = raw input) thay vì as-sent artifact (ĐÚNG LOÀI).
- **#6 CITE-TYPE-MATCH (V3.5r NEW · link OPS E8)**: claim cite `[per pX]` nhưng pX.loài ≠ claim.loài (inferred from hints regex) → FAIL.

## Renumber note

**HAI SỔ KHÔNG GIẪM SỐ:** LINT dùng #1-#6. OPS dùng E1-E8. Read context để biết corpus.

## Kỷ nguyên artifact

Kể từ V3.5o: `nansen_snapshots` = RAW = VOID cho mọi mục counter. Chỉ artifact `[SENT]` (tg_final_*.txt + bell_journal) là hợp lệ.
