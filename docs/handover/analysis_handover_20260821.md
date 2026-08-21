# ANALYSIS HANDOVER — 21/08/2026 (topic 17-21/08 đóng)

**Người viết:** ANALYSIS topic (boot 17/08, đóng 21/08). **Người đọc:** ANALYSIS kế nhiệm — boot từ SỔ, không thừa kế trí nhớ.
**Boot sequence topic mới:** ① INDEX.md ② analysis_playbook.md ③ FILE NÀY ④ `D:/Data back test/whale_data/proposals/unhedge_registry_spec.md` (§E-R canonical, ER-HOME Option 2 ký 21/08) + phase_tag_spec v0.3.3 ⑤ TASKS.md/CASE_INDEX đối chiếu. Đọc xong: tóm 10 dòng + flag lệch (nghi ngờ → tin SỔ).

---

## §0. BA DÂY TREO TỪ NGÀY BOOT 17/08 — ĐÒI ĐẦU TIÊN, ĐỪNG ĐỂ SANG TOPIC THỨ BA

1. **ÁN E VERDICT** (LSR-merge GUA/APR, verdict draft trình ký 17/08: fix B+C+D + L-49/L-50): operator CHƯA KÝ. Chặn: repair APR (null 75.2% Jul19+) + acceptance #17 PHASE-TAG. GUA đã repair một-lần theo exhibit (data sạch), APR CHƯA.
2. **COOKIE-GATE-PASS (a)**: chưa ký → tin đòi gate GOM-C 15/08 chưa relay được. Intel mới làm nóng case: COOKIE neg_div GIỮA pump 08-11 + harvest 08-12 (bẫy BTW-khuôn) — đáng xem lại state REARM-watch.
3. **TST-RESCUE**: lệnh 09/08, **ngày mất thứ 11**, chưa có ack. Động cơ mới: pos-break −61% ngày 07-15 (phát hiện qua replay PHASE-TAG) cần chuỗi LSR đầy đủ mới kết án. Câu đòi: "đã chạy chưa + count per endpoint + ngày đầu cứu được".

## §1. TRẠNG THÁI CASE (thay đổi phiên này — bảng 17 case cũ xem handover 17/08)

**CỤM KHUÔN "DEPOSIT-TRONG-PUMP" — phát hiện lớn nhất phiên: 6 token / 8 ngày:**

