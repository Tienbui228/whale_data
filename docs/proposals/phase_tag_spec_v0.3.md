# PHASE-TAG v0.3 — Stage Classifier + Daily Scan Report (SCREEN display layer)

**Version:** 0.3 · **Ngày:** 18/08/2026 · **Soạn:** ANALYSIS (boot 17/08) · **Review:** FB-1, FB-2 (17/08) + DEV escalation (17-18/08)
**Trạng thái:** TRÌNH KÝ — khi operator ký: file này vào `docs/proposals/phase_tag_v0.3.md`, là GATE CỨNG cho DEV bắt đầu code (§9)
**Trả nợ:** L-19 · nuốt F1-tagger · **Deliverable:** bot scan daily → report 5 khối
**Cross-ref:** master plan §1+§5 · playbook §VIII · gom_detect_spec v3.1 (C1 §1.3, rule-iv §8) · CASE_INDEX.xlsx (state canonical) · 12-case + 70-fire · Doctrine G1

---

## CHANGELOG

**v0.1 → v0.2** (tóm — chi tiết trong phase_tag_spec_v0.2.md): #1 join state + khối STATE-CONFLICT (FB-1 L1, nâng demote→section) · #2 B2.5 S3-GRIND pointer C1 (FB-1 L2) · #3 S0-POSTFLUSH (FB-1 L3) · #4 S3-HARVEST (FB-2 PH1) · #5 CROWD-CHASE (FB-2 PH2) · #6 luật ground-truth hai-lớp, TAG=documentation (FB-2 PH3, ANALYSIS bác một nửa) · #7-12 chốt Q1-Q6 · #13 nhà chính CSV · #14 fw-139 unify · #15 acceptance re-baseline.

**v0.2 → v0.3:**

| # | Sửa | Nguồn |
|---|---|---|
| 16 | Khối 🔻 PHÂN PHỐI/SUY TÀN transition-based (§0, §6.2) — thay luật "S4/S5 không in" | Yêu cầu operator qua DEV escalation |
| 17 | Event `PHASE-BREAK` (mọi cú vào S4/S5) | Đi kèm #16 |
| 18 | §7 thêm 2 ngưỡng tự chế: transition-window 5d · B2h rolling-window 14d | #16 + chốt D3 |
| 19 | **D1 chốt:** `case_state_map.md` = VIEW SINH từ cột state CASE_INDEX.xlsx (tiền lệ lessons_learned.md) — KHÔNG rename case_tracker.md (khác semantics: hành-chính-án vs trạng-thái-phân-tích-ký) | DEV D1 + ANALYSIS |
| 20 | **D3 chốt:** rule-iv canonical KHÔNG đổi (chain-lifetime peak giữ cho chuỗi). B2h mượn MAGNITUDE −25% qua pointer; khung 14d = tham số LOCAL stateless (§7). DEV viết helper local `harvest_drop()`, không gọi rule-iv chain helper — sửa §9.1.2 v0.2 | DEV D3 + ANALYSIS |
| 21 | Acceptance dòng 20-21 (khối 🔻: BANK/AKE vào đúng cửa sổ · CLO mạn tính không in) | #16 |

---

## §0. Tóm + hình dạng deliverable

Detector hiện hành trả lời "có tell X" — không cái nào trả lời "token ở ĐÂU trong S0→S5" (bệnh L-19). PHASE-TAG chấm daily mỗi token fw-139 (theo config) một nhãn stage + evidence + confidence, thuần từ store (0 API call), display-only.

**Report daily (Telegram 08:25 VN, chung chuyến GOM scan) — 5 KHỐI:**

