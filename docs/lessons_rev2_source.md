# LESSONS LEARNED — FreshWatch (rev.2 source — operator approved 2026-07-30)

> Ban goc operator duyet. File nay la nguon de sync vao CASE_INDEX sheet LESSONS.
> KHONG dung file nay lam tai lieu chinh — chinh thuc la sheet LESSONS.
> Lan sinh: 2026-07-30 (rev.2 — sua theo review advisor 30/07). Tong: 34 bai (L-01 → L-34)
>
> Rev.2 changes:
> - L-14/15/16/17/18/19/20: sua noi dung (xem ghi chu tung bai)
> - L-26→L-31: bai moi (wrong-side fuel, M2 dao dau, tu-ha-cap narrative,
>   alpha_vol_suspect, Bitget lech ngay, consolidation nguon)
> - L-26 (file-canonical) + L-27 (fn=1 guard) cu → renumber L-32 + L-33
> - L-34: PermissionError → RAISE, cam silent-save ten khac

---

## I. SIGNAL-LEVEL

### L-01
- ngay: 2026-07-30
- case_nguon: BR (+BAS,TUT,BANK)
- bai_hoc: OI-floor = so vi the MM: ratio doc tai day OI trong so cao (retail da roi); pos_r nhich tai nen chet = tin hieu som dam; ratio tai OI-peak phai chiet khau
- loai: dinh luat
- trang_thai: DA VAO master plan §1 #9
- hanh_dong_tiep: oi_floor_flag (OI<=1.1x min30d) lam he so ranker — chua active, thu bang chung

### L-03
- ngay: 2026-07-29
- case_nguon: BANK (ho so 4 lop)
- bai_hoc: Tell som nhat co the nam tron MOT lop don doc 11 ngay (perp) — doi da lop lam dieu kien ARMED se lot ho BANK. Xac nhan da lop chi den DUNG luc no
- loai: thesis
- trang_thai: DA VAO — so do cho R4-TRIGGER (khong lop nao bat buoc)
- hanh_dong_tiep: moi case moi: ghi T-k lan dau >=2 lop nguoc gia vao ho so

### L-04
- ngay: 2026-07-29
- case_nguon: BANK
- bai_hoc: concentration_shift KHONG ban tren BANK = negative case HOP LE: level-type (div cao tinh) vs delta-type (acc sap pos giu) la HAI ho tin hieu khac nhau, khong va sensor de om ca hai
- loai: rule
- trang_thai: GHI NHAN — cho test duong tren TUT (CASE-04)
- hanh_dong_tiep: neu TUT ban dung 10-12/07 -> sensor song, xet vao screen ranker

### L-06
- ngay: 2026-07-28
- case_nguon: TAG (Gate probe)
- bai_hoc: Inventory != gom: toan khoi luong (V_venue vs $withdrawal) phan xu duoc 'vua mua' hay 'hang co san'. Book sieu mong = BAI DO — withdrawal khoi bai do = khoa float, khong doc thanh 'chuyen di ban'
- loai: rule
- trang_thai: GHI NHAN — dua vao khung E4/M4 khi cham diem transfer
- hanh_dong_tiep: nguong nhap: V_14d >= 2x withdrawal moi coi la 'co the gom tren venue'

### L-11
- ngay: 2026-07-28
- case_nguon: TAG 27-28 (BULLA truoc do)
- bai_hoc: Wash-by-rally: crowd tu roi bang chot loi vao da tang — cu ru bo sung KHONG bat buoc truoc leg. gLSR giam trong ngay gia tang = nhien lieu dang duoc don, doc BULLISH cho campaign
- loai: thesis
- trang_thai: DA CO tu BULLA — TAG cung co lan 2
- hanh_dong_tiep: glsr_slope am trong ngay xanh = co xac nhan

### L-14 (rev.2 — viet lai)
- ngay: 2026-07-30
- case_nguon: TAG 08-09/07 + AKE 08-10/07
- bai_hoc: Dump manh + gLSR SAP >=30%/<=3d = wash-by-crash: mot phat an hai: don chi phi long + nap nhien lieu short (crowd short moi = nhien lieu re cho squeeze). La bien the crowd_flush thu nhat, doi xung L-11 (rally) va L-15 (bait). Phan biet ro voi L-26: gLSR SAP khi gia sap (wash) vs gLSR TANG khi gia sap (wrong-side fuel)
- loai: thesis
- trang_thai: DA VAO yaml (crowd_flush cause=crash)
- hanh_dong_tiep: phan biet ro voi L-26 (gLSR TANG khi gia sap = hien tuong nguoc, KHONG phai wash)

