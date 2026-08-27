# PHASE-TAG v0.4 — PHÁT HIỆN TỪ 5 CASE PROVEN (BANK · TUT · CYS · AKE · BTW)

**Ngày:** 21/08/2026 · **rev9 (30/08)** (+§9.6 Binance-spot addendum — L-52(c): S1-TUT/S1-BANK/HEMI-THIN sửa) (+§9 trục spot/alpha · csv v3 theo L-52(b) venue-by-median: CYS=bitget, BANK=bitget→gate switch 22/07, BTW=bitget realign) · **Soạn:** ANALYSIS (boot 21/08) · **Trạng thái:** PROPOSAL — chưa ký, chưa phải spec
**Data:** CASE_*.xlsx post-V 21/08 (md5 BANK 34c2e30b · TUT cf83e377 · BTW 2304de27 · CYS cd61959d · AKE 7744cd6d), đã kiểm vol_perp_usd = fapi k[7] 100% (V1), LSR/OI theo LAYER COVERAGE R7. Spot-ext + Alpha = CHƯA-TRA (chờ contract). Vân4 = [chưa-điền] toàn bộ.
**Phương pháp:** đọc tay ANALYSIS trên DAILY (không phải máy replay). CYS đọc MÙ (cắt 12/08, phán trước, mở sau — kết quả §6). Bốn con còn lại đọc biết kết cục → mọi "tell" ở 4 con đó là hậu-nghiệm, chỉ thành luật khi qua test §4.
**Nhãn:** [DATA] số từ file · [INF] suy luận · [HYP] giả thuyết n nhỏ · [FALS] đã bị data bác.

---

## §1. BẢNG TỔNG — chiến dịch theo số [DATA]

| | BANK | TUT | CYS | AKE | BTW (chiến dịch 2) |
|---|---|---|---|---|---|
| Ignition (ngày-1) | 11/07 | 09/07 | 04/08 | 15/07 | 03/08 |
| Close-top | **26/07** | **09/08** | 12/08 | 14/08 (chưa chắc xong) | **20/08 = close-high mới, ĐANG CHẠY** |
| Bội từ close hôm trước ignition | ×10.4 / 15d | ×20.9 / 31d | ×5.9 / 8d | ×55.8 / 30d | ×5.4 / 17d |
| Drawdown sau top → 20/08 | −90% | −84% | −67% | −19% | — |
| gLSR tại close-top | 0.43 | 0.45 | 0.60 | 0.48 | 0.60 |
| pos_r tại close-top | 1.31 | 1.15 | 0.81 | 0.84 | 1.67 |
| acc_r hôm trước ignition → min D0-D3 | 0.68 → 0.63 (đã short sẵn) | 3.68 → 1.34 | 1.56 → 0.38 | 2.40 → 0.34 | 1.52 → 0.66 |
| B2h harvest_drop bắn lần đầu | 13/07 (D+2) | 09/07 (D+0) | 05/08 (D+1) | 16/07 (D+1) | không bắn (pos giữ 1.5-1.9) |
| Giá còn đi ×? SAU khi B2h bắn | **×9.0** | **×19** | ×2.0 | **×10.3** | — |
| OI đỉnh tuyệt đối rơi ngày | 27/07 (= top+1, ngày đỏ đầu) | 10/08 (top+1) | 13/08 (top+1) | n/a (OI từ 23/07) | 19/08 (rồi 20/08 lập high mới) |
| Funding trong markup | ghim ~0 | ghim ~0 | squeeze âm (−0.69/−0.96%) | dương (leg-1) → squeeze −1.16% (24/07) | dương 0.04-0.10%/d |
| taker_buy trong markup | 50-52% | 48-53% | 50-52% | 50-52% (57.9% chỉ D−1) | 50-52% |

Đọc ngang: **taker không phân biệt được gì** (5/5 ≈ 51%); **gLSR ở đỉnh đều ≤0.6** (5/5); **B2h bắn đúng ngày vào** (4/4); **OI đỉnh = ngày đỏ đầu sau top** (3/3 case đã xong).

---

## §2. BA LOÀI NỀN (pha 1) — trả lời câu "gom hay có sẵn hàng"

| Loài | Case | Chữ ký perp tại nền | Gom hay có sẵn? |
|---|---|---|---|
| **(i) whale-long-vs-crowd** | BANK | div 3.4-5.5 + gLSR 0.45-0.8 từ **ngày đầu có data 09/06** (≥32d trước ignition); funding ghim; OI $4.3-4.7M chết; probe 02/07 (vol 10×) → bait-flush 03/07 (gLSR −40%); pos_r rebuild 2.91→3.72 (03→10/07) khi giá bò xuống đáy tháng | GOM trên perp rõ nhất bộ. Vân4 để xác nhận kho rút tại nền [chưa-điền] |
| **(ii) captive-long-pinned** | TUT, CYS | Crowd long 2-3:1 (TUT gLSR 3.1-3.6; CYS 1.0→1.9), pos_r thấp-phẳng (TUT 4.4≈acc; CYS 1.3-1.4), funding ghim ≥14d, OI sàn, giá nén hoặc chảy. TUT: shakeout 05-08/07 (pos −30%, OI −14%) rồi ignition hôm sau. CYS: pos_r rebuild +26% tại OI-floor 17/07→01/08 | Perp KHÔNG cho thấy gom (pos_r không leo ở TUT; CYS leo nhẹ). Nếu có gom, nó nằm ở kho/Vân4 — đúng note Tiên "CYS gom onchain" [chưa-điền] |
| **(iii) staged-dump-kho-sẵn** | AKE, BTW | AKE: nạp 11B lên Gate (twelve_cases) + đạp −28%/−35% trên vol 9× (04, 07/07, taker 42-47%) → plateau 8 ngày → pos_r +33% (1.19→1.59, 08-14/07) → taker 57.9% D−1. BTW: listing-pump 04-20/06 không có nền perp; tháng 7 = captive-long base (pos 1.6→2.0, gLSR 1.0→2.2, OI 6.7→12.7M) → shakeout 01-02/08 (vol 11×) → run | **CÓ SẴN HÀNG** — đúng trực giác Tiên. Pha 1 trên perp = rũ-bằng-đạp + plateau ngắn, không phải texture tích lũy dài |

→ Không có một texture "gom" chung. Cái chung 5/5 ở nền chỉ là **funding ghim/trung tính + OI sàn + giá nén** — và đó cũng là texture của đa số token chết. **Chưa có control set thì không được nâng thành luật** (xem §4).

---

## §3. PHÁT HIỆN XUYÊN CASE

**F1 [FALS] — "Cờ đỉnh gLSR→~1" SAI.** 5/5 close-top xảy ra khi gLSR 0.43-0.60 (củi còn đầy). gLSR về 1 chỉ xuất hiện **sau** cú sập (BANK 29-31/07: 0.39→0.94→1.8; TUT 13-15/08; CYS 16-18/08) = short cover vào dump. → Bỏ khỏi cờ đỉnh twelve_cases; chuyển thành texture S5 (hậu-sập).

