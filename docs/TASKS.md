# TASKS — FreshWatch Task Ledger

Cập nhật: 11/08/2026. **Mỗi session mở đầu bằng diff file này.**
Format cột Status: `QUEUED` / `DOING` / `DONE <commit>` / `BLOCKED <lý do>`

| ID | Ngày giao | Tóm tắt | Status |
|----|-----------|---------|--------|
| MARGINAL-V4 | 11/08 | Marginal logger chạy từ 11/08. Đồng hồ V4: nếu đến 25/08 — **≤3 chuỗi/2 tuần mở-đóng-lặp vì A2/A3 marginal → đóng án (logger-only)**; **>3 HOẶC giết-mở-giết ≥2 vòng → mở proposals/persist2d_contingency_PENDING.md + re-gate + operator ký**. data/logs/marginal_hits.csv; mốc nộp 25/08. | DOING — đồng hồ bắt đầu 11/08 |
| COOKIE-GATE-PASS | 11/08 | V5(a): khi operator ký → đóng băng. Án COOKIE ②③ chấm hồi tố CHỈ SAU khi C1-spec thành văn ký (không chấm trên con trỏ). C1 hiện tại (v1.5) = code-pointer `stealth_grind(days,i,cfg)` — THIẾU thành văn tự đứng. | BLOCKED — chờ C1-spec thành văn (deadline 14/08) + operator V5(a) ký |
| XS | 06/08 | XPIN spot/DEX/Alpha audit XS1-XS4: 181 bars GeckoTerminal, wash test, detection floor $571K/day | DONE 4d3f676 7104037 |
| K0 | 06/08 | Tạo TASKS.md task ledger — baseline tracking từ nay | DONE c0c5d24 |
| K1 | 06/08 | Merge MM-ECON section VII vào analysis_playbook.md + LAYER COVERAGE + lesson ô-điền | DONE c0c5d24 |
| K2 | 06/08 | Dọn proposals/: mm_econ_v0 archive, tut/clo evidence move, playbook → docs/ | DONE c0c5d24 |
| K3 | 06/08 | Tạo docs/INDEX.md cây 4 tầng + thêm vào prompt_analysis_topic.md | DONE c0c5d24 |
| K4 | 06/08 | Grep .md orphan trong docs/ → bảng trình operator | DONE c0c5d24 |
| BANK-T30 | 06/08 | BANK T+30 09/08: px=0.0495 operator confirmed, verdict FULL COLLAPSE (-75% từ đỉnh) | DONE 4d3f676 |
| TUT-T30 | 06/08 | TUT OUTCOME T+30 = 08/08 — monitor sát ngày | DOING — deadline 08/08 |
| BANK-V2 | ongoing | BANK Vòng 2 watch: 3 điều kiện (gLSR/pos_r/funding pin) — 0/3 thỏa 05/08 | DOING — tiếp tục monitor |
| IDOL-UNLOCK | 06/08 | IDOL 11/08 unlock watch: 97.29M tokens (2.03% supply) | QUEUED — D-day 11/08 |
| IDOL-58BRO | 06/08 | IDOL 58bro net: 32.44M tokens pending verify | QUEUED — chờ operator ledger |
| TUT-OUTCOME | 08/08 | TUT T+30 outcome chính thức + write CASE_TUT OUTCOME sheet | QUEUED — sau 08/08 |
| COOLDOWN | - | Cooldown review AKE/CLO/TUT resolved verdict | BLOCKED — chờ operator phán |
| CASE-CLO | - | CASE_CLO hồ sơ chiến dịch đầy đủ (C1-C6 analysis + verdict) | QUEUED |
| CASE-AKE | - | CASE_AKE tạo + cold start pack (AKE chưa có file) | QUEUED |
| XPIN-ONCHAIN | - | XPIN on-chain: kho wallet + vesting + BitMart verify (BscScan) | BLOCKED — Nansen LOCKED + PENDING OPERATOR |
| MM-ECON-SIG | - | mm_econ_v0.2 operator ký → dùng vào live signal | BLOCKED — ANALYSIS ONLY, chờ operator ký |
| XS3B-RETRY | - | XPIN XS3b retry: GeckoTerminal trades endpoint (rate-limited 06/08) | QUEUED |
| HANDOVER | 08/08 | Lưu handover bản 08/08 + tạo prompt_analysis_topic.md + đóng topic analysis 03→08/08 | DONE ac84dba |
| GOM-SPEC | 08/08 | gom_detect_spec.md v1.5 (D1 spec-drift sync): §1.3 GOM-C, §3 Q2_net, §6 backtest, §7 gaps, §9 conformance | DONE whale:04cd2ad bot:cc661d75 |
| GOM-BUILD | 08/08 | gom_scan.py + screen_thresholds.yaml: Bước 2 offline build | DONE 4d0987c |
| GOM-B3 | 08/08 | Backtest §6: 10/10 PASS — operator duyệt (TUT PASS, BULLA→GOM-B, BANK PASS G4) | DONE 4d0987c |
| GOM-B4 | 08/08 | Deploy cron VPS (01:25 UTC) + fw-filter + Telegram CAMPAIGN-TRACK format | DONE a655ad9 whale:04cd2ad |
| GOM-C-D1 | 08/08 | D1 spec-drift sync: fw_loader_utils _interval_h + gom_scan C2_quiet normalize + run_gom_daily CAMPAIGN-TRACK | DONE whale:04cd2ad |
| GOM-C-TRIAGE | 08/08 | D2 triage COOKIE/CYS/TST: report docs/reports/gom_c_triage_20260808.txt — ANALYSIS gửi operator (session này) | DOING — CHỜ OPERATOR CHẤM PACK |
| GOM-C-BANANAS31 | 08/08 | D3 BANANAS31 15/08 negative test. Owner: DEV. PASS def (frozen, no paraphrase): GOM-C code (post-conformance commit whale:04cd2ad) KHÔNG fire trên bất kỳ non-suspect row nào trong backtest window BANANAS31; suspect rows liệt kê tường minh và loại khỏi phán xét; nếu fire: full row dump + condition trace. Test chạy trên code sau conformance, trước ngày 15/08. | BLOCKED — wait 15/08 |
| GOM-C-SIGNOFF | 08/08 | GOM-C β final sign-off. Điều kiện: (1) BANANAS31 PASS 15/08; (2) operator review triage D2. Sau sign-off: promote từ β→v1.0, xóa [PROVISIONAL], cập nhật §6 spec. | BLOCKED — wait GOM-C-BANANAS31 + GOM-C-TRIAGE |
