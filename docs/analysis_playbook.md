# Analysis Playbook — FreshWatch
**Version:** 0.2 (06/08/2026) · **Chủ sổ:** operator (Tien)
**Nguồn:** tổng hợp từ master plan §1, case_tracker.md, lessons L-01→L-42, mm_econ_v0.2
**Layer coverage:** I (Perp) · II (Crowd) · III (On-chain/M2) · IV (Funding) · V (External venue) · VI (Pre-ARM) · VII (MM-ECON model) · Spot/DEX — CASE_*.xlsx DAILY vol_spot_usd

> Playbook này là danh sách kiểm tra THỰC HÀNH — HOW TO READ từng case,
> theo trình tự 6 lớp. Mỗi lớp có thể suppress các lớp sau (không vượt suppressor).
> Số mục §1 #X = tham chiếu master plan gốc. Lessons Lx = nguồn bài học.

---

## I. Perp Signal Layer

**Mục đích:** Phát hiện tell sớm nhất có thể từ dữ liệu perp công khai (1 nguồn, 0 API call ngoài).

### I.1 OI-floor tell (L-01, master plan §1 #9)
- OI ≤ 1.1× min30d = sàn MM đang nắm vị thế → ratio tại đây cần trọng số cao
- pos_r nhích tại nền chết = tín hiệu sớm đám (L-01)
- OI tại peak phải chiết khấu (crowd đã vào, MM thoát)

### I.2 Funding regime
- PIN tuyệt đối (min=max=0.00005) = MM kiểm soát hoàn toàn
- Burst ≥ 15bps = thông điệp chủ ý (L-15 bait-probe)
- Interval: xác nhận 4h vs 8h trước khi đếm fn (L-41)

### I.3 Volume tell
- vol spike ≥ 8× med14 + giá bị từ chối ≤ 2d = bait-probe (L-15)
- vol persistence T+1 phân biệt bait vs ignition thật

### I.4 Crowd flush sơ bộ (perp only)
- gLSR sập ≥ 30% / ≤ 3d khi giá sập = wash-by-crash (L-14) → BULLISH fuel
- gLSR TĂNG khi giá sập = wrong-side fuel → SUPPRESS, cần rửa trước (L-26)
- gLSR sập khi giá TĂNG = wash-by-rally → BULLISH (L-11)

---

## II. Crowd Structure

**Mục đích:** Xác nhận fuel direction + subtype campaign (tác động đến exit clock).

### II.1 gLSR_base → Subtype (L-42 + MM-ECON v0.1)
| gLSR_base | Subtype | OI_mult est. | Exit clock |
|-----------|---------|-------------|------------|
| < 0.70 | SHORT-WASH | 4–8× | D+8→12 |
| 0.70–0.90 | SHORT-WASH-MILD | 3–5× | TBD |
| 0.90–1.30 | NORMAL | 2–4× | D+10→12 |
| 1.30–2.50 | CROWD-LONG | 1.5–3× | UNKNOWN |
| > 2.50 | 1-WHALE hoặc HYBRID | 2–3× / wave | D+3→5 / wave |

### II.2 pos_r + acc_r divergence
- pos_r > 1.5 AND acc_r < 1.0 = BTW pattern (whale long / retail short) → CAUTION
- pos_r > 4.0 = crowd-long pre-loaded, MM build tốn ít effort
- acc_r crash < 1.0 khi OI flat = tài khoản nhỏ flip short, không phải liquidation

### II.3 L-26 crowd_flush prerequisite
- Trước bất kỳ leg thật: crowd long phải được rửa
- pos_r drop ≥ 30% trong 3d = điều kiện tháo trần STAND_ASIDE (L-26)
- Thiếu L-26 → giữ STAND_ASIDE dù gLSR có đẹp

---

## III. M2 — CEX Balance Flow + On-chain Read

**Mục đích:** Đọc dòng tiền CEX và ý nghĩa transfer on-chain. Lớp nặng nhất về rủi ro diễn giải sai.

