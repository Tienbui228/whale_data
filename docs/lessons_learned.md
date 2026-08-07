# Lessons Learned — FreshWatch

> Auto-generated tu CASE_INDEX.xlsx sheet LESSONS. Khong edit file nay truc tiep.
> Lan sinh: 2026-08-07 · Tong: 47 bai hoc (L-01 → L-48)

## L-01 [2026-07-30] BR (+BAS,TUT,BANK) — `dinh luat` · DA VAO master plan §1 #9
OI-floor = so vi the MM: ratio doc tai day OI trong so cao (retail da roi); pos_r nhich tai nen chet = tin hieu som dam; ratio tai OI-peak phai chiet khau
*Hanh dong tiep: oi_floor_flag (OI<=1.1x min30d) lam he so ranker — chua active, thu bang chung*

## L-02 [2026-07-28] AKE (an PA-B) — `process/rule` · DA VAO GATE dict + §10 (commit b0b4cff4)
KHONG amend dinh nghia signal de om case ngoai ho cua no — ghi miss + negative assertion. lsr_accum nghieng ho bid-walk, s3_eve ganh ho taker-driven: hai signal BU nhau
*Hanh dong tiep: ap dung lai khi concentration_shift gap BANK (L-04)*

## L-03 [2026-07-29] BANK (ho so 4 lop) — `thesis` · DA VAO — so do cho R4-TRIGGER (khong lop nao bat buoc)
Tell som nhat co the nam tron MOT lop don doc 11 ngay (perp) — doi da lop lam dieu kien ARMED se lot ho BANK. Xac nhan da lop chi den DUNG luc no
*Hanh dong tiep: moi case moi: ghi T-k lan dau >=2 lop nguoc gia vao ho so*

## L-04 [2026-07-29] BANK — `rule` · GHI NHAN — cho test duong tren TUT (CASE-04)
concentration_shift KHONG ban tren BANK = negative case HOP LE: level-type (div cao tinh) vs delta-type (acc sap pos giu) la HAI ho tin hieu khac nhau, khong va sensor de om ca hai
*Hanh dong tiep: neu TUT ban dung 10-12/07 -> sensor song, xet vao screen ranker*