### L-15 (rev.2 — bo sung co che)
- ngay: 2026-07-30
- case_nguon: BANK 02/07 + BASED 01&09/07 + POWER 08-09/07
- bai_hoc: Vol spike >=8x med14 + gia bi tu choi <=2d = bait-probe: muc dich khong phai markup het ma la DAY crowd short → nap nhien lieu squeeze. Sau bait canh gLSR sap trong <=3d lam xac nhan; vol persistence T+1 phan biet bait vs ignition that
- loai: thesis
- trang_thai: DA VAO yaml (crowd_flush cause=bait)
- hanh_dong_tiep: tag probe events trong EVENTS log khi thay pattern

### L-16 (rev.2 — doi ten, KHONG phai 'M2 dao dau')
- ngay: 2026-07-30
- case_nguon: BR + EVAA + CLO
- bai_hoc: div_raw truot tu >1 xuong <1 = vi the lon thu hep/dao long bias = chom phan phoi; flag STAND_ASIDE review; khong ARM sau div-flip neu chua co bang chung re-gom. LUU Y THUAT NGU: day KHONG phai 'M2 dao dau' — M2 la module CEX balance flow (xem L-27)
- loai: thesis
- trang_thai: GHI NHAN
- hanh_dong_tiep: flag div-flip trong DAILY log; ho hang gan voi lsr_dist (da la suppressor yaml)

### L-17 (rev.2 — RULE ve nguyen ban)
- ngay: 2026-07-30
- case_nguon: AKE + ESPORTS
- bai_hoc: Squeeze/markup chet khi nhien lieu chet — hai cua dong an: (a) gLSR hoi ve ~1 (crowd short dau hang), (b) muc tieu cu the goc (TARGETED_SQUEEZE). Dang giu vi the ma mot trong hai bat → EXIT_NOW. [De xuat CHUA CALIB: thao tac hoa bang glsr_slope_5d doi dau — chua test case nao, glsr_slope_5d hien chi la cot hien thi (A5), khong phai gate]
- loai: dinh luat
- trang_thai: DA VAO master plan §1 #5 + EXIT_NOW conditions
- hanh_dong_tiep: neu muon slope-flip thanh trigger → di duong proposal + calib nhu #17

### L-18 (rev.2 — xoa so bia)
- ngay: 2026-07-30
- case_nguon: u50_verdicts §2 (n=18)
- bai_hoc: Truoc ARM phai check du 3: (1) pha chu ky (nhin du px7/px14 + oi_cycle_pos, khong chi cua so 28d), (2) crowd structure (gLSR + dao ham — co tinh gan vo dung), (3) OI khong tai PEAK. Thieu 1/3 = low-conviction. KHONG trich dan % precision khi chua do — precedent dem that (n=...), cam noi %
- loai: thesis
- trang_thai: GHI NHAN
- hanh_dong_tiep: phase_check vao ARM checklist; precision that do bang shadow-mode P2 + alerts_log

### L-23
- ngay: 2026-07-30
- case_nguon: TAG
- bai_hoc: Fire margin mong -> fade la kich ban xac suat cao: TAG 28/07 fire bien mong, ret_3d=-9.87%, crowd nap long vao duong gia xuong (gLSR 1.30->1.61). Invalidate som: gia khong confirm T+1/T+2 + gLSR tang tiep = WATCH-ha-nhiet, khong ARM lai som
- loai: thesis
- trang_thai: GHI NHAN
- hanh_dong_tiep: them T+1/T+2 price-confirm check vao S1 handover (48h khong confirm = WATCH-ha-nhiet)

### L-26 (MOI rev.2 — tach tu L-14 cu)
- ngay: 2026-07-30
- case_nguon: ESPORTS hau-climax + TAG 29/07 + BLUAI
- bai_hoc: Gia sap/roi + gLSR TANG = crowd long bat dao = nhien lieu SAI phia — NGUOC han wash-by-crash (L-14: gLSR SAP). He qua: (a) leg-len ke tiep can lua long nay bi rua truoc, (b) con dang SUPPRESSED co pattern nay thi REMAIN, (c) khong doc nham thanh 'co nguoi gom'
- loai: thesis
- trang_thai: GHI NHAN
- hanh_dong_tiep: dieu kien tien quyet "crowd flush truoc leg" ghi vao chot canh cac case dinh (TAG, BR, ESPORTS)

---

## II. MM-LEVEL

