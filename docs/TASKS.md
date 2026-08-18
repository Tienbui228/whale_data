# TASKS — FreshWatch Task Ledger

Cập nhật: 18/08/2026. **Mỗi session mở đầu bằng diff file này.**
Format cột Status: `QUEUED` / `DOING` / `DONE <commit>` / `BLOCKED <lý do>`

## Khối NET-DOSE (mã án `M6-20260818`, án semantic-drift, operator signed via relay 17-18/08)

Chi tiết đầy đủ: `docs/handover/analysis_handover_addendum_20260818.md §B`.

| ID | Ngày giao | Tóm tắt | Status |
|----|-----------|---------|--------|
| M6-R0 | 17/08 | Verdict semantic-drift ký relay: `net_oi_delta` cũ nhiễm chase-pump, split 3 vars (gross_adds · net_oi_window · net_gated CANONICAL). LUẬT NHÃN "ĐO GÌ / KHÔNG ĐO GÌ". | DONE — signed 17/08 |
| M6-N0..N4 | 17/08 | Code split gom_scan.py + formatter run_gom_daily.py + label L-31 addendum. Unit-check AKE `{window +$14.67M · gross $0 · gated −$5.16M}`. | DONE `da81774` |
| M6-R1a | 18/08 | Backfill net_gated Option 2 (chain window, ret-gate only) — 56 chapters, freshwatch_daily dedup-safe. | DONE `scratch/r1_backfill_net_gated_20260818.csv` |
| M6-R1b | 18/08 | Backfill Option 1 canonical (FIRE ∧ counts_q1) — 32/56 MATCH · 24 MISMATCH loại · ROBO/AKE verify khớp. Persist `scratch/r1b_fireday_flags_20260818.json`. | DONE |
| M6-R2 | 18/08 | Day-k=3 re-run trên `net_gated_usd` (biến canonical, lần đầu). Đăng-ký-trước hai phía đã ghi: PASS Δ%mg>15% ≥+15pp ∧ Δmedian ≥+5pp CÙNG DẤU; n(A)<8 → UNDERPOWERED không verdict. n(C)=62.5% tại fire+3 → thêm K=5 secondary (primary VẪN K=3). | QUEUED — chờ operator/ANALYSIS trigger |
| M6-DORMANT | 18/08 | DORMANT-register: net_raw → net_gated, threshold `$634K` **ĐÓNG BĂNG** (đổi biến ≠ refit). Đánh giá lại threshold SAU R-2 kết luận. | BLOCKED — chờ M6-R2 |
| M6-U0..U6 | 18/08 | Distribute addendum sang canonical homes: gom_detect_spec §M6 · playbook §VIII.15 · lessons_pending_batch · TASKS khối này · INDEX cross-ref. Hai commit prefix `[M6-20260818]`. | DOING |

**Trình tự đọc net-dose (đã đăng ký):** R-0 → N0..N4 → R-1a → R-1b → R-2 (chờ) → operator đọc → verdict thứ 4 (biến đúng nghĩa + tập ngày đúng doctrine + tiêu chí đăng-ký-trước — VÒNG ĐẦU TIÊN đủ tư cách verdict cuối câu net-dose).

**Câu hỏi cũ "net-signal đóng":** VÔ HIỆU (đo biến sai). MỞ LẠI trên `net_gated`, phân xử bởi M6-R2.

---

## Khối cũ (tài sản trước 18/08)

