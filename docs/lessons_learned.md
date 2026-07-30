# Lessons Learned
_Generated from CASE_INDEX.xlsx sheet LESSONS — 39 entries_

**L-01** (2026-07-30): OI-floor = so vi the MM: ratio doc tai day OI trong so cao (retail da roi); pos_r nhich tai nen chet = tin hieu som dam; ratio tai OI-peak phai chiet khau

**L-02** (2026-07-28): KHONG amend dinh nghia signal de om case ngoai ho cua no — ghi miss + negative assertion. lsr_accum nghieng ho bid-walk, s3_eve ganh ho taker-driven: hai signal BU nhau

**L-03** (2026-07-29): Tell som nhat co the nam tron MOT lop don doc 11 ngay (perp) — doi da lop lam dieu kien ARMED se lot ho BANK. Xac nhan da lop chi den DUNG luc no

**L-04** (2026-07-29): concentration_shift KHONG ban tren BANK = negative case HOP LE: level-type (div cao tinh) vs delta-type (acc sap pos giu) la HAI ho tin hieu khac nhau, khong va sensor de om ca hai

**L-05** (2026-07-30): Withdrawal gan dinh = MOI on-chain (bang chung #2, vong doi 4 thang truy tron: rut-tai-dinh -> phan phoi -> redeposit). Moi withdrawal cua nhom MM-BAIT phai doc ngo toi da

**L-06** (2026-07-28): Inventory != gom: toan khoi luong (V_venue vs $withdrawal) phan xu duoc 'vua mua' hay 'hang co san'. Book sieu mong = BAI DO — withdrawal khoi bai do = khoa float, khong doc thanh 'chuyen di ban'

**L-07** (2026-07-30): Pump-to-distribute: kho len san = CHUAN BI DAN, khong xa tai gia hien tai — can leg keo tao hype truoc. Khong long theo khi KHONG co ghe big-long de di cung (div ~1) = vi tri con moi. Dieu kien tien quyet cua leg that: crowd long phai bi rua

**L-08** (2026-07-30): MM profile la NUA verdict — moi MM danh mot kieu (bid-walk kien nhan / bait-withdrawal / squeeze muc tieu). Gan MM_ID can >=3 van tay trung; gan au te hon khong gan

**L-09** (2026-07-29): KHONG tin loi giai thich fire — chi tin bang dieu kien tung dong (an 'vol drop faster than OI' la cau bia; fire dung nhung narrative sai van la doc sai). Moi fire phai tu bao ve bang input series + yaml check

**L-10** (2026-07-29): Data hong cung phai ghi (data_bad=1, to cam) — lo hong la thong tin; dong non (funding_n thieu) phai bi guard loai khoi moi streak/window

**L-11** (2026-07-28): Wash-by-rally: crowd tu roi bang chot loi vao da tang — cu ru bo sung KHONG bat buoc truoc leg. gLSR giam trong ngay gia tang = nhien lieu dang duoc don, doc BULLISH cho campaign

**L-12** (2026-07-30): Unlock la dong cung CO LICH — MM biet truoc va danh quanh no (keo truoc unlock de xa vao hype / de truoc unlock de gom re). Case thieu khoi J = mu mot mat

**L-13** (2026-07-30): Phan vai: ledger = so cai NGANG (thong ke precision, may doc); tracker = ho so DOC (thesis-check, nguoi doc). Verdict chi song MOT noi (case file), ledger Zone B rut gon state+case_id. Mot chieu du lieu, khong ghi nguoc

**L-14** (2026-07-30): Dump manh + gLSR SAP >=30%/<=3d = wash-by-crash: mot phat an hai: don chi phi long + nap nhien lieu short (crowd short moi = nhien lieu re cho squeeze). La bien the crowd_flush thu nhat, doi xung L-11 (rally) va L-15 (bait). Phan biet ro voi L-26: gLSR SAP khi gia sap (wash) vs gLSR TANG khi gia sap (wrong-side fuel)

**L-15** (2026-07-30): Vol spike >=8x med14 + gia bi tu choi <=2d = bait-probe: muc dich khong phai markup het ma la DAY crowd short nap nhien lieu squeeze. Sau bait canh gLSR sap trong <=3d lam xac nhan; vol persistence T+1 phan biet bait vs ignition that

**L-16** (2026-07-30): div_raw truot tu >1 xuong <1 = vi the lon thu hep/dao long bias = chom phan phoi; flag STAND_ASIDE review; khong ARM sau div-flip neu chua co bang chung re-gom. LUU Y THUAT NGU: day KHONG phai 'M2 dao dau' — M2 la module CEX balance flow (xem L-27)

**L-17** (2026-07-30): Squeeze/markup chet khi nhien lieu chet — hai cua dong an: (a) gLSR hoi ve ~1 (crowd short dau hang), (b) muc tieu cu the goc (TARGETED_SQUEEZE). Dang giu vi the ma mot trong hai bat = EXIT_NOW. [De xuat CHUA CALIB: thao tac hoa bang glsr_slope_5d doi dau — chua test case nao, glsr_slope_5d hien chi la cot hien thi (A5), khong phai gate]

**L-18** (2026-07-30): Truoc ARM phai check du 3: (1) pha chu ky (nhin du px7/px14 + oi_cycle_pos, khong chi cua so 28d), (2) crowd structure (gLSR + dao ham — co tinh gan vo dung), (3) OI khong tai PEAK. Thieu 1/3 = low-conviction. KHONG trich dan % precision khi chua do — precedent dem that (n=...), cam noi %

**L-19** (2026-07-30): Signal fire ban giong nhau o pha gom va pha phan phoi — can phase_tag (ACCUMULATE/MARKUP/DISTRIBUTE/UNKNOWN) tu oi_cycle_pos + div trend + glsr_slope de loc; den khi co phase_tag: moi fire phai kem phase check tay (L-18). Khong trich % false-rate khi chua do

**L-20** (2026-07-30): fn=1 / data_bad=1 / missing >3 ngay trong window / so tu 1 nguon khong kiem chung → low_conf=True; so bi ha cap KHONG lam threshold ARM/FIRE

**L-21** (2026-07-30): OI daily canonical = export Binance openInterestHist 00:00 UTC. So intraday (Coinglass/GMGN) chi vao EVENTS kem timestamp, khong vao DAILY. An 30/07: BR 4,634,000 (intraday) vs 3,782,263 (export 00:00) chenh 22%. Rule: mot cot DAILY mot so canonical

**L-22** (2026-07-30): fn=1 (native_1d low_conf) khong dung lam so chot ARM/FIRE. Fallback: Zone A aggregate tu ledger_v2.xlsx CAMPAIGNS, ghi ro Zone-A-agg. TAG 29/07: gLSR 1.81 (fn=1 SUSPECT) vs 1.61 (Zone-A-agg) — chenh 0.2 du dao nhan dinh toc do nap crowd

**L-23** (2026-07-30): Fire margin mong -> fade la kich ban xac suat cao: TAG 28/07 fire bien mong, ret_3d=-9.87%, crowd nap long vao duong gia xuong (gLSR 1.28->1.81). Invalidate som: gia khong confirm T+1/T+2 + gLSR tang tiep = WATCH-ha-nhiet, khong ARM lai som

**L-24** (2026-07-30): oi_vs_med14 Excel != oi_vs_med14 signals.py (window ket thuc ngay khac). Moi so DAILY phai mang nhan: nguon + window cu the. Khong dung Excel calc lam proxy signals.py canonical. Hai nguoi doc hai so khac nhau cung ten = an tranh luan vo ich

**L-25** (2026-07-30): Mot-nha-mot-data tai pham x2 trong session 30/07: (1) OI DAILY 2 so tu 2 nguon; (2) gLSR/div dung fn=1 raw thay vi aggregate canonical. Rule: moi cot DAILY mot nguon canonical khai bao tuong minh. >=2 so cung metric -> chon canonical + ghi an vao EVENTS

**L-26** (2026-07-30): Gia sap/roi + gLSR TANG = crowd long bat dao = nhien lieu SAI phia — NGUOC han wash-by-crash (L-14: gLSR SAP). He qua: (a) leg-len ke tiep can lua long nay bi rua truoc, (b) con dang SUPPRESSED co pattern nay thi REMAIN, (c) khong doc nham thanh 'co nguoi gom'

**L-27** (2026-07-30): M2 (CEX balance flow) tu no KHONG mang y dinh — dau cua no do boi canh quyet: vi tri chu ky + funding regime + hanh vi gia. Chay M2 don le la An tron bay BTW. Suppressor o bat ky lop nao phu quyet moi bullish cua ca ba lop

**L-28** (2026-07-30): Moi narrative dung tren mot nguon phai kiem nguon goc (aggregator != klines; mep cua so = artifact ung vien). Narrative khong con dung duoc → RUT cong khai va GHI SO muc 'da tu ha cap' — de khong tu lua va khong tai sinh. Cu luan diem chi giu phan con dung tren bang chung

**L-29** (2026-07-30): alpha_vol_suspect = vol_spot/vol_perp > 3x → moi metric VOL SPOT cua con do ABSTAIN (khong wash-check, khong #17, khong bang chung dong tien); van dung depth/price/taker. takerBUY spot lech cuc doan (<35% hoac >70%) tren vol khong lo = hinh dang farming. Guard chi ha long tin, khong sinh bullish → ap ngay

**L-30** (2026-07-30): Token venue_top=bitget: cam so sanh spot-vs-perp cung-ngay cho den khi bug lech ngay duoc xac minh/va; phan tich cross-market phai shift-test truoc. Ghi chu venue vao moi bang so sanh

**L-31** (2026-07-30): Tong hop/dien giai tu tai lieu cu = vung rui ro cao: moi entry phai trace ve cau chu nguon (dinh nghia lay tu yaml/reference, khong tu tri nho dien giai); so lieu khong co trong nguon = khong viet; thuat ngu he thong (M1/M2/ten signal) dung dung nghia goc, khong tai dinh nghia. L-09 ap cho ca tai lieu, khong rieng fire

**L-32** (2026-07-30): Backfill save nhầm file (_NEW suffix) do file gốc bị lock trong Excel — INDEX vẫn trỏ tên cũ → case_daily ghi vào file cũ (4 dòng) thay vì canonical (35 dòng). Fix: sau bất kỳ backfill nào, verify INDEX trỏ đúng canonical; canonical phải có đúng tên gốc.

**L-33** (2026-07-30): fn=1 fallback (Zone-A-agg) chỉ dành cho cột taker_buy_pct — KHÔNG mượn sang gLSR/pos_r/acc_r. Metric ratio phải đến từ export CSV hoặc để TRỐNG + comment, không ghép chéo metric. Guard bằng assert EXPORT_COL_MAP tại import time trong case_daily.py.

**L-34** (2026-07-30): PermissionError khi save xlsx → RAISE RuntimeError ngay, cam silent-save sang ten khac (_NEW suffix). Ten file khac = INDEX tro sai = case_daily ghi nham → data bi pha vo im lang. Fix: close xlsx roi retry

**L-35** (2026-07-31): Bo calib (12 file _result.txt + GATE dict + replay.py) phai song trong git cung voi code — da dung, ghi nhan de giu. Quy tac: moi repo moi can regression suite commit ngay tu dau, khong de calib file ngoai version control. Loi that nhat la khi calib tach khoi code: code duoc update ma calib cu → false pass / false fail.

**L-36** (2026-07-31): Tai tao data file phai test bang suite nguyen ban (replay.py goc tu git), KHONG tu viet harness moi. Harness tu viet dan den 3 assertion sai: (1) AKE lsr_accum: viet fires_in thay vi never_in; (2) BASED crowd_flush: viet fires_in thay vi never_in; (3) BULLA pos_rerate: dung file tai tao (pos 07-20=1.75) thay vi file goc (1.99). An: bao 40/43 gia, mat thoi gian debug. Fix: dung replay.py goc → 43/43 PASS.

**L-37** (2026-07-31): Repo chi local (khong remote git server) = single point of failure — mot loi o dia hay OneDrive deauth mat het. Giai phap toi thieu: git bundle → SCP len VPS /root/archive/ trong vong 24h tao repo, sau do bundle lai tai moi milestone lon. Da ap 4 repo ngay 31/07: binance-bot-signals, whale_data, Check onchain, Whales_scan. Repo OneDrive them an: file-lock + single-copy = combo sinh an (CASE_BANK_NEW, L-34).

**L-38** (2026-07-31): Mot metric mot ngay ra 4 con so khac nhau (1.75/1.68/1.981/1.99) tu 4 nguon: (1) u50 loose = 1.75 (nguon khong ro, retired); (2) top_pos_1h keep-last 23:00 UTC = 1.6811; (3) derived_1h = 00:00 UTC dau ngay = 1.981; (4) native_1d repo goc = 1.99. Nguyen nhan: quy uoc canonical CHUA TON TAI khi calib duoc viet. He qua: verdict buoc phai chon nguon theo ket luan muon co = vi pham nguyen tac. Fix: quy uoc phai duoc ky TRUOC khi bat ky so nao duoc trich dan vao calib/DAILY. Xem proposals/ratio_daily_canonical_20260731.md cho de xuat keep-last canonical.

**L-39** (2026-07-31): Quy ước boundary phải TEST bằng đối chiếu nguồn (21/21 diff 0%) trước khi văn bản hóa — proposal v1 hợp lý trên giấy nhưng ngược 180° với thực nghiệm; n=1 suy luận đẹp vẫn phải qua n=21.
