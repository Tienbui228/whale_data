# TICKET · UNIVERSE-IN-GIT · KÝ 17/09

## Bối cảnh

`data/config/freshwatch_symbols.txt` + `data/config/freshwatch_source.json` bị `.gitignore` chặn
(cùng pattern `data/config` với các file khác). Kết cục:
- Universe hiện tại chỉ có bản duy nhất trên VPS
- Không có version history, không audit trail cho lần đổi
- Nếu VPS mất data hoặc universe bị ghi sai → không rollback được

Đúng lỗ đã gặp với crontab (KÝ 13/09, Ticket A/B/C, chọn Option C).

## Áp Option C (giống crontab)

**Manual commit mỗi lần universe đổi + drift-check qua sidecar mtime**:
1. Mỗi lần `refresh_universe_weekly.py` (hoặc thủ công) ghi mới → COPY sang `ops/` với ngày suffix
2. Commit git với message ghi rõ n_added + lý do
3. Sidecar drift-check hàng ngày: nếu `freshwatch_source.json` mtime > `ops/freshwatch_source_LATEST.json` mtime + 24h → alert (universe đổi nhưng chưa commit)

## Files niêm

Chép snapshot hôm nay (post-O5):

- `ops/freshwatch_symbols_20260917.txt` · md5 `e7cab7650c3ac3ec2ef4c5c5eea28073` · 226 lines
- `ops/freshwatch_source_20260917.json` · md5 `2435c1a836992eccc3b496c10bcdfce3` · 226 entries (147 curated + 79 auto)

## Workflow · mỗi lần universe đổi

```bash
# Sau khi refresh_universe_weekly.py chạy (auto) hoặc operator ký thêm tay:
scp root@5.223.67.21:/root/Data_back_test/whale_data/data/config/freshwatch_symbols.txt ops/freshwatch_symbols_$(date -u +%Y%m%d).txt
scp root@5.223.67.21:/root/Data_back_test/whale_data/data/config/freshwatch_source.json ops/freshwatch_source_$(date -u +%Y%m%d).json
git add ops/freshwatch_*_$(date -u +%Y%m%d).*
git commit -m "universe snapshot YYYYMMDD · n=X · diff: +N added, -M stale"
```

## Rollback path (nếu universe bị ghi sai)

```bash
# Restore về snapshot ngày cụ thể
ssh root@5.223.67.21 "cp ~/whale_data/data/config/freshwatch_symbols.txt.bak_147_4dba2ae10758_20260917 ~/whale_data/data/config/freshwatch_symbols.txt"
# Rebuild ledger scope
ssh root@5.223.67.21 "cd ~/whale_data && for t in $(seq 0 6); do python3 scripts/ledger_backfill_30d_v3_5.py --target $(date -u -d "$t days ago" +%Y-%m-%d) --window 30; done"
```

## Chờ chữ

Ticket ghi luật, không tự thi hành. Operator ký "ok universe-in-git Option C" → agent
apply workflow trên (bao gồm khi N5 cron auto-thêm token, agent SCP + commit ngay).