### L-05
- ngay: 2026-07-30
- case_nguon: BR + BTW
- bai_hoc: Withdrawal gan dinh = MOI on-chain (bang chung #2, vong doi 4 thang truy tron: rut-tai-dinh -> phan phoi -> redeposit). Moi withdrawal cua nhom MM-BAIT phai doc ngo toi da
- loai: dinh luat
- trang_thai: DA CO trong §1 #1 (rule dao dau M2) — BR cung co them
- hanh_dong_tiep: token dinh bai nay vao SO DEN trong MM_BOOK

### L-07
- ngay: 2026-07-30
- case_nguon: BR (operator)
- bai_hoc: Pump-to-distribute: kho len san = CHUAN BI DAN, khong xa tai gia hien tai — can leg keo tao hype truoc. Khong long theo khi KHONG co ghe big-long de di cung (div ~1) = vi tri con moi. Dieu kien tien quyet cua leg that: crowd long phai bi rua
- loai: thesis
- trang_thai: GHI NHAN — khuon moi, BR la test song
- hanh_dong_tiep: neu BR keo that: doi chieu chot 1+2 co bao truoc khong

### L-08
- ngay: 2026-07-30
- case_nguon: BANK/BTW/ESPORTS/BR
- bai_hoc: MM profile la NUA verdict — moi MM danh mot kieu (bid-walk kien nhan / bait-withdrawal / squeeze muc tieu). Gan MM_ID can >=3 van tay trung; gan au te hon khong gan
- loai: process
- trang_thai: DA VAO tracker v1.1 (§I + MM_BOOK)
- hanh_dong_tiep: cross-campaign trung dia chi/van tay = alert cap he thong

### L-12
- ngay: 2026-07-30
- case_nguon: BR (operator)
- bai_hoc: Unlock la dong cung CO LICH — MM biet truoc va danh quanh no (keo truoc unlock de xa vao hype / de truoc unlock de gom re). Case thieu khoi J = mu mot mat
- loai: process
- trang_thai: DA VAO tracker v1.1 (§J bat buoc)
- hanh_dong_tiep: viec tay: tra unlock BR/TAG/BANK — BR truoc

### L-27 (MOI rev.2)
- ngay: 2026-07-30
- case_nguon: BTW vs BAS/TAG | AKE/IDOL
- bai_hoc: M2 (CEX balance flow) tu no KHONG mang y dinh — dau cua no do boi canh quyet: vi tri chu ky + funding regime + hanh vi gia. Chay M2 don le la An tron bay BTW. Suppressor o bat ky lop nao phu quyet moi bullish cua ca ba lop
- loai: dinh luat
- trang_thai: DA VAO master plan §1 #1 + A1 (R4)
- hanh_dong_tiep: giu ten 'M2' doc quyen cho balance flow — khong dung cho div/ratio (an L-16 rev.1)

---

## III. DATA-QUALITY

### L-09
- ngay: 2026-07-29
- case_nguon: P1 fire audit
- bai_hoc: KHONG tin loi giai thich fire — chi tin bang dieu kien tung dong (an 'vol drop faster than OI' la cau bia; fire dung nhung narrative sai van la doc sai). Moi fire phai tu bao ve bang input series + yaml check
- loai: process
- trang_thai: DA VAO ky luat A4 (mo rong A4.2)
- hanh_dong_tiep: ap cho ca advisor: so tay cua toi dung sai spec cu (1.5x vs 1.3x da ky) — yaml locked la luat

### L-10
- ngay: 2026-07-29
- case_nguon: BR/TAG pipeline
- bai_hoc: Data hong cung phai ghi (data_bad=1, to cam) — lo hong la thong tin; dong non (funding_n thieu) phai bi guard loai khoi moi streak/window
- loai: process
- trang_thai: DA VAO P1 (funding_n guard) + tracker schema
- hanh_dong_tiep: an pipeline MISSING cuoi thang: kiem toan store dinh ky

### L-19 (rev.2 — xoa so bia)
- ngay: 2026-07-30
- case_nguon: u50 §2 + CLO/BLUAI/STAR (n=18)
- bai_hoc: Signal fire ban giong nhau o pha gom va pha phan phoi — can phase_tag (ACCUMULATE/MARKUP/DISTRIBUTE/UNKNOWN) tu oi_cycle_pos + div trend + glsr_slope de loc; den khi co phase_tag: moi fire phai kem phase check tay (L-18). Khong trich % false-rate khi chua do
- loai: process
- trang_thai: GHI NHAN — no P2
- hanh_dong_tiep: thiet ke phase_tag inference trong P2

### L-20 (rev.2 — tach phan narrative sang L-28)
- ngay: 2026-07-30
- case_nguon: TAG/BR 28-29/07
- bai_hoc: fn=1 / data_bad=1 / missing >3 ngay trong window / so tu 1 nguon khong kiem chung → low_conf=True; so bi ha cap KHONG lam threshold ARM/FIRE
- loai: process
- trang_thai: DA VAO CLAUDE.md (fn=1 rule)
- hanh_dong_tiep: mo rong tu-ha-cap cho data_bad flag (ngoai fn=1)

### L-21
- ngay: 2026-07-30
- case_nguon: BR (an 30/07)
- bai_hoc: OI daily canonical = export Binance openInterestHist 00:00 UTC. So intraday (Coinglass/GMGN) chi vao EVENTS kem timestamp, khong vao DAILY. An 30/07: BR 4,634,000 (intraday) vs 3,782,263 (export 00:00) chenh 22%. Rule: mot cot DAILY mot so canonical
- loai: rule
- trang_thai: DA VAO CLAUDE.md
- hanh_dong_tiep: khi co so OI: xac nhan nguon + gio chup truoc khi ghi DAILY

### L-22
- ngay: 2026-07-30
- case_nguon: TAG+BR 28-29/07
- bai_hoc: fn=1 (native_1d low_conf) khong dung lam so chot ARM/FIRE. Fallback: Zone A aggregate tu ledger_v2.xlsx CAMPAIGNS, ghi ro Zone-A-agg. TAG 29/07: gLSR 1.81 (fn=1 SUSPECT) vs 1.61 (Zone-A-agg) — chenh 0.2 du dao nhan dinh toc do nap crowd
- loai: rule
- trang_thai: DA VAO CLAUDE.md
- hanh_dong_tiep: khi fn<6: tu dong dung Zone-A-agg + flag SUSPECT trong handover

### L-24
- ngay: 2026-07-30
- case_nguon: BR/TAG (an 30/07)
- bai_hoc: oi_vs_med14 Excel != oi_vs_med14 signals.py (window ket thuc ngay khac). Moi so DAILY phai mang nhan: nguon + window cu the. Khong dung Excel calc lam proxy signals.py canonical. Hai nguoi doc hai so khac nhau cung ten = an tranh luan vo ich
- loai: rule
- trang_thai: DA VAO CLAUDE.md (facts da chot)
- hanh_dong_tiep: moi oi_vs_med14 phai kem (signals.py, window=...) hoac (Excel, col X)

### L-25
- ngay: 2026-07-30
- case_nguon: BR+TAG (tai pham 30/07)
- bai_hoc: Mot-nha-mot-data tai pham x2 trong session 30/07: (1) OI DAILY 2 so tu 2 nguon; (2) gLSR/div dung fn=1 raw thay vi aggregate canonical. Rule: moi cot DAILY mot nguon canonical khai bao tuong minh. >=2 so cung metric -> chon canonical + ghi an vao EVENTS
- loai: rule
- trang_thai: DA VAO CLAUDE.md (KY LUAT)
- hanh_dong_tiep: audit cot DAILY hien tai: co cot nao 2 nguon khong khai bao khong?

### L-29 (MOI rev.2 — tu u50 §3a)
- ngay: 2026-07-30
- case_nguon: OPN + HYPER (u50 §3a, n=2)
- bai_hoc: alpha_vol_suspect = vol_spot/vol_perp > 3x → moi metric VOL SPOT cua con do ABSTAIN (khong wash-check, khong #17, khong bang chung dong tien); van dung depth/price/taker. takerBUY spot lech cuc doan (<35% hoac >70%) tren vol khong lo = hinh dang farming. Guard chi ha long tin, khong sinh bullish → ap ngay
- loai: guard
- trang_thai: DA VAO amendment A6 (guard)
- hanh_dong_tiep: cot alpha_vol_suspect vao triage/snapshot khi build spot collector (P1.5)

### L-30 (MOI rev.2 — tu u50 no ky thuat #2)
- ngay: 2026-07-30
- case_nguon: BLUAI + ARX (u50)
- bai_hoc: Token venue_top=bitget: cam so sanh spot-vs-perp cung-ngay cho den khi bug lech ngay duoc xac minh/va; phan tich cross-market phai shift-test truoc. Ghi chu venue vao moi bang so sanh
- loai: data-bug
- trang_thai: GHI NHAN (no ky thuat u50 #2, muc CAO)
- hanh_dong_tiep: probe xac minh offset tren 2 token + va tai ingest

---

## IV. PROCESS

### L-02
- ngay: 2026-07-28
- case_nguon: AKE (an PA-B)
- bai_hoc: KHONG amend dinh nghia signal de om case ngoai ho cua no — ghi miss + negative assertion. lsr_accum nghieng ho bid-walk, s3_eve ganh ho taker-driven: hai signal BU nhau
- loai: process/rule
- trang_thai: DA VAO GATE dict + §10 (commit b0b4cff4)
- hanh_dong_tiep: ap dung lai khi concentration_shift gap BANK (L-04)

### L-13
- ngay: 2026-07-30
- case_nguon: ledger vs tracker
- bai_hoc: Phan vai: ledger = so cai NGANG (thong ke precision, may doc); tracker = ho so DOC (thesis-check, nguoi doc). Verdict chi song MOT noi (case file), ledger Zone B rut gon state+case_id. Mot chieu du lieu, khong ghi nguoc
- loai: process
- trang_thai: DA DUYET 30/07 — xem sheet PHAN_VAI
- hanh_dong_tiep: them cot case_id vao Zone B (viec tay 1 phut)

### L-28 (MOI rev.2 — tu u50 §6)
- ngay: 2026-07-30
- case_nguon: u50 §6 (AGT / HUMA-AT sync / listing 04-14)
- bai_hoc: Moi narrative dung tren mot nguon phai kiem nguon goc (aggregator != klines; mep cua so = artifact ung vien). Narrative khong con dung duoc → RUT cong khai va GHI SO muc 'da tu ha cap' — de khong tu lua va khong tai sinh. Cu luan diem chi giu phan con dung tren bang chung
- loai: process
- trang_thai: GHI NHAN — u50 §6 la mau chuan
- hanh_dong_tiep: moi report lon co muc 'bang chung da tu ha cap' nhu u50

### L-31 (MOI rev.2 — an chinh file nay)
- ngay: 2026-07-30
- case_nguon: lessons_learned.md rev.1
- bai_hoc: Tong hop/dien giai tu tai lieu cu = vung rui ro cao: moi entry phai trace ve cau chu nguon (dinh nghia lay tu yaml/reference, khong tu tri nho dien giai); so lieu khong co trong nguon = khong viet; thuat ngu he thong (M1/M2/ten signal) dung dung nghia goc, khong tai dinh nghia. L-09 ap cho ca tai lieu, khong rieng fire
- loai: process
- trang_thai: GHI NHAN
- hanh_dong_tiep: moi consolidation sau nay kem bang trace entry-nguon khi operator yeu cau kiem

---

## Bai renumber (tu agent session 30/07)

### L-32 (= L-26 cu — file-canonical)
- ngay: 2026-07-30
- case_nguon: BANK
- bai_hoc: Backfill save nham file (_NEW suffix) do file goc bi lock trong Excel — INDEX van tro ten cu → case_daily ghi vao file cu (4 dong) thay vi canonical (35 dong). Fix: sau bat ky backfill nao, verify INDEX tro dung canonical; canonical phai co dung ten goc
- loai: process/rule
- trang_thai: GHI NHAN
- hanh_dong_tiep: them buoc verify file name + row count vao checklist sau backfill

### L-33 (= L-27 cu — fn=1 guard)
- ngay: 2026-07-30
- case_nguon: BANK
- bai_hoc: fn=1 fallback (Zone-A-agg) chi danh cho cot taker_buy_pct — KHONG muon sang gLSR/pos_r/acc_r. Metric ratio phai den tu export CSV hoac de TRONG + comment, khong ghep cheo metric. Guard bang assert EXPORT_COL_MAP tai import time trong case_daily.py
- loai: rule
- trang_thai: GHI NHAN
- hanh_dong_tiep: assert da vao case_daily.py dong sau FORMULA_COLS

### L-34 (MOI — PermissionError RAISE)
- ngay: 2026-07-30
- case_nguon: CASE_BANK_NEW.xlsx (an 30/07), fix da commit
- bai_hoc: PermissionError khi save xlsx → RAISE RuntimeError ngay, cam silent-save sang ten khac (_NEW suffix). Ten file khac = INDEX tro sai = case_daily ghi nham → data bi pha vo im lang. Fix: close xlsx roi retry
- loai: process/rule
- trang_thai: DA VAO case_daily.py (L-34 raise, commit 2026-07-30)
- hanh_dong_tiep: backfill script cung phai RAISE neu gap lock (kiem tra backfill.py)
