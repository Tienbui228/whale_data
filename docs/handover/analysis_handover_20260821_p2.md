# ANALYSIS HANDOVER — 21/08/2026 PHẦN 2 (topic registry/conformance đóng)

**Đọc CÙNG:** `analysis_handover_20260821.md` (phần 1 — bảng case, học thuyết, pipeline). File này chỉ chứa diễn biến SAU phần 1: án E-R doctrine-pack + án conformance lib. Boot topic mới: đọc phần 1 trước, file này sau.

---

## §1. VIỆC DUY NHẤT ĐANG CHẶN ĐƯỜNG

**GÓI CONFORMANCE 21/08 — TRẠNG THÁI: [CHỜ OPERATOR KÝ / đã ký ngày ___]**
Nguyên văn cần ký (nếu dòng trên chưa điền ngày, đòi chữ ký này ĐẦU TIÊN):
> "Ký gói conformance 21/08: ① struct_n canonical = count(div≤0.5), ep_len đổi tên, CẢ HAI consumer dùng canonical — watchlist 20-21/08 audit biên struct_n, lật quyết định → CORRECTIONS lớp-2 ② luật mỗi-consumer-giữ-tiền-extract-của-nó, lib generic + adapter ③ revert B/C/F/G theo bảng A-H (F thành văn vào §E-R1(b): eligibility ≤30d hậu-break) ④ fixture L-58 pin cả hai consumer (HEMI/ON/GUA/CARV/ARIA + 1 case gap), không-pass-không-merge."

Sau chữ ký, chuỗi CƠ HỌC (không còn quyết định doctrine): DEV apply diff → pin fixture → re-run 2 consumer trên snapshot pin → 5-token + 31→27 giải thích trọn A-H → audit watchlist 20-21/08 biên struct_n → tái phát T0-T3 → **Phần B tự kích hoạt** (struct_n=3 nếu bảng giữ kết luận) → ANALYSIS verdict cuối → **PHASE-2 GOM-E full + cron ⚡**.

## §2. ĐÃ KÝ PHIÊN NÀY (chat-ký, đã merge có diff)

1. **§E-R4b v1.2-FINAL** = Version A (px/local_low ≥1.15 ∧ oi/local_low ≥1.30, cooldown 3d, inclusive-D) + BỎ đóng MARKUP-GIỮ (đóng hẳn chỉ RE-HEDGED/EXPIRED-90d/KHO-RÚT) + RE-ARM-MISS log. Wave-end v1.2 = REJECTED (falsified by HEMI), lưu proposals/ header REJECTED. **§2.1 merged vào `proposals/unhedge_registry_spec.md` (46db911, fe4e38c, 22faf1f) — ER-HOME Option 2 ký 21/08.**
2. **Gói E-R doctrine 21/08** (Phần A hiệu lực / Phần B armed):
   - reg% = **weekpeak**/fw-139, cap 25% (thống nhất gate iv + §E-R8②)
   - §E-R8① metric = **MFE_k7 ≥+10% cho ≥50% alerts wave-2+** (30d forward → ANALYSIS-ONLY nếu vi phạm); **wave-1 = INTEL-grade report-only** (fizzle là đặc tính loài, L-54)
   - MISSED-WAVE: scope closed-rows-only; m1 pump-khi-hedged (out-of-scope, evidence GOM-D) / m2 expired-rồi-pump / m3 miss-thật (trigger: ≥3 trong 60d forward → án calib) / HAND-OFF + row-mở-có-trigger = không miss
   - Trần re-arm 50% RÚT → productive-share gap≥2d report-only 30d (falsifier chỉ khi n≥10 ∧ <40%)
   - **Phần B (armed):** struct_n=3 theo luật pre-commit (weekpeak ≤25% ∧ HEMI+ON sống ∧ hit ≥72%) — TỰ kích hoạt khi baseline tái lập, bảng đổi thì chấm lại cùng luật.

## §3. SỐ QUAN TRỌNG TỪ BACKTEST (T0-T3, baseline CHƯA ổn định — đọc như sơ bộ)

- **Wave-2+ MFE: 80% ≥+10%, med +21.1%** — máy chống-miss-×2 hoạt động; med_ret_k7 = −10.9% xác nhận doctrine #10 bằng phân bố (sóng thật rồi dump — thoát bằng HARVEST-tell, không giữ k7).
- Wave-1: 34.3% MFE — cờ-sớm intel, đúng thiết kế.
- **m1 = 19/29 = 65% MISSED-WAVE là pump-khi-hedge-còn** = định lượng đầu tiên lãnh thổ **GOM-D** (draft chờ ký từ 17/08 — án kế tiếp sau phase-2, giờ có 19 bằng chứng biết tên).
- Re-arm: gap≤1d 100% (tautology thiết kế) · gap≥2d productive 66.7%/n=9.
- HEMI chuỗi chuẩn: un-hedge 12/07 → wave-1 20/07 → re-arm 06/08 (px/low 1.160, biên thật) → ⚡ 15/08 = ngày-1 D2. **Câu miss-×2 khai sinh án: ĐÃ trả lời bằng replay.**