> **⚠️ GATE L-42 — ĐỌC TRƯỚC KHI VÀO MA TRẬN M2:**
> Phân loại kho theo ownership TRƯỚC khi đọc bất kỳ transfer nào.
> - **Loại A** (kho mượn từ team) → mọi dòng M2 đọc là THÔNG ĐIỆP, KHÔNG vào cột bằng chứng;
>   chỉ Loại B/C mới chạy ma trận M2 như bình thường.
> - Xem L-42 để biết tell phân loại. Không xác định được loại → ghi ABSTAIN + PENDING OPERATOR.

### III.1 Phân loại kho ownership (L-42)
| Loại | Đặc điểm | Nguồn kho | Hành vi hậu định |
|------|----------|-----------|------------------|
| A — Mượn team | P&L 100% ở perp; kho là đạo cụ | deployer/team wallet | Round-trip nguyên đại; dập giá hậu campaign để mua lại trả nợ |
| B — Unlock/đầu tư | Sở hữu thật, cost thấp; phải hiện thực hóa | vesting contract đúng lịch | Deposit ≤ 48h sau unlock (tell hạng nhất) |
| C — Tự mua thị trường | Conviction thật; cost basis = floor có nghĩa | gom lẻ nhiều nguồn dài hạn | Không deadline; duy nhất "đi cùng thuyền" được |

### III.2 Ma trận M2 (chỉ áp khi xác nhận Loại B hoặc C)

*→ Chèn đầu mục khi Loại A xác nhận: bỏ qua toàn bộ III.2, ghi nhãn M2=THÔNG_DIEP_DAO_CU.*

| Signal M2 | Đọc khi Loại B/C | Đọc khi Loại A |
|-----------|-----------------|----------------|
| Withdrawal gần đỉnh | Bằng chứng phân phối thật (L-05) | Đạo cụ — không vào bằng chứng |
| Deposit lên sàn | Chuẩn bị bán thật hoặc cung cấp thanh khoản | Staging shape — thông điệp cho người đọc on-chain |
| Redeposit sau rút | Bằng chứng re-accumulate (L-07) | Leg 3 đạo cụ: round-trip nhằm tạo narrative |
| Inventory trên sàn | Phân tích được (L-06) | Không phân tích được (hàng không thuộc MM) |

### III.3 Transfer shape interpretation

Các shape "đẹp" (chia đều + Sent=0) KHÔNG đồng nghĩa với ý nghĩa kinh tế:
- Shape đẹp (chia đều + Sent=0 trưng bày) trên token nghi Loại A = **tín hiệu rẻ** → mặc định nghi dàn dựng (bài IDOL: 8% → 273M staging 13 ví → redeposit 102M).
- Shape chỉ được tin khi **sống sót qua thời gian ≥X ngày** (X chưa calib, IDOL tan tác < 3d).
- Tell phân biệt: transfer Loại C thường không đều, không cần show, không Sent=0 có tính toán; Loại A thì ngược lại.

---

## IV. Funding Regime Deep-read

**Mục đích:** Funding là thông điệp rõ nhất về ai kiểm soát, và bao lâu.

### IV.1 PIN tuyệt đối
- Funding min = max = 0.00005 suốt campaign = MM kiểm soát hoàn toàn
- Breaks (>10bps) = moment "hở" — ghi vào EVENTS với timestamp
- Interval 4h (fn=6) phổ biến hơn chuẩn 8h — verify trước khi đếm (L-41)

### IV.2 Âm dài
- Funding âm dài = MM thu phí crowd-long → pattern MM-BAIT (BTW, BR)
- Kết hợp với bait-withdrawal = BAIT-B sổ đen (L-05, L-07)

### IV.3 Burst sau PIN
- Burst ≥ 15bps sau giai đoạn PIN = ignition signal
- BANK: 08/06 23.4bps, 28/06 25.3bps (mini-pump signals)

---

## V. External Venue — Gate / Tape / Alpha

**Mục đích:** Kiểm tra cross-venue consistency; phát hiện controlled-fill (L-06) và alpha suspect (L-29).

