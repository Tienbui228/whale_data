# MODE-SWITCH DETECT SPEC (GOM-E "ĐỔI-CHẾ-ĐỘ") · v0.9.2 DRAFT
Ngày: 12/08/2026 · ANALYSIS soạn theo thesis operator · CHỜ OPERATOR KÝ HƯỚNG.
Spec-trước-code: mọi điều kiện copy NGUYÊN VĂN vào comment.
Changelog: v0.9 gốc → v0.9.1 (§5-T2 forming) → v0.9.2 (phân xử 12/08 sáu điểm
+ seam D−2 thành phép đo + tag parity + log hai chiều + 4 note spec-thành-code).

## §0. THESIS (một đoạn — của operator, ghi công vào sổ)
Loài captive dùng pha chờ làm MÁY THU: giữ kho spot + chân SHORT lớn trong cụm
top-value (div = pos/acc < 1), để crowd long trả funding dương đều — vừa thu phí
vừa mài kiên nhẫn đàn. Khi đàn mỏi (crowd mỏng/flush), operator ĐÓNG HEDGE và đổi
sang kéo. Cú đóng hedge = tiếng mở khóa: ON cover 17–18/07 → ignite 19/07
(+230%/12 ngày), trễ 1 ngày. Bot KHÔNG dự đoán giá — phát hiện TOKEN ĐANG ĐỔI
CHẾ ĐỘ để người review.

## §1. HAI TRẠNG THÁI + BIẾN (nguồn: freshwatch export canonical, nến NGÀY)
Biến: div_raw = pos_r/acc_r · div_avg3 (Phụ lục A) · oi_token · f_avg · pin_streak
· gLSR · d_pos_2d = pos_r(t)/pos_r(t−2) − 1 · d_acc_2d tương tự · d_oitok_2d =
oi_token(t)/oi_token(t−2) − 1.

STATE 1 — HEDGE-FARM (điều kiện VÀO registry, loose):
  H1: div_avg3 ≤ 0.85 trong ≥10/20 ngày gần nhất
  H2: f_avg > 0 trong ≥12/20 ngày (crowd đang trả phí)
  H3: [điểm cộng] gLSR ≥ 1.5 đa số ngày
  → vào registry, ghi: ngày vào · số ngày trong mode · f_avg trung bình.
  RA registry: div_avg3 > 1.0 bền 5d HOẶC symbol hết data.

STATE 2 — MODE-SWITCH-CANDIDATE (fire trên token TRONG registry HOẶC vừa ra ≤3 ngày):
  E1 (div-thaw):  div_raw(t) − min(div_raw, 5d) ≥ +0.15
  E2 (tử số):     d_pos_2d ≥ +0.15
  E3 (cover):     d_oitok_2d ≤ 0
  E4 (điểm cộng): pin_streak ≥10 vừa VỠ trong ≤3 ngày
  E5 (điểm cộng): deposit-bậc GOM-D D3 sống ≤7d (nếu data có; không có → bỏ, không chặn)
FIRE = E1 AND E2 → alert "MODE-SWITCH-CANDIDATE" + tag cơ chế (KHÔNG chặn, chỉ dán nhãn):
  [NUM-DRIVEN]   nếu E3 pass → khớp khuôn cover ON — loại đắt
  [DENOM-ASSIST] nếu |d_acc_2d| > d_pos_2d → div lên nhờ mẫu sập (flush-shape, GUA 05–07/08)
  [OI-EXPAND]    nếu d_oitok_2d > +0.10 → long mới chứ không phải cover — loại nghi ngờ
  + [marginal] cho mọi giá trị sát ngưỡng.
Cooldown: cùng token không lặp alert trong 3 ngày trừ khi tag cơ chế ĐỔI (DENOM→NUM
= tin mới, bắn lại).

## §2. OUTPUT HÀNG NGÀY (hai bảng, Telegram + log append-only)
Bảng A — HEDGE-FARM REGISTRY: symbol · ngày-trong-mode · div_avg3 · gLSR · f_avg
  · [NEW] nếu vừa vào. Tự nó là intel.
Bảng B — MODE-SWITCH alerts: symbol · E1..E5 giá trị · tag · ngày-trong-mode trước
  switch · dòng state từ case_state_map.md nếu có ([state-conflict] chuẩn §6 gói 11/08).

