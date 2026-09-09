# OPS-CORPUS · V3.5n · KÝ 2026-09-09

**V3.5n directive item 5:** LINT-corpus (pointer-OK · 5/5-WIRED · ✅-giả) ≠ OPS-corpus. Hai sổ tách khỏi giẫm số.

## OPS-CORPUS (theo dấu ANALYSIS · án lệ vận hành)

### E1 · phantom-grep (V3.5j)
> Bịa blocker vì grep sai file. Ví dụ: `grep -c TG_CHAT_ID_DAILY .env = 0` → tuyên "env not set" mà không grep `/root/.env_tg` (nơi thật · chmod 600).
Root: sai path/file khi verify claim.
Fix: grep multiple candidate paths trước khi tuyên missing.

### E2 · catchup-no-bell (V3.5m)
> CATCH-UP script chạy đúng nhưng output đi stdout không append vào log file cần thiết. Kết quả: `[SENT] phase_map ok=True` sinh ra trong shell nhưng phase_tag.log không có → verdict grep miss.
Bằng chứng: 09-08 CATCH-UP phase_map output không xuất hiện trong data/logs/phase_tag.log · verdict sent_leg[phase_map] = MISS despite artifact tồn tại.
Fix: CATCH-UP script phải append trực tiếp vào log file target hoặc call log_bell() để populate bell_journal.

### E3 · claim-wired-vs-cron deadlock (V3.5n cạnh E2)
> Code wired local nhưng KHÔNG deploy VPS trước cron cycle → cron chạy bản cũ. Đêm sau operator hỏi "log_bell đã wire chưa?" · answer "yes wired" mà cron log không có bell_journal entry.
Bằng chứng: gom_daily/phase_map/watchlist log_bell wired 09-09 sáng nhưng chưa có bell_journal entry nào từ cron (chỉ manual sends).
Fix: DEPLOY-ORDER PROOF · md5 VPS↔local mỗi commit + first-cron-after-wire verify.

### E4 · deploy-lag pair cùng E3 (V3.5n)
> Fix commit local ≠ VPS runtime · gap = 1 cron cycle (24h). Đêm N deploy · đêm N+1 mới có kết quả runtime · claim "deploy done" đêm N là ✓-suy.
Cặp deadlock với E3.
Fix: post-commit auto-SCP + first-cron mtime-verify.

### E5 · chờ-operator-no-cite (V3.5m)
> Blocker-shift "chờ operator" mà không cite bằng-chứng-tường {lệnh/path · hit/miss}.
Ví dụ SAI: "chờ operator xác định 'registry'" (không cite gì).
Ví dụ ĐÚNG: "chờ operator · evidence: grep LIST-A hedge_watchlist_09-08.json AIO=miss GIGGLE=miss"
Luật-con V3.5m: "Mọi mục 'Chờ operator' PHẢI cite bằng-chứng-tường {lệnh/path · hit/miss}"

## LINT-CORPUS (in `label_claims_lint.py`)

Riêng khác OPS. Lint bắt orphan CLAIM {sorted · sort: · ✓ · checked · verified · OK · PASS · đã-*}:
- pointer-integrity OK mồ côi
- 5/5 WIRED ✅ không biên lai
- claim-✅-giả toàn phần

LINT catches VĂN BẢN (label không kèm evidence). OPS ghi ÁN LỆ VẬN HÀNH (root cause + fix pattern).

## Renumber conflict

**LƯU Ý:** LINT corpus dùng E1-E4 (nội bộ lint), OPS corpus dùng E1-E5 (án lệ vận hành). HAI SỔ KHÁC SỐ · không giẫm. Read context để biết which corpus.
