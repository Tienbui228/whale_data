# FRESHWATCH CASE TRACKER — Hồ sơ chiến dịch từ phát hiện đến kết cục

Version: 1.1 · 2026-07-30 · Chủ sổ: operator (Tien) · Máy điền số, operator điền verdict
Vị trí repo: `docs/case\_files/case\_tracker.md` + `docs/case\_files/data/<TOKEN>\_daily.csv` (mỗi case một file data)

**Đổi so v1.0:** thêm §H Daily State Log (máy tự cập nhật mỗi ngày — bảo tồn trạng thái TIỀN-sự-kiện để hậu kiểm), §I MM Profile, §J Tokenomics/Unlock. Nguyên tắc mới: *mọi phân tích hôm nay có thể sai — thứ không được phép thiếu là bản ghi trạng thái đầy đủ trước khi pump/phân phối xảy ra, để quay lại đối chiếu được sai ở đâu và thesis thiếu gì.*

\---

## 0\. CÁCH DÙNG

* Một case = một chiến dịch có chủ trên một token. Vòng đời: `OPEN → TRACKING → RESOLVED (pump / dump / trap / fizzle / invalidated)`.
* **Hai tầng lưu:**

  * `case\_tracker.md` (file này): hồ sơ đọc — verdict, chốt, nhật ký sự kiện, outcome, bài học. Người đọc chính.
  * `data/<TOKEN>\_daily.csv`: **daily state log máy tự append** — một dòng/ngày, schema §H, KHÔNG BAO GIỜ sửa dòng cũ. Máy đọc chính. File md chỉ trích các dòng then chốt.
* **Kỷ luật:** verdict chỉ operator ghi · số kèm nguồn · thiếu ghi `PENDING` không đoán · dự đoán sai không xóa (outcome sai là data quý nhất — bài PARTI) · cột manual bỏ trống hợp lệ, cột máy bỏ trống = bug phải điều tra.
* **Mục đích cuối:** ≥5 case RESOLVED → so cột dọc daily log giữa các case (cùng T−n, khác kết cục) → rút rule bằng đếm. Daily log chính là nguyên liệu thô — không có nó thì hậu kiểm chỉ còn trí nhớ.

\---

## 1\. §H — DAILY STATE LOG (lõi của v1.1)

### H1. Schema CSV — `data/<TOKEN>\_daily.csv` (một dòng/ngày, nến ĐÃ ĐÓNG)

**Nhóm PERP (máy — nguồn: export freshwatch\_daily / parquet VPS):**

