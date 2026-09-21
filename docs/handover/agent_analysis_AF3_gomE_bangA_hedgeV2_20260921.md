# AGENT → ANALYSIS · AF3 · GOM-E Bảng A vs HEDGE v2 List A · MỘT DÒNG

**Bối cảnh (30s)**: GOM-E T1 hiện in Bảng A (121 tokens hedge-farm registry) + Bảng B
(mode-switch alerts). HEDGE v2 spec (`docs/HEDGE_report_v2_spec_20260921.md`) mô tả
List A (73 tokens hedge tracker + acc·pos·funding·kr). **Cả hai mô tả hedge**.

## Đo bằng chứng

- GOM-E Bảng A · [gom_e.py:686-694](scripts/gom_e.py#L686-L694): 121 tokens · `sym · days · div_avg3 · gLSR · f_avg` · condition = H1/H2/H3 (§1 spec v0.9.2 · div≤0.85 trong 10/20 ngày ∧ f_avg>0 trong 12/20)
- HEDGE v2 List A · spec §2: 73 tokens · `sym · div · acc_r · pos_r · funding_state · sn · kr% · dist%` · condition = div_avg3 ≤0.5 run ≥3d (`watchlist_daily.py` LIST A gate)

**Chồng chéo**: cả 2 dựa freshwatch daily · đo hedge structure · nhưng ngưỡng khác nhau (GOM-E lỏng div≤0.85, HEDGE v2 chặt div≤0.5). Tokens overlap phần lớn.

## Ba đường (xin chốt một dòng)

`AF3: 1|2|3`

**(1) DỜI Bảng A sang HEDGE v2 · GOM-E chỉ giữ phần MODE-SWITCH** — DEV đề nghị
- GOM-E T1 = chỉ Bảng B (alerts + tag NUM-DRIVEN/DENOM-ASSIST/OI-EXPAND) · summary line
- HEDGE v2 kế thừa List A (đã có · thêm 4 cột · nới ngưỡng nếu cần match GOM-E Bảng A)
- **Ưu**: GOM-E body ~500-800 chars (chỉ header + alerts) · KHÔNG cần nén · KHÔNG cần thay slice ngay · không lo n_sent=5/6 skip
- **Nhược**: HEDGE v2 phải cover superset (73 chặt + phần rộng còn lại)

**(2) GIỮ CẢ HAI** (Bảng A ở GOM-E + List A ở HEDGE v2)
- 2 tin cùng mô tả hedge (khác cutoff) · hai câu chuyện có thể mâu thuẫn
- GOM-E vẫn cần nén (7728-8130 chars → ≤4066)
- **Ưu**: giữ nguyên semantic cũ
- **Nhược**: dupe · vẫn nợ nén GOM-E

**(3) DỜI toàn bộ GOM-E T1 vào HEDGE v2 · retire gom_e T1 cron**
- HEDGE v2 = Bảng A + SỰ KIỆN (bao gồm MODE-SWITCH alerts)
- Retire `run_gom_daily → gom_e` slice-truncate path hoàn toàn
- **Ưu**: một tin duy nhất mô tả hedge · KHÔNG dupe
- **Nhược**: HEDGE v2 phình to · cần đo lại budget · mất phân tách intent (T1 daily vs T2 intraday)

## Ràng buộc phát hiện AF2

Đêm nay gom_e nếu thay slice → verdict fresh = `KÍCH` (đo grep [master_preview_send.py:505-508](scripts/master_preview_send.py#L505)) → standing FAIL → cron SKIP mất bản tin master. Cấm sửa slice trước format.

Nếu **(1)** hoặc **(3)** → GOM-E không cần format nén, không cần thay slice ngay — rủi ro cron thấp nhất.

Nếu **(2)** → phải nén GOM-E TRƯỚC khi thay slice.

## Chờ

`AF3: 1|2|3` — sau chốt DEV wire theo thứ tự an toàn (không đảo). Không code trước khi có chữ.