### V.1 Kiểm tra inventory vs volume (L-06)
- V_14d ≥ 2× withdrawal = có thể gom trên venue
- Book siêu mỏng = BẪI ĐỖ — withdrawal từ bãi đỗ ≠ bán

### V.2 Alpha volume suspect (L-29)
- vol_spot / vol_perp > 3× → ABSTAIN mọi metric vol spot ngày đó
- taker spot lệch cực đoan (< 35% hoặc > 70%) trên vol không lớn = farming shape

### V.3 Gate tape (khi có)
- spot_tape_1d từ Gate = lớp xác nhận controlled-fill
- Hiện tại: tape_targets.json chưa deploy → ABSTAIN lớp này cho BR/TAG

---

## VI. Pre-ARM Checklist

**Mục đích:** Điều kiện cần trước khi gán ARM/FIRE. Thiếu bất kỳ điều kiện bắt buộc → WATCH.

### VI.1 Perp layer (bắt buộc)
- [ ] OI tại/gần floor (oi_cycle_pos ≠ PEAK)
- [ ] funding_regime ≠ NEG_DIV hoặc có giải thích
- [ ] fn ≥ 6 hoặc có fallback Zone-A-agg (L-22)
- [ ] pos_r trend: không đang di chuyển ngược lại leg kỳ vọng

### VI.2 Crowd fuel (bắt buộc)
- [ ] gLSR_base phù hợp subtype (không phải extreme-long khi muốn short-wash)
- [ ] Chưa L-26 → STAND_ASIDE (chưa đủ fuel flush)
- [ ] Không BTW-pha-2 suppressor (px flat ≤7% + funding ≤-2e-4)

### VI.3 On-chain / kho (nếu có data)
- [ ] Kho phân loại xong (A/B/C/lai) — Loại A không ARM theo on-chain thesis
- [ ] Không có bất thường withdrawal mới chưa giải thích
- [ ] **□ Kho Loại A hồi đáy vùng đáy sau campaign = thu mua trả nợ kho → xác nhận campaign đã khép + dập giá có chủ đích.** Nếu phát hiện: đóng án, ghi vào OUTCOME, KHÔNG ARM tiếp.

### VI.4 Đa lớp xác nhận (khuyến nghị)
- Mục tiêu: ≥ 2 lớp đồng thuận trước khi ARM (L-03)
- T−k ghi nhận lần đầu ≥ 2 lớp ngược giá → ghi vào hồ sơ
- Chỉ 1 lớp ban = low-conviction, ghi rõ

---

## VII. MM-ECON — Economic Model (v0.2, calibration thực nghiệm)

**Reference đầy đủ:** `docs/proposals/mm_econ_v0.2.md` (ANALYSIS ONLY — operator ký trước khi dùng live)

> **L-KNOW "ô-điền-≠-đã-trả-lời":** Bảng M1 có cột `kho_vol_ratio` cho 6 token — chỉ BANK có số thật (n=1, resolved). ESPORTS/IDOL/TUT/AKE/CLO = PENDING. Ô điền "PENDING" không phải "đã trả lời bằng PENDING" — đó là lỗ hổng chưa lấp. Không dùng cột PENDING để luận kết quả.

### VII.1 Bảng M1 — 6 Campaign (n=2 fully resolved: BANK + ESPORTS; n=1 partial: IDOL)

| Token | Subtype | OI_mult | MM_mult | kho_vol_ratio | T+30 | Status |
|-------|---------|---------|---------|---------------|------|--------|
| BANK | SHORT-WASH | **6.15×** (n=1) | **5.00×** (n=1, HIGH) | **2.6%** (n=1) | +31.3% vs T0 | RESOLVED+CLOSED |
| ESPORTS | 1-WHALE | **2.27×** (n=1) | **2.18×** (n=1, HIGH) | PENDING | PENDING | RESOLVED Jul wave |
| IDOL | NORMAL | **2.73×** (n=1) | **~1.57×** (n=1, MED) | PENDING | PENDING | PARTIAL crowd_flush |
| TUT | CROWD-LONG | LIVE | PENDING | PENDING | T+30=08/08 | LIVE — L-26 chưa |
| CLO | SHORT-WASH | ABSTAIN | ABSTAIN | ABSTAIN | N/A | ABSTAIN — T0 unconf. |
| AKE | FLIP-TO-SW-XL | 23.55× live | PENDING | PENDING | N/A | LIVE — L-26 chưa |