|Cột|Nghĩa|
|-|-|
|`date`|ngày UTC đã đóng|
|`px\_open, px\_close, px\_high, px\_low`|OHLC ngày (range% tính được)|
|`ret\_1d`|% ngày|
|`vol\_perp\_usd`|vol perp|
|`taker\_buy\_pct`|taker buy % perp|
|`funding\_avg, funding\_min, funding\_max, funding\_n`|funding ngày đủ kỳ (n phải = kỳ vọng interval)|
|`funding\_regime`|máy gán: `PINNED / FLOAT / NEG\_DIV / EXTREME / HOT` + `pin\_streak` (số ngày)|
|`oi\_usd`|OI đóng ngày|
|`oi\_vs\_med14`|OI / median14|
|`oi\_cycle\_pos`|`FLOOR / MID / PEAK` — vị trí trong chu kỳ 60d (định luật #9: FLOOR = sổ MM, ratio trọng số cao)|
|`lsr\_pos\_r, lsr\_acc\_r, lsr\_global\_r`|3 ratio (ratio-space)|
|`div\_raw, div\_avg3`|pos/acc thô + smooth|
|`glsr\_slope\_5d`|gLSR(t)/gLSR(t−5) — nạp/xả nhiên liệu|
|`d\_pos\_3d, d\_acc\_3d`|delta 3 ngày (nguyên liệu concentration\_shift)|
|`signals\_bullish`|pipe-list từ signals\_log (vd `lsr\_accum|
|`signals\_suppress`|pipe-list suppressor|
|`screen\_rank`|rank trong UNI-137 ngày đó (từ screen v2)|
|`low\_conf`|cờ vol/OI nhỏ|

**Nhóm SPOT (máy — nguồn: Gate/Binance public API, snapshot 1 lần/ngày giờ cố định):**

|Cột|Nghĩa|
|-|-|
|`spot\_venue`|venue chính|
|`vol\_spot\_usd`|vol spot ngày|
|`taker\_buy\_spot\_pct`|nếu venue expose (Binance) — nguyên liệu #17|
|`spot\_vs\_perp\_taker`|chênh taker spot−perp (controlled-fill tell)|
|`depth\_bid2\_usd, depth\_ask2\_usd`|depth ±2% snapshot|
|`bid\_wall\_px, bid\_wall\_usd`|lệnh bid lớn nhất trong ±5%: giá + size (ai ĐỠ ở đâu)|
|`ask\_wall\_px, ask\_wall\_usd`|lệnh ask lớn nhất trong ±5% (ai CHẶN/XẢ ở đâu)|
|`alpha\_vol\_suspect`|vol\_spot/vol\_perp — >3× thì mọi cột vol spot ngày đó tự ABSTAIN|
|`cvd\_spot\_1d`|delta CVD spot ngày (nếu nguồn có — Velo)|

**Nhóm ON-CHAIN (bán tự động — BscScan watcher khi có, tay khi chưa):**

|Cột|Nghĩa|
|-|-|
|`exch\_balance\_delta`|đổi balance sàn ngày (nạp+/rút−, $ hoặc token)|
|`watch\_wallet\_activity`|tx từ các ví trong watchlist case: `NONE` hoặc mô tả ngắn `0x34..→gate:8M`|
|`dominance\_pct`|% supply trên sàn (cache 7d, điền khi refresh)|

**Nhóm MANUAL (operator — bỏ trống hợp lệ, nhưng ngày có biến nên có):**

|Cột|Nghĩa|
|-|-|
|`note\_operator`|quan sát tay: "bid $80k đỡ 0.142 suốt phiên Á", "ví X xả qua Y", tin/news|
|`mm\_note`|dấu hiệu liên quan MM hôm đó (đổi hành vi quote, spread bất thường...)|

### H2. Vận hành

* **Job đề xuất `case\_daily`** (nối vào chuỗi ledger\_daily 01:00 UTC hoặc job riêng 01:15): với mỗi case status OPEN/TRACKING trong tracker → build dòng từ export + signals\_log + screen output + spot API snapshot → append CSV. Cột on-chain/manual để trống chờ điền. **Chưa build — nợ P-CD trong §5.** Trước khi build: máy điền bằng prompt tay mỗi sáng (một lệnh cho Claude Code: "append dòng hôm qua cho 3 case").
* Snapshot depth/wall lấy **giờ cố định** (đề xuất 00:55 UTC ngay trước chốt sổ) — wall là ảnh chụp thời điểm, ghi giờ vào ghi chú schema, không giả vờ là số cả ngày.
* Ngày dữ liệu hỏng (funding\_n thiếu, MISSING): dòng vẫn append với cờ `data\_bad=1` — lỗ hổng cũng là thông tin (bài BR MISSING Jul24–26).
* Khi case RESOLVED: CSV đóng băng, không append nữa — thành khối input cho refit.

### H3. Vì sao tầng này tồn tại (đọc một lần)

Verdict hôm nay dựng trên snapshot hôm nay; nếu 3 tuần sau token nổ theo hướng ngược, câu hỏi duy nhất đáng giá là **"tại T−k, biến nào đã nói mà mình không nghe / thesis thiếu chiều nào"**. Không có daily log thì câu đó không trả lời được bằng số — chỉ còn kể chuyện. Đây là phiên bản per-case của bài học "kho ratio 30d phải tự lưu vì Binance không giữ hộ".

\---

## 2\. §I — MM PROFILE (mỗi case một khối; sổ MM chung xem §4)

> \*\*Nguyên tắc: mỗi MM/operator có cách đánh khác nhau — nhận diện được TAY CHƠI là nửa verdict.\*\* Cùng một tín hiệu, MM-kiểu-BANK (bid-walk kiên nhẫn, pin tuyệt đối) và MM-kiểu-ESPORTS (squeeze săn mục tiêu) cho hai kịch bản khác hẳn. Profile không cần danh tính pháp lý — cần VÂN TAY HÀNH VI.

Template khối I trong mỗi case:

```markdown
### I. MM / OPERATOR PROFILE
| Trường | Giá trị |
|---|---|
| MM công bố / nghi vấn | tên nếu biết (DWF/Gotbit/GSR/nội bộ dự án/unknown) + nguồn (công bố dự án, hồ sơ listing, đồn có kiểm chứng?) |
| Vân tay funding | pin tuyệt đối / pin từng đoạn / thả nổi / để âm dài (thu phí crowd) |
| Vân tay markup | taker-driven (AKE) / bid-walk stealth (BANK,TUT) / squeeze-mục-tiêu (ESPORTS) / chưa rõ |
| Kỹ thuật quản crowd đã thấy | wash-by-crash / wash-by-rally / bait-probe / chưa thấy |
| Kỹ thuật mồi on-chain | bait-withdrawal (BTW,BR) / staging thật (IDOL,TAG) / chưa thấy |
| Venue hoạt động | sàn nào là sân chính, sàn nào là bãi đỗ |
| Cross-campaign link | trùng vân tay/địa chỉ với case nào khác (HUMA↔AT là mẫu) |
| Ứng xử với mình | playbook có dấu hiệu đổi sau khi mình bắt bài? (rủi ro #5 master plan) |
```

## 3\. §J — TOKENOMICS / UNLOCK (mỗi case một khối)

> Unlock là dòng cung có LỊCH — MM biết trước và đánh quanh nó (kéo trước unlock để xả vào hype, hoặc đè trước unlock để gom rẻ của người sợ). Case nào không có khối J coi như mù một mắt.

```markdown
### J. TOKENOMICS / UNLOCK
| Trường | Giá trị |
|---|---|
| Circulating / Total supply | ... ( % float) |
| Nguồn tra | CryptoRank/TokenUnlocks/tokenomics dự án — ghi link/ngày tra |
| Unlock KẾ TIẾP | ngày · lượng · % circulating · nhóm (team/investor/ecosystem) |
| Unlock 90 ngày tới | bảng ngắn các đợt |
| Cliff lớn gần nhất đã qua | ngày · hành vi giá quanh nó (mẫu hành vi của tay chơi với unlock) |
| Đọc | sự kiện case này đứng TRƯỚC/SAU unlock bao xa — có khớp kịch bản đánh-quanh-unlock không |
```

\---

## 4\. SỔ MM CHUNG (cross-case — phần thân file, lớn dần theo thời gian)

|MM\_ID (tự đặt)|Vân tay lõi|Case đã thấy|Ghi chú|
|-|-|-|-|
|MM-BIDWALK-A|pin tuyệt đối + bid-walk + wash-by-bait, div kỷ lục, không bao giờ taker≥55|BANK, nghi HUMA/AT (div\~8 + pin + controlled-fill + cùng venue)|nếu HUMA hoặc AT ignite → con kia nâng canh NGAY|
|MM-BAIT-B|bait-withdrawal tại đỉnh + xả qua chân short + funding dương dài thu phí crowd|BTW, **BR** (vòng đời 4 tháng truy được trọn)|sổ đen mồi-on-chain; mọi withdrawal của nhóm này đọc ngờ tối đa|
|MM-SQUEEZE-C|grind-down thu funding + squeeze mục tiêu + ngắt đúng lúc mục tiêu gục|ESPORTS|canh xuất hiện ở token khác = alert cấp hệ thống|
|(thêm dần)||||

Quy tắc: gán case mới vào MM\_ID cũ CHỈ khi ≥3 vân tay trùng; không đủ thì tạo dòng mới hoặc để `unknown` — gán ẩu tệ hơn không gán (bài WBNB/hot-wallet trong funder ladder).

\---

## 5\. TEMPLATE CASE ĐẦY ĐỦ v1.1 (copy cho case mới)

Thứ tự khối: **Meta → A Input 4 lớp → B Đọc án (+ "điều gì chứng minh SAI") → C Chốt theo dõi → D Nhật ký sự kiện → E Outcome (T+7/14/30/60: px, ret%, drawup/drawdown, OI, gLSR, verdict-check) → F Khép án → G Revision → H Daily log (tham chiếu CSV + trích dòng then chốt) → I MM Profile → J Unlock.**
(Khối A–G như v1.0; H/I/J theo §1–§3 trên.)

\---

## 6\. CASE ĐANG MỞ — đã nâng lên v1.1

### CASE-01 BANK · TRACKING

(A–G như v1.0 — hồ sơ 4 lớp trong `BANK\_4layer.md`)

* **H:** `data/BANK\_daily.csv` — KHỞI TẠO: backfill từ export May26→nay (máy làm được ngay, 0 call). Dòng then chốt đã biết: T−11 lsr\_accum bật · T−8 bait · T0 07-10 · T+1 pin break · 07-28 dist\_wall+post\_climax.
* **I:** ứng viên MM-BIDWALK-A (5/5 vân tay khớp). Ứng xử-với-mình: PENDING.
* **J:** PENDING toàn bộ — tra unlock BANK là việc tay đầu tiên khi nâng hồ sơ.

### CASE-02 TAG · OPEN, WATCH-nóng

(A–G như v1.0)

* **H:** `data/TAG\_daily.csv` — KHỞI TẠO: backfill Jul01→nay từ export (đã có sẵn trong tay từ bảng 28/07). Cột `watch\_wallet\_activity`: 6 địa chỉ cụm. Cột wall: bắt đầu snapshot từ hôm nay — đặc biệt quan trọng với TAG vì book Gate mỏng, một wall $50k đã là tuyên bố.
* **I:** vân tay hiện có: pin-xuyên-bão (cũ) + staging-5-ví + kho-inventory-Gate + bid-walk. Chưa đủ gán MM\_ID — nghi họ bid-walk nhưng kỹ thuật mồi khác BANK. Để `unknown`, chờ leg này lộ thêm.
* **J:** PENDING — supply TAG + % của 22.77B rút ra (nợ cũ) + lịch unlock. Nếu có unlock lớn 30–60d tới thì kịch bản kéo-trước-unlock phải vào bảng B.

### CASE-03 BR · OPEN, STAND\_ASIDE (pump-to-distribute)

(A–G như v1.0)

* **H:** `data/BR\_daily.csv` — KHỞI TẠO: backfill từ export (LƯU Ý cờ data\_bad Jul24–26 MISSING, Jul28 PARTIAL — án pipeline). Cột wall tối quan trọng cho case này: chốt C1 "pos\_r nhích tại nền" và C2 "rửa crowd" đều sẽ hiện ở book trước — **ai bid mạnh ở giá nào chính là câu hỏi Tien đặt, cột bid\_wall trả lời nó hằng ngày.**
* **I:** **MM-BAIT-B** (gán được: bait-withdrawal tại đỉnh ✓ + funding dương dài thu phí ✓ + xả không qua book ✓ — 3/3). Hàng chờ vân tay: leg kéo sắp tới (nếu có) sẽ lộ vân tay markup → hoàn thiện profile.
* **J:** PENDING — unlock BR là mảnh thiếu nặng nhất: deposit 6% hôm nay đứng cách unlock kế tiếp bao xa? Nếu có unlock lớn sắp tới, kịch bản "kéo tạo hype để xả" có thêm deadline tự nhiên → tra NGAY (CryptoRank/TokenUnlocks, việc tay 10 phút).

\---

## 7\. HÀNG CHỜ CASE

|Token|Lý do|Ghi chú|
|-|-|-|
|TUT|CASE-04 — test dương concentration\_shift|hồi tố, daily CSV backfill được trọn|
|BTW|CASE-05 — hồ sơ dump/trap mẫu cho MM-BAIT-B|hồi tố|
|PARTI|CASE-06 — cấu trúc đẹp gãy (calib #13 NEGATIVE)|hồi tố|
|HUMA / AT|mở case khi tell bắn hoặc resolve — sẵn ứng viên MM-BIDWALK-A|leading indicator của nhau|

## 8\. NỢ VẬN HÀNH

|#|Việc|Mức|
|-|-|-|
|1|**P-CD: job case\_daily** — auto-append CSV mỗi case OPEN/TRACKING (export + signals\_log + screen rank + spot snapshot 00:55 UTC). Trước khi build: prompt tay mỗi sáng|CAO|
|2|Khởi tạo 3 CSV (BANK/TAG/BR) — backfill từ export, một prompt Claude Code|CAO — làm ngay|
|3|Tra unlock 3 con (BR trước — quyết kịch bản), điền khối J|CAO — tay, 30'|
|4|Nhắc mốc outcome E trong report sáng (nối ledger\_daily)|TB|
|5|TAG: verify txhash 2 ví vân tay đôi ($26M vs $17.9M) · BANK: điền E chính xác từ export|TB|
|6|BscScan watcher tự động cho cột watch\_wallet\_activity (thiết kế E8 có sẵn, chưa build)|TB|