| Token | Verdict ký | Pha | Ghi chú |
|---|---|---|---|
| GUA | KHÔNG-VÀO / STAND-ASIDE (verdict tái lập 19/08 trên data niêm) | Xả nửa chân perp (OI −47.7%), kho 130M chờ, van duy nhất Alpha (Gate=ISOLATED) → **bắt buộc đốt FOMO lại** (doctrine #10, DATA) | Identity Path A ĐÓNG: contract seal 3/3, Alpha SẠCH, "SUPERFORTUNE" = chính GUA. Marker: UN-HEDGE-GUA (pos≥15%/2d ∧ OI co) · vol_alpha ≥5× · deposit thêm |
| TRIA | KHÔNG-VÀO / STAGED-DIST ACTIVE | Pump 17-19/08 = xả (pos −24% intraday vào pump, deposit 200M TRONG pump, funding lật âm, un-pin sau 30d pin) | Bybit = chân spot chính ($2.3M ngày nổ — bài L-52). "Short-cover 18/08" của watchlist = STALE ARTIFACT (forensic đóng) |
| STBL | KHÔNG entry / WATCH cao — **chờ Vân4 + contract từ operator** | Pin 30/30 + hedge sâu + ignite 16-17/08 spot-cùng-nổ 4 van; 17-18/08 = **crowd flip SHORT trong pump** (acc −35%, gLSR −39%) = củi squeeze họ CLO, KHÔNG phải un-hedge (tử-mẫu: pos đứng 0.97) | 4 van THÔNG (Gate/KuCoin/MEXC/Alpha) — nếu kho NẠP → con thứ 3 cụm; kho RÚT → ứng viên gom-ignite hiếm |
| AIN | STAND-ASIDE (lệnh refresh+Gate ext ĐÃ PHÁT 19/08 — **KẾT QUẢ CHƯA VỀ**) | Deposit +37M lên GATE trong giá +23% (10-17/08) — staging màn kéo-xả, sân khấu Gate | Nợ operator từ handover cũ vẫn treo: contract + ví nguồn + unlock |
| HEMI | KHÔNG-VÀO / STAGED-DIST ACTIVE — pha MUỘN nhất cụm | Crescendo 3 sóng: D2 +43.6% (15/08) → flush nạp-củi (OI ×2.9, 16/08) → HARVEST −57% (ghế rời, PHASE-TAG bắt live 18/08) → D3 +22.7% SAU khi ghế rời + deposit 100M trong pump | Nền = archetype **committed-captive vùng-giữa** (div 0.9-1.1, pos TĨNH 3.5, un-hedge 5 tuần trước ignite) — GOM/watchlist im là ĐÚNG THIẾT KẾ (L-53). "Chuyên gia nói gom ở 0.045" = đúng bàn-tay sai ý-định |
| PUMPBTC | KHÔNG-VÀO / TRACKING + **DRIP-WATCH** (20/08) | Trại farm-funding có bảo hiểm: hedge sâu **51+ ngày** (episode dài nhất sổ, List-A giữ), crowd long 5.4-6.3 trả phí (21/61 ngày >2bps), kho nạp bậc thang +203%/90d, đẩy-cao = yếu (3 điều kiện đều ngược) | **Quả bom hẹn giờ đẹp nhất cho REGISTRY**: episode-51d break = (a)-BREAK evidence nặng nhất. DRIP-WATCH: div≥0.35 ∨ pos+15%/2d ∨ gLSR flush ≥30%/3d ∨ episode break → đọc lại ngay. List B đang re-report drip +0.015/5d hàng ngày = NOISE dưới ngưỡng sự kiện 10× |
| CLO | STAND-ASIDE (18/08) | Pump +27% 18/08 = bid-walk nạp short (POSITION phẳng 1.002 suốt cú kéo, ACCOUNT flip short, gLSR 2.75→1.12) — squeeze-fuel chất sẵn, "còn chân" ≠ kèo | Refresh 18/08 xong; thesis "spot-đạo-cụ/két perp" được data mới củng cố |

**Case cũ đổi trạng thái:** BANK quay lại texture S2-MID trong PHASE-MAP — nghi **chu-kỳ-2 đầu tiên hệ chứng kiến từ đầu**, kéo lại watch daily; vòng-2 unlock refresh (lệnh A cũ 17/08) CHƯA CHẠY. BTW: hiện ⚠ STATE-CONFLICT đúng thiết kế. IDOL: 4b lật NEGATIVE (build 27-31/07 tại OI-peak = crowding, outcome không-leg-2 xác nhận — định luật #9 thắng).

## §2. HỌC THUYẾT MỚI PHIÊN (đã ký trong batch V1 — verify agent đã nhập LESSONS sheet, bằng chứng CHƯA VỀ sau 2 lần đòi)

- **L-49** schema-drift-câm · **L-50** write-after-guard · **L-51** identity-check + **Step-0 TOKEN identity** (contract canonical operator-niêm — bài SUPERFORTUNE suýt nhiễm 48 dòng) · **L-52** venue coverage + vế "đường-hàng-thông" (pair ∧ deposit-đóng = van giấy; Gate-GUA ISOLATED) · **L-53** captive-kho vùng-giữa (4 điểm mù cấu trúc, CẤM p-hack A1/B1) · **L-54** tín-hiệu-mồ-côi = INTEL ≠ ENTRY (evidence: 315 corrections watchlist)
- **Doctrine #10 (băng thông xả):** kho/Σ-van-THÔNG > 30-60d → xả âm thầm bất khả → pump kế = pump-chức-năng-xả mặc định. CẤM tính khi spot-ext CHƯA-TRA. (GUA ~trăm ngày = bắt buộc FOMO; TRIA Bybit ×27 nới; HEMI dùng van Gate rồi)
- **SQUEEZE-FUEL-CHECK** (nhúng E-R3): gLSR GIẢM trong pump = crowd-short củi (CLO, STBL — còn chân) · TĂNG = crowd-long thanh-khoản-thoát (TRIA — bẫy). Biến phân xử cặp CLO/TRIA.
- **STATIC-SEAT** (candidate, n=1 HEMI): pos ≥2.5-3 TĨNH 14d ∧ OI≤$5M ∧ pin ∧ kho-sàn — bắt bằng MỨC không DELTA. Lệnh calib ĐÃ PHÁT (screen fw-139 + anchor BTW-July) — **kết quả chưa về**.
- **Ground-truth hai lớp** (§8.1 phase_tag): bản-án-cuối, lọc qua input-space; TAG = documentation case.
- **Batch V2 CHỜ KÝ:** L-55→59 (go-live≠verify · merge-before-gate · schema-append · spot-collect · watchlist-timing — đánh số lại từ DEV, KHÔNG đè L-53/54 đã ký).

## §3. PIPELINE/MÁY

| Máy | Trạng thái |
|---|---|
| **PHASE-TAG v0.3.3** | PRODUCTION — cron 01:30, CSV 139 rows/11 cột (F1 fix verified 20/08), Telegram 5 khối (🟢🟡🔴🔻⚠), render luật (A) LOW-hiện. Nợ nhẹ: backfill CSV 17-18/08; bug-watch: CLO 18/08 chấm UNKNOWN thay S3 (nghi range-anchor B2 — chưa mở án, chờ ca thứ 2); conf HIGH-rẻ S2-EARLY → amendment v0.3.4 chờ số conf-audit (lệnh đã phát) |
| **Watchlist v1.4** | PRODUCTION hậu-fix: cron 01:40, guard §5.11 (D-1 fresh assert), as_of per-row, 315 CORRECTIONS (226 đảo B1↔B2 + 89 phồng = 25.2% log Aug sai — lịch sử GIỮ + lớp đính chính). **Baseline lịch sử watchlist-log = BẨN, cấm dùng đối chiếu** |
| **UNHEDGE-REGISTRY (§E-R gom_detect_spec)** | v1.0 merged + v1.1 (struct_n≥3, ký). **E-R4b = ĐIỂM NÓNG:** Version A (px/local_low ≥1.15 ∧ oi/local_low ≥1.30 — recovery-from-low) ĐÃ IMPLEMENT + HEMI PASS 3 vế (wave-1 07-20, re-arm 08-06 biên thật, ⚡ 15/08 ngày-1 D2) nhưng **vào repo KHÔNG QUA KÝ** (relay-loss #5); wave-end v1.2 của ANALYSIS ĐÃ RÚT; **chữ ký treo:** "v1.2-FINAL = Version A + bỏ MARKUP-GIỮ + §E-R8 falsifier + RE-ARM-MISS log". **struct_n CHƯA CHỐT** — luật pre-commit: NHỎ NHẤT thỏa ≤25% fw-139 ∧ HEMI+ON sống ∧ hit ≥72% (sn=3 = 39a/25.9%/74.0% — VƯỢT cap; sn=4/5 SỐ THẬT chưa về sau 3 lần đòi). **Phase-2 (GOM-E full E1-E5+U1-U5+cron+⚡) CHỜ: chữ ký + 6 số + E-R7e** |
| **GOM-A/B/C** | Production. Gate GOM-C 15/08 vẫn treo (chốt = COOKIE-PASS chưa ký — §0.2) |
| **Bybit side-collector** | **HỦY** (operator nguyên tắc "1 venue lớn nhất, taker-không-có-thì-thôi") — SQUEEZE-FUEL chạy bằng gLSR perp vĩnh viễn; SPOT-EXT-LEAD đóng băng n=1 (TRIA-Bybit 14/08) = intel, CLOSED-BY-POLICY |
| **Schema CASE v2.1** | Cols 51-52 (vol_spot_ext + venue, CHỈ venue lớn nhất, price-band ±20% + contract Step-0 trước khi nhận); cols 53-54 HỦY. LAYER COVERAGE: spot-ext CHƯA-TRA ≠ N/A |

## §4. ÁN MỞ / LỆNH ĐÃ PHÁT CHƯA VỀ

1. **E-R7e + bảng struct_n sn=4/5** (DEV — prompt trong handover DEV 20/08, ĐÃ SỬA target Version A)
2. **AIN refresh + Gate spot-ext** (agent, phát 19/08)
3. **STATIC-SEAT calib screen** (agent, Khối-2 ký 20/08)
4. **Batch V1 nhập LESSONS — bằng chứng** (đòi lần 3)
5. **SYNC-PACK 21/08** (agent — consolidate phase_tag v0.3.3 full + verify các sổ + xuất file-path cho operator update project)
6. **Handover DEV 20/08 sửa 2 lệch** (E-R4b "đã ký" sai + số lesson đè) — bằng chứng chưa về
7. Conf-audit PHASE-TAG (amendment v0.3.4)
8. Nợ nhỏ DEV: backfill phase_tag CSV 17-18/08 · M6-reconcile · dead-code P3 · CSV as_of rows cũ

## §5. HÀNG CHỮ KÝ OPERATOR (xếp theo mở-khóa)

1. **§E-R4b v1.2-FINAL** (một dòng, nguyên văn trong §3) → mở E-R7e → phase-2
2. **struct_n** (khi 6 số về — luật chọn đã pre-commit, ký 1 dòng)
3. **Án E verdict** (§0.1 — treo 4 ngày)
4. **COOKIE-GATE-PASS (a)** (§0.2)
5. **Batch V2 lessons** (L-55→59)
6. **CAMPAIGN-RIDE v0.1** — khuôn đầy đủ đã soạn (điều kiện registry-ngày-1, thoát bắt buộc theo HARVEST/dist_wall/neg_div, SQUEEZE-FUEL định hướng, pilot 3-ride, tự-treo 3-lỗ): **thiếu duy nhất size % + chữ ký nguyên văn**. Không ký = registry reo cũng chỉ được nhìn — trạng thái hợp lệ nếu đó là lựa chọn, nhưng phải là LỰA CHỌN không phải quên.

## §6. NGUYÊN TẮC VẬN HÀNH RÚT TỪ PHIÊN (cho ANALYSIS kế nhiệm)

- **Merge-before-gate** (5 evidence relay-loss/tuần): amendment ký chat → agent merge file + paste diff TRƯỚC khi gate chạy; mọi run gate in `spec_version + amendments_applied=[...]`; mọi dòng "ĐÃ KÝ" trong sổ phải trỏ được về nguyên văn chat-ký, không trỏ được = ghi "CHỜ KÝ".
- **Tử-hay-mẫu trước mọi div/ratio** — ba lần cứu phiên này (STBL "un-hedge" = acc sập; GUA "ghế yên" = ratio che OI −48%; TRIA div leo = mẫu sập).
- **Vân4 operator là separator duy nhất** gom vs xả (G1) — 6/6 verdict cụm đứng trên ảnh tracker, không cái nào đứng trên perp đơn độc.
- **Số trong report ≠ số trong sổ** — verdict chỉ viện dẫn số đã nằm canonical file hoặc đeo nhãn [điểm-đơn/chưa-điền].
- **Check-trạng-thái + đọc-spec-nguyên-văn trước khi phán rule** (List B "un-hedge" PUMPBTC = drip dưới ngưỡng sự kiện 10× — hai máy hai vai, đừng dịch List B thành mũi tên).
- Máy hiện **giỏi nói KHÔNG hơn nói CÓ** — 6 verdict KHÔNG-VÀO đều là tiền-không-mất; nửa nói-CÓ (registry + falsifier forward §E-R8) đang chờ 30 ngày forward chấm bằng data. Đừng để "không-vào-là-thắng" thành thuốc an thần: câu miss-×2 của operator là câu thật, và registry là câu trả lời — ship nó.

*Hết. Topic 17-21/08: boot từ sổ → PHASE-TAG sống → watchlist sạch ma → registry một chữ ký nữa là reo. Kế nhiệm: vận hành, đừng xây lại.*
