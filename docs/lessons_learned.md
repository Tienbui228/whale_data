# Lessons Learned — FreshWatch

> Auto-generated từ CASE_INDEX.xlsx sheet LESSONS. Không edit file này trực tiếp.

## L-01 [2026-07-30] BR (+BAS,TUT,BANK) — `dinh luat` · DA VAO master plan §1 #9
OI-floor = so vi the MM: ratio doc tai day OI trong so cao (retail da roi); pos_r nhich tai nen chet = tin hieu som dam; ratio tai OI-peak phai chiet khau
*Hành động tiếp: oi_floor_flag (OI<=1.1x min30d) lam he so ranker — chua active, thu bang chung*

## L-02 [2026-07-28] AKE (an PA-B) — `process/rule` · DA VAO GATE dict + §10 (commit b0b4cff4)
KHONG amend dinh nghia signal de om case ngoai ho cua no — ghi miss + negative assertion. lsr_accum nghieng ho bid-walk, s3_eve ganh ho taker-driven: hai signal BU nhau
*Hành động tiếp: ap dung lai khi concentration_shift gap BANK (L-04)*

## L-03 [2026-07-29] BANK (ho so 4 lop) — `thesis` · DA VAO — so do cho R4-TRIGGER (khong lop nao bat buoc)
Tell som nhat co the nam tron MOT lop don doc 11 ngay (perp) — doi da lop lam dieu kien ARMED se lot ho BANK. Xac nhan da lop chi den DUNG luc no
*Hành động tiếp: moi case moi: ghi T-k lan dau >=2 lop nguoc gia vao ho so*

## L-04 [2026-07-29] BANK — `rule` · GHI NHAN — cho test duong tren TUT (CASE-04)
concentration_shift KHONG ban tren BANK = negative case HOP LE: level-type (div cao tinh) vs delta-type (acc sap pos giu) la HAI ho tin hieu khac nhau, khong va sensor de om ca hai
*Hành động tiếp: neu TUT ban dung 10-12/07 -> sensor song, xet vao screen ranker*