> **Đọc cột n=:** n=1 = chỉ 1 case. Không đủ để gán CI. Dùng để định hướng, không để cắt lỗ/chốt lời theo số cứng.

### VII.2 Phân Loại Subtype (gLSR_base tại T0)

| gLSR_base | Subtype | OI_mult est. | Exit clock | Evidence (n=) |
|-----------|---------|-------------|------------|---------------|
| < 0.70 | SHORT-WASH | 4–8× | D+8→12 | n=1 (BANK 6.15×, D+10) |
| 0.70–0.90 | SHORT-WASH-MILD | 3–5× | TBD | n=0 |
| 0.90–1.30 | NORMAL | 2–4× | D+10→12 | n=1 (IDOL 2.73×, D+11) |
| 1.30–2.50 | CROWD-LONG | 1.5–3× | UNKNOWN | n=0 resolved |
| > 2.50 | 1-WHALE hoặc HYBRID | 2–3× per wave | D+3→5 per wave | n=1 (ESPORTS 2.27×, D+4) |

**Flag FLIP**: Nếu gLSR_base >2.50 nhưng post-ignition flip xuống <0.70 → reclassify **FLIP-TO-SHORT-WASH** (AKE pattern). OI_mult có thể cực cao (AKE live = 23.55×).

### VII.3 M6 — Taker Detection Floor (n=1 BANK)

```
kho_vol_ratio = (kho_tokens × avg_px_at_exit) / total_spot_vol_campaign

kho_vol_ratio < 10%  → ABSTAIN taker detection (on-chain balance thay thế)
kho_vol_ratio 10–30% → Taker signal nghi ngờ được — cần taker <45% sustained ≥2d
kho_vol_ratio > 30%  → Taker signal có thể phát hiện
kho_vol_ratio > 50%  → Taker signal mạnh: sell wall pattern rõ
```

**BANK (n=1):** kho_vol_ratio = 2.6% → taker AMBIGUOUS (confirmed). Rule thực nghiệm — cần validate với ≥2 case thêm.

**Hệ quả P8:** P8 "kéo-sau-ghế-thoát-kho" không thể xác nhận bằng taker spot khi kho nhỏ. Dùng: (a) on-chain exchange balance delta, (b) perp pos_r crash timing vs px peak.

### VII.4 Vòng 2 Watch Criteria (từ BANK Vòng 1, n=1)

Sau khi campaign RESOLVED + kho tiếp tục nạp, cần 3/3 điều kiện để WARN Vòng 2:
1. gLSR ổn định > 1.5 liên tục ≥3 ngày
2. pos_r ổn định > 1.5 liên tục ≥3 ngày
3. Funding pin dương: f_avg > +0.00005 liên tục ≥3 ngày

**BANK Vòng 2 status (05/08):** 0/3 thỏa — funding âm, gLSR đang giảm. Theo dõi tiếp.

**ĐIỀU KIỆN KẾT THÚC CAMPAIGN (L-xx(a) draft):**
- **Loài A:** ghế-rời perp = kết thúc campaign (kho là đạo cụ, MM mất incentive duy trì giá sau khi out).
- **Loài B/C:** ghế-rời perp = CHUYỂN PHA, không phải kết thúc (kho chưa monetize, campaign tiếp tục qua chương kho). Kết thúc thật khi:
  - **Cửa A:** kho/vol-regime ≤ 10% (tàng hình được → xả tự nhiên không lộ tay)
  - **Cửa B:** funding âm sâu + OI cao + pos thấp hậu đỉnh = campaign kết thúc qua short-hedge (TUT pattern 08-06)