## §4. ÁN CONFORMANCE (relay-loss #6 — ngữ-nghĩa-đổi-dưới-tên-cũ)

lib/hedge_episode.py extract (E-R7d) đổi 5+ ngữ nghĩa không ký → baseline trôi 5 token (ARIA/CARV/GUA/SHELL/SIGN) + re-arm 31→27. Bảng A-H phân xử xong (verdict trong chat 21/08 + commit 591b1cb):
- A/D: KHỚP, no action · B/C/F/G: SPEC-IM-LẶNG → mặc-định-cũ, revert phía registry-probe/adapter, KHÔNG chạm lib · E: struct_n = count(div≤0.5) canonical (chờ ký gói) · H: SIGN = data-drift → luật mới: baseline chấm trên **snapshot pin**, đổi snapshot phải khai.
- **⚠ E NHIỄM PRODUCTION:** watchlist từ 8e679d9 (20/08) gate List B bằng ep_len đội tên struct_n = điều kiện ký (≥5) bị nới ngầm — audit 20-21/08 nằm trong gói ký, cửa sổ 2 ngày.
- **L-58-draft** (batch V2): lib-share extract phải kèm conformance fixture pin output mọi consumer, không-pass-không-merge; đổi ngữ nghĩa = amendment ký riêng. Họ L-51 tầng code.

## §5. BÀN OPERATOR (không đổi từ phần 1, cộng dồn)

1. **Gói conformance** (§1 — chặn đường, ký trước)
2. Án E verdict (treo từ 17/08) · COOKIE-GATE-PASS(a) · TST-RESCUE (ngày mất 11+)
3. Batch V2 lessons (L-55→59, giờ gồm L-58 fixture)
4. CAMPAIGN-RIDE v0.1 — thiếu size % + ký nguyên văn
5. Sau phase-2: **GOM-D** (19 evidence m1 chờ)

## §6. NGUYÊN TẮC MỚI PHIÊN NÀY (cộng vào §6 phần 1)

- **Phân-xử-đặt-trước-khi-thấy-bảng**: luật xử A-H đặt TRƯỚC khi số về (spec-nói→spec; IM-LẶNG→tiền-extract-của-chính-consumer) — chống chấm-theo-kết-quả, kể cả của ANALYSIS.
- **Hai biến trùng tên = chưa có biến nào**: struct_n vs ep_len — đình chỉ mọi quyết định dùng biến đó đến khi tách tên.
- **Metric phải khớp vai máy**: registry là máy INTEL trên cụm pump-để-xả — chấm nó bằng ret_k7 close-basis là chấm sai câu hỏi; MFE đo "alert có trỏ wave thật", ret đo "giữ lệnh có lời" — hai câu khác nhau.
- **Backtest "FAIL" có thể là doctrine ĐÚNG**: med_ret âm hậu-alert = xác nhận pump-chức-năng-xả, không phải registry hỏng.

*Hết phần 2. Topic đóng tại: một chữ ký cách phase-2. Kế nhiệm: đòi chữ ký §1, giám sát chuỗi cơ học, rồi chuyển sang GOM-D.*

---

## §7. LỘ TRÌNH ĐỌC CHO ANALYSIS KẾ NHIỆM — HỌC CÁCH PHÂN TÍCH, KHÔNG CHỈ NẠP TRẠNG THÁI

Đọc theo đúng thứ tự. Mỗi tầng ghi rõ: doc nào → dạy gì → tự kiểm bằng gì.

### Tầng 1 — NỀN TƯ DUY (đọc trước mọi thứ, ~1 giờ)
| Doc | Dạy gì |
|---|---|
| `analysis_playbook.md` (trọn, đặc biệt §VIII 14 khối) | Toàn bộ khung đọc: bốn-vân + 2×2 (pos_r × on-chain — bảng phân loại gom-thật vs staged), un-hedge anatomy, rũ-đàn 4 màn, SPRINT/GRIND/BLEED, anti-look-ahead, họ-bệnh-công-thức. **Đây là doc số 1 — thiếu nó mọi số đều đọc mù** |
| `FRESHWATCH_SYSTEM.md` + `INDEX.md` | Kiến trúc 3 vai (DEV/ANALYSIS/Operator), sổ nào ở đâu, ai được quyết gì |
| Phần 1 handover §2 + file này §6 | Các định luật đúc trong 2 phiên gần nhất: định luật #9 (OI-floor = sổ MM, ratio tại OI-peak phải chiết khấu) · doctrine #10 (băng thông xả = Σ van THÔNG) · tử-hay-mẫu · SQUEEZE-FUEL-CHECK · G1 (perp không tách gom/xả — Vân4 operator là separator duy nhất) |

