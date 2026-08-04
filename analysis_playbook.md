# Analysis Playbook — FreshWatch
**Version:** 0.1 (04/08/2026) · **Chủ sổ:** operator (Tien)
**Nguồn:** tổng hợp từ master plan §1, case_tracker.md, lessons L-01→L-42

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

## Phụ lục: Cross-reference Lessons theo Lớp

| Lớp | Lessons chính |
|-----|--------------|
| I (Perp) | L-01, L-09, L-10, L-15, L-20, L-21, L-24, L-25, L-41 |
| II (Crowd) | L-11, L-14, L-16, L-17, L-18, L-19, L-26 |
| III (M2/On-chain) | **L-42**, L-05*, L-06*, L-07*, L-27, L-29, L-31 |
| IV (Funding) | L-10, L-20, L-22, L-23 |
| V (External) | L-06, L-28, L-29, L-30 |
| VI (ARM) | L-02, L-03, L-04, L-08, L-12, L-13, L-18, L-38 |

*L-05/06/07: áp dụng khi xác nhận Loại B/C; Loại A xem L-42 trước.*

---

*Playbook v0.1 — tạo 04/08/2026. Nội dung thô; operator review + ký trước khi dùng chính thức.*
*Cập nhật: khi có thêm case RESOLVED → update subtype table II.1 + exit clock estimate.*