### VII.5 — ĐỒNG HỒ THEO LOÀI (L-42 archetype quyết định band)

> **GATE:** Phân loại xong Loại A/B/C (§ III.1) MỚI được tra bảng. Chưa phân loài → output = bảng nhánh, CẤM gán số band.

| Loại | Band ΔOI/B | Exit clock | n= | Đặc trưng |
|------|-----------|------------|----|-----------| 
| **A — kho-mượn** | ~1–2× | flip ≤2 tuần | n=2 (IDOL/CLO, partial) | Cửa ghế sập khi OI tăng 1-2× build; MM trả kho nên exit nhanh; không có "nạp lại" |
| **B — kho-unlock** | ~5–7× | ignite T−7±3 · deposit ≤48h hậu-unlock | n=1 (BANK 6.15×) | Neo lịch vesting cứng; chân-3 = short-hedge tranche tương lai (kho chưa unlock); tell hạng nhất: deposit ≤48h sau event |
| **C — kho-tự-mua** | calib đang chạy (TUT) | cost basis = floor thật | n=0 resolved | Không deadline; conviction genuine; "đi cùng thuyền" duy nhất có nghĩa |

**Nếu chưa phân loài:** xuất bảng nhánh (3 cột A/B/C × giá trị tương ứng) — không chọn một số.

**Nguồn band:** [n=2 IDOL/CLO] Loại A partial-resolved · [n=1 BANK] Loại B. CI chưa đủ → dùng định hướng, không cắt lỗ/chốt lời theo band cứng.

**Ghế-rời vs. Kết thúc campaign (L-xx(a) draft):**
- Loài A: ghế rời = hết ngay. Loài B/C: ghế rời = chuyển pha (kho là bên quyết định đồng hồ, không phải perp book).
- Cửa A exit: kho/vol ≤ 10% → xả tàng hình được → MM bán mà không lộ tay.
- Cửa B exit: MM short-hedge toàn bộ kho qua perp (funding âm sâu + OI cao + pos thấp hậu đỉnh) = campaign kết thúc mà không bán spot.

---

### VII.6 — CÔNG THỨC FORWARD

#### B — Sổ Perp MM (Base OI)

```
B = OI_base = OI tại điểm MM bắt đầu build vị thế
   Dấu hiệu build: OI tăng trong nến xanh + pos_r tăng + funding pin

Trần cứng (hard ceiling):
  ΔOI tổng trong cửa sổ build (chỉ đếm nến đỏ ngày MM ép short)
  = trần lý thuyết của fuel có thể chiết từ crowd

Không có trần (seat-rotation build):
  OI phẳng + pos_r leo = MM rotate ghế (mua long / short đồng thời)
  → không đếm được ΔOI → ước qua pos/acc share [nhãn: INFERENCE]
```

#### Quan hệ ① — exit-VWAP ≈ build_VWAP × (ΔOI/B tại pos_r sập) [n=2]

```
MM_mult = exit_VWAP / build_VWAP ≈ ΔOI/B tại thời điểm pos_r sập ≥30%

BANK (n=1): build=0.0394 · exit=0.1971 · MM_mult=5.00× · ΔOI/B=6.15×  ✓ gần đúng
IDOL (n=1): MM_mult≈1.57× · ΔOI/B=2.73×  (partial — L-26 chưa hoàn tất)

Lưu ý: ΔOI/B ≠ MM_mult — ΔOI đo lượng fuel crowd, MM_mult đo lợi nhuận MM.
Hai số gần nhau khi kho/vol nhỏ (crowd là nguồn lợi chính).
```

#### Trần Fuel từ Crowd Structure