| ID | Ngày giao | Tóm tắt | Status |
|----|-----------|---------|--------|
| CASE-CYS | 13/08 | CASE_CYS.xlsx COLD_START: C-0→C-8 collect CYSUSDT. 224 rows Jan-Aug12. GOM-C Aug07 PROVISIONAL (gate 15/08). Bốn vân: pos_r−63.5%(giảm), hedge Jul02-18, squeeze Aug05, on-chain missing. Verdict: C/D ô staged-pump — DỪNG CHỜ ĐỌC. | DOING — _collect_cys_20260813.md sẵn sàng |
| ACU-CYS-GOM | 13/08 | GOM-A/B/C on ACUUSDT + CYSUSDT (store Jun01→Aug07): 0/0/0 fires cả 2 token. ACU: churn/wrong-side (gLSR=3-4, div_ratio=0.44<1.5). CYS: distribution Jun-Jul + short squeeze Aug04-07 (funding=-1.3e-3). Kết luận: KHÔNG có lực gom RÒNG. | DONE — DỪNG CHỜ ĐỌC _collect_acu_cys_20260813.md |
| APR-REFRESH | 13/08 | APR (aPriori) post-ignition audit P-0→P-6: multi-chain confirmed, DAILY Aug10-12 appended (294 rows), Aug12 SHORT SQUEEZE +192.3% $903M, GOM-D 4/4 PASS draft. Verdict tầng HUMAN. | DONE 75bd388 — DỪNG CHỜ ĐỌC |
| VPS-SCP-P1 | 13/08 | SCP batch audit P1 fixes lên VPS: (B) taker_pct→taker_buy_pct (đã fix local 75bd388); (C) fundingInfo fail-open (đã fix local). Rebuild 5 CASE packs sau SCP. CẦN OPERATOR SSH vào VPS để pull/scp. | QUEUED — post-gate 15/08 |
| PARK-BROCCOLIF3B | 12/08 | BROCCOLIF3BUSDT không có trong fw139 — tra tên đúng, kiểm delist/drift. Chạy SAU C4 (15/08). | QUEUED — sau C4 |
| PARK-H1-HIDDEN | 12/08 | DOODUSDT(avg_div=0.42)/TOSHIUSDT(avg_div=0.53) div thấp nhưng không vào registry — đọc code eval_hedge_farm entry, có điều kiện ẩn ngoài div_avg3 không (H2 funding? LSR gap?). Chạy SAU C4. | QUEUED — sau C4 |
| MARGINAL-V4 | 11/08 | Marginal logger chạy từ 11/08. Đồng hồ V4: nếu đến 25/08 — **≤3 chuỗi/2 tuần mở-đóng-lặp vì A2/A3 marginal → đóng án (logger-only)**; **>3 HOẶC giết-mở-giết ≥2 vòng → mở proposals/persist2d_contingency_PENDING.md + re-gate + operator ký**. data/logs/marginal_hits.csv; mốc nộp 25/08. | DOING — đồng hồ bắt đầu 11/08 |
| COOKIE-GATE-PASS | 11/08 | V5(a): khi operator ký → đóng băng. Án COOKIE ②③ chấm hồi tố CHỈ SAU khi C1-spec thành văn ký (không chấm trên con trỏ). C1 hiện tại (v1.5) = code-pointer `stealth_grind(days,i,cfg)` — THIẾU thành văn tự đứng. | BLOCKED — C1-spec KÝ 12/08 ✓; chờ BANANAS31 gate PASS 15/08 + operator V5(a) ký |
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
| CASE-AIN | 13/08 | CASE_AIN.xlsx COLD_START AI-0→AI-8 (224 rows). Intel: 30M token nạp từ 04/08. GOM-D 4/4, GOM-E 29d. Taxonomy BLEED. Chain UNKNOWN. CẦN OPERATOR on-chain. | DONE 3279c86 — DỪNG CHỜ ĐỌC _collect_ain_20260813.md |
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
| GOM-C-BANANAS31 | 08/08 | D3 BANANAS31 15/08 negative test. Owner: DEV. PASS def (frozen, no paraphrase): GOM-C code (post-conformance commit whale:04cd2ad) KHÔNG fire trên bất kỳ non-suspect row nào trong backtest window BANANAS31; suspect rows liệt kê tường minh và loại khỏi phán xét; nếu fire: full row dump + condition trace. Test chạy trên code sau conformance, trước ngày 15/08. | DOING — verdict template tại docs/handover/bananas31_gate_20260815.md; data cleared (54 evaluable, taker auto-thỏa). CHẠY 15/08. |
| GOM-C-SIGNOFF | 08/08 | GOM-C β final sign-off. Điều kiện: (1) BANANAS31 PASS 15/08; (2) operator review triage D2. Sau sign-off: promote từ β→v1.0, xóa [PROVISIONAL], cập nhật §6 spec. | BLOCKED — wait GOM-C-BANANAS31 + GOM-C-TRIAGE |
