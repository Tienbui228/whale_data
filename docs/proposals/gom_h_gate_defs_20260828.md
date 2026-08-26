# GOM-H GATE & CENSUS — ĐỊNH NGHĨA CANONICAL (28/08/2026, ANALYSIS soạn — DEV merge verbatim vào docs/proposals/)

Nguồn quyền lực: chuỗi chat-ký E-GATE 27-28/08 (operator relay). File này canonical-hóa những định nghĩa trước đó chỉ sống trong chat (bài file-trong-chat ≠ file-trong-repo). Mọi số `[ ]` = operator điền, PROVISIONAL cho đến chữ ký control-gate.

## §1. BỐN BẢNG T
- **T-①** (H1-companion evidence): 9 hàng = 9 sự kiện kho-step evidence (findings rev7 §10 V1, mỗi case một–hai step) × 4 cột giá trị sub-vế T0.1 **tại ngày cuối cửa sổ step**: funding_max14 · oi/min30 · |ret14| · med7(vol)/med30. Mục đích: phân bố cho operator chọn tổ hợp H1-companion (tách tên khỏi T0.1).
- **T-②** (floor_obs_min): 6 case có sự kiện seat-lift H2 (BANK · CYS · AKE · HEMI · ON · CAP — theo findings §3-F5/§12/§13) × earliest-eligible-date của vế pos-ratio dưới floor_obs_min n∈{10,14,21,30}, đặt cạnh ngày seat-lift thật (findings §6/§11-13). Kèm phân bố universe: per token `n_obs_oi` (số ngày OI non-null) + earliest_date đạt từng n.
- **T-③** (giá trị biên div-cut): ma trận hàng = 14 fires H2 hiện có + 7 sự kiện seat-lift evidence; cột = vế bắt {pos-ratio | div-cut | cả hai | không}. Đọc: div-cut có catch-duy-nhất nào không.
- **T-④** (E1 render): 8-9 case × {H1 · H2∧T0.1 · compose} × {ngày fire đầu tiên trong cửa sổ đánh giá · lead so D0 · trạng thái evaluable}. DEV render, ANALYSIS chấm, operator ký.

## §2. EVALUABLE (cho T-④ và mọi gate per-case)
- Cửa sổ đánh giá của case = `[max(data_start, D0−30) .. D0−1]` (ngày lịch UTC; D0 theo §4).
- Một H **evaluable cho case** ⇔ tồn tại ≥1 ngày trong cửa sổ mà H đánh giá được (raw ∈ {True, False}; N/A-WARMUP / N/A-GAP / N/A-STATE / thiếu exch_balance = không đánh giá được).
- H không-evaluable → **loại H khỏi case đó** (không đếm miss). Mọi H đều không-evaluable → case = **NOT-EVALUABLE**, rút khỏi mẫu số, in danh sách rõ.
- Gate đọc `passes/evaluable`; mẫu số co thì báo co, không độn.
- Phân biệt: "evaluable" (định nghĩa trên, cho gate) ≠ "PENDING <30d tuổi" (chỉ áp cho chấm TP/FP census §5).

## §3. GATE E1/E2 — tiêu chí đăng-ký-trước
- **E1** (đã đăng ký trong §1-H spec draft): PASS-case = ≥1 fire compose với **lead ≥1 ngày** trước D0. Gate = passes/evaluable ≥ **[6/8]** (số trong ngoặc — operator xác nhận tại điểm dừng).
- **E1-caveat by-construction** (nghĩa trong tiêu chí): ngưỡng hiện fit trên chính 8-9 case positive → E1 chỉ là **điều kiện cần**: E1 FAIL ⇒ chặn; E1 PASS ⇒ chưa phải bằng chứng, bắt buộc kèm E2 trước khi operator điền số. Cấm trích E1-PASS như validation.
- **E2**: trần FP-rate **CHƯA đăng ký** — [CẦN KÝ]: ANALYSIS trình phân bố FP từ census (§5) + control-set, operator đặt số. DEV không chạy verdict E2 trước chữ ký; chỉ render số liệu.