```
SHORT-RICH  (gLSR ≤ 0.6 AND div_avg3 ≥ 3):
  Fuel multiplier est. 3–10× từ nạp gần nhất
  Chạy được cả hậu-ghế (fuel chưa cạn sau exit)
  Mỗi crowd_flush RESET quota mới

LONG-HEAVY  (gLSR ≥ 1.2):
  Fuel multiplier est. 1.2–2× TỪ LẦN NẠP GẦN NHẤT
  Không có flush = không có quota (crowd đã loaded, không còn gì để chiết)
  Crowd_flush phải xảy ra TRƯỚC khi fuel được tái sinh
```

#### Kho/Vol-Regime (chương thoát-kho)

```
kho_vol_ratio = (kho_tokens × avg_px_at_exit) / total_spot_vol_campaign

≤ 3–10%  → xả tàng hình được (BANK 2.6% — không phát hiện qua taker)
10–30%   → taker signal nghi ngờ được (cần taker <45% sustained ≥2d)
≥ 50–100% → chương bán CHƯA THỂ mở (thoát kho lộ tay)
             → phải kéo dài campaign HOẶC chuyển Cửa B:
               Cửa B = short-hedge kho (funding âm sâu + OI cao + pos thấp hậu đỉnh)
```

---

### VII.7 — BA CÂU KẾT ĐỊNH LƯỢNG

> Mọi case sống phải trả lời bằng số (hoặc ABSTAIN có lý do). KHÔNG chấp nhận "có vẻ như" hay "có thể".

```
□ Q1: Loài gì → đồng hồ nào?
      [Loại A/B/C hoặc "UNKNOWN + bảng nhánh"]
      Nguồn: III.1 + VII.5

□ Q2: ΔOI/B hiện tại = ? · cách band (A:1-2× / B:5-7×) còn bao nhiêu ×?
      B = OI lúc MM bắt đầu build (VII.6)
      [số thực / ABSTAIN nếu T0 chưa xác định]

□ Q3: kho/vol-regime → chương thoát-kho mở được chưa?
      kho_vol_ratio = ? → regime (tàng-hình / nghi ngờ / chưa-thể-mở)
      [số thực / ABSTAIN nếu kho data LOCKED]

□ Q4: build-window dài bao nhiêu → kỳ vọng thời lượng campaign?
      build_window_days = OI_floor → T0 · kho_size_est ≈ ?
      Tham chiếu draft n=4 (L-xx(b)):
        BANK  (Loại B): build ~17d → campaign D+17 (chain_close 07-16)
        IDOL  (Loại A partial): build ~7d → campaign D+11 (partial)
        CLO   (Loại A partial): build TBD → campaign ongoing
        TUT   (Loại C): build 13d (07-09→07-22) → campaign D+16+ ongoing
      Hypothesis: campaign_days ∝ build_window × kho_size (chưa đủ n để calib)
      [ABSTAIN nếu T0 chưa xác định]
```

**Mốc invalidate của dự đoán (IV.3 áp cho VII):**
- pos_r drop ≥30% từ peak trong 3d = fuel đã dùng, reset Q2
- funding âm sâu ≥-15bps xuất hiện SAU PIN = Cửa B pattern, re-read VII.6
- OI break dưới floor30d = B mới cần thiết lập lại

---

### VII.8 — DURATION SCALING (L-45 draft, n=4)

> Hypothesis: campaign_days ∝ build_window_days × kho_size. Chưa đủ n để calib — dùng định hướng.

| Token | Loại | build_window | kho_size est. | campaign_days | ratio | Ghi chú |
|-------|------|-------------|--------------|--------------|-------|---------|
| BANK | B (unlock) | ~17d (OI_floor→T0 est.) | kho vesting | D+17 close-iv | 1.0× | Baseline (n=1 fully resolved) |
| IDOL | A partial | ~7d est. | kho mượn | D+11 partial | 0.65× | Partial — exit chưa clean |
| CLO  | A partial | TBD | TBD | ongoing | — | ABSTAIN |
| TUT  | C (tự-mua) | 13d (07-09→07-22) | ~83% supply | D+16+ ongoing | >1.0× | Ongoing — final số chưa có |