```
━ PHASE-MAP DD/MM ━
🟢 GOM (S2*)              — sort: RIPE trước, rồi conf
🟡 TEST-RŨ (event hôm nay) — BAIT/WASH/CHASE + test-result
🔴 ĐẨY GIÁ (S3*)          — TAKER/BIDWALK/GRIND; HARVEST in đỏ đậm
🔻 PHÂN PHỐI / SUY TÀN     — transition-based (§6.2): S4 dòng riêng, S5 dòng riêng
⚠ STATE-CONFLICT          — nhãn máy ngược verdict ký (bắt buộc, không giấu)
(S0/UNKNOWN: không in. S4/S5: in theo luật §6.2 — mới-vào ≤5d ∨ có case mở;
 mạn tính không case = CSV-only.)
```

Mỗi dòng: `TOKEN · stage · conf · evidence-ngắn · flags · [case_state nếu có]`.

---

## §1. Phạm vi & Non-goals

**Làm:** nhãn stage daily (`S0 / S0-POSTFLUSH / S1 / S2-EARLY / S2-MID / S2-LATE / S3-TAKER / S3-BIDWALK / S3-GRIND / S3-HARVEST / S4 / S5 / UNKNOWN`) · event tags (§3) · đồng hồ S2 (`wash_count_30d`, `herd_return`) · report 5 khối.

**KHÔNG làm:**
- KHÔNG phân biệt gom-thật vs captive-chờ-xả (Doctrine G1) — mọi S1/S2 mang `[OWNERSHIP-UNVERIFIED]` đến khi operator đóng Vân4. Máy in nhãn, operator đóng dấu.
- KHÔNG tạo entry, KHÔNG đổi state machine, KHÔNG suppress. Entry giữ nguyên: staged = S1-CONFIRMED churn ≥8× duy nhất; gom-thật = Pre-ARM checklist VI.
- KHÔNG dự đoán giá. UNKNOWN = ABSTAIN hợp lệ.
- **KNOWN-GAP G-committed-long:** loài committed-long (BTW-July: div 1.3-1.5, ghế insider, không pin) perp câm là bản chất — tell nằm on-chain/ví, ngoài input-space. Máy thấy nửa hedged-waiting (`CAPTIVE?`); nửa committed-long mù, ghi nhận tường minh.

---

## §2. Input (0 call mới)

Daily, nến ĐÓNG (L-21), per token fw-139: `px o/h/l/c` · `vol_perp_usd` · `oi_usd` (**dedup-at-read — án OI-dup**) · funding (min/max/avg, fn, interval verify L-41) · `lsr_pos_r / lsr_acc_r / lsr_global_r` (ratio-space, 00:00 UTC quy ước v2) · dẫn xuất sẵn: `div_avg3`, `div_raw`, `glsr_slope_5d`, `oi_cycle_pos`, `med14(vol)`, `min30d(oi)`, `rolling_peak14(pos_r)`.

**Join bắt buộc: `docs/case_files/case_state_map.md`** — VIEW SINH máy-đọc-được từ cột state CASE_INDEX.xlsx (canonical). Format: `token · state_ký · ngày_ký · verdict_ref`. Agent generate khi CASE_INDEX đổi; operator ký state trong CASE_INDEX như cũ — map là ống dẫn read-only, không phải nơi ký. Đọc map = đọc verdict người ký, KHÔNG phạm Δ5. `case_tracker.md` giữ nguyên tên/vai (hành chính án OPEN/RESOLVED/BLOCKED — khác sổ).

---

## §3. Event tagger (chạy TRƯỚC cây, mỗi ngày)