## L-05 [2026-07-30] BR + BTW — `dinh luat` · DA CO trong §1 #1 (rule dao dau M2) — BR cung co them
Withdrawal gan dinh = MOI on-chain (bang chung #2, vong doi 4 thang truy tron: rut-tai-dinh -> phan phoi -> redeposit). Moi withdrawal cua nhom MM-BAIT phai doc ngo toi da
*Hành động tiếp: token dinh bai nay vao SO DEN trong MM_BOOK*

## L-06 [2026-07-28] TAG (Gate probe) — `rule` · GHI NHAN — dua vao khung E4/M4 khi cham diem transfer
Inventory != gom: toan khoi luong (V_venue vs $withdrawal) phan xu duoc 'vua mua' hay 'hang co san'. Book sieu mong = BAI DO — withdrawal khoi bai do = khoa float, khong doc thanh 'chuyen di ban'
*Hành động tiếp: nguong nhap: V_14d >= 2x withdrawal moi coi la 'co the gom tren venue'*

## L-07 [2026-07-30] BR (operator) — `thesis` · GHI NHAN — khuon moi, BR la test song
Pump-to-distribute: kho len san = CHUAN BI DAN, khong xa tai gia hien tai — can leg keo tao hype truoc. Khong long theo khi KHONG co ghe big-long de di cung (div ~1) = vi tri con moi. Dieu kien tien quyet cua leg that: crowd long phai bi rua
*Hành động tiếp: neu BR keo that: doi chieu chot 1+2 co bao truoc khong*

## L-08 [2026-07-30] BANK/BTW/ESPORTS/BR — `process` · DA VAO tracker v1.1 (§I + MM_BOOK)
MM profile la NUA verdict — moi MM danh mot kieu (bid-walk kien nhan / bait-withdrawal / squeeze muc tieu). Gan MM_ID can >=3 van tay trung; gan au te hon khong gan
*Hành động tiếp: cross-campaign trung dia chi/van tay = alert cap he thong*

## L-09 [2026-07-29] P1 fire audit — `process` · DA VAO ky luat A4 (mo rong A4.2)
KHONG tin loi giai thich fire — chi tin bang dieu kien tung dong (an 'vol drop faster than OI' la cau bia; fire dung nhung narrative sai van la doc sai). Moi fire phai tu bao ve bang input series + yaml check
*Hành động tiếp: ap cho ca advisor: so tay cua toi dung sai spec cu (1.5x vs 1.3x da ky) — yaml locked la luat*

## L-10 [2026-07-29] BR/TAG pipeline — `process` · DA VAO P1 (funding_n guard) + tracker schema
Data hong cung phai ghi (data_bad=1, to cam) — lo hong la thong tin; dong non (funding_n thieu) phai bi guard loai khoi moi streak/window
*Hành động tiếp: an pipeline MISSING cuoi thang: kiem toan store dinh ky*

## L-11 [2026-07-28] TAG 27-28 (BULLA truoc do) — `thesis` · DA CO tu BULLA — TAG cung co lan 2
Wash-by-rally: crowd tu roi bang chot loi vao da tang — cu ru bo sung KHONG bat buoc truoc leg. gLSR giam trong ngay gia tang = nhien lieu dang duoc don, doc BULLISH cho campaign
*Hành động tiếp: glsr_slope am trong ngay xanh = co xac nhan*

## L-12 [2026-07-30] BR (operator) — `process` · DA VAO tracker v1.1 (§J bat buoc)
Unlock la dong cung CO LICH — MM biet truoc va danh quanh no (keo truoc unlock de xa vao hype / de truoc unlock de gom re). Case thieu khoi J = mu mot mat
*Hành động tiếp: viec tay: tra unlock BR/TAG/BANK — BR truoc*

## L-13 [2026-07-30] ledger vs tracker — `process` · DA DUYET 30/07 — xem sheet PHAN_VAI
Phan vai: ledger = so cai NGANG (thong ke precision, may doc); tracker = ho so DOC (thesis-check, nguoi doc). Verdict chi song MOT noi (case file), ledger Zone B rut gon state+case_id. Mot chieu du lieu, khong ghi nguoc
*Hành động tiếp: them cot case_id vao Zone B (viec tay 1 phut)*

## L-14 [2026-07-30] ESPORTS + twelve_cases_ref — `thesis` · GHI NHAN
Wash-by-crash: crowd flush khi gia sap (long dung lo, short mo them) -> gLSR tang -> squeeze nguoc gia bat, short ket = nhien lieu pump. Signal: gia sap + gLSR TANG dong thoi = tiem nang squeeze nguoc (nguoc chieu voi wash-by-rally L-11)
*Hành động tiếp: kiem xac nhan wash-by-crash tren ESPORTS daily log khi backfill*

## L-15 [2026-07-30] twelve_cases_ref + BANK/TAG — `thesis` · GHI NHAN
Bait-probe: MM tao probe nho (vol spike ngan + gia retreat) do phan ung crowd. Crowd khong khang cu = san sang markup; crowd short ngay = can them wash. Probe khac markup that: khong co vol sustained sau probe
*Hành động tiếp: tag probe events trong EVENTS log (BANK/TAG neu thay pattern)*

## L-16 [2026-07-30] twelve_cases_ref + BR/EVAA — `dinh luat` · GHI NHAN
M2 dao dau (div_raw tu >1 xuong <1 = acc_r vuot pos_r): smart money khong con long bias hon crowd, crowd bat dau hold nhieu hon. Dao dau M2 = phase distribution bat dau. BR: div_raw 1.114->0.51 qua 10 ngay; EVAA tuong tu
*Hành động tiếp: flag M2-flip trong DAILY log; xet lam trigger STAND_ASIDE review*

## L-17 [2026-07-30] ESPORTS + twelve_cases_ref — `dinh luat` · GHI NHAN
Squeeze chet khi nhien lieu chet: gLSR quay dau (gLSR_slope_5d doi dau) = short positions dong/chuyen long, het nhien lieu pump. Theo doi glsr_slope_5d: duong->am = tank can; squeeze khong the keo dai sau khi crowded-short tan
*Hành động tiếp: them glsr_slope_5d vao S1 handover checklist*

## L-18 [2026-07-30] u50_verdicts §2 — `thesis` · GHI NHAN
u50 §2 — Fire khong = markup ngay: can dong thoi (1) MM phase gom/markup (khong phai phan phoi), (2) crowd structure sach (gLSR hop ly), (3) OI khong PEAK. Thieu 1/3 = low-conviction, khong arm. Fire-without-phase-check dung ~40% tu 50-verdict review
*Hành động tiếp: them phase_check vao ARM checklist truoc khi ARM*

## L-19 [2026-07-30] u50_verdicts §3 — `process` · GHI NHAN
u50 §3 — He thong thieu phase-context filter: signal fire ban giong nhau o phase gom va phan phoi. Can phase_tag (ACCUMULATE/MARKUP/DISTRIBUTE) tu oi_cycle_pos + div_raw de loc false-fire trong phan phoi. ~30% fire trong DISTRIBUTE la false theo u50
*Hành động tiếp: thiet ke phase_tag inference (oi_cycle_pos + div_raw + M2) — no P2*

## L-20 [2026-07-30] u50_verdicts §6 + TAG/BR 29/07 — `process` · DA VAO CLAUDE.md (fn=1 rule)
u50 §6 tu-ha-cap: agent ha cap confidence + ghi low_conf=True khi: fn=1, data_bad=1, missing >3 ngay trong window, hoac so chot tu 1 nguon khong kiem chung duoc. So bi ha cap khong duoc lam threshold ARM/FIRE
*Hành động tiếp: mo rong tu-ha-cap cho data_bad flag (ngoai fn=1)*

## L-21 [2026-07-30] BR (an 30/07) — `rule` · DA VAO CLAUDE.md
OI daily canonical = export Binance openInterestHist 00:00 UTC. So intraday (Coinglass/GMGN) chi vao EVENTS kem timestamp, khong vao DAILY. An 30/07: BR 4,634,000 (intraday) vs 3,782,263 (export 00:00) chenh 22%. Rule: mot cot DAILY mot so canonical
*Hành động tiếp: khi co so OI: xac nhan nguon + gio chup truoc khi ghi DAILY*

## L-22 [2026-07-30] TAG+BR 28-29/07 — `rule` · DA VAO CLAUDE.md
fn=1 (native_1d low_conf) khong dung lam so chot ARM/FIRE. Fallback: Zone A aggregate tu ledger_v2.xlsx CAMPAIGNS, ghi ro Zone-A-agg. TAG 29/07: gLSR 1.81 (fn=1 SUSPECT) vs 1.61 (Zone-A-agg) — chenh 0.2 du dao nhan dinh toc do nap crowd
*Hành động tiếp: khi fn<6: tu dong dung Zone-A-agg + flag SUSPECT trong handover*

## L-23 [2026-07-30] TAG — `thesis` · GHI NHAN
Fire margin mong -> fade la kich ban xac suat cao: TAG 28/07 fire bien mong, ret_3d=-9.87%, crowd nap long vao duong gia xuong (gLSR 1.28->1.81). Invalidate som: gia khong confirm T+1/T+2 + gLSR tang tiep = WATCH-ha-nhiet, khong ARM lai som
*Hành động tiếp: them T+1/T+2 price-confirm check vao S1 handover (48h khong confirm = WATCH-ha-nhiet)*

## L-24 [2026-07-30] BR/TAG (an 30/07) — `rule` · DA VAO CLAUDE.md (facts da chot)
oi_vs_med14 Excel != oi_vs_med14 signals.py (window ket thuc ngay khac). Moi so DAILY phai mang nhan: nguon + window cu the. Khong dung Excel calc lam proxy signals.py canonical. Hai nguoi doc hai so khac nhau cung ten = an tranh luan vo ich
*Hành động tiếp: moi oi_vs_med14 phai kem (signals.py, window=...) hoac (Excel, col X)*

## L-25 [2026-07-30] BR+TAG (tai pham 30/07) — `rule` · DA VAO CLAUDE.md (KY LUAT)
Mot-nha-mot-data tai pham x2 trong session 30/07: (1) OI DAILY 2 so tu 2 nguon; (2) gLSR/div dung fn=1 raw thay vi aggregate canonical. Rule: moi cot DAILY mot nguon canonical khai bao tuong minh. >=2 so cung metric -> chon canonical + ghi an vao EVENTS
*Hành động tiếp: audit cot DAILY hien tai: co cot nao 2 nguon khong khai bao khong?*

## L-26 [2026-07-30] BANK — `process/rule` · GHI NHAN
Backfill save nhầm file (_NEW suffix) do file gốc bị lock trong Excel — INDEX vẫn trỏ tên cũ → case_daily ghi vào file cũ (4 dòng) thay vì canonical (35 dòng). Fix: sau bất kỳ backfill nào, verify INDEX trỏ đúng canonical; canonical phải có đúng tên gốc.
*Hành động tiếp: thêm bước verify file name + row count vào checklist sau backfill*

## L-27 [2026-07-30] BANK — `rule` · GHI NHAN
fn=1 fallback (Zone-A-agg) chỉ dành cho cột taker_buy_pct — KHÔNG mượn sang gLSR/pos_r/acc_r. Metric ratio phải đến từ export CSV hoặc để TRỐNG + comment, không ghép chéo metric. Guard bằng assert EXPORT_COL_MAP tại import time trong case_daily.py.
*Hành động tiếp: assert đã vào case_daily.py dòng sau FORMULA_COLS*