**Kết luận tạm:** Với n=4 (2 partial, 2 ongoing), build 13d (TUT) > build 7d (IDOL) → TUT kỳ vọng dài hơn. Số ratio chưa thể calib bởi TUT/CLO chưa resolved. Update khi TUT closed.

*fit/residual/evidence: `docs/proposals/mm_econ_v0.2.md` — playbook thắng khi hai bản lệch, mm_econ là nơi sửa band TRƯỚC rồi sync vào đây (một chiều: mm_econ → playbook).*

---

## Phụ lục A — ĐỊNH NGHĨA BIẾN DẪN XUẤT (canonical)

> Ba biến dưới đây đều từng bị tính sai ít nhất một lần trong sổ.
> Mọi script build case file BẮT BUỘC import/đối chiếu công thức từ đây
> (hoặc signals.py canonical) — CẤM viết lại từ trí nhớ (L-31).
> Khi số trong file lệch định nghĩa này → file sai, định nghĩa thắng.

### A.1 div_raw — tham khảo / cảnh báo sớm

```
div_raw(t) = pos_r(t) / acc_r(t)
```

- Tử = topLSR theo GIÁ TRỊ vị thế · Mẫu = topLSR theo SỐ tài khoản.
  Nguồn câu chữ: U50 "divergence ratio between topLSR_pos and topLSR_acc".
- Vai: tham khảo + cảnh báo sớm (bắt div-flip <1 kiểu L-16 sớm một nhịp).
- **KHÔNG dùng chấm ngưỡng.** Nhạy nhiễu một-ngày của mẫu số.

### A.2 div_avg3 — canonical cho MỌI so sánh ngưỡng

```
div_avg3(t) = avg3(pos_r) / avg3(acc_r)   [avg 3 ngày TỪNG THÀNH PHẦN, rồi chia]
```

- Áp cho: lsr_accum ≥1.5 · hedge_structure ≤0.5 · GOM-A điều kiện A1 ·
  mọi band mục VII.
- **Bẫy toán (CẤM):** `mean(div_raw, 3d) ≠ div_avg3` — trung bình của tỷ số
  ≠ tỷ số của trung bình; lệch mạnh đúng những ngày mẫu số giật.

### A.3 glsr_slope_5d — ratio, không phải %chg

```
glsr_slope_5d(t) = gLSR(t) / gLSR(t−5)   [ratio; 1.00 = phẳng]
```

- Ngưỡng tham chiếu: >1.15 = nhiên liệu đang xả (GOM-A A3 chặn);
  <1.0 = crowd bò về short (fuel nạp).
- Format %chg (+16.6) không hợp lệ — ngưỡng 1.15 chỉ có nghĩa trên ratio.

### A.4 Tiền lệ án (lý do phụ lục này tồn tại)

| Biến | Án | Ngày | Bài |
|------|----|------|-----|
| div_raw dùng chấm ngưỡng | IDOL: raw phồng 2.22 vì acc_r sập MỘT ngày (1.36→0.99), avg3 mượt — suýt chấm lsr_accum sai | 28/07 | Ngưỡng chỉ chấm trên avg3 |
| div sai công thức nền | HEI: build script tự viết div = pos_r × gLSR (tái định nghĩa thuật ngữ) | 08/08 | L-31: import từ canonical, không viết lại |
| div_avg3 sai cách avg | HEI: mean(div_raw 3d) thay vì avg3-thành-phần | 08/08 | Bẫy trung-bình-của-tỷ-số |
| glsr_slope format | HEI: %chg thay vì ratio t/t−5 | 08/08 | Ngưỡng gắn với format |

*Cross-ref: L-16 (div-flip) · L-25 (một-nhà-một-data) · L-31 (câu chữ nguồn) · gom_detect_spec §1 (A1/A3/B1 tiêu thụ các biến này).*
### A.5 Bảng ba-đạo-hàm: Video vs Photo

> Phân biệt "Video" (build thật) vs "Photo" (snapshot đẹp nhưng static) bằng ba tầng kiểm tra.
> Áp dụng khi pos_r >4 hoặc có câu hỏi "BTW hay phân phối?".