| Tag | Điều kiện | Đọc |
|---|---|---|
| `TEST-BAIT` | vol ≥8× med14 (1d) + giá bị từ chối ≤2d; xác nhận: gLSR −≥30%/≤3d | Test cung TRÊN + dạy crowd short (BANK 02/07) |
| `WASH-CRASH` | giá −15%+ ∧ gLSR −≥30%/≤3d | Test cung DƯỚI + rửa long (TAG/AKE) |
| `WASH-RALLY` | giá +8%+ ∧ gLSR −≥30%/≤3d | Rũ-nến-xanh (màn 3 thước ON) — KHÔNG đọc là mất đà |
| `WRONG-SIDE` | giá sập ∧ gLSR TĂNG | Fuel sai phía — cờ đỏ L-26 |
| `CROWD-CHASE` | giá +8%+ ∧ (glsr_slope_5d >1.15 ∨ gLSR +≥30%/3d) | Đám tự đẩy giá vào vị thế mình (XPIN 31/07-07/08) |
| `PHASE-BREAK` | mọi cú chuyển nhãn VÀO S4 hoặc S5 — ghi nhãn nguồn (`S3-BIDWALK→S4`) | Mở phân phối / vào suy tàn — feed khối 🔻 |

**Dẫn xuất:** `wash_count_30d` · `herd_return` (rolling-14d, ≥80% tiền-flush → TRUE, lật muộn được phép — BROCCOLIF3B 15d; ngưỡng PROVISIONAL §7; **mọi cú lật = một dòng EVENTS**; sanity chiều: IDOL 02/08 TRUE→không leg-2 ✓, TUT 10-12/07 FALSE→leg chạy ✓, BR 03/08 mở) · test-result BAIT: ≥97% tiền-probe sau 3d = `HELD`/`REJECTED`.

**Một nhà EVENTS duy nhất** (chống dup L-25): `source=phase_tag` / `source=gom_e` — không nhà thứ hai.

---

## §4. Cây phân loại (precedence — dừng ở nhánh đầu khớp)

Suppressor đè bullish — S4/S5 chấm TRƯỚC mọi texture gom (fix cơ khí L-19).

```
B1. SUPPRESSOR:
    dist_wall ∨ lsr_dist                              → S4
    post_climax ∨ decay ∨ funding_neg_div              → S5

B2. MARKUP (breakout ≥15%/range14d trong ≤5d ∧ OI ≥1.5× med14):
    B2h. harvest_drop: pos_r −≥[MAG] từ rolling_peak14
         [MAG = pointer magnitude rule-iv GOM §8 (hiện 25%) — đồng bộ khi rule-iv đổi;
          khung 14d = tham số LOCAL stateless (§7 #7), KHÔNG phải rule-iv chain]
                                                       → S3-HARVEST  (hiệu lực NGAY)
         · chú thích in kèm: two-legged-kho — harvest = CHUYỂN PHA, campaign chưa
           chắc hết (kho spot quyết)
    max(takerBUY cửa sổ) ≥55%                          → S3-TAKER   (AKE)
    else                                               → S3-BIDWALK (TUT/BULLA/BANK)

B2.5. GRIND [gọi C1 canonical gom_detect_spec §1.3 — KHÔNG re-implement số;
      C1 đổi sau gate → B2.5 tự theo]:
    C1 true                                            → S3-GRIND
    + B2h áp chồng: đồng thời harvest → S3-HARVEST thắng

B3. TEXTURE S2 (không markup ∧ oi_cycle_pos ≤ 0.5):
    div_avg3 ≥1.5 ∧ avg5(gLSR) ≤1.1                    → S2-LATE
    hedge_structure (div ≤0.5) bền ≥7d ∧ (pinned ∨ absorption) → S2-EARLY
    (pinned ∨ absorption) ∧ 0.5<div_avg3<1.5           → S2-MID
       · sub S2-MID↑ khi d_pos_3d>0 ∧ div_raw ≥1.5     [raw = cảnh-báo-sớm]

B4. S1 [chỉ khi deposit-feed sống (GOM-D D3)]:
    deposit lớn ≤14d ∧ ret14d ≥ −10% ∧ chưa đủ B3      → S1
    [khuyết feed → SKIP, không proxy]

B5. S0:
    a. oi ≤1.1× min30d ∧ med7(vol) ≤0.5× med30 ∧ gLSR∈[0.8,1.3]         → S0
    b. crowd_flush ≤7d ∧ gLSR −≥40% từ đỉnh 14d ∧ herd_return≠TRUE       → S0-POSTFLUSH

B6. else → UNKNOWN
    + flag FUEL-STANDING: avg30(gLSR) ≤0.90 ∧ không texture S2 (loài APR)
```