**F2 [FALS] — B2h harvest_drop không phải HARVEST.** **5/5** (HEMI 16/08 D+1: pos_r 3.61→1.47 = −59%, sau đó +62%) bắn tại D+0..D+2 của ignition, sau đó giá ×1.6-19. pos_r sập khi OI nở ×1.5-3 = **pha loãng tập top-account** (định luật #9 chiều ngược), không phải ghế rời. BTW (pos_r giữ 1.5-1.9 suốt run) cho thấy khi MM thực sự long trong top-set thì ratio **không** sập. → Đổi tên B2h thành SEAT-DILUTION, giá trị = "không vào mới", KHÔNG phải "chuyển pha". Acceptance §7 #7 ("BANK 19-21/07 + TUT 02+05/08 phải bắn") đang neo vào **ngày cắt data của topic cũ**, không phải đỉnh: BANK top 26/07, TUT top 09/08.

**F3 [HYP n=3/3, 1 case đang test] — TOP-CONFIRM trễ 1 ngày.** Ngày đỏ đầu tiên (≤−10%) sau close-top = ngày OI đạt max tuyệt đối (BANK 27/07, TUT 10/08, CYS 13/08). BTW đã có 2 lần "ngày đỏ + OI max" (17/08, 19/08) rồi vẫn lập high mới → precision chưa biết; BTW tuần này là test sống. Dùng cho cổng 🔻, không dùng để đoán đỉnh.

**F4 [DATA 5/5] — Củi short được chính cú pump tạo ra trong 1-3 ngày.** acc_r sập 57-86% từ D−1 đến D+3 ở 5 nền crowd-long (TUT/CYS/AKE/BTW/**HEMI** −71% D+1). BANK không cần (crowd đã short). Sau cú lật, mỗi case còn đi ≥×2. → SQUEEZE-FUEL-CHECK (gLSR giảm trong pump = còn chân) xác nhận 5/5 như tín hiệu **tiếp diễn**; TRIA (gLSR tăng = bẫy) là mặt đối. Đây là tell sớm nhất có độ tin cao **sau** ignition — vật liệu cho CAMPAIGN-RIDE "registry-ngày-1".

**F5 [HYP n=3/4] — POS-REBUILD-AT-FLOOR.** pos_r +25..33% trong ≤14d khi OI ở sàn, funding ghim, giá phẳng/xuống: BANK 03→10/07 (lead 1-8d), CYS 17/07→01/08 (lead 3-18d), AKE 08→14/07 (lead 1-7d, OI không có). TUT **không có** (pos giảm trong shakeout, rerate 3.0→5.8 xảy ra SAU ignition 12-15/07). Máy v0.3.3 không nhấc cả 3 vì ngưỡng div 1.5/S2-LATE đo bằng mức, không bằng delta. → Amendment A1, cần control.

**F6 [DATA] — taker_buy_pct vô dụng cho 5/5.** 50-52% suốt markup; cú duy nhất >55% là AKE 14/07 (D−1, vol 0.93× med → trượt vol-floor). s3_eve = loài hiếm; bid-walk/squeeze là mặc định.

**F7 [INF] — Hai đồng hồ khác nhau.** BANK/TUT/CYS: một parabol rồi sập −67..−90%. AKE: ba chân 30 ngày, top-account **net short** (pos 0.73-0.86) suốt leg 2-3 mà giá ×3 → mua nằm ở spot/Alpha, perp = két hedge bị squeeze (doctrine #10: pump-chức-năng-xả kho Gate). BTW: top-account long giữ 1.5-1.9 + crowd short + funding dương = cấu hình BANK 24-26/07 (div 3.2-4.0, gLSR 0.45-0.6, OI ×15 nền, ×8.7 từ đáy). n=1 tham chiếu — **không phải dự đoán**, là cảnh báo vị trí.

---

## §4. AMENDMENT ĐỀ XUẤT CHO v0.4 (mỗi cái kèm test đăng-ký-trước, operator chọn số)

| # | Đề xuất | Bằng chứng | Test trước khi ký |
|---|---|---|---|
| A1 | Thêm sub-signal S2 **POS-REBUILD-AT-FLOOR**: Δpos_r ≥[+25%]/≤14d ∧ oi ≤[1.2]×min30 ∧ funding ghim ∧ \|ret14\| ≤[10%] → S2-MID↑ bất kể mức div | F5 (3/4) | Chạy trên fw-139 60d: bao nhiêu token bật / bao nhiêu đi ≥+50% trong 30d. Tiên chọn ngưỡng từ phân bố (recall-first) |
| A2 | B2h → **SEAT-DILUTION** (intel, không đổi stage) khi OI ≥[1.5]×med14 cùng cửa sổ; HARVEST chỉ khi pos_r sập mà OI **không** nở | F2 (4/4) | Replay 5 case: SEAT-DILUTION phải bắn D+0..2; HARVEST không được bắn trước top |
| A3 | **TOP-CONFIRM** (cổng S4, trễ 1d): ret ≤[−10%] ∧ oi = max30 ∧ close14d-ago ≤ c/[3] | F3 (3/3 + BTW đang test) | Forward 30d + replay 12-case; nếu BTW lập high sau 19/08 ≥2 lần nữa → precision <60%, hạ xuống intel |
| A4 | Xóa "gLSR→1" khỏi cờ đỉnh; thêm texture S5: gLSR từ <0.6 lên >0.9 trong ≤3d **sau** ret ≤−25% | F1 (5/5) | Replay: không case nào gLSR>0.9 trước close-top |
| A5 | **CROWD-FLIP-D3** (tín hiệu tiếp diễn cho registry/CAMPAIGN-RIDE): acc_r −≥[50%] trong D0..D3 của breakout → continuation; acc_r tăng → bẫy (TRIA) | F4 (4/4 + TRIA đối) | Registry §E-R8 forward: MFE_k7 của alert có CROWD-FLIP vs không |
| A6 | Ghi vào playbook §IX: **taker không phải trục phân biệt**; s3_eve giữ nhưng hạ ưu tiên | F6 (5/5) | — |

**Điều kiện cứng cho mọi A:** có **control set** (≥20 token fw-139 không đi ≥+50% trong cùng cửa sổ) trước khi ký. 5 positive không đủ — bất kỳ luật nào cũng "đúng" trên tập toàn positive (L-53 cấm p-hack).

---

## §5. ĐÍNH CHÍNH SỔ (ANALYSIS tự đề xuất, Tiên ký)

1. **BANK top = 26/07, không phải 19-21/07.** twelve_cases "smart money đã ra 19-20/07" viết tại ngày cắt data; sau đó +40-70% nữa. EVENTS BANK + phase_tag §7 #7 phải re-date. CASE_BANK OUTCOME: ×10.4 (26/07) → −90% (0.0351, 16/08).
2. **TUT top = 09/08 ×20.9**, không phải "+37% grind" — grind 16/07-02/08 chỉ là chặng giữa; parabol 03-09/08 ×11. OUTCOME T+30 (08/08) = 0.10907 [DATA], 20/08 = 0.03277.
3. **AKE "staging xả 20/07" = SAI.** Ba chân đến 14/08, ×55.8. Sổ đọc đúng cơ chế (redeposit, kho Gate) nhưng sai kết luận giá.
4. **BTW "chương xả nghi đã mở 12-13/08" (handover 17/08) = FALSIFIED-SO-FAR**: +59% sau đó, close-high 20/08. Xả qua spot có thể đang xảy ra cùng lúc (doctrine #10) nhưng perp không cho thấy đỉnh. Trạng thái đề xuất: DISTRIBUTION-WATCH giữ nguyên, thêm cờ "đang ở vị trí BANK 24-26/07 theo 4 biến" [INF n=1].
5. **BANK chu-kỳ-2 (tháng 8):** nền hiện tại là crowd LONG (gLSR 1.3-2.0 = người mua đáy kẹt), pos_r 1.3→1.9 leo chậm, OI 11-18M (×3 nền cũ). Khác hẳn nền chu-kỳ-1 (crowd short = củi). Loài = committed-long captive (BTW-July, L-53) → GOM im là đúng; STAND-ASIDE đến khi gLSR <1 + Vân4 rút.
6. **Lỗi đọc của ANALYSIS (ghi để không lặp):** CYS mù — P1 "còn 1 chân" SAI (đỉnh là chính ngày đọc), P2 nửa, P3 đúng. Bỏ sót tell 12/08: +55% với **OI −26%** = long đóng vào lực mua cưỡng bức (nhưng BANK 22/07 +26%/OI −46% rồi vẫn lên 4 ngày → tell này **không đủ một mình**, cần kèm vol-divergence: BANK 26/07 vol 721M vs kỷ lục 1.6B; CYS 12/08 322M vs 476M). [HYP]

---

## §6. BẢN ÁN ĐỀ XUẤT GHI EVENTS (ranh giới pha, nguồn [DATA perp] trừ chỗ ghi)

**BANK:** P1 ≤09/06→10/07 (loài i; probe 02/07; bait-flush 03/07; rebuild 03-10/07) · P2 = 02-03/07 + rũ giữa markup 21/07 (−31.7%) · P3 11/07→26/07 · P4 27/07→02/08 (OI 70.8M→17M; −90%) · Chu-kỳ-2 base 03/08→ (loài captive-long).
**TUT:** P1 ≤21/06→04/07 (loài ii, pin 29d) · P2 05-08/07 shakeout · P3a 09/07→02/08 grind (+85%) · P3b 03-09/08 parabol (×11) · P4 10/08→ (−84%).
**CYS:** P1 01/06→16/07 BLEED + **17/07→03/08 rebuild-at-floor** (tell) · P2 16-17/07 probe + 29-30/07 (rũ không thành) · P3 04→12/08 · P4 13/08→ (OI đỉnh 13/08, wick 1.84 15/08, −67%).
**AKE:** P1 ≤03/07 nạp Gate [twelve_cases, Vân4 chưa-điền] · P2 04+07/07 đạp −28/−35% · P1' plateau 08-14/07 + rebuild +33% · P3 leg-1 15-18/07 (×8), leg-2 23/07-01/08 (×3, squeeze 24/07), leg-3 13-14/08 (×2.5) · P4 = CHƯA XÁC ĐỊNH (20/08 −19%, OI 32M, top-set short, crowd short).
**BTW:** Chiến dịch 1: listing-pump 04-20/06 (high 0.2051) → bẫy 22-26/06 (pos 1.72 giữ, funding −0.10% 26/06) → −62% · Chiến dịch 2: P1 01/07→31/07 captive-long base · P2 01-02/08 (−22% / vol 11×) · P3 03/08→ ĐANG CHẠY (20/08 close-high 0.4348) · P4 —.

---

## §7. TIÊN CẦN CUNG CẤP (xếp theo giá trị)

1. **Vân4 tại 5 cửa sổ** (ảnh tracker/on-chain): CYS 17/07-03/08 · BANK 27/06-10/07 · AKE 03-14/07 (Gate) + 20/08 (kho còn bao nhiêu) · BTW 01-31/07 + hôm nay · TUT 27/06-08/07. Mỗi ảnh đóng một ô 2×2; không có ảnh thì pha 1 của 5 case treo ở [INF].
2. **5 contract** → nhịp 2 (spot-ext/Alpha) → phân xử AKE/BTW "mua ở đâu" (F7).
3. **Quyết định A2** (đổi nghĩa B2h) — đây là thay đổi semantics spec, cần ký riêng (L-57/L-58).
4. **BTW hôm nay:** Tiên có vị thế không? Nếu có, F3/F7 là cảnh báo cho người cầm, không phải lệnh.

---

## §8. VIỆC MÁY SAU FILE NÀY

- DEV: harness replay (câu treo) — chạy v0.3.3 trên 5 DAILY để so với §1 (máy vs tay; tay không phải ground truth).
- Agent: nhịp 2 khi có contract; control set 20 token fw-139 60d cho §4.
- ANALYSIS: sau control set → bảng "% bắt / % báo giả" từng A → Tiên chọn số → v0.4 viết trên nền v0.3.3 consolidated (SYNC-PACK E1).



---

## §9. TRỤC SPOT/ALPHA — bổ sung 21/08 sau csv per-day (scratch/spot_alpha_5case_daily_20260821.csv)

**Nguồn + trạng thái:** venue = 1 sàn vol lớn nhất (BANK mexc · TUT gate · CYS gate · AKE gate · BTW bitget), Alpha = bapi (BANK/TUT fullyDelisted → không có). **Contract 5/5 UNVERIFIED** (bapi symbol-string, chờ operator so tracker). **CYS vol_alpha = X5 SUSPECT** — kết luận CYS dưới đây đứng trên Gate (identity PASS), Alpha chỉ phụ họa. BTW bitget = **1Dutc realign** (csv v2) → đọc ngày được. BANK venue = **Gate** (MEXC loại theo L-52-AMD 21/08; số MEXC trong v0.2 đã rút). Vol không có side: mọi câu "mua/xả" dưới đây là [INF], băng thông là [DATA].

### §9.1 Ba ô treo

| Ô | Kết quả | Nhãn |
|---|---|---|
| **CYS 17/07→03/08 — gom?** (venue = **Bitget**, median-winner $180K > Gate $145K) | 17/07→02/08: Bitget $17-142K = **0.1-0.9× nền** ($162K), Alpha 0.1-1.1× → **không có khối lượng gom** trên spot sàn suốt cửa sổ pos_r rebuild (29/07 ×2.4 là ngày bán). NHƯNG **03/08 (D−1): Bitget $321K = ×2 nền, share 40% perp, perp ×0.52 nền (chết), giá −0.8% → hôm sau +98.6%**. Gate cùng ngày 0.2× nền — **sàn thắng 24h (Gate) hoàn toàn không thấy**; chỉ sàn thắng median (Bitget) thấy | [DATA] CYS **CÓ spot-lead D−1** trên đúng một sàn. Gom tích lũy vẫn không hiện qua sàn → Vân4 cho 17/07-02/08; pha 1 CYS = ghế perp (pos_r rebuild) + **kho động trên Bitget đúng hôm trước** — lai (ii)+(iii). Kết luận v0.3 "không có spot-lead" = **sai do chọn sàn** |
| **AKE — mua ở đâu?** | Leg-1 (15-18/07): spot+Alpha share 1.2-1.5% → perp-led squeeze. **D−1 14/07: Alpha ×6.6 + Gate ×4.6 nền trong khi perp ×1.0 (phẳng), share 29%/23%, giá +0.5%** → SPOT-LEAD sạch nhất bộ, khớp twelve_cases "7B rút khỏi Gate 14/07". **Leg-2 (22-24/07): Alpha ×119→401 nền ($17.6M→$59.6M), Gate ×207-314 ($35-53M), share 8-13%** (gấp 7× leg-1) đi cùng funding perp −1.16% + top-set pos<1 → chân 2 = spot/Alpha dẫn, perp bị squeeze. Leg-3 (13-14/08) share về 3% = perp-led lại | [DATA] băng thông; [INF] hướng. Với kho ~22B token (~$55M tại 0.0025), hai ngày 23-24/07 có **$85-110M/ngày spot+Alpha** = đủ băng thông để monetize trọn kho trong leg-2 (doctrine #10). Vân4 20/08: kho còn bao nhiêu? |
| **BTW 03/08→20/08** (realign) | Nền tháng 7: spot share (alpha+bitget)/perp **9-15%** — dày nhất bộ. 27/07: perp ×14 trên +3.6%, spot share rơi 5% = churn perp ẩn. Run tháng 8: share giữ **8-15%** mọi ngày, không có ngày spot-lead (11/08 = 10.9%, bình thường — con số 34% trong v0.2 là artifact UTC+8, **rút**). **19/08: Bitget ×129, Alpha ×51, perp ×113 — cùng tỷ lệ, share 8.7% không đổi** → flush toàn thị trường (thanh lý), KHÔNG phải chữ ký xả-qua-spot; ứng viên đỉnh của BTW chỉ còn đứng trên perp (F3/F7). **20/08: share 3.9% = thấp nhất run**, high mới làm trên spot mỏng [INF: đẩy perp-only]. **Tuần bẫy 22-26/06: share leo 6→10→14→19→25.5%** mỗi ngày khi giá đứng 0.094-0.101 = spot dày dần trong khi perp đỡ giá → khớp cơ chế twelve_cases [DATA vol / side chưa]. **18/06: Bitget $32.8M (×46 nền), share 56%, perp chỉ ×5, giá +7% → hôm sau +90%** = SPOT-LEAD thứ hai của bộ |

### §9.2 Phát hiện xuyên case trên trục spot

**S1 [DATA 3/3] — Nền của BANK/TUT/CYS không có KHỐI LƯỢNG gom trên spot sàn** (lead D−1 của CYS là chuyện khác — S2). BANK Gate nền $40K (09/06→01/07, nhiều ngày $4-20K), share **0.5-2% trong MỌI pha** (nền · probe 02/07 ×6.7 cùng perp ×8.2 · ignition ×10 cùng perp ×10 · đỉnh · sập · chu-kỳ-2) — spot BANK là **follower thuần**. Bitget pre-22/07 (venue median-winner kỳ đó) thêm 3 ngày giữa tháng 6 (17, 19, 24/06) ×2-3 nền ($200-350K) share 10-13% trên perp chết — hoạt động spot nhỏ tại nền [INF: gom lẻ?], không phải lead (ignition 17 ngày sau). TUT gate $3-53K (≤2.2× nền) suốt pin. CYS như §9.1. → Loài (i)/(ii) tích lũy (nếu có) bằng **ghế perp + ví on-chain**, không bằng spot CEX. Spot-ext cols 51-52 ở nền ba con này đúng là ~0 thông tin — phải ghi N/A-THIN chứ không nên đọc.

**S2 [DATA 3/3 D−1] — SPOT-LEAD hôm trước ignition, ở mọi case có kho trên sàn.** AKE 14/07 (share 23-29%, Gate ×4.6 + Alpha ×6.6, perp ×1.0, hôm sau +257%) · **BTW 18/06** (share 56%, Bitget ×46, perp ×5, hôm sau +90%) · **CYS 03/08** (share 40%, Bitget ×2, perp ×0.52, hôm sau +98.6%). Cả ba đều **đúng D−1**, không sớm hơn. BANK: không (Bitget 10/07 0.78× nền, share 2%) — loài ghế-perp thuần. TUT: không D−1 sạch, chỉ ramp 03-07/08. **Tell này sống trên MỘT sàn** (CYS: Bitget có, Gate không) → sweep phải quét mọi van THÔNG cho marker, dù cols 51-52 chỉ lưu một. TUT biến thể **SPOT-SHARE-RAMP**: share leo 4.3→4.5→7.8→8.2→**11.5%** qua 5 ngày 03-07/08 (×32→×296 nền) ngay trước ngày +180%; rồi rơi về 2% khi perp ×750-2000 nền. BANK/CYS: không có. → Khi MM có kho trên sàn, kho động trước perp; khi MM chỉ có ghế perp, spot im.

**S3 [HYP n=4] — Spot share dày lên khi chiến dịch già.** AKE leg-1 1.3% → leg-2 9% · TUT grind 2-4% → tiền-blowoff 11.5% · CYS P3 3% → P4 6.4% (Gate ×100 nền trong 3 ngày sập) · **BTW bẫy 22-26/06: 6→25.5% leo 5 ngày liền khi giá đứng** (ca rõ nhất, nằm đúng pha xả). BANK chu-kỳ-2 đã rút khỏi danh sách (MEXC). Cơ chế [INF]: pump tạo băng thông, kho ra qua băng thông đó (doctrine #10) — tức **spot share tăng ở pha muộn = kênh monetize mở**, ứng viên marker S3-LATE/S4 rẻ hơn mọi ratio perp.

**S4 [HYP n=3] — Alpha nổ trên nến đỏ hậu-đỉnh.** AKE 17/08 ×80 (share 8.9%), BTW 19/08 ×51, CYS 13-17/08 ×35-98 trong cú sập. Alpha = van BSC hướng retail; nổ ngày đỏ = retail bắt dao hoặc kho xả vào retail — không có side. Giữ làm cờ S4/S5 documentation, chưa phải rule.

**S5 — RÚT TOÀN BỘ (v0.2 → v0.3).** "BANK chu-kỳ-2 có chân spot" đứng trên MEXC = wash. Gate: share 0.7-1.6% suốt 03-20/08, 13/08 ×27 nền nhưng perp ×70 cùng ngày (share 0.78%) = theo perp; 17-20/08 $130-220K. **Không có regime spot nào ở chu-kỳ-2.** Giả thuyết chu-kỳ-2 BANK quay về đứng trên mỗi pos_r 1.3→1.9 + Vân4. Bài: venue xếp theo 24h hôm nay chọn sai sàn (MEXC chỉ thành #1 về sau; Gate nền tháng 6 lớn hơn) → xếp theo median window.

### §9.3 Amendment bổ sung (cùng điều kiện control set §4)

| # | Đề xuất | Bằng chứng | Test |
|---|---|---|---|
| A7 | **SPOT-LEAD** (D−1 tell): trên **bất kỳ** van THÔNG: venue_vol ≥[2]× nền-pha ∧ share(venue+alpha)/perp ≥[20%] ∧ perp_vol ≤[1.5]×med14 ∧ \|ret\| ≤[10%] → cờ 1-2 ngày. Cols 51-52 giữ 1 venue; **marker quét mọi venue** (ops: chỉ cho token đang S2-MID↑/RIPE) | AKE 14/07 · BTW 18/06 · **CYS 03/08** (3/3 D−1) · BANK/TUT không | fw-139 60d: tỷ lệ ngày bật được theo sau ≥+30%/3d; chỉ áp token có venue THÔNG vol ≥[$100K] (loại thin) |
| A8 | **SPOT-SHARE-RAMP** (S3-LATE marker): share tăng [3] ngày liên tiếp ∧ đạt ≥[2×] median-pha-P3 ∧ giá đã ≥[×3]/14d | TUT 03-07/08; AKE leg-2; CYS P4; BANK c2 | Replay 5 case + control; đo precision như F3 |
| A9 | LAYER COVERAGE cột 51-52: venue vol ≤[$100K]/ngày ∧ share ≤[2%] → ghi `THIN`, máy không đọc | S1 (BANK/TUT/CYS nền) | — |

### §9.4 Sửa sổ do chính §9

- Lời ANALYSIS 21/08 "BTW 18/08 Bitget ≈ perp" = artifact UTC+8 → **rút**; chỉ 19/08.
- 11 dòng EVENTS agent ghi 21/08 (CAMPAIGN/WAVE-2/SPOT-EXT-LEAD) = heuristic, nhiều dòng trái §6 (CYS start 08/08 vs ignition 04/08; BANK "WAVE-2 13-14/08" là ngày −14%/−4%) → đổi type `AGENT-HEUR-*`, không dùng làm ranh giới.
- CYS vol_alpha col 35 đã ghi số dù X5 SUSPECT → revert về `ABSTAIN-SUSPECT(X5)` cho đến khi X5 giải; §9 CYS không dùng Alpha làm trụ.
- v0.2 dùng MEXC cho BANK và bitget chưa realign cho BTW → mọi số BANK/BTW trong v0.2 thay bằng v0.3; S5 rút; BTW 11/08 SPOT-LEAD rút; BTW 19/08 hạ từ "xả ba van" xuống "flush toàn thị trường, share không đổi".
- v0.3 đọc CYS trên Gate (sàn thắng 24h) → kết luận "CYS không có spot-lead" **SAI**; rev4 đọc Bitget (sàn thắng median, L-52(b)) → CYS có lead D−1 03/08. Bài: **sàn chọn sai = tell biến mất**, không phải "tell yếu".
- Bitget bar = UTC+8 → **VENUE-BAR-BOUNDARY-draft** (bước 3b cạnh L-51 price-band); audit mọi venue đang dùng ở case khác (PUMPBTC-bitget, TRIA-bybit, STBL/HEMI gate-mexc-kucoin).

### §9.5 Câu Vân4 thu hẹp sau §9 (thay §7.1)

1. **CYS ví 17/07→03/08**: có chuyển kho ví→ví / OTC không? (spot sàn đã loại trừ — đây là câu duy nhất còn lại cho pha 1 CYS)
2. **AKE Gate balance 22/07 vs 25/07 vs 20/08**: kho 22B ra bao nhiêu trong leg-2?
3. **BTW deposit Bitget + Alpha/BSC 18-19/08** và tuần 22-26/06.
4. **BANK 13-20/08 flow on-chain** (MEXC loại, Gate không có tín hiệu): chỉ ví → ô trống duy nhất còn lại của chu-kỳ-2. Thêm: **BANK Bitget 17-24/06** — ví nào nạp/rút Bitget tuần đó?
6. **CYS Bitget 02-03/08**: deposit lên Bitget hôm 02-03/08? (spot-lead D−1 = kho động — ai?)
5. TUT 03-07/08 Gate: nạp trước blowoff? (SPOT-SHARE-RAMP là gom-vào hay xả-ra)

---

## §10. TRỤC VÂN4 — tracker operator (ảnh 23/08, [DATA-Vân4], số đọc từ biểu đồ ±5%)

| Case | Nền / staging | Trong markup | Sau đỉnh | Top-100 |
|---|---|---|---|---|
| BANK | 580M → **rút −225M (−39%) 01-02/06** = D−40; phẳng 350M suốt nền + ignition. (Zoom 17-25/06 hiện 588M = view lỗi; 1Y xác nhận 350M.) Tiên: kho chuyển cho MM tháng 6 | **+70M ~19-20/07 (climax) · +180M ~29/07-01/08 (trong sập)** → về 590M = đúng số đã rút | phẳng → chu-kỳ-2 **không có gì** on-chain | 51% |
| TUT (lời Tiên) | không nạp ở nền pin | nạp 29-31/07 = D−3..−5 trước parabol | −84% | — |
| CYS | 80M → **rút 3.5M (19-21/07) → nạp lại 4.5M (24-26/07)** = vòng OTC trong cửa sổ pos_r rebuild | **nạp +10M (+13%) 03-05/08** = D−1..+1 (trùng spot-lead Bitget 03/08) → giữ 85-88M | 82-85M: kho không rút = đã bán vào pump | 81% |
| AKE | 16.5B → **nạp +14.5B (02-05/07)** = D−10..−13 | 31B → 23B (16/07) → **8B (26/07)** → 4.5B: rút −85% float sàn khi giá ×55 | rút tiếp | **86%** (+50%) |
| BTW | 570M → **nạp +75M (26-27/07)** = D−7 (trùng perp ×14 churn 27/07) | phẳng 645M → **rút −295M (−46%) 14-20/08, −130M đúng ngày flush 19/08** | cao mới 20/08 | **96%** |
| HEMI | 490M phẳng | **nạp +90M (+18%) 14-15/08** = D−1..D0 → 592M (+2%) | (đang chạy) | 770M |

**V1 [DATA 6/6] — KHO-STEP trước chân nổ, ở mọi case.** |Δ số dư sàn| ≥10% trong ≤3 ngày: BANK rút D−40 · AKE nạp D−10..−13 · CYS vòng D−9..−16 rồi nạp D−1 · BTW nạp D−7 · TUT nạp D−3..−5 · HEMI nạp D−1..0. **Không case nào mở màn bằng gom thị trường.** Dấu không cố định (BANK rút), nên detector là **bậc thang bất kể dấu**. False positive có sẵn: BANK 04/2026 nạp +255M, 3 tháng không campaign → một mình chưa đủ, phải ghép nền nén.

**V2 [HYP n=5, +HEMI đang test] — Hướng số dư sàn trong markup tách kết cục.** Rút ròng (AKE −85%, BTW −46%) ↔ đa chân, top-100 ≥86%. Nạp ròng (BANK +70%, CYS +13%, TUT) ↔ một parabol rồi −67..−90%. HEMI nạp +18% rồi +2% → rơi ô "nạp" → dự đoán §11.

**V3 — F7 cho BTW bị Vân4 bác.** Perp: BTW ≈ BANK 24-26/07 trên 4 biến. Vân4: BANK climax = nạp, BTW 19/08 = rút −130M. BTW cùng loài AKE, không cùng BANK. **Cảnh báo "vị trí BANK" rút.** Tell thoát cho loài này = ngày đầu nạp ròng sau chuỗi rút (T4.4), chưa có.

**V4 — CYS pha 1 = STAGED.** Vòng rút→nạp (OTC về MM) + pos_r rebuild cùng tuần + spot-lead Bitget D−1 + nạp +13% trong pump + kho không rút sau đỉnh. 2×2: pos_r leo ∧ NẠP → staged-pump. Khớp −67%.

**V5 — Trả lời câu operator "nếu biết sắp đẩy thì xây long perp trước":** 6/6 không có long perp lớn ở nền (OI $1.6-8M, ghế chỉ +22-33%). Lợi nhuận của họ ở kho (top-100 51-96%). Perp dùng làm: ghế nhỏ · **hedge short** (AKE/BTW/HEMI top-set short hoặc div<0.7 ở nền) · máy gặt crowd. Cái họ làm trước khi đẩy là **gỡ hedge** (div 0.5→1.0 tại OI-floor: AKE, CYS, HEMI) chứ không phải xây long — registry §E-R xây đúng trên cái này. Đề xuất doctrine (chờ ký): *pha 1 = HANDOFF (kho-step) + SEAT-LIFT (pos_r +25% hoặc div 0.5→1.0 tại OI-floor); perp giữ vai xác nhận/thời điểm.*

---

## §11. HEMI — case thứ 6 (CASE_HEMI post-P6, md5 xlsx theo agent; DAILY 01/06→22/08; spot Gate THIN, Alpha delisted)

**Loài nền:** (ii) captive-long + **hedged**: acc 3.0-4.2, gLSR 2.4-3.4, pos_r 1.7-2.4 → div 0.47-0.68 (episode hedge 05-09/07, struct_n=5), funding ghim 5e-5, OI $1.6-2.3M, giá 0.0043-0.0056. Giống TUT (crowd long 3:1) cộng top-set short-lệch — đúng loài registry.

| Mốc | Ngày | Số [DATA] | Đối chiếu 5 case |
|---|---|---|---|
| Probe | 01/07 | +22% vol ×4, hôm sau −7.7% OI +39% | PROBE T1.5 (D−19 trước wave-1) |
| Un-hedge | 12/07 | div_avg3 0.47→0.57→0.68 (16/07), pos_r 1.75→2.32, OI phẳng 1.8-1.9M, giá −4% | = **SEAT-LIFT** (V5): AKE/CYS cùng khuôn |
| Wave-1 | 20/07 | +51.5% vol ×50, **OI phẳng** cùng ngày; 21/07 −21.6% **OI ×3.1**, acc 4.0→1.9 (−52%), pos 2.11→1.27 | Fizzle → registry đúng: wave-1 = INTEL |
| Re-arm | 06/08 | px/low14 1.205 · **oi/low14 1.073** · pos_r 2.70 | ⚠ xem ghi chú dưới |
| Pos-rebuild | 10-14/08 | pos_r 3.16→3.61 (+22%) khi giá −5/−8/−2%, OI phẳng 3.2-3.3M, acc 3.8-3.9 | T1.3 ✓ (4/6 giờ) — lead 1-4d |
| Kho-step | 14-15/08 | nạp +90M (+18%) | V1 ✓ 6/6 (D−1..0) |
| Spot-lead | 14/08 | Gate $32K, share 1.3% | **THIN — không quan sát được** (T0.2 phải tắt tell) |
| ⚡ ignition | 15/08 | +43.6% vol ×46, **OI ×2.8 cùng ngày** (khác 5 case: OI nổ D+1) | registry nói CÓ tại D0 close |
| Crowd-flip | 16/08 (D+1) | acc 3.78→1.11 (**−71%**), gLSR 2.79→1.07, vol ×110 (ngày lớn nhất), giá −10.6% | F4 5/5 → tiếp diễn: sau đó ×1.6 |
| B2h "HARVEST" | 16/08 (D+1) | pos_r 3.61→1.47 (−59%) — sổ gọi 18/08 "HARVEST −57%, ghế rời" | F2 5/5: **ghế-loãng, không phải rời** — giá +62% sau |
| Leg-2 | 19/08 | +22.7%, OI ×1.9 (8.9→17.1M), gLSR 1.25→1.01 | SQUEEZE-FUEL |
| Leg-3 / close-high | 21/08 | 0.01017 (+17%), vol $281M, OI đỉnh 16.6M **trên ngày xanh**, gLSR 0.92, pos 2.13, funding +0.02%/d | ×2.1 từ 14/08 · gLSR thấp ở high mới = F1 |
| 22/08 | | −1.7%, OI −12.7%, gLSR 0.76, acc 0.95, pos 2.30, div 2.15 | crowd short 1:1.3 = củi còn; top-set long giữ (kiểu BTW) |

**Verdict sổ "KHÔNG-VÀO / STAGED-DIST, pha MUỘN nhất cụm" (21/08) viết tại 0.0070 trên HARVEST-tell; giá +46% sau đó.** Giữ KHÔNG-VÀO (×2.1, staged, nạp kho), **rút chữ "pha muộn nhất"** — nó đứng trên F2 đã bị bác.

**⚠ Re-arm 06/08 không thỏa Version A theo số agent:** oi/local_low14 = 1.073 < 1.30 (px/low 1.205 ≥1.15 ✓). Sổ ghi "re-arm 06/08 (px/low 1.160, biên thật)" — hai bộ số khác nhau (1.205 vs 1.160). Hoặc cửa sổ local_low của agent khác spec (inclusive-D, 30d?), hoặc re-arm 06/08 trong sổ là sai. Không kết luận — DEV đối chiếu nguyên văn §E-R4b rồi tính lại, paste công thức + số.

**Dự đoán đăng ký cho HEMI (chấm sau 14 ngày):**
- H-P1: số dư sàn KHÔNG rút ≥15% (ô "nạp" V2) → close-top ≤ +30% trên 0.01017, trong 21-28/08.
- H-P2: sau close-top, −50% trong ≤14 ngày; OI đỉnh tuyệt đối rơi ngày đỏ đầu (F3).
- Falsifier: số dư sàn rút ≥15% → HEMI là loài SUPPLY-SQUEEZE, H-P1/P2 hủy, V2 thêm một điểm ngược chiều.

**HEMI cho "nhận ra sớm":** kho-step D−1 (Vân4) · pos-rebuild D−1..−4 (perp, máy v0.3.3 không nhấc) · registry ⚡ = D0 close. Không có tell nào sớm hơn 4 ngày ngoài un-hedge 12/07 (34 ngày, nhưng wave-1 fizzle xen giữa). Spot mù vì THIN.

---

## §12. ON — case thứ 7 (CASE_ON post-O5; DAILY 10 tháng, LSR/OI từ 27/06; spot Gate $108K median; tracker 90D)

**Loài nền:** hedged-waiting giáo khoa (đúng sổ): acc 2.0-2.8, gLSR 2.4-3.3, pos_r 1.1-1.7, div 0.42-0.77, funding ghim, OI $1.4-2.0M. Episode hedge 29/06-02/07 (struct_n=4).

Chuỗi: **SEAT-LIFT hai mode** — 02/07 pos_r 1.12→1.66 (+48%, tử-leo) rồi 13-19/07 acc 2.72→1.61 (mẫu-sập = rũ-đàn 4 màn của sổ), div cắt 1.0 đúng 20/07 · **kho-step +10% 13-19/07 (D−6..−1, tracker — cụm ví insider sổ đã ghi)** · wave-1 19-20/07 (+19%, +30%) · crowd-flip chậm: acc −33% D+3, **−63% D+5** · B2h bắn 23/07 tại 0.193 → **×2.1 sau** · nạp kho +90% (14.5→30.8M) trong markup 20-27/07 → giá vẫn ×2.1 tiếp (0.19→0.4028) · close-top **13/08** · nay 0.2516 = **−38%**, kho phẳng 28M (không rút = đã bán vào pump), gLSR 0.54 (crowd short kẹt chiều ngược).

**ON phá F3:** OI max tuyệt đối rơi **28/07 — ngày +84% giữa campaign**, không phải ngày đỏ sau top; 14/08 (đỏ đầu sau top) OI 16.8M < max30 → TOP-CONFIRM **không bao giờ bắn** cho đỉnh ON. F3 giờ: 3/4 case-xong hit (miss ON) + BTW 2 false → **A3 hạ xuống intel-flag**, không đủ làm cổng đơn độc.

**ON thêm một tell hậu-top [HYP n=1]:** 16/08 (3 ngày sau top, giá phẳng) Gate $3.59M = ×33 nền, share **25.8%** → hai ngày kế −11%, −18%. SPOT-DIST-BURST — cùng họ S3.

Pending: **un-hedge date chính thức chưa có trong sổ** — registry đang chạy trên proxy auto 02/07; operator ký milestone (một dòng) trước khi ON được dùng làm anchor conformance.

## §13. CAP — case thứ 8, COLD (perp 27/06, contract VERIFIED bit-compare; tracker 90D)

**Spot/Alpha CAP = NHIỄM WASH SỐNG:** ngày artifact share (alpha+bybit)/perp = 480-2300% (04/07 · 08/07 · 24-25/07 alpha $598-639M · 05-08/08) — u50 "wash-machine 2000:1" xác nhận về loài, sai về ngày (10/07 không reproduce vì đó là ngày máy wash TẮT). → trục spot CAP tắt theo LAYER-COVERAGE; đọc perp + on-chain.

**Perp:** bleed 0.027→0.016 (11/07) với **lsr_accum BANK-texture: div 2.0-2.3 ∧ gLSR 0.63-0.80 suốt 05-19/07** (T1.4 giờ 2/8: BANK, CAP) — u50 17/07 đọc "0.63→1.08 xả" chính là nền này. Rồi crowd đảo long (acc 0.79→2.49, 20-29/07), ignition 30/07 +32%/OI ×2, crowd-flip 31/07 (acc −61% D+1 ✓), thang + squeeze: funding min −0.52% (06/08) · −0.56% (14/08) · **−0.81% (15/08)**, close-top ~0.0705 (17/08), nay 0.0702 (22/08) = retest, ×4.4 từ đáy, OI 13M, gLSR 0.68-0.98, div leo 1.24→1.81.

**On-chain (tracker):** nạp-BẬC liên tục +103% (120→244M) qua toàn campaign (đúng taxonomy SPRINT của sổ), **phẳng tuần cuối** cùng giá phẳng tại đỉnh. Registry im đúng thiết kế (0 episode div≤0.5 — CAP chưa từng hedge).

**Dự đoán đăng ký CAP (loài "nạp", V2):** C-P1: không còn chân ≥+50% từ 0.0702; C-P2: −40% trong ≤21 ngày kể từ khi kho ngừng nạp (mốc: tuần 16-23/08 đã phẳng). Falsifier: kho rút ≥15% → CAP đổi loài, C-P hủy.

## §14. BỘ ĐẾM SAU 8 CASE (BANK · TUT · CYS · AKE · BTW · HEMI · ON · CAP)

| Tell | Đếm | Đổi gì |
|---|---|---|
| V1 KHO-STEP trước chân nổ | **8/8** | vững nhất bộ; CAP = nạp-bậc liên tục, ON = +10% D−6..−1 |
| F2 B2h = ghế-loãng (giá ×2-19 sau khi bắn) | **7/7** (ON ×2.1 · CAP ×3.7) | đóng án — đổi tên bắt buộc |
| F1 gLSR <1 tại mọi đỉnh | 8/8 (ON 0.79 · CAP 0.94-0.98) | giữ phản-tell |
| F4 crowd-flip | 6/7 trong D+3 (ON −63% tại **D+5**) | nới cửa sổ [D+3]→[D+5] khi calib |
| SEAT-LIFT (div cắt ~1.0 hoặc pos +25% tại floor) | **6/8** (miss TUT, BTW) · hai mode: tử-leo / mẫu-sập — log tử-hay-mẫu | định nghĩa M2 giữ, thêm mode |
| T1.4 lsr_accum (BANK-texture) | 2/8 (BANK, CAP) | giữ, ưu tiên thấp |
| F3/A3 TOP-CONFIRM | 3/4 xong + **miss ON** + BTW 2 false | **hạ xuống intel**; M5-D thoát = thang + vol-divergence, không tựa một cổng |
| SPOT-LEAD D−1 | 3/3 nơi quan sát được (ON/HEMI/CAP: spot thin/poisoned → tắt) | giữ, kèm coverage |
| V2 hướng-số-dư (nạp→parabol / rút→đa-chân) | 5 xong đúng + ON đúng hướng (−38%) + 3 forward (HEMI, CAP, BTW/AKE) | phép thử sống lớn nhất |

---

## §15. BTR — case thứ 9 (CASE_BTR cold-start 02f0a347; DAILY 01/05→22/08; spot [UNVERIFIED-contract]; tracker 90D; giá 23-26/08 ngoài file, đọc từ tracker)

**Án khởi đầu "watchlist không bắt" — phân xử 7 giả thuyết:** a✗ (div xuống sâu 0.26-0.37, không mù trục) · b✗ (struct_n 25/15 ≫5) · c✗ **tin tốt: gate List A trong code = `sn_count_le050` canonical — fix conformance đã sống, án D5 đóng chiều này** · d✗ · e✗ · **f/g ✓ = lỗ VẬN HÀNH.** Bằng chứng bác RCA "BTR không có trong freshwatch": LSR BTR non-null **27/06→22/08** với đúng dấu vân gap 24-25/07 của store — LSR tháng 7 **không thể backfill ngày 24/08** (fapi retention 30d chỉ với tới 26/07) → BTR được thu sống trong universe từ 27/06; tag vol/taker 24/08 là rebuild toàn-universe F5/⑩, không phải bằng chứng vắng mặt.

**Replay + forensics CHỐT (29/08, thay toàn bộ RCA cũ — "log 3 run" là artifact grep, đã rút):** máy **detect BTR từ 11/08** (8 rows List A+B, div 0.3258, drift 12/08) — đúng ngày wave-1 +42.4%; List B bắn 10-12/08 (delta +0.10→+0.238). **Alert-wire Telegram = 13/08 (fed3369)** → hai tầng miss, không tầng nào là máy-sai:
- **11-12/08 = cost-of-wiring**: detect có, kênh chưa nối (họ save_snapshot — máy tính mà không nói). Từ nay fixture có assertion tầng-alert trong wrapper Telegram.
- **14→23/08 watchlist im ĐÚNG LUẬT** (thoát List B >2d, chuông hedge hết việc by design). Im lặng trước ⚡ D0 23/08 thuộc **phase-2 chưa deploy**, không thuộc nghi-thức-đọc.
- **Ngày biên 13/08 = [PENDING-GREP]**: report gửi 13/08 có dòng BTR không? Có → một alert tới tay và trôi (hở-đọc thật, một ngày). Không → chuỗi miss không có chân lỗi-người.
Gap 18/08 một đêm (pre-STALENESS-FIX) = ghi chú forensics, không án. **Spec + code + vận-hành-run đều vô tội** — BTR là hóa đơn hai chân của wiring-timing + phase-2.

**Chuỗi campaign (M-machine):**
| Mốc | Số [DATA] |
|---|---|
| Kho-step #1 | +20M (+35%) 23/06→01/07 — **trùng ngày mở hedge episode #1 (29/06)** |
| Nền | hedged-captive cực đoan: gLSR **3.9-4.0** (crowd long 4:1, cao nhất bộ 9), pos_r 1.06, div 0.26-0.37, hedge 46 ngày (ep_len production 5→46) |
| Kho-step #2 | +18M 28/07→02/08 — **trùng ngày mở episode #2** → ứng viên sub-pattern **DEPOSIT+HEDGE-NGAY** (họ PUMPBTC farm-có-bảo-hiểm) [HYP n=2] |
| Un-hedge | 11-14/08: div 0.30→0.37→0.50→0.72, break xác nhận 14/08 |
| Wave-1 | **11/08 +42.4%**, px/low14 1.86, **oi/low14 3.47** |
| Re-arm-quiet | 12-22/08: giá 0.028-0.031, kho phẳng 104M, div hồi về 0.58 (21-22/08 — nghi re-hedge dở) |
| Ignite | **23-26/08 +178% → 0.083** [tracker], **kho nạp +19%** (104→123.7M) trong pump → loài NẠP |

**Registry cost-of-delay #2:** chuỗi un-hedge → wave-1 → quiet 10 ngày → ignite của BTR là đúng khuôn miss-×2 mà §E-R sinh ra để bắt; ⚡ 23-24/08 lẽ ra reo — **phase-2 cron chưa deploy** nên không ai reo. HEMI được cứu bằng probe tay; BTR thì không.

**Dự đoán đăng ký (loài NẠP, V2):** B-P1: một parabol, đỉnh ≤[+60%] trên 0.083 trong ≤7 ngày; B-P2: −50% trong ≤14 ngày sau đỉnh; falsifier: kho rút ≥15% → BTR đổi loài, hủy cả hai.

**Bộ đếm cập nhật (9 case):** V1 KHO-STEP **9/9** (BTR ×2 step, mỗi step mở một hedge episode) · gLSR<1 tại đỉnh: chờ BTR đỉnh · SEAT-LIFT: BTR = mode div-cắt ✓ (7/9) · List-B-đúng-thiết-kế: BTR chứng minh chuông kêu đúng chỗ **khi máy chạy**.

---

## §9.6. ADDENDUM BINANCE-SPOT (rev9, 30/08 — sau L-52(c); nguồn: tut/bank/hemi_binance_spot_20260827.csv, md5 trong report agent)

**Bối cảnh:** sweep cũ mù Binance spot (giả định theo-lớp); BANK/TUT/HEMI có listing, vol gấp 4-43× venue cũ. Mọi số spot của ba con trong §9.1-9.4 đọc trên sàn 1/4-1/43 chợ → các dòng dưới đây THAY THẾ.

**TUT — claim operator "chỉ phát hiện được bằng spot được gom", phép thử đăng ký, 3 tầng [DATA]:**
- Pin-era 21/06→08/07: vol med $335K = **0.66× nền** tiền-pin ($505K), taker mean 50.0%, CVD ≈ +$4K/ngày (nhiễu), **0 ngày absorption** (vol≥1.5× ∧ |ret|≤3% ∧ taker≥55%).
- Lịch sử 15 tháng (518 bar): **CVD âm gần như mọi tháng** 03/25→06/26 (đỉnh bán: 10/2025 −$11.2M trên −77% capitulation); dương lần đầu = tháng campaign 07-08/26.
- **Verdict: NOT-VISIBLE-at-daily-tape** — không tín hiệu gom nào dựng được từ klines ngày, kể cả trên sàn thật.
- **NHƯNG — caveat cơ học quan trọng (mới):** taker-CVD **mù cấu trúc với gom-phía-maker**. MM ngồi bid → người bán hit bid → tape in taker-SELL trong khi MM đang gom. CVD âm 15 tháng *tương thích* với gom-qua-bid suốt bleed (và cũng tương thích với xả — tape không tách được). → **G1 sâu thêm một tầng: ngay cả tape sàn đúng cũng không tách gom/xả; trục tách của loài TUT là HOLDER (kho 83% trên sàn, top-100) = Vân4/Nansen holder-trend, không phải volume.** Claim của operator đúng về BẢN CHẤT (gom tại/trên sàn), sai chỗ DẤU VẾT (không nằm trong klines).

**BANK — S1 sửa số [DATA]:** share Binance/perp tại nền = **22.9%** (không phải "0.5-2% follower thuần" — số cũ đọc trên Gate). Spot = 1/4 chợ ở nền. Timing vẫn đồng pha perp (probe 02/07 share giữ 22.8%) → "follower về timing" đứng, "spot chết" rút. Mới: **D−1..D0 taker 45.5%** — giá +13% trên taker-sell ròng = người mua là MAKER [texture gom-passive, HYP].

**HEMI — hai sửa [DATA]:** (1) "spot THIN" **rút** — share nền-pha 25/07-13/08 = **27.2%** ($978K/ngày); THIN là artifact Gate. (2) Spot-lead D−1 14/08: **vẫn KHÔNG có, giờ vì lý do đúng** — vol 14/08 = 0.64× nền (điều kiện ≥2× trượt xa), không phải vì không nhìn thấy. S2 giữ 3/3. Mới: **10-11/08 shakeout hấp thụ tại taker 37.8-41%** (CVD −$500K/2 ngày, giá giữ) — cùng texture maker-absorption với BANK [HYP n=2, ứng viên tell, chờ control 27/09 — KHÔNG phải rule].

**Hệ quả cho mắt-thứ-ba:** loài captive KHÔNG cứu được bằng sweep spot-volume (TUT chứng minh); nguồn đúng = **holder-trend** (exchange-dominance/top-100/smart-money từ Nansen). SPOT-ABSORB nếu có thì là taker-THẤP (maker-side), ngược hẳn ngưỡng ≥55% tôi đăng ký — ghi để control-set kiểm cả hai chiều.

*Hết rev9 (30/08). Không số nào trong file này là ngưỡng doctrine; mọi [ ] trong §4/§9.3 là chỗ trống Tiên điền.*
