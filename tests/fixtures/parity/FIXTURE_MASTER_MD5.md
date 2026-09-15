# FIXTURE MASTER · V3.5m · KÝ 2026-09-09

## NIÊM SCOPE (V3.5m directive item 3)

BỘ-NIÊM CURRENT = p1-p22 ONLY (14 pins digest namespace).
p23-p26 = NGOÀI bộ-niêm cho tới khi ANALYSIS xác định nguồn GOM-E as-printed thật.
Proxy source (LIST-A + freshwatch_daily) bị bác vì AIO/GIGGLE lệch spec (p24 SPEC-DISCREPANCY).

## p20 SIDECAR-MISSING → N/A-ERROR (in-niêm)
Expected: _hedge_line("") returns string containing "N/A-ERROR" · NO digit chars.
Legacy evidence: 09-08 watchlist Path-bug crash → sidecar missing.

## p21 PX-NA → WATCH (in-niêm)
Expected: APR target=09-08 rendered as ⏸ WATCH [PX-PENDING] NOT → PRE.

## p22 COUNT ≡ PRINTED (in-niêm · đen→xanh V3.5l fix)
Expected: ⭐-PRE header N = printed_lines + tail (+K nữa: ...) with K=N-TOP_K=6.

## PENDING p23-p26 (NGOÀI-NIÊM · chờ ANALYSIS)
Rollback V3.5m: ⭐-PRE PRE trần + [SUBTAG-PENDING] banner · zero proxy label.
Đêm 1/2 KHÔNG được đếm · đồng hồ chờ nguồn thật.

## LUẬT-CON (V3.5m item 5)
"Mọi mục Chờ-operator PHẢI cite bằng-chứng-tường {lệnh/path · hit/miss}."
Blocker-shift = corpus L-79 exhibit · phải có evidence · cấm no-cite.

## AMENDMENT · MASTER-LIVE + V1.3-SPECIES-LAYOUT-ONLY · KÝ 15/09

### p21 tái định (V1.3 layout-only)
Token PX-PENDING (px_now=None) route vào khối loài theo tagger nhị phân
(scripts/species_tag.py md5 388ac36f), KHÔNG cứng vào khối ⏸ WATCH-PX-PENDING.
Expected FAIL: dòng có "⏸" hoặc "[PX-PENDING]" cũng chứa "→ PRE".
Expected PASS: mọi dòng px-missing giữ direction WATCH (không → PRE bất kể khối).
Backward-compat V1.2: giữ semantic APR ghim cứng nếu marker V1.3 vắng.

### p22 tái định (V1.3 layout-only)
Header đếm ≡ dòng token in + tail names, cho MỌI khối có (N):
  ⭐-PRE (V1.2 · pre-cutover) · 🔻 XẢ-WATCH · POST-DUMP · ⏸ WATCH-PX-PENDING
  ── A/B/C/D/E/? CHƯA XẾP LOÀI ── (V1.3 species blocks).
TOP_K-agnostic: block CÓ THỂ truncate top-K + tail HOẶC in-all — cả hai PASS
miễn header = printed + tail. Dòng nhắc "(→ xem X)" KHÔNG tính.
Rỗng-hết species (mọi khối loài (0)) → N/A (không PASS · thiếu chủ thể chấm).

### p27 concat-seal (mới · AMD-07 both-ends)
· artifact = data/artifacts/master_concat_<target>.txt (body sans seal)
· body sent = data/artifacts/master_body_<target>.txt (artifact + seal line)
· PASS ≡ md5(artifact)[:12] == seal-line-trong-body
· FAIL: artifact missing · body missing · seal vắng · md5 lệch

### p81 counter-CHỜ (bug counter chặn 09-13 / 09-14)
Preview era n>2 → nhãn "[ĐỦ 2/2 · CHỜ 'ok master live']" · KHÔNG đếm 3/2, 4/2.
Post-cutover (target ≥ 2026-09-15) → "[MASTER · live từ 2026-09-15]" · không đếm.

### Footer meta (V1.3 layout-only)
`ledger_state=<md5> · fixture_master=<md5> · species=388ac36f · book=77d86654 ·
 amendments_applied=[MASTER-LIVE, V1.3-SPECIES-LAYOUT-ONLY]`