## §3. CALIB SET (chạy TRƯỚC khi ký — tránh án C1/GOM-C)
POSITIVE (phải fire, đúng cửa sổ, tag NUM-DRIVEN):
  ON 17–18/07 [ground truth: pos +30%/1d, oi_token ↓2 ngày, pin-47d vỡ cùng ngày — E1✓E2✓E3✓E4✓]
  GUA 08–10/08 [PENDING data — nếu confirm → positive #2; nếu không → ghi negative-shape]
NEGATIVE-BY-TAG (fire được nhưng PHẢI mang tag đúng):
  GUA 05–07/08 flush [DENOM-ASSIST — acc sập 6.1→2.76]
  COOKIE 07–08/08 [DENOM-ASSIST — flush hậu-grind]
KHÔNG-FIRE (registry có, switch không):
  BROCCOLIF3B toàn kỳ [div 0.25–0.42 lì, không thaw]
  AGT hiện tại [đang HEDGE-FARM — con bảng A phải HIỆN, bảng B phải IM đến khi thật sự đổi]
FORWARD TEST: AGT (template BTW + un-hedge tell) — bắt switch trước ignite → SIGNED per L-44.
GATE PASS = ON fire đúng + tags đúng nhóm negative-by-tag + BROCCOLIF3B im + AGT đúng bảng A.

## §4. RANH GIỚI + KNOWN GAPS
- SCREEN-tier recall-first: ngưỡng H/E chỉnh tự do có log (không re-gate), NHƯNG mọi
  nâng lên hành-động (ARM/PREP) = người.
- Bot không phân biệt "operator tháo hedge" vs "cá voi độc lập cover" — việc review + on-chain (phân vai).
- G1: BTW-loài committed-long (div ≥1.3 từ đầu) không qua registry — loài đó đã có GOM-D
  canh (deposit-bậc); hai detector BỔ nhau: GOM-D bắt logistics, GOM-E bắt tư thế.
  Con nào cả hai cùng bắn = tín hiệu hạng nhất.
- G2: LSR retention 30d — token vào registry muộn có thể thiếu nền H1 20 ngày; đếm từ
  ngày có data, ghi cờ SHORT-BASE.
- Đồng hồ [n=1 ON]: switch → ignite ≈1–2 ngày. KHÔNG dùng làm luật — làm mức ưu tiên
  review (NUM-DRIVEN = review TRONG NGÀY).

## §5. VẬN HÀNH — HAI TẦNG (v0.9.2)

### T1 DAILY (chính thức)
cron 01:25 UTC cùng gom_scan · incremental, lịch sử đóng băng + MD5 (chuẩn 11/08) ·
registry append-only · guard L-34 · report: số token quét / số trong registry / số alert.
Chấm trên nến ĐÓNG. Full Bảng A + Bảng B + tags. TẦNG DUY NHẤT ghi sổ / đếm calib /
đủ tư cách trích dẫn. Biến/điều kiện = đúng bộ §1 (FIRE=E1&E2, tags, cooldown 3d).

### T2 INTRADAY EARLY-WARNING (chỉ registry members HOẶC vừa ra ≤3 ngày)
NGUYÊN TẮC: T2 KHÔNG có công thức riêng — chấm phiên bản _prov của đúng bộ E daily.
Mọi lịch sử = nến NGÀY đã đóng; ô ngày-t điền tạm bằng nến 1h đóng gần nhất. Cùng 4
endpoint canonical, period=1h — KHÔNG nguồn mới (L-25). ref_method="1h-series".
Candidate set live = registry lần T1 ghi gần nhất.

ĐỒNG-PHƯƠNG-PHÁP BẮT BUỘC (đóng seam by construction — mọi cặp so sánh _prov cùng chuỗi 1h):
  pos_now / acc_now      := nến 1h ĐÓNG gần nhất, 4 endpoint canonical period=1h.
  pos_close(D−2)/acc_close(D−2) := nến 1h CUỐI ngày D−2 (boundary 00:00 UTC), cùng 4 endpoint period=1h.
  oi_close(D−2)          := bar 1h cuối D−2 từ Binance openInterestHist (period=1h).
  oi_now                 := /fapi/v1/openInterest.
  CẤM mọi nguồn OI thứ ba — án Coinglass lệch 22% so openInterestHist 00:00 (L-21). Ghi bia này vào comment.

Biến _prov:
  div_raw_prov  = pos_now / acc_now
  d_pos_2d_prov = pos_now / pos_close(D−2) − 1
  d_acc_2d_prov = acc_now / acc_close(D−2) − 1
  d_oitok_prov  = oi_now  / oi_close(D−2)  − 1
  min5d         = min(div_raw trên 5 NẾN NGÀY ĐÓNG, KHÔNG tính forming)
forming_frac = 2/3: quy ước KHAI BÁO, không fit. Đổi qua config + log. (2/3)·0.15 = +0.10.

PING khi:
  [div_raw_prov − min5d ≥ (2/3)·0.15]   (E1_prov, = +0.10)
  AND [d_pos_2d_prov ≥ (2/3)·0.15]      (E2_prov, = +0.10)
  AND NOT [d_oitok_prov > +0.10]        (OI-EXPAND chặn ping)

Tag cơ chế (bộ ba OI + DENOM chồng độc lập):
  d_oitok_prov ≤ 0          → [NUM-forming]  (ưu tiên cao nhất)
  0 < d_oitok_prov ≤ +0.10  → [MIXED]        (OI nhích nhẹ, cơ-chế-chưa-phân-định, chờ close;
                                              ping VẪN bắn vì E2 đã bảo đảm pos tăng ≥ forming)
  d_oitok_prov > +0.10      → suppress (log, KHÔNG ping) → verdict suppress_oi_expand
  chồng độc lập: |d_acc_2d_prov| > d_pos_2d_prov → [DENOM-ASSIST] (tag, không chặn;
                 NUM-forming + DENOM-ASSIST cùng lúc → ghi CẢ HAI, người đọc tự cân).

REFERENCE BAR — bar TỒN TẠI, không nội suy (Note-1):
  Bar 23:00 D−2 khuyết → lùi bar 1h ĐÓNG gần nhất TRONG D−2, ghi bar-time thật (ref_bar_ts).
  ĐỪNG lấy bar D−1 rồi gọi D−2 (L-24). Cùng luật cho oi_close_Dm2.
  Không có bar nào trong CẢ ngày D−2 → verdict suppress_no_ref, log, KHÔNG ping.

gap_pct — PHÉP ĐO SEAM, cùng boundary (Note-2):
  gap_pct = pos_close_Dm2 (1h-series, mốc D−2 00:00) vs pos_close_Dm2_canon (canonical 00:00 D−2).
  CÙNG token, CÙNG mốc D−2 00:00, chỉ khác đường rút số. CHỈ điền khi canonical D−2 đã tồn tại.
  Đây là chỗ DUY NHẤT T2 chạm số DAILY — chỉ để ĐO, KHÔNG chấm; không vi phạm L-21.
  Mục đích: sau 2 tuần, phân phối gap trả lời "canonical rút từ period nào" bằng data.
  gap≈0 → canonical = keep-last-1h, hai hệ khớp. gap có phân phối → biết chính xác độ méo cross-method.

RÀNG BUỘC:
  - 1 ping / symbol / ngày.
  - T1 đã bắn symbol trong ngày → T2 CÂM symbol đó.
  - cooldown T1 × T2 ĐỘC LẬP.
  - KHÔNG ghi DAILY (L-21). PROVISIONAL KHÔNG đếm calib (nguyên tắc, không số hiệu — tinh thần L-20).
  - T2 = process/entrypoint RIÊNG đọc config flag; tắt T2 ⇏ đụng T1 (T1 tự đứng trọn vẹn).
  - log bắt buộc gom_e_t2_log.csv append-only.

TEMPLATE PING:
  "⚡ MODE-SWITCH FORMING <SYM> [INTRADAY-PROVISIONAL·SUSPECT] — pos_prov <x> vs close
   D−2 <y> (+z%) · div_prov <d> · oiΔ_prov <w>. Chấm chính thức tại close."

verdict enum (Note-3) — 5 nhánh:
  {ping · suppress_oi_expand · suppress_t1_dup · suppress_daily_quota · suppress_no_ref}
  Thứ tự đánh giá: daily_quota → t1_dup → tính E1/E2/E3 → verdict.
  Quy ước log (GẬT 12/08):
    suppress_oi_expand   → log VÔ ĐIỀU KIỆN (không kèm ràng E1∧E2 — cần thống kê 2 tuần
                           để biết OI-EXPAND-block là guard hay mù; đòi E1∧E2 mới log sẽ
                           mất ca "E1 pass, E2 chưa, OI đã nở" = tiền-cảnh-báo false-shape).
    suppress_t1_dup      → log CHỈ KHI E1_prov ∧ E2_prov đều pass ("suýt-ping").
    suppress_daily_quota → log CHỈ KHI E1_prov ∧ E2_prov đều pass ("suýt-ping").
    ping                 → luôn log.
    suppress_no_ref      → luôn log (missing-bar = data gap, cần audit).
  Symbol không đạt E1_prov/E2_prov và không bị chặn → no_signal, KHÔNG log
  (tránh nổ dòng registry×poll×ngày).

CALIB chấm trên T1 (Note-4):
  Calib/GATE (§3) chấm trên T1 DAILY. T2 (_prov) CHỈ nhập gom_e_t2_log, KHÔNG BAO GIỜ
  vào GATE hay bảng calib (L-21/L-20). GUA 08–10/08: data về → chấm T1 cho gate;
  T2-bắt-GUA-sớm = quan sát ghi t2_log, không phải điểm gate.

LOG SCHEMA — gom_e_t2_log.csv (append-only):
  ts_utc · symbol · pos_now · acc_now · div_raw_prov · pos_close_Dm2 · acc_close_Dm2
  · d_pos_2d_prov · d_acc_2d_prov · oi_now · oi_close_Dm2 · d_oitok_prov · min5d
  · pos_close_Dm2_canon · gap_pct · ref_method="1h-series" · ref_bar_ts
  · pass_E1 · pass_E2 · tag · verdict · t1_confirmed_at_close · price_Tplus1

## §6. (không đổi — kế thừa gói 11/08: incremental + đóng băng lịch sử + MD5 + guard L-34)