## L-05 [2026-07-30] BR + BTW — `dinh luat` · DA CO trong §1 #1 (rule dao dau M2) — BR cung co them
Withdrawal gan dinh = MOI on-chain (bang chung #2, vong doi 4 thang truy tron: rut-tai-dinh -> phan phoi -> redeposit). Moi withdrawal cua nhom MM-BAIT phai doc ngo toi da
*Hanh dong tiep: token dinh bai nay vao SO DEN trong MM_BOOK*

## L-06 [2026-07-28] TAG (Gate probe) — `rule` · GHI NHAN — dua vao khung E4/M4 khi cham diem transfer
Inventory != gom: toan khoi luong (V_venue vs $withdrawal) phan xu duoc 'vua mua' hay 'hang co san'. Book sieu mong = BAI DO — withdrawal khoi bai do = khoa float, khong doc thanh 'chuyen di ban'
*Hanh dong tiep: nguong nhap: V_14d >= 2x withdrawal moi coi la 'co the gom tren venue'*

## L-07 [2026-07-30] BR (operator) — `thesis` · GHI NHAN — khuon moi, BR la test song
Pump-to-distribute: kho len san = CHUAN BI DAN, khong xa tai gia hien tai — can leg keo tao hype truoc. Khong long theo khi KHONG co ghe big-long de di cung (div ~1) = vi tri con moi. Dieu kien tien quyet cua leg that: crowd long phai bi rua
*Hanh dong tiep: neu BR keo that: doi chieu chot 1+2 co bao truoc khong*

## L-08 [2026-07-30] BANK/BTW/ESPORTS/BR — `process` · DA VAO tracker v1.1 (§I + MM_BOOK)
MM profile la NUA verdict — moi MM danh mot kieu (bid-walk kien nhan / bait-withdrawal / squeeze muc tieu). Gan MM_ID can >=3 van tay trung; gan au te hon khong gan
*Hanh dong tiep: cross-campaign trung dia chi/van tay = alert cap he thong*

## L-09 [2026-07-29] P1 fire audit — `process` · DA VAO ky luat A4 (mo rong A4.2)
KHONG tin loi giai thich fire — chi tin bang dieu kien tung dong (an 'vol drop faster than OI' la cau bia; fire dung nhung narrative sai van la doc sai). Moi fire phai tu bao ve bang input series + yaml check
*Hanh dong tiep: ap cho ca advisor: so tay cua toi dung sai spec cu (1.5x vs 1.3x da ky) — yaml locked la luat*

## L-10 [2026-07-29] BR/TAG pipeline — `process` · DA VAO P1 (funding_n guard) + tracker schema
Data hong cung phai ghi (data_bad=1, to cam) — lo hong la thong tin; dong non (funding_n thieu) phai bi guard loai khoi moi streak/window
*Hanh dong tiep: an pipeline MISSING cuoi thang: kiem toan store dinh ky*

## L-11 [2026-07-28] TAG 27-28 (BULLA truoc do) — `thesis` · DA CO tu BULLA — TAG cung co lan 2
Wash-by-rally: crowd tu roi bang chot loi vao da tang — cu ru bo sung KHONG bat buoc truoc leg. gLSR giam trong ngay gia tang = nhien lieu dang duoc don, doc BULLISH cho campaign
*Hanh dong tiep: glsr_slope am trong ngay xanh = co xac nhan*

## L-12 [2026-07-30] BR (operator) — `process` · DA VAO tracker v1.1 (§J bat buoc)
Unlock la dong cung CO LICH — MM biet truoc va danh quanh no (keo truoc unlock de xa vao hype / de truoc unlock de gom re). Case thieu khoi J = mu mot mat
*Hanh dong tiep: viec tay: tra unlock BR/TAG/BANK — BR truoc*

## L-13 [2026-07-30] ledger vs tracker — `process` · DA DUYET 30/07 — xem sheet PHAN_VAI
Phan vai: ledger = so cai NGANG (thong ke precision, may doc); tracker = ho so DOC (thesis-check, nguoi doc). Verdict chi song MOT noi (case file), ledger Zone B rut gon state+case_id. Mot chieu du lieu, khong ghi nguoc
*Hanh dong tiep: them cot case_id vao Zone B (viec tay 1 phut)*

## L-14 [2026-07-30] TAG 08-09/07 + AKE 08-10/07 — `thesis` · DA VAO yaml (crowd_flush cause=crash)
Dump manh + gLSR SAP >=30%/<=3d = wash-by-crash: mot phat an hai: don chi phi long + nap nhien lieu short (crowd short moi = nhien lieu re cho squeeze). La bien the crowd_flush thu nhat, doi xung L-11 (rally) va L-15 (bait). Phan biet ro voi L-26: gLSR SAP khi gia sap (wash) vs gLSR TANG khi gia sap (wrong-side fuel)
*Hanh dong tiep: phan biet ro voi L-26 (gLSR TANG khi gia sap = hien tuong nguoc, KHONG phai wash)*

## L-15 [2026-07-30] BANK 02/07 + BASED 01&09/07 + POWER 08-09/07 — `thesis` · DA VAO yaml (crowd_flush cause=bait)
Vol spike >=8x med14 + gia bi tu choi <=2d = bait-probe: muc dich khong phai markup het ma la DAY crowd short nap nhien lieu squeeze. Sau bait canh gLSR sap trong <=3d lam xac nhan; vol persistence T+1 phan biet bait vs ignition that
*Hanh dong tiep: tag probe events trong EVENTS log khi thay pattern*

## L-16 [2026-07-30] BR + EVAA + CLO — `thesis` · GHI NHAN
div_raw truot tu >1 xuong <1 = vi the lon thu hep/dao long bias = chom phan phoi; flag STAND_ASIDE review; khong ARM sau div-flip neu chua co bang chung re-gom. LUU Y THUAT NGU: day KHONG phai 'M2 dao dau' — M2 la module CEX balance flow (xem L-27)
*Hanh dong tiep: flag div-flip trong DAILY log; ho hang gan voi lsr_dist (da la suppressor yaml)*

## L-17 [2026-07-30] AKE + ESPORTS — `dinh luat` · DA VAO master plan §1 #5 + EXIT_NOW conditions
Squeeze/markup chet khi nhien lieu chet — hai cua dong an: (a) gLSR hoi ve ~1 (crowd short dau hang), (b) muc tieu cu the goc (TARGETED_SQUEEZE). Dang giu vi the ma mot trong hai bat = EXIT_NOW. [De xuat CHUA CALIB: thao tac hoa bang glsr_slope_5d doi dau — chua test case nao, glsr_slope_5d hien chi la cot hien thi (A5), khong phai gate]
*Hanh dong tiep: neu muon slope-flip thanh trigger di duong proposal + calib nhu #17*

## L-18 [2026-07-30] u50_verdicts §2 (n=18) — `thesis` · GHI NHAN
Truoc ARM phai check du 3: (1) pha chu ky (nhin du px7/px14 + oi_cycle_pos, khong chi cua so 28d), (2) crowd structure (gLSR + dao ham — co tinh gan vo dung), (3) OI khong tai PEAK. Thieu 1/3 = low-conviction. KHONG trich dan % precision khi chua do — precedent dem that (n=...), cam noi %
*Hanh dong tiep: phase_check vao ARM checklist; precision that do bang shadow-mode P2 + alerts_log*

## L-19 [2026-07-30] u50 §2 + CLO/BLUAI/STAR (n=18) — `process` · GHI NHAN — no P2
Signal fire ban giong nhau o pha gom va pha phan phoi — can phase_tag (ACCUMULATE/MARKUP/DISTRIBUTE/UNKNOWN) tu oi_cycle_pos + div trend + glsr_slope de loc; den khi co phase_tag: moi fire phai kem phase check tay (L-18). Khong trich % false-rate khi chua do
*Hanh dong tiep: thiet ke phase_tag inference trong P2*

## L-20 [2026-07-30] TAG/BR 28-29/07 — `process` · DA VAO CLAUDE.md (fn=1 rule)
fn=1 / data_bad=1 / missing >3 ngay trong window / so tu 1 nguon khong kiem chung → low_conf=True; so bi ha cap KHONG lam threshold ARM/FIRE
*Hanh dong tiep: mo rong tu-ha-cap cho data_bad flag (ngoai fn=1)*

## L-21 [2026-07-30] BR (an 30/07) — `rule` · DA VAO CLAUDE.md
OI daily canonical = export Binance openInterestHist 00:00 UTC. So intraday (Coinglass/GMGN) chi vao EVENTS kem timestamp, khong vao DAILY. An 30/07: BR 4,634,000 (intraday) vs 3,782,263 (export 00:00) chenh 22%. Rule: mot cot DAILY mot so canonical
*Hanh dong tiep: khi co so OI: xac nhan nguon + gio chup truoc khi ghi DAILY*

## L-22 [2026-07-30] TAG+BR 28-29/07 — `rule` · DA VAO CLAUDE.md
fn=1 (native_1d low_conf) khong dung lam so chot ARM/FIRE. Fallback: Zone A aggregate tu ledger_v2.xlsx CAMPAIGNS, ghi ro Zone-A-agg. TAG 29/07: gLSR 1.81 (fn=1 SUSPECT) vs 1.61 (Zone-A-agg) — chenh 0.2 du dao nhan dinh toc do nap crowd
*Hanh dong tiep: khi fn<6: tu dong dung Zone-A-agg + flag SUSPECT trong handover*

## L-23 [2026-07-30] TAG — `thesis` · GHI NHAN
Fire margin mong -> fade la kich ban xac suat cao: TAG 28/07 fire bien mong, ret_3d=-9.87%, crowd nap long vao duong gia xuong (gLSR 1.28->1.81). Invalidate som: gia khong confirm T+1/T+2 + gLSR tang tiep = WATCH-ha-nhiet, khong ARM lai som
*Hanh dong tiep: them T+1/T+2 price-confirm check vao S1 handover (48h khong confirm = WATCH-ha-nhiet)*

## L-24 [2026-07-30] BR/TAG (an 30/07) — `rule` · DA VAO CLAUDE.md (facts da chot)
oi_vs_med14 Excel != oi_vs_med14 signals.py (window ket thuc ngay khac). Moi so DAILY phai mang nhan: nguon + window cu the. Khong dung Excel calc lam proxy signals.py canonical. Hai nguoi doc hai so khac nhau cung ten = an tranh luan vo ich
*Hanh dong tiep: moi oi_vs_med14 phai kem (signals.py, window=...) hoac (Excel, col X)*

## L-25 [2026-07-30] BR+TAG (tai pham 30/07) — `rule` · DA VAO CLAUDE.md (KY LUAT)
Mot-nha-mot-data tai pham x2 trong session 30/07: (1) OI DAILY 2 so tu 2 nguon; (2) gLSR/div dung fn=1 raw thay vi aggregate canonical. Rule: moi cot DAILY mot nguon canonical khai bao tuong minh. >=2 so cung metric -> chon canonical + ghi an vao EVENTS
*Hanh dong tiep: audit cot DAILY hien tai: co cot nao 2 nguon khong khai bao khong?*

## L-26 [2026-07-30] ESPORTS hau-climax + TAG 29/07 + BLUAI — `thesis` · GHI NHAN
Gia sap/roi + gLSR TANG = crowd long bat dao = nhien lieu SAI phia — NGUOC han wash-by-crash (L-14: gLSR SAP). He qua: (a) leg-len ke tiep can lua long nay bi rua truoc, (b) con dang SUPPRESSED co pattern nay thi REMAIN, (c) khong doc nham thanh 'co nguoi gom'
*Hanh dong tiep: dieu kien tien quyet 'crowd flush truoc leg' ghi vao chot canh cac case dinh (TAG, BR, ESPORTS)*

## L-27 [2026-07-30] BTW vs BAS/TAG | AKE/IDOL — `dinh luat` · DA VAO master plan §1 #1 + A1 (R4)
M2 (CEX balance flow) tu no KHONG mang y dinh — dau cua no do boi canh quyet: vi tri chu ky + funding regime + hanh vi gia. Chay M2 don le la An tron bay BTW. Suppressor o bat ky lop nao phu quyet moi bullish cua ca ba lop
*Hanh dong tiep: giu ten 'M2' doc quyen cho balance flow — khong dung cho div/ratio (an L-16 rev.1)*

## L-28 [2026-07-30] u50 §6 (AGT / HUMA-AT sync / listing 04-14) — `process` · GHI NHAN — u50 §6 la mau chuan
Moi narrative dung tren mot nguon phai kiem nguon goc (aggregator != klines; mep cua so = artifact ung vien). Narrative khong con dung duoc → RUT cong khai va GHI SO muc 'da tu ha cap' — de khong tu lua va khong tai sinh. Cu luan diem chi giu phan con dung tren bang chung
*Hanh dong tiep: moi report lon co muc 'bang chung da tu ha cap' nhu u50*

## L-29 [2026-07-30] OPN + HYPER (u50 §3a, n=2) — `guard` · DA VAO amendment A6 (guard)
alpha_vol_suspect = vol_spot/vol_perp > 3x → moi metric VOL SPOT cua con do ABSTAIN (khong wash-check, khong #17, khong bang chung dong tien); van dung depth/price/taker. takerBUY spot lech cuc doan (<35% hoac >70%) tren vol khong lo = hinh dang farming. Guard chi ha long tin, khong sinh bullish → ap ngay
*Hanh dong tiep: cot alpha_vol_suspect vao triage/snapshot khi build spot collector (P1.5)*

## L-30 [2026-07-30] BLUAI + ARX (u50) — `data-bug` · GHI NHAN (no ky thuat u50 #2, muc CAO)
Token venue_top=bitget: cam so sanh spot-vs-perp cung-ngay cho den khi bug lech ngay duoc xac minh/va; phan tich cross-market phai shift-test truoc. Ghi chu venue vao moi bang so sanh
*Hanh dong tiep: probe xac minh offset tren 2 token + va tai ingest*

## L-31 [2026-07-30] lessons_learned.md rev.1 — `process` · GHI NHAN
Tong hop/dien giai tu tai lieu cu = vung rui ro cao: moi entry phai trace ve cau chu nguon (dinh nghia lay tu yaml/reference, khong tu tri nho dien giai); so lieu khong co trong nguon = khong viet; thuat ngu he thong (M1/M2/ten signal) dung dung nghia goc, khong tai dinh nghia. L-09 ap cho ca tai lieu, khong rieng fire
*Hanh dong tiep: moi consolidation sau nay kem bang trace entry-nguon khi operator yeu cau kiem*

## L-32 [2026-07-30] BANK — `process/rule` · GHI NHAN
Backfill save nhầm file (_NEW suffix) do file gốc bị lock trong Excel — INDEX vẫn trỏ tên cũ → case_daily ghi vào file cũ (4 dòng) thay vì canonical (35 dòng). Fix: sau bất kỳ backfill nào, verify INDEX trỏ đúng canonical; canonical phải có đúng tên gốc.
*Hanh dong tiep: thêm bước verify file name + row count vào checklist sau backfill*

## L-33 [2026-07-30] BANK — `rule` · GHI NHAN
fn=1 fallback (Zone-A-agg) chỉ dành cho cột taker_buy_pct — KHÔNG mượn sang gLSR/pos_r/acc_r. Metric ratio phải đến từ export CSV hoặc để TRỐNG + comment, không ghép chéo metric. Guard bằng assert EXPORT_COL_MAP tại import time trong case_daily.py.
*Hanh dong tiep: assert đã vào case_daily.py dòng sau FORMULA_COLS*

## L-34 [2026-07-30] CASE_BANK_NEW.xlsx (an 30/07), fix da commit — `process/rule` · DA VAO case_daily.py (L-34 raise, commit 2026-07-30)
PermissionError khi save xlsx → RAISE RuntimeError ngay, cam silent-save sang ten khac (_NEW suffix). Ten file khac = INDEX tro sai = case_daily ghi nham → data bi pha vo im lang. Fix: close xlsx roi retry
*Hanh dong tiep: backfill script cung phai RAISE neu gap lock (kiem tra backfill.py)*

## L-35 [2026-07-31] binance-bot-signals P0 regression suite — `process/rule` · GHI NHAN
Bo calib (12 file _result.txt + GATE dict + replay.py) phai song trong git cung voi code — da dung, ghi nhan de giu. Quy tac: moi repo moi can regression suite commit ngay tu dau, khong de calib file ngoai version control. Loi that nhat la khi calib tach khoi code: code duoc update ma calib cu → false pass / false fail.
*Hanh dong tiep: moi repo moi commit regression suite cung voi code trong 24h dau — khong phan tach calib khoi git*

## L-36 [2026-07-31] P0 gate session 31/07 (TAG/BTW reconstruct) — `process/rule` · GHI NHAN
Tai tao data file phai test bang suite nguyen ban (replay.py goc tu git), KHONG tu viet harness moi. Harness tu viet dan den 3 assertion sai: (1) AKE lsr_accum: viet fires_in thay vi never_in; (2) BASED crowd_flush: viet fires_in thay vi never_in; (3) BULLA pos_rerate: dung file tai tao (pos 07-20=1.75) thay vi file goc (1.99). An: bao 40/43 gia, mat thoi gian debug. Fix: dung replay.py goc → 43/43 PASS.
*Hanh dong tiep: quy trinh tai tao data: viet file → chay replay.py goc tu git → PASS truoc khi commit bat ky thu gi*

## L-37 [2026-07-31] B0 bundle backup 4 repo (31/07) — `rule` · DA VAO — bundle 4 repo len VPS /root/archive/ ngay 31/07
Repo chi local (khong remote git server) = single point of failure — mot loi o dia hay OneDrive deauth mat het. Giai phap toi thieu: git bundle → SCP len VPS /root/archive/ trong vong 24h tao repo, sau do bundle lai tai moi milestone lon. Da ap 4 repo ngay 31/07: binance-bot-signals, whale_data, Check onchain, Whales_scan. Repo OneDrive them an: file-lock + single-copy = combo sinh an (CASE_BANK_NEW, L-34).
*Hanh dong tiep: moi repo moi phai co bundle tren VPS trong 24h; nhac lai tai moi milestone lon*

## L-38 [2026-07-31] BULLA 07-20 (B4 probe — 4 nguon 4 so) — `rule` · GHI NHAN — proposals/ratio_daily_canonical_20260731.md cho operator ky
Mot metric mot ngay ra 4 con so khac nhau (1.75/1.68/1.981/1.99) tu 4 nguon: (1) u50 loose = 1.75 (nguon khong ro, retired); (2) top_pos_1h keep-last 23:00 UTC = 1.6811; (3) derived_1h = 00:00 UTC dau ngay = 1.981; (4) native_1d repo goc = 1.99. Nguyen nhan: quy uoc canonical CHUA TON TAI khi calib duoc viet. He qua: verdict buoc phai chon nguon theo ket luan muon co = vi pham nguyen tac. Fix: quy uoc phai duoc ky TRUOC khi bat ky so nao duoc trich dan vao calib/DAILY. Xem proposals/ratio_daily_canonical_20260731.md cho de xuat keep-last canonical.
*Hanh dong tiep: ky proposals/ratio_daily_canonical_20260731.md truoc khi chay backfill tu ngay 31/07*

## L-39 [2026-07-31] proposal v2 (31/07) — boundary canonical — `rule` · GHI NHAN — proposal v2 ký 31/07, CLAUDE.md updated
Quy ước boundary phải TEST bằng đối chiếu nguồn (21/21 diff 0%) trước khi văn bản hóa — proposal v1 hợp lý trên giấy nhưng ngược 180° với thực nghiệm; n=1 suy luận đẹp vẫn phải qua n=21.
*Hanh dong tiep: trước khi văn bản hóa quy ước metric nào: test >= 21 điểm thực nghiệm đối chiếu nguồn*

## L-40 [2026-08-02] NANSEN_KEY_LOCKED blast-radius (02/08) — bot fresh wallets — `rule` · DA SUA — run_daily_wrapper.py (02/08); FreshWatch task updated
Chốt chặn cấp máy có blast radius cấp máy — trước khi gạt công tắc dùng chung (env/key/config toàn cục), bắt buộc liệt kê MỌI consumer hợp lệ; ràng buộc nhắm vào agent phải đặt ở tầng hẹp nhất đủ dùng (per-process wrapper), không đặt tầng chung. Bằng chứng: bot fresh wallets chết 3 ngày (gap 31/07–02/08) vì NANSEN_API_KEY rename sang NANSEN_KEY_LOCKED — automated job \FreshWatch không đọc được key.
*Hanh dong tiep: trước khi rename/remove bất kỳ env/key/config toàn cục: grep MỌI consumer (scheduled task + code), sửa wrapper per-process trước khi rename*

## L-41 [2026-08-03] IDOL/TAG/BR/BANK fn=1 28-31/07 (timing bug) — `rule` · DA SUA — cron + script fixed 03/08; 28-31/07 re-generated
Job aggregate ngay phai chay SAU khi ngay dong tron. Export mid-day = so non co he thong: tai 00:50 UTC IDOL chi co 1/6 ky funding trong store, 5 ky con lai (04:00/08:00/12:00/16:00/20:00) collect trong ngay nhung export da freeze voi fn=1. Fix: cron export 01:20 UTC D+1 (sau khi D dong + buffer 1h20); loai D khoi default_dates() range; them --force-regen de re-generate khi can.
*Hanh dong tiep: verify vong tu nhien: export sang 04/08 phai ra fn=6 cho ngay 03/08. Neu PASS → dong an. Quy tac: khong bao gio generate D truoc 00:05 UTC D+1.*

## L-42 [2026-08-04] IDOL/TAG/BANK — kho spot MM: phan loai theo SO HUU truoc khi doc on-chain — `rule` · OPERATOR KY 04/08
Kho spot cua MM khong tu no la 'hang se xa' — ham muc tieu phu thuoc SO HUU kho. Phan 3 loai TRUOC khi doc bat ky transfer nao: LOAI A (kho MUON tu team — khong gia tri voi MM; P&L 100% o perp; moi deposit/withdrawal la THONG DIEP nhung nguoi doc on-chain, khong phai bang chung; endgame kho round-trip nguyen dai; dong co DAP GIA hau campaign de mua lai tra no kho — canh kho hoi day o day). LOAI B (kho unlock/dau tu — so huu that, cost thap; doanh thu phai hien thuc hoa; neo lich unlock; deposit-len-san <=48h sau ngay unlock = tell hang nhat — BANK 17/07->18/07). LOAI C (tu bo tien mua tai cho — conviction that, cost basis = floor co nghia, khong deadline; loai duy nhat 'di cung thuyen' duoc). Tell phan loai: (1) NGUON kho — deployer/team wallet = nghi A; vesting contract dung lich = B; gom le nhieu nguon dai han = C; (2) nhip voi lich unlock; (3) hanh vi kho HAU DINH — round-trip nguyen = A, ban that = B; (4) do 'dien' cua transfer — chia may deu + Sent=0 trung bay = tin hieu re, nghi A. Bang chung: IDOL 3 man mot dao cu (8% vao 03-05/07 -> rut 273M staging shape 13 vi -> redeposit 102M) trong khi ket that o perp ~$1.2-1.8M; TAG 90B round-trip May->Jul; BANK chan unlock ban that (lai A+B); AKE 'perp vol 70x spot — spot la can gat'.
*Hanh dong tiep: (a) cot mm_archetype{A/B/C/lai} + kho_nguon cham hoi to 12 case + case song; (b) BR kho 6% trace nguon = viec phan loai dau tien — neu team wallet -> Loai A -> cu flush gLSR 03/08 doc lai duoi anh sang 'dao cu man hai'; (c) moi dong PnL spot chua co sell-side xac nhan ha nhan 'unverified inference' (IDOL 111M, BANK $12-28M); (d) K3 sell-side Pancake IDOL van la test phan xu — PENDING.*

## L-44 [L-44(a) DIEU KIEN KET THUC CAMPAIGN: Loai A (kho-muon) = ghe-roi perp la het. Loai B/C (unlock/tu-mua) = ghe-roi perp la CHUYEN PHA — ket thuc that khi kho/vol ≤10% (Cua A) hoac Cua B kich hoat (short-hedge). TUT: pos_r crash 08-05 (−48%) = GHE-ROI LAN 2 (HARVEST-INTO-STRENGTH), KHONG phai L-26, campaign van tiep tuc.] TUT — `DRAFT` · 
2026-08-08

## L-45 [L-45(b) DURATION SCALING: Thoi luong campaign ty le thuan voi build_window va kho_size. Tham khao draft n=4: BANK (build ~17d, Loai B) → campaign D+17; IDOL (build ~7d, Loai A partial) → D+11; TUT (build 13d, Loai C) → D+16+ ongoing. CLO TBD. Hypothesis: dai build = dai campaign; chua du n de calib chinh xac.] TUT/BANK/IDOL/CLO — `DRAFT` · 
2026-08-08

## L-46 [2026-08-09] CASE_BANANAS31 + CASE_HEI — `ARM` · ACTIVE
Video vs Photo: hai hồ sơ pos_r cao nhưng ý nghĩa khác nhau. "Video" (CASE_HEI) = build thật: pos_r vừa phải, đồng-bộ giá, ít dist_wall. "Photo" (CASE_BANANAS31) = snapshot đẹp nhưng static: pos_r=6.7 RẤT CAO nhưng sign-corr Δpos_r vs ret_1d ~50% (47.7% opposite) — pos_r KHÔNG predict giá. Thêm: dist_wall_day=57/503 (11.3%), knife_crowd=9 ngày — dấu MM đang bán vào pump. Kết luận: pos_r level đơn độc KHÔNG phân biệt được BTW vs phân phối. Cần 3 đạo hàm: level + slope + sync. Xem Phụ lục A.5. Nguồn: CASE_BANANAS31 phân tích 08-09/08/2026 · ký 09/08 · đối chứng: CASE_HEI.xlsx
*Hanh dong tiep: Khi pos_r >5: check sign-corr Δpos_r vs ret_1d (30d OLS). <55% → Photo → TRACKING-passive. Không vào setup cho đến đồng hồ cụm trigger (xem L-47). Implement: build_case.py đã in OLS slope + sign-corr.*

## L-47 [2026-08-09] CASE_BANANAS31 — `ARM` · ACTIVE
Đồng hồ cụm: Build-into-weakness không kéo dài vô tận. BANANAS31 pump cluster: Jun/Aug/Oct 2026 [n=3 inference từ vol spikes ≥8×med14]. Build cụm #3 từ 06/2026 → đồng hồ ~60-90 ngày → cụm #4 dự kiến Aug-Oct/26. Nếu không có ignite (gLSR≤0.7 + pos rebuild ≥3d) trong cửa sổ → build failed → MM exit. Hiện tại gLSR=1.20 > ngưỡng ignite 1.1 → block entry (crowd đã long hết). Verdict NO_SETUP — TRACKING-passive. Nguồn: CASE_BANANAS31 · ký 09/08
*Hanh dong tiep: Mỗi case BTW: ghi ngày dự kiến đồng hồ cụm tiếp theo. Theo dõi: gLSR drop về ≤0.7 (lý tưởng) hoặc ≤0.9 (cảnh báo). Nếu hết cửa sổ không trigger → escalate INVALIDATE check.*

## L-48 [2026-08-09] CASE_BANANAS31 + CASE_IDOL — `DATA` · ACTIVE
fullyDelisted Alpha → ABSTAIN taker_alpha. Klines[9]==klines[5] trên BAPI khi fullyDelisted=True (taker column = close price, không phải real taker). Đã confirm: IDOL (ALPHA_223, L-43 context) + BANANAS31 (ALPHA_21). Rule chốt: IF offline=True OR offsell=True OR fullyDelisted=True → taker_alpha=NaN, flag=ABSTAIN. Áp dụng ngược cho mọi case đang mở có Alpha token. Nguồn: CASE_BANANAS31 + CASE_IDOL · ký 09/08
*Hanh dong tiep: Khi collect Alpha mới: check fullyDelisted trước khi parse klines[9]. Script build_case.py đã implement ABSTAIN block. Audit retrospective: CASE_TUT/BR/CLO — check Alpha status.*