### Tầng 2 — HỌC TỪ ÁN THẬT (cách phân tích nằm ở đây, ~2-3 giờ)
| Doc | Dạy gì |
|---|---|
| `twelve_cases_reference.md` | 12 case calibration = bộ chữ cái: BANK (chuỗi chuẩn S2→ignite→harvest→S5), ON (un-hedge anatomy giáo khoa), BTW (bẫy committed-long — bài đắt nhất sổ), POWER/BASED (S2 early/late), TAG (texture đẹp = S4 ngụy trang), ESPORTS (suppressor thắng texture). **Đọc từng case như đọc chính tả: che kết luận, tự chấm bằng số, rồi so** |
| `lessons_learned.md` / LESSONS sheet | Mỗi lesson = một lần trả học phí. Tối thiểu thuộc: L-21 (nến đóng), L-26 (flush trước bullish), L-28 (retraction protocol), L-37 (backup), L-41 (funding interval), L-48→54 (batch phiên này: schema-drift, write-after-guard, token-identity, venue-thông, captive-vùng-giữa, tín-hiệu-mồ-côi) |
| `u50_verdicts.md` + các `CASE_*.xlsx` (GUA, TRIA, HEMI, CLO là 4 hồ sơ giàu nhất) | Verdict thành phẩm trông thế nào: mọi số kèm nguồn+boundary, nhãn [DATA/INFERENCE/UNVERIFIED], falsifier bắt buộc, đề xuất state. Sheet EVENTS + TRIGGERS của CASE_HEMI = mẫu một chiến dịch được ghi trọn từ nền đến harvest |

### Tầng 3 — MÁY MÓC ĐANG CHẠY (để không phán rule sai lớp, ~1-2 giờ)
| Doc | Dạy gì |
|---|---|
| `gom_detect_spec.md` (A/B/C + §E-R registry) | Signal layer: điều kiện từng máy, ngưỡng nào LOCKED, §E-R = registry un-hedge + RE-ARM + §E-R8 falsifier. Chú ý ranh giới: List-B/registry/GOM-E U-block — ba máy ba tốc độ un-hedge |
| `phase_tag_spec` v0.3.3 | SCREEN layer: cây S0→S5, precedence suppressor-first, luật ground-truth hai-lớp §8.1, render luật (A). Hiểu vì sao PHASE-TAG lỏng-có-chủ-đích so với GOM |
| `hedge_watchlist_spec.md` v1.3+ | List A/B ±1% recall-first, §0 ranh giới cứng "**không phải signal, là chuông gọi đi soi on-chain**" — vi phạm ranh này là nguồn của 2 suýt-ngã phiên trước (TRIA, STBL) |
| `freshwatch_m45_master_plan.md` §1+§5 | State machine 6 pha + signal library gốc — từ điển mọi tên signal xuất hiện trong các spec |

### Tầng 4 — BÀI TỰ KIỂM (làm trước khi nhận việc thật)
1. Mở `CASE_STBL.xlsx` DAILY 14-18/08, che mọi kết luận → tự trả lời: "17-18/08 là un-hedge hay crowd-flip?" bằng tử-hay-mẫu. Đáp án trong chat-log 19/08 (+ phần 1 §1): pos đứng 0.97, acc −35% = mẫu sập = crowd flip short.
2. Cầm ảnh tracker GUA (18/08) + bảng perp → tự khép ô 2×2 → so verdict đã ký.
3. Đọc dòng List B bất kỳ hôm nay → phân loại: NOISE-drip / sự-kiện-registry / cover-thật — dùng ngưỡng drift 0.15 và bài PUMPBTC 20/08 làm chuẩn.
Ba bài khớp đáp án = đủ tay nghề nhận case mới. Lệch = đọc lại tầng tương ứng, đừng nhận việc.

### Nguyên tắc dùng lộ trình
- **Sổ > trí nhớ topic cũ** — mọi mâu thuẫn: tin sổ, flag lệch.
- Doc nào chưa đọc mà việc đụng tới → đọc TRƯỚC khi phát biểu (bài "theo tài liệu hedge_watchlist_spec.md" 19/08: phán rule trước khi mở spec = suýt oan cho bot).
- Học phí đã trả nằm hết trong LESSONS — mỗi lần định "cải tiến" gì, grep LESSONS trước: khả năng cao đã có án.