## §4. D0 (ignition) canonical — nguồn findings rev7 (md5 2d520397)
| token | D0 | ghi chú | nhãn |
|---|---|---|---|
| BANK | 2026-07-11 | §1 | [DATA] |
| TUT | 2026-07-09 | §1 | [DATA] |
| CYS | 2026-08-04 | §1 | [DATA] |
| AKE | 2026-07-15 | §1 | [DATA] |
| BTW | 2026-08-03 | chiến dịch 2, §1 | [DATA] |
| HEMI | 2026-08-15 | ⚡ D2; wave-1 20/07 = INTEL, không phải D0 | [DATA] §11 |
| ON | 2026-07-19 | wave-1 +19.4% mở markup | [DATA] §12 |
| CAP | 2026-07-30 | +32%, OI ×2 | [DATA] §13 |
| BTR | 2026-08-26 | +99% vol $235M; wave-1 11/08 (+42%) = registry wave, không phải D0 | [DATA] §15 |
Định nghĩa D0 đang dùng: ngày đầu sau nền có ret_close ≥ ~+15% (BANK +13.4% chấp nhận, vol 10.7×) ∧ vol ≥ ~10×med14, chốt thủ công có số kèm trong findings từng §. D0 là **anchor niêm theo bảng này** — thay đổi = amendment ký.

## §5. CENSUS TP/FP — luật chấm (ANALYSIS chấm, DEV viết validator)
- Tập giá trị hợp lệ: `{TP, FP, PENDING, NOT-EVALUABLE}`.
- **TP** = trong D0..D+30 sau fire, close đạt ≥ **[+50%]** so close ngày fire, HOẶC fire nằm trong cửa sổ campaign đã niêm ở findings (§6/§11-15). **FP** = ngược lại với đủ 30 ngày dữ liệu. **PENDING** = fire <30 ngày tuổi tại data_through — loại khỏi cả tử lẫn mẫu FP-rate.
- PENDING hết hạn: tự động khi fire đủ 30d tuổi → re-grade ở lần census kế; mỗi grade ghi `graded_at + data_through`.
- Chấm trên **bản copy**: file gốc census bất biến; grades vào `census_63_grades_<date>.csv` append-only, join khóa (token, date, vế). Không sửa lịch sử.

## §6. §8.4(i) COOLDOWN — làm rõ runtime (bổ sung dòng spec đã ký, không đổi nghĩa)
- Cooldown khởi từ **alert compose phát ra per-lane** ({H1-kho} · {H2∧T0.1}), không từ raw-condition.
- 14d cooldown đếm **ngày lịch UTC**; "≥3d sạch" đếm **hàng dữ liệu đánh-giá-được** với raw_condition(lane)=False liên tiếp; N/A (mọi loại) không đếm là sạch.
- Warmup ⑨: raw = N/A-WARMUP → không fire, không đếm sạch, không khởi cooldown.
- Đồng hồ sạch chạy trên **raw_condition của lane**; DQ serial-pump là điều kiện chặn fire độc lập, không tham gia đồng hồ.
- Ngày raw=True trong cooldown → in `[SUPPRESSED n/14]`, không im.

## §7. ROW 14 BANANAS31 — PASS def re-target [CẦN KÝ, đã xếp hàng ký ⑪]
Expected = **toàn compose GOM-H not-fire** (mọi lane) trong kỳ serial-pump theo probe 14/08 (ngày kỳ: đọc từ probe — file/§ do DEV trỏ). Trước khi DQ serial-pump merge: fires hiện hữu = **FP thật, đếm đủ vào FP-rate, row FAIL trung thực** — không thu hẹp expected thành "H1-not-fire".

## §8. ROW TYPE 3 — KNOWN-MISS-BY-SCOPE (VÁ thêm 28/08 ANALYSIS, per operator relay)

**KNOWN-MISS-BY-SCOPE:** expected = 0 alert vì loài nằm ngoài scope thiết kế hiện hành; row PASS khi máy im, nhưng render bắt buộc in nhãn này + pointer exhibit — không được hiển thị như negative. Đổi scope để phủ loài = amendment ký, khi đó row chuyển positive.

**Ứng dụng trực tiếp — Row 2 AKE (fixture 2-row 28/08):**
- Row 2 AKE = **KNOWN-MISS-BY-SCOPE**
- Pointer: exhibit câu ①, loài **staging-dump (M2/T1.7)**
- Lý do out-of-scope: AKE ret14 = 168%..2198% (newly-listed high-vol), H1 doctrine (kho ∧ compression) target mature tokens quiet accumulation; V① shadow (kho ∧ |ret14|≤0.15) cũng không phủ (0/19 kho_raw days pass shadow).
- Render bắt buộc: `[KNOWN-MISS-BY-SCOPE — staging-dump M2/T1.7, câu ①]`
- Row PASS vì máy im ĐÚNG THIẾT KẾ; không đếm miss vào FP-rate.