| Đạo hàm | Biến | Video (HEI) | Photo (BANANAS31) | Kết luận nếu Photo |
|---------|------|------------|------------------|--------------------|
| 1 — Level | pos_r hiện tại | ~2–4 (vừa) | 6.7 (rất cao) | Level cao ≠ bullish — cần check đạo hàm 2+3 |
| 2 — Slope | Δpos_r 30d OLS | Dương + đồng-trend giá | +0.036/ngày trong dump | Slope dương trong dump = Photo suspect |
| 3 — Sync | sign(Δpos_r) vs sign(ret_1d) | ≥55% đồng hướng | ~50/50 (47.7% opposite) | <55% → pos_r không predict giá |

**Cặp đối chứng (ký 09/08/2026):**

| Chỉ tiêu | CASE_HEI (đối chứng DƯƠNG) | CASE_BANANAS31 (đối chứng ÂM) |
|----------|--------------------------|-------------------------------|
| Verdict | BUILD-setup VALID | NO_SETUP — TRACKING-passive |
| pos_r level | Bình thường | 6.7 (cực cao) |
| Sign-corr Δpos_r/ret | Đồng bộ (>55%) | ~50/50 (47.7% opposite) |
| dist_wall_day / tổng | Thấp | 11.3% (57/503 ngày) |
| flag_knife_crowd | Hiếm | 9 ngày |
| gLSR hiện tại | Trong ngưỡng | 1.20 > 1.1 (block GOM-A A2) |
| Đồng hồ cụm | Active | Hết hạn 06/26, cụm #4 dự kiến Aug-Oct/26 |

**Quy trình khi thấy pos_r cao (>4):**
1. Check **đạo hàm 3** (sign-corr 30d). Nếu <55% → Photo → bước 2.
2. Check **dist_wall_streak** ≥ 3d. Nếu có → MM đang bán vào tăng.
3. Check **gLSR vs 1.1** (GOM-A A2). Nếu gLSR > 1.1 → crowd đã long → mất fuel.
4. Kết: TRACKING-passive, không vào setup đến khi **đồng hồ cụm** kế tiếp trigger (xem L-47).

*Cross-ref: L-46 (Video vs Photo) · L-47 (đồng hồ cụm) · L-48 (Alpha ABSTAIN) · CASE_HEI.xlsx · CASE_BANANAS31.xlsx*



---

## Phụ lục: Cross-reference Lessons theo Lớp

| Lớp | Lessons chính |
|-----|--------------|
| I (Perp) | L-01, L-09, L-10, L-15, L-20, L-21, L-24, L-25, L-41 |
| II (Crowd) | L-11, L-14, L-16, L-17, L-18, L-19, L-26 |
| III (M2/On-chain) | **L-42**, L-05*, L-06*, L-07*, L-27, L-29, L-31 |
| IV (Funding) | L-10, L-20, L-22, L-23 |
| V (External) | L-06, L-28, L-29, L-30 |
| VI (ARM) | L-02, L-03, L-04, L-08, L-12, L-13, L-18, L-38, **L-46, L-47** |
| VII (MM-ECON) | L-42 (archetype), L-26 (exit clock), L-05/B/C (kho classification) |
| DATA | **L-48** (Alpha fullyDelisted ABSTAIN) |

*L-05/06/07: áp dụng khi xác nhận Loại B/C; Loại A xem L-42 trước.*

---

*Playbook v0.2 — cập nhật 06/08/2026: thêm section VII (MM-ECON), LAYER COVERAGE header. cập nhật 08/08/2026: Phụ lục A biến dẫn xuất (án HEI div/slope). cập nhật 09/08/2026: Phụ lục A.5 bảng ba-đạo-hàm (Video vs Photo, cặp đối chứng HEI/BANANAS31).*
*Vị trí canonical: `docs/analysis_playbook.md`. Cập nhật: khi thêm case RESOLVED → update VII.1 + VII.2 n=.*
