# HANDOVER ANALYSIS � 2026-08-17
Topic cũ �óng (context �ã compact). File n� y = mục "��c thứ nhì" trong INDEX.md.
**Boot topic m�i:** INDEX.md � analysis_playbook.md � FILE N�Y � TASKS.md � CASE_INDEX.
Nguyên tắc thừa kế: topic m�i �ứng trên S�, không �ứng trên trí nh� topic cũ. M�i s� trích từ CASE_*.xlsx / spec / report � file n� y ch� TR�, không thay s�.

---

## §1. BẢNG TR� NG TH�I CASE (17 h� sơ)

| Token | State | C� �ang canh / vi�c treo |
|---|---|---|
| **AIN** | TRACKING-ACTIVE · DEPOSIT-LEAD (m� 17/08) | K� $2.4M vs spot $10.6K/ng� y � **nếu n� bắt bu�c perp-centric/FOMO-mode**. Canh: un-hedge NUM (pos+15%/2d + OI co) · D5 churn �8� = S1-CONFIRMED (�i�m entry duy nhất) · gLSR xuyên 2�1.2. Falsifier: nạp+bleeding (RIVER-shape) / 3-4 tuần im. CẦN OPERATOR: ladder verify 30M · ví ngu�n (vesting? cụm?) · unlock · contract |
| **AGT** | WATCH-template-BTW · canh S1 DAILY | Marker S1 = deposit-v�-s� n (kh�i 520M quay lại) + churn �8�. **Nh�p cụm ~12d: GUA 05-08/08 � AGT cửa s� � NGAY B�Y GI� (17-20/08)**. Un-hedge tell �ã thêm TRIGGERS. Sensor: ví insider operator. Falsifier: ví bán s�m / 6-8 tuần không S1 / ignite thẳng từ gLSR �2.7 |
| **GUA** | S2-WATCH · DISTRIBUTION side | **�N LSR-MERGE M�I** (§4) � file rebuild mất LSR, ��i chiếu backup 10/08. PENDING: un-hedge check 08-10/08 (calib GOM-E #2). Vol Alpha 16/08=$234K � cần chu�i so n�n T7 + tuần n� (FOMO tắt chưa?). C� xả: gLSR�1 · deposit thêm · dist_wall |
| **BTW** | DISTRIBUTION-WATCH | Fire 10/08 = state-conflict (net_k3 +$14.8M = FOMO �u thang, KH�NG phải gom). Depth 12-13/08 �9.3% bid-stack � chương xả nghi �ã m�. C�: pos_r sập · gLSR�1 · deposit thêm. CẦN OPERATOR: BscScan trace cụm nạp 100M � ví insider 03/07 |
| **ON** | DISTRIBUTION-WATCH · S2-leg3 | Trim rải pos 1.66�1.13. Fire 14/08 = state-conflict. **Un-hedge anatomy 17-18/07 = ground truth GOM-E** (§2). C� xả: pos<1.0 · gLSR�1 · deposit thêm |
| **APR** | DISTRIBUTION-WATCH (13/08) | OI $50.5M FOMO-long ��nh + deposit +11.5M TRONG pump = staging xả. GOM-D positive #6 (bậc 10-11/08 � +192% 12/08, T�2). **�ính chính: DEX vol thật $807K/ng� y � s� $42.6M RETRACTED (double-count/wash)**. �N LSR-merge cùng GUA |
| **FF** | WATCH-B-M� NH | Ch� pos_rerate (+0.23/+0.25 sát nút) · CONFIRM 0.1 �áy-n�n (klines patch) · L-44 packet ch� ký. Audit $2M khép: gross $1.99M/net +$0.75M/VWAP $0.0645. Unlock 29/09, ignite window dự phóng 19-25/09 |
| **TUT** | TRACKING (wave-2 watch) | Xác nhận wave-2: pos �óng �2.8 giữ 2d + pin + gLSR �1.1. Bác b�: pos<2.0 + funding âm + deposit (Cửa B). **T+30 scorecard VẪN ch� operator feed v� thế** (nợ từ 08/08) |
| **BANK** | Vòng-2 watch · **UNLOCK 17/08 = H�M NAY** | 3 �i�u ki�n (crowd_flush gLSR �30%/3d · pos>1.5 b�n · tái pin) � 0/3 tại 05/08, CẦN REFRESH S� M�I. Verdict cũ vẫn treo chữ ký. Composite mẫu v� ng: fire 04/07 � nạp $11M 15-26/07 � +144.9% |
| **COOKIE** | TRACKING-ACTIVE hậu-reset | REARM-WATCH: P1 re-pin �3d � P2 div�1.0 b�n + chạm 1.5 � P3 pos build, overlap �1d; falsifier div�0.5/5d � reset. COOKIE-GATE-PASS definition (a) ch� ký. Fire 03/08 không s�ng sót rechấm v1.5 |
| **KOMA** | TRACKING-ACTIVE (cặp COOKIE) | Chưa từng pin 43d � **pin �ầu tiên = tín hi�u tr�ng s� cao**. Sau �ó: div�1.5 b�n + pos ��  � GOM-A. Falsifier: crowd bò lại �3:1 |
| **TST** | �ang-cháy (squeeze 04-07/08) | **TST-RESCUE LSR status UNKNOWN � VERIFY NGAY** (deadline rolling, m�i ng� y mất 1 ng� y phim; l�nh phát 09/08). Sau rescue: re-chấm screens + Q2 khép "gom bao nhiêu" |
| **CYS** | Fire 13/08 · mg14 �18.3% | Note operator: "gom trên onchain". **CASE_CYS collect �ã prompt � KẾT QUẢ CHƯA V�**. L�  positive-case GOM-H cũ (archived) � gi� ch� cần case thư�ng |
| **BANANAS31** | TRACKING-passive · ��ng h� cụm #4 Aug-Oct | **Fire M�I 14/08 (file 70-fire) � ��ng h� cụm có th� �ang �i�m, cần ��c**. Chu�i marker: flush lửa long (gLSR�0.7 + pos giữ) � vol �3� � tell |
| **HEI** | STAND_ASIDE �ến ~20/08 � **SẮP HẾT H� N** | ��c lại wave-5: fuel �ã cháy (short-cover 07/08), cần fuel m�i. Serial squeeze 4 wave |
| **XPIN** | NO_SETUP passive | Negative-case #3 gate H (�ã archive). CẦN OPERATOR: trace redeposit 05-07/08 |
| **BROCCOLIF3B** | NO_SETUP passive (trại farm) | M� lại khi: giặt kế tiếp m�  crowd KH�NG bò lại + div flip �1.5 + pin �ầu tiên |
| **ZBT** | Trạng thái cũ WATCH-A/ARMED-candidate | Không revisit topic n� y. Fire-list: mg14 +3.3%, note operator "rút 13M+5M �ảo cơ mkt" |

**Cụm ví insider (trục xuyên case):** ON deposit 13-19/07 � BTW 26/07 � GUA 05-08/08 � ví 03/07 @0.06 � ��i chiếu ��a ch� = vi�c operator; trùng �3 vân � MM_BOOK h� sơ cụm �a-token �ầu tiên, AGT �ược trực bằng sensor lo� i.

---

## §2. H�C THUYẾT PHI�N N�Y � CẦN APPEND PLAYBOOK (chưa v� o, sẽ mất nếu không ghi)

1. **B�n-vân GOM THẬT + bảng 2�2** (khung trung tâm): Vân1 tử-s� pos_r leo · Vân2 chi-phí (pin trả HOẶC div<1 thu) · Vân3 ki�m-soát-giá (dip b� mua-�ảo) · Vân4 on-chain R�T-tại-n�n. Bảng: (pos leo? � rút/nạp?) � trên-trái=GOM THẬT (FF/ZBT/TUT, �i cùng) · dư�i-phải=STAGED-DIST (ON/BTW/GUA/APR/AIN, tránh �ư�ng). "Gom bao nhiêu" v�i captive = câu sai thì.
2. **Giải phẫu un-hedge ON** (ground truth): trình tự chuẩn lo� i **deposit(T�6) � flush(T�5) � un-pin+un-hedge(T�2, pin vỡ + cover C�NG NG�Y 17/07, pos +30%/1d + OI_token giảm êm 2d) � ignite(T0, tr� 1 ng� y) � +230%/12d � div không bao gi� quay lại <1**. Tử-mẫu bắt bu�c: cover thật = TỬ S� + OI co; DENOM-thaw (acc sập) = flush, không phải un-hedge.
3. **Hai tư thế ch� của captive**: hedged-waiting (div<1, thu funding � ON/AGT/GUA/AIN) vs committed-long (div�1.3 � BTW). Pin không phải �i�u ki�n cần của lo� i (ON có 47d, BTW không).
4. **Thư�c rũ-�� n 4 m� n** (ON): bò-sữa � rũ-thất-bại (flush crash �� n bò lại) � **rũ-bằng-NẾN-XANH** � lật phe (xuyên 1.0). M�c: gLSR 1.2/1.0. Quy luật: nến l�n nhất ch� �ến SAU �� n sạch. �ừng ��c "gLSR rơi trong rally" l�  mất ��  � �ó l�  m� n rũ �úng b� i.
5. **M6 HAI CHẾ ��** (operator sửa khung, GUA 11/08): STEALTH-mode (�10% vol hi�n h� nh) vs **FOMO-mode (pump TỰ SẢN XUẤT vol � KOMA $1.2B/48h/MC $8.5M; bán v� o euphoria + bán tiếp v� o collapse)**. K�/MC >100% (GUA 260%) = bắt bu�c FOMO-mode/nhi�u-wave/perp-centric. Dùng stealth-math cho FOMO-campaign � "bất khả thi" giả.
6. **Taxonomy nạp-k� SPRINT/GRIND/BLEED** (70-fire ground truth 15/08): nạp-BẬC + giá giữ = SPRINT ��ng h� 1-6d [APR/BANK/BULLA/CAP/GUA] · nạp-��U + giá giữ = GRIND tuần-tháng, **cu�i cùng vẫn >80%** [BTR/AT/TURTLE/BMT] · nạp + giá BLEEDING = xả [RIVER]. **Discriminator thắng/thua = CHI�U GI� trong cửa s� nạp; hình dạng ch� quyết T�C �� ��ng h�.**
7. **Composite fire�deposit** = hai thì m�t câu: fire = ghế xong; nạp-bậc sau fire 1-22d = ��ng h� ignite (BANK fire 04/07 � nạp 15-26/07 � +144.9%).
8. **Outcome-window THEO LO�I**: sprint 7-14d, grind 30-60d/t�i-sự-ki�n. M�t cửa s� chung tự chế nhóm "flat" không t�n tại (án BTR/AT/TURTLE/BMT b� mg14 dán flat trong khi >80%).
9. **Fire-date = m�c �o ti�n-��nh** (close-date �o hậu-campaign, câu h�i khác) + **anti-look-ahead**: filter ch� dùng thông tin có tại �i�m entry (net>0-tại-close l�  look-ahead; bản hợp l� = net-to-date tại fire+K).
10. **proven_pump prior** (PARTI): team chưa từng �ẩy +100%/�7d � m�i staging mang mùi xả. Check EVENTS m�t dòng.
11. **net_k3 âm �ậm = c� xấu �n ��nh** (SKYAI �11.3M � hold 0.157; cụm �0.6M..�1M ��u flat/âm). Dấu dương không ch�n ngư�i thắng (BANK âm vẫn +145%).
12. **��nh luật #5 validated thêm** (TUT: gLSR 1.11 � ��nh sau ~24h) · **pin vỡ = phát l�nh** (ON/TAG-khuôn) · **APR lesson: pin/build KH�NG phải �i�u ki�n cần lo� i event-serial có fuel-short sẵn** � GOM-A fire + oi_floor + gLSR�1.2 + nh�p event = �ủ nâng WATCH-B (autopsy WATCH-C miss �3).
13. **H� b�nh công thức** (regression checklist): mean-of-ratios (M1) · **share-based-metric mẫu-s�-phụ-thu�c-archetype** (h2 confound; biến th� #2 = hi�u-tuy�t-��i scale-dependent � h2r ratio-log l�  chuẩn) · outcome-window-��ng-loạt (§2.8).
14. **Check-trạng-thái-trư�c-phát-bi�u**: trư�c verdict nhắc m�t h�/spec � check s�ng/chết trong s� TRƯ�C (án A�H 13/08: ANALYSIS viết trên H-tier �ã archive vì ��c context nén).

---

## §3. SPEC PIPELINE

| Spec | Trạng thái | Vi�c kế |
|---|---|---|
| **GOM-A/B/C v2.0 + v1.5 M1-M5** | Production. A3=A3f slope-fuel (�2 phân xử xong). **Gate GOM-C 15/08: C1 ký 12/08 �, KẾT QUẢ GATE CHƯA B�O V� TOPIC � H�I NGAY** | Verify �1/�2 �ã sync commit · ��c kết quả gate |
| **GOM-D staged-pump v0.9** | Draft n=6 positive + negative sửa lại (��u-trong-bleed, không phải ��u) + amendment DEPOSIT-WATCH 3 nhánh sau m�i A/B-fire | **CH� K�: hư�ng + ngu�n D3** (a BscScan watcher / b tracker-feed / c Nansen / d Dune-probe � Dune tự chấm bằng 3 bậc ground-truth) |
| **GOM-E mode-switch v0.9.2** | Phân xử T1/T2 xong (D�2 anchor, ��ng-phương-pháp 1h, forming_frac 2/3, OI-EXPAND chặn, MIXED/DENOM tags, log schema + gap_pct �o seam). **�� xuất U1-U5 � v0.9.3**: U1 �� o 70-token tìm mẫu un-hedge (n=1�5-8, chạy �ược ngay) · U2 E5 ba-nhánh SPRINT/GRIND/BLEED (BLEED=suppress) · U3 proven_pump c�t registry · U4 E3 band cover-êm vs CRASH-EXIT (ch� mẫu) · U5 FULL-SEQUENCE alert (E5-SPRINT � PRE-ARMED � E1+E2 �7d) | CH� K� hư�ng · GUA calib #2 PENDING · **AIN = registry-member s�ng �ầu tiên** · deploy �i�u ki�n: E3 ��c OI qua dedup-at-read (án OI-dup còn chảy) |
| **GOM-H texture** | **ARCHIVED-BY-NUMBER 13/08** (commit 85af107; XPIN�BANK cả 3 metric, XPIN outrank 2/3) | Carve-out: h2r_log forward (schema 3 c�t ch�t: h2r · h2r_log · rate_neg_usd_hr; NaN không cap; song song 30d r�i drop h2 cũ) · data-path note klines-1h=fapi-paginate |
| **Unified v3.0-FINAL** | �1/�2 D-fix + §H0-H7; H phần ARCHIVED, D-fix s�ng | � |
| **Verdict hysteresis** | Q3 ch�t · KH�NG δ (kill-list FF/ZBT/AKE �óng khung) · persist-2d = �ơn dự phòng | **25/08 ��c marginal_hits.csv** � tiêu chí �3 chu�i m�-�óng-lặp = �óng án |
| **Fire-date/day-k** | Fire-date ti�n-��nh ký · **day-k=3 re-run DEV �ANG CH� Y � kết quả chưa v�** | ��c kết quả � nếu pass: CONFIRM-M5 câu 0.6 "net-to-date tại fire+3 >0?" |
| **DORMANT net-dose** | Re-anchor fire-date · ngưỡng $634K ��NG B�NG · tiêu chí PASS: 2� base + dose-response �ơn �i�u tercile | M�c ��c: �100 chain net>0 hoặc �25 vượt ngưỡng (~cu�i T10) |
| **Spot-top-venue** | Howto done + áp 3 case. Luật: ch�n venue M�T LẦN (Binance > CEX-wash-pass > Alpha > DEX), ��i = venue_change metadata. C�t: 31 vol_spot_usd (ngo� i) · 35 vol_alpha · ratio = t�ng/oi | Th� nh bư�c chuẩn m�i case m�i |
| **Tape (taker/CVD)** | collect_tape Gate chạy cron sẵn · TP-1-5 giao DEV: c�t **36-37** taker_spot_ext/cvd_spot_usd [from-tape, forward-only] · Binance aggTrades = backfill �ược (ki�m alpha_id_map AIN/GUA trư�c) · cron 18/08 | ��c khi n�i xong: **CVD AIN cửa s� nạp (k� bán chưa?)** · CVD GUA tuần n� · APR texture |

---

## §4. �N / INFRA

- **�N M�I � LSR-merge GUA/APR (17/08, ưu tiên 1):** guard A-0b bắn `pos_r null 100%` ��NG nhưng b� �óng sai bằng "fapi không có LSR" � **s� có counter-evidence** (CASE_GUA 10/08 nguyên chu�i LSR). Nghi: rebuild ��c scratch m�i � �ứt merge (h� scratch-stale). L�nh: ��i chiếu backup L-37, tìm ch� merge gãy, CẤM �óng bằng known-gap khi s� cãi.
- **Scratch-stale:** staleness guard (gap>2d � RuntimeError) �ã thêm build_case � **generalize cho M�I case build**, không ch� AIN.
- **Guard-câm:** CLOSED (md5 a5a929dc). H� h� ng m�i: build-âm-thầm-data-cũ (= cùng b�nh).
- **OI double-write:** vẫn chảy (xác nhận 13/08) � forensic parked; **seam-check T1** (daily vs Σ1h, 20 symbol � 7d, dung sai vol ±0.5%/taker ±0.5pp/ret ±0.1pp) = công cụ �o bán kính nhi�m, chạy sau day-k + fired_by. GOM-E E3 bắt bu�c dedup-at-read.
- **fired_by(A/B/C) schema:** nợ, ưu tiên nâng (chặn phân tầng lo� i).
- **marginal_hits.csv:** logger sẵn từ 11/08 (header-only lúc tạo) � V4 ��c 25/08.
- **Persist 1h watchlist:** bật (nuôi h2r + GOM-E T2). Watchlist = h� m-theo-ng� y (E-registry � case OPEN � D-fires 30d) � KH�NG hardcode.
- **Kênh liên-topic:** file �ính kèm h�ng cả hai chi�u � **docs/handover/ trong repo** + verdict quan tr�ng paste text.
- **Encoding:** export CSV verdict tay của operator � UTF-8 (file 70-fire �ã vỡ dấu, ��c qua latin-1).

---

## §5. H�NG �ỢI CHỮ K� OPERATOR (theo �� nóng)

1. **Kết quả gate GOM-C 15/08** � h�i/��c/ký (COOKIE-GATE-PASS definition (a) �i kèm)
2. **GOM-D: hư�ng + ngu�n D3** (a/b/c/d-Dune) � m�i bằng chứng �ã �ủ, n=6+ground-truth 12 �i�m
3. **GOM-E v0.9.2 + gật U1-U5** (U1 chạy �ược ngay không cần ch� phần khác)
4. **L-44 FF acceptance packet**
5. **Batch lessons** (§2.5-2.14 + cron-không-viết-lại-l�ch-sử + �ính chính A�H)
6. **Verdict drafts:** AIN TRACKING-ACTIVE · APR�DIST-WATCH · DORMANT-register · APR-DEX-RETRACTED
7. **NỢ CŨ HAI TOPIC:** BANK verdict ký · TUT T+30 feed v� thế

## §6. L�CH 7 NG�Y + PENDING DATA

- **17/08 (H�M NAY):** BANK unlock � refresh 3 �i�u ki�n vòng-2 GẤP · AGT cửa s� S1 theo nh�p cụm � �ang m� (17-20/08) � trực daily
- **18/08:** IDOL cooldown hết + P1-P8 chấm · tape cron bật (TP-5) · IDOL unlock-test 11/08 kết quả CHƯA B�O � �òi
- **~20/08:** HEI STAND_ASIDE hết hạn � ��c wave-5 fuel
- **25/08:** marginal verdict V4 (tiêu chí �ặt sẵn §3)
- **PENDING v� bất kỳ lúc n� o:** GUA un-hedge 08-10/08 · CYS collect · TST rescue status (VERIFY NGAY � rolling deadline) · day-k=3 re-run · BANANAS31 fire 14/08 ��c (��ng h� cụm #4?) · seam-check T1 · TP-1-5 tape report

## §7. NGUY�N TẮC (nhắc 10 giây)
Verdict ch� operator ký · s� tự bảo v� (ngu�n+boundary+fn) · suppressor �è bullish · KH�NG SHORT · KH�NG �u�i (entry duy nhất lo� i staged = S1-CONFIRMED churn) · LAYER COVERAGE m�i lần ��c · nến �óng L-21 · tử-hay-mẫu trư�c m�i kết luận div · check-trạng-thái-trư�c-phát-bi�u · agent thu thập không verdict · máy thấy biến, ngư�i thấy ��ng cơ � **�� operator nói s�m những quan sát ki�u "acc > position", ba lần phiên n� y chúng nâng cả khung** (hai-chân-kho · FOMO-mode · un-hedge anchor).