**Sub-annotation S2:** `RIPE` (wash_count_30d ≥2 ∧ herd_return=FALSE — đầu sort khối GOM) · `CAPTIVE?` (div<1 ∧ funding âm/pin ∧ OI-kệ lớn — nhắc operator đóng Vân4).

**Hysteresis:** nhãn ghi khi giữ 2d. Carve-out hiệu lực NGAY: B1 · B2 markup · B2h HARVEST. Ngày chuyển tiếp hiển thị `S2-LATE→S3?`. (Khác lớp án no-δ — persist trên nhãn display; tiền lệ B1 persist-7d: 220 marginal/0 tai nạn.)

---

## §5. Guards

Nến đóng L-21 · anti-look-ahead §VIII.9 · fn<6 → SUSPECT nhánh ratio · symbol <14d → skip · vol <$200k ∨ OI <$1M → `low_conf` · **LSR null → `UNKNOWN(DATA)` nổ ra mặt** (L-49-draft) · Alpha fullyDelisted → L-48 ABSTAIN · universe verify fw-139.

---

## §6. Output + luật hiển thị

### §6.1 CSV (nhà chính)
`data/screener/phase_tag_daily.csv` (append-only, forward-only). CASE_*.xlsx chỉ nhận stage khi refresh case (file-lock L-34 + tinh thần L-50). Cột: `date, token, stage, stage_conf (HIGH ≥2 mảnh — L-03 / MED / LOW), stage_evidence, stage_flags, event_tag, wash_count_30d, herd_return, case_state, state_conflict, operator_stage_hint (máy không đọc)`.

### §6.2 Khối 🔻 PHÂN PHỐI/SUY TÀN — luật transition-based
Ba cửa:
- **Cửa chính:** token MỚI vào S4/S5 trong ≤5d (ngưỡng §7 #6) — in kèm mũi tên nguồn `S3-BIDWALK→S4 (d+2)`. Hết cửa sổ → rời report (CSV giữ đủ).
- **Cửa case:** có case_state mở ∧ nhãn máy S4/S5 → in LUÔN, bất kể bao lâu.
- **Cửa xác:** S4/S5 mạn tính, không case → KHÔNG in (CSV-only).

Hai dòng tách (doctrine tách thì report tách): **S4** (đang xả — hành động: tránh/thoát; case mở → canh chân-2 kho spot) · **S5** (`funding_neg_div` = bẫy BTW-khuôn in ĐẬM — bẫy đang hoạt động; `post_climax/decay` = xác, in thường).

### §6.3 STATE-CONFLICT (fix "BTW ★$7.5M" tầng mới)
case_state phía DISTRIBUTION/SUPPRESSED ∧ máy chấm S2*/S3* → (a) LOẠI khỏi khối GOM/ĐẨY-GIÁ, (b) vào khối ⚠ với cả hai nhãn cạnh nhau, (c) không bao giờ RIPE. Đọc: "texture gom trên con người-ký-đang-xả" thường = crowd đu (BTW 10/08 net_k3 +$14.8M) — tín hiệu loại riêng, hiển thị không giấu, không sort ưu tiên. **Ranh với khối 🔻:** ⚠ = máy-sổ CÃI NHAU; 🔻 = máy-sổ ĐỒNG THUẬN xả — không nhập.

---

## §7. SỔ NGƯỠNG TỰ CHẾ (7 con — mọi số khác thừa kế/pointer)

| # | Ngưỡng | Giá trị | Trạng thái | Đường calib |
|---|---|---|---|---|
| 1 | herd_return | 80% / rolling-14d | PROVISIONAL | Phân bố mọi flush-event 70-fire + 12-case |
| 2 | S0-POSTFLUSH | gLSR −≥40%/đỉnh 14d | PROVISIONAL (n=2) | Cùng bài phân bố |
| 3 | CROWD-CHASE vế 2 | gLSR +≥30%/3d | soi-gương flush (0 sáng tác về số) | Xác nhận cùng bài |
| 4 | FUEL-STANDING | avg30(gLSR) ≤0.90 | neo biên subtype | Forward |
| 5 | Sanity UNKNOWN | ≤40%/ngày thường | floor thực dụng | — |
| 6 | Transition-window khối 🔻 | 5d | PROVISIONAL | Phân bố dwell S3→S4 trên 12-case (BANK 19-21→24/07 ≈ 3-5d) |
| 7 | B2h rolling-window | 14d | PROVISIONAL (LOCAL — không đụng rule-iv canonical) | Replay: BANK 19-21/07 + TUT 02+05/08 phải bắn; trượt → chỉnh theo phân bố dwell |

---

## §8. Acceptance gate

### §8.1 Luật ground-truth (áp mọi gate tương lai)
**Ground truth = bản án cuối của case, không phải bản án tại trận.** Phin lọc input-space: thông tin phân biệt NẰM TRONG input perp (BANK harvest, BTW suppressor) → hồi tố, miss = FAIL cứng. NGOÀI input (TAG — chỉ hiện on-chain 1Y/round-trip 90B) → DOCUMENTATION CASE: chấm sự-hiện-diện của cờ `OWNERSHIP-UNVERIFIED`, không chấm nhãn — ép nhãn = leak/overfit. *(Phân xử ANALYSIS ngược một phần FB-2 — điểm cần mắt operator khi ký.)*

### §8.2 Bảng kỳ vọng (luật chấm: NEGATIVE/SUPPRESSOR/HARVEST/EVENT = FAIL cứng · TEXTURE ≤2 miss · DOCUMENTATION chấm cờ · SANITY floor)

| # | Case · ngày | Kỳ vọng | Lớp |
|---|---|---|---|
| 1 | POWER 20/07 | S2-EARLY | TEXTURE |
| 2 | BASED 20/07 | S2-LATE | TEXTURE |
| 3 | BAS 20/07 | S0 → S2* | TEXTURE |
| 4 | IDOL 20/07 | S2* (build 28-31/07 thấy S2-MID↑) | TEXTURE |
| 5 | TUT 20/07 | S3-BIDWALK ∨ S3-GRIND (either) | TEXTURE |
| 6 | BULLA 20/07 | S3-BIDWALK | TEXTURE |
| 7 | AKE 20/07 | S4/S5-side | SUPPRESSOR |
| 8 | CLO 20/07 | S4 | SUPPRESSOR — cứng |
| 9 | BTW toàn kỳ | KHÔNG ngày nào S2* | NEGATIVE — cứng |
| 10 | ESPORTS 19/07 | climax thắng mọi texture | SUPPRESSOR — cứng |
| 11 | BANK chuỗi | S2-LATE (~29/06) → TEST-BAIT 02/07 → S3-BIDWALK (10-11/07) → S3-HARVEST 19-21/07 (một nhãn/ngày) | HARVEST — cứng |
| 12 | TUT 02+05/08 | S3-HARVEST cả hai cú | HARVEST — cứng |
| 13 | TAG 20/07 | texture bất kỳ + cờ OWNERSHIP-UNVERIFIED hiện diện | DOCUMENTATION |
| 14 | XPIN 31/07-07/08 | không S2* + CROWD-CHASE | NEGATIVE — cứng |
| 15 | KOMA + COOKIE 02-09/08 | S0-POSTFLUSH | TEXTURE |
| 16 | TST tháng 7 | S3-GRIND (C1 toàn px/OI/taker — không chờ LSR-rescue) | TEXTURE |
| 17 | APR 05-06/08 | S2-LATE tại fire (div 1.90/1.83) — **CHỈ SAU án-E repair** (Jul19+ đang NULL; sớm = FAIL giả) | TEXTURE — gated |
| 18 | Event đếm đủ | BASED bait 01+09/07 · BANK bait 02/07 · TAG/AKE crash · TUT/BULLA rally | EVENT — cứng |
| 19 | Sanity | UNKNOWN ≤40% | SANITY |
| 20 | Khối 🔻 | BANK ~24/07 + AKE hậu-markup xuất hiện đúng cửa sổ transition, kèm PHASE-BREAK event | TEXTURE |
| 21 | Cửa xác | CLO mạn tính không case → KHÔNG xuất hiện trong report (CSV có) | NEGATIVE — cứng |

Trượt dòng FAIL-cứng → không ship, autopsy ghi sổ.

---

## §9. Hợp đồng build cho DEV

**GATE CỨNG: chưa có file này ký trong `proposals/` = chưa code.**

**§9.1 Trình tự (probe-first):**
1. Prerequisite: agent generate `case_state_map.md` từ CASE_INDEX.xlsx (view read-only, format §2) — việc AGENT, không phải DEV.
2. `scanner/phase_tag.py` — pure function `tag(days, i, cfg, case_state) -> row` trên signals.py sẵn có. KHÔNG sửa signals.py/gom_scan.py, KHÔNG API, KHÔNG commit.
3. B2.5 gọi C1 canonical. **B2h = helper LOCAL `harvest_drop(days, i)`** — magnitude import/đồng bộ từ rule-iv (25%), window 14d local (§7 #7). KHÔNG gọi rule-iv chain helper (sửa v0.2 §9.1.2).
4. Threshold §7 vào `screen_thresholds.yaml` — KHÔNG đụng `thresholds.yaml` LOCKED.
5. `replay_phase.py` chạy §8.2 (trừ #17) trên 12 file `*_result.txt` + store — **paste bảng thô 21 dòng expected-vs-actual**, chưa ship.
6. Bài calib phân bố §7 (#1-3, #6-7) trên mọi flush-event + dwell S3→S4 — paste phân bố.
7. ANALYSIS verdict PASS/FAIL kèm falsifier → operator ký → mới nối cron (chung chuyến 08:25, sau GOM scan, **incremental-only env-var + assert**) + Telegram 5 khối + CSV.
8. Live-test tuần đầu: herd_return trên AIN 15-16/08 (acc 1.93→2.58).

**§9.2 Dependency:** acceptance #17 (APR) CHỈ chạy sau án LSR-merge repair (fix B+C+D + re-merge đạt số exhibit). Chạy trước = FAIL giả, cấm dùng sửa cây.

**§9.3 Ranh giới hệ:** PHASE-TAG không đọc registry GOM-E (máy-mù-nhau Δ5); GOM-E report được in cột stage (display-for-human). EVENTS một nhà, cột source. Funding cutover `_vps.py` fail-loud = việc song song, cửa sổ deploy do operator chốt (đề xuất: ngay sau chuyến scan sáng ngày D, buffer ~23h, chuyến D+1 = bài test fail-loud tự nhiên).

---

## §10. Falsifier + việc mở sau ship

- **Falsifier hậu-deploy:** 30d forward, ≥3 case nhãn S2* mà hồi tố xác nhận S4 (khuôn BTW) → kéo về ANALYSIS-ONLY, mở án.
- Sau ship: đóng L-19 trong LESSONS (trỏ spec này) · chốt ngưỡng PROVISIONAL theo phân bố → v0.4 · S1 chờ GOM-D D3 · G-committed-long giữ KNOWN-GAP đến khi có sensor on-chain.

---

**Ô ký operator:** ⬜ Ký hướng v0.3 (chữ ký phủ: 7 ngưỡng tự chế §7 · phân xử TAG §8.1 · D1 view-sinh · D3 local-window) — ngày ___ /08/2026
