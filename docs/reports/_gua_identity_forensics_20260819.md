# GUA / SUPERFORTUNE token-identity forensics — 19/08/2026

**Án:** ĐỌC-ONLY. Không sửa/xóa/revert/patch file nào kể cả thấy sai rành. Sửa = Path A/B, chỉ SAU contract operator niêm + operator chọn path.

**Chờ:** contract GUA canonical operator niêm phong (chưa có tại thời điểm probe).

**Data provenance (L-48):**
- data-source: `data/config/alpha_id_map.json` · `D:\Check onchain fresh wallets\u50_universe.csv` · bapi `https://www.binance.com/bapi/defi/v1/public/{alpha-trade/klines,wallet-direct/buw/wallet/cex/alpha/all/token/list}` · gateio `api/v4/spot/candlesticks` · fapi `fapi.binance.com/fapi/v1/klines`
- machine: local Windows probe (READ-ONLY, VPS không đụng)
- date-range: probe run 2026-08-19; F2 dates 2026-08-15..17; F4 date 2026-08-17
- code-commit: pending (probe `_probe_gua_identity_forensics_20260819.py` chưa commit)

---

## [F0] KHÓA read-only + backup

**5 file backup vào `/tmp/gua_forensics_20260819/` (KHÔNG repo):**

| File | md5 (bản gốc) | md5 (backup) | match |
|---|---|---|:-:|
| `docs/case_files/CASE_GUA.xlsx` | `9c984a52cd6e6e71730bf724b3a70932` | `9c984a52cd6e6e71730bf724b3a70932` | ✓ |
| `docs/reports/_gua_refresh_20260818.md` | `dedfff525db3bbc40208961bb099f1ce` | `dedfff525db3bbc40208961bb099f1ce` | ✓ |
| `docs/reports/_gua_gate_backfill_20260819.md` | `9b9e0e25b354aefbae37ee5f09b8fe3e` | `9b9e0e25b354aefbae37ee5f09b8fe3e` | ✓ |
| `data/config/alpha_id_map.json` | `57d385638c17ab1597a56928a2c3c663` | `57d385638c17ab1597a56928a2c3c663` | ✓ |
| `scripts/collect_alpha_daily.py` | `b24440cfe068dd2162598daf8e839906` | `b24440cfe068dd2162598daf8e839906` | ✓ |

Ghi thêm probe vào /tmp: `probe_output.txt` (F1-F4 raw output). KHÔNG ghi repo (per F0 rule).

---

## [F1] TRACE LOOKUP CHAIN — GUA → ALPHA_483

### F1.a — `alpha_id_map.json` (nghi phạm)

```json
"GUA": "ALPHA_483"
```

Total 137 entries. Key = **symbol string** (`futures_base`). **KHÔNG unique semantic** — hai token khác chain có thể trùng symbol.

### F1.b — LOOKUP CODE (`scripts/collect_alpha_daily.py:176-207`)

```python
def _load_alpha_map(path: Path) -> dict[str, str]:
    # Just reads JSON — no contract verify
    mapping = json.loads(path.read_text(encoding="utf-8"))
    return mapping

alpha_map = _load_alpha_map(ALPHA_MAP_PATH)      # line 176
work = alpha_map                                  # line 184
...
for sym, alpha_id in work.items():                # line 206
    ticker = f"{alpha_id}USDT"                    # line 207 ← build ALPHA_483USDT
    arr, status = _bapi_get(BAPI_KLINES_PATH, {"symbol": ticker, ...})
```

**Match bằng trường gì:** KEY của dict = symbol (`GUA`). **UNIQUE?** NO — không có contract-check tại lookup time.

### F1.c — MAP CREATION (`scripts/archive/_task_write_alpha_config_20260804.py:47-57`)

```python
rows = list(csv.DictReader(open(U50, encoding="utf-8-sig")))  # u50_universe.csv
for r in rows:
    sym = r["futures_base"]                          # "GUA"
    bsc = (r.get("bsc_address") or "").lower().strip()  # "0xa5c8e15..."
    t   = alpha_by_addr.get(bsc)                     # LOOKUP by CONTRACT ✓
    if t:
        alpha_id = t.get("alphaId") or ""
        if alpha_id:
            mapping[sym] = alpha_id                  # WRITE by symbol key
```

**Map creation match bằng CONTRACT (canonical)**. Sau đó ghi vào dict key = symbol string → **thông tin contract mất tại lookup runtime**.

### F1.d — 3-way contract check (probe result)

`bapi/wallet-direct/alpha/all/token/list` returned 663 tokens. Search 3 cách:

```
matches alphaId == "ALPHA_483"                          : 1 hit
  {alphaId:"ALPHA_483", symbol:"GUA", name:"SUPERFORTUNE",
   chainId:"56", contractAddress:"0xa5c8e1513b6a08334b479fe4d71f1253259469be"}

matches contract == "0xa5c8e1513b6a08334b479fe4d71f1253259469be" : 1 hit (SAME record)
matches symbol   == "GUA"                                        : 1 hit (SAME record)
```

**Không collision trên bapi alpha token list:** chỉ có 1 GUA, 1 contract, 1 alphaId. Bit-equal.

**u50 canonical bsc_address cho GUA (row 138):**
```csv
GUA,GUA,superfortune,0xa5c8e1513b6a08334b479fe4d71f1253259469be,1878437,cg
```
→ **KHỚP contract Alpha ALPHA_483 bit-equal.**

### F1 kết luận

- Map CHAIN OF TRUST: u50.bsc_address == Alpha.contractAddress → **contract-verified TẠI MAP CREATION**.
- Nhưng runtime lookup CHỈ dùng symbol string (mất contract info). Nếu ai đó edit `alpha_id_map.json` tay hoặc rebuild với `u50_universe.csv` có bsc_address sai, lookup vẫn chạy êm — **KHÔNG có guard runtime**.
- Hiện tại (data ngày 19/08): 3-nơi contract khớp bit-equal — u50 = Alpha = (Gate metadata — xem F2).

---

## [F2] TAM GIÁC GIÁ 15-17/08

⚠ Cạnh ① (Alpha) đến từ CÙNG lookup [F1] đang nghi. Đọc kết quả với cảnh báo: **không tự nói cái nào GUA-thật**, contract operator niêm mới quyết.

```
─── 2026-08-15 ───────────────────────────────────────────────────
  ① Alpha ALPHA_483USDT   close=$0.041424  avg_px=$0.040945  qv=$134,566
  ② Gate  GUA_USDT        close=$0.173890                    qv=$10,245
  ③ Perp  GUAUSDT (fapi)  close=$0.041540                    qv=$2,139,961

─── 2026-08-16 ───────────────────────────────────────────────────
  ① Alpha ALPHA_483USDT   close=$0.042158  avg_px=$0.042850  qv=$234,378
  ② Gate  GUA_USDT        close=$0.192410                    qv=$22,136
  ③ Perp  GUAUSDT (fapi)  close=$0.042400                    qv=$3,185,451

─── 2026-08-17 ───────────────────────────────────────────────────
  ① Alpha ALPHA_483USDT   close=$0.042731  avg_px=$0.041536  qv=$107,060
  ② Gate  GUA_USDT        close=$0.190260                    qv=$14,349
  ③ Perp  GUAUSDT (fapi)  close=$0.042810                    qv=$1,750,576
```

### Cấu hình giá

- ①③ KHỚP: Alpha ≈ Perp ≈ **$0.042** cả 3 ngày (≤ 3% diff)
- ② TÁCH: Gate ≈ **$0.19** cả 3 ngày (**4.4-4.6× cao hơn** ①③)
- Contract cả 3 nơi bit-equal `0xa5c8e15...469be` (per F1.d + prev turn Gate `chains[0].addr`)

### Đọc kết quả (cấm over-claim)

**KHÔNG kết luận venue nào là GUA-thật.** THU HẸP:

- Có token giá **~$0.042** tại Alpha bapi + Binance perp (cùng contract khai) — ①③
- Có "token/pair" giá **~$0.19** tại Gate GUA_USDT (cùng contract khai) — ②
- **Contract khai giống nhau BIT-EQUAL cả 3 nơi**, nhưng giá tách 4.5× → 3 khả năng cho operator quyết:
  - (H1) Gate liệt kê nhầm contract nhưng trade token khác (Gate metadata sai)
  - (H2) Gate pair implicit multiplier / wrapped variant với contract SUPERFORTUNE tổ (kiểu 1 pair = N base tokens, nhưng Gate không khai)
  - (H3) Segmentation cực đoan (không có arb bridge Gate ↔ Alpha/Perp) — nhưng 4.5× hai đầu 3 ngày liên tiếp = khó tin

**Cạnh nào là GUA-thật:** operator NIÊM CONTRACT làm trọng tài. Nếu contract operator = `0xa5c8e15...469be` → ①②③ đều khai đúng contract, thì giá-tách Gate = anomaly nội tại pair Gate (Path A). Nếu contract operator KHÁC → ta có collision-3-cách kỳ lạ (Path B).

---

## [F3] KIỂM VÒNG LẶP "khớp sổ" — $234K (15/08 refresh sanity)

### Đường đọc trong report `_gua_refresh_20260818.md`

- line 85: "Sổ có vol Aug16 = $234,378 (khớp handover 17/08). Alpha alive → nguồn số vẫn tin cậy được cho vol_alpha"
- line 98: `vol_alpha = "alpha_klines_bapi:107060"` (07-17 giá trị)

### Đường sinh $234K

- `collect_alpha_daily.py` line 207: `ticker = f"{alpha_id}USDT"` với alpha_id = ALPHA_483 (từ alpha_id_map.json)
- bapi klines fetch `ALPHA_483USDT` 08-16 → `k[7]` (quote_vol) = $234,378

### Đường "khớp handover 17/08"

- Handover 17/08 (chưa trace source đến root) trả về $234K
- Nếu handover BÊN NGOÀI (ví dụ operator paste từ Bloomberg / third-party) → độc lập, sanity valid
- Nếu handover TỰ SINH cùng lookup ALPHA_483 → **vòng tròn A khớp A**

### Probe re-fetch (verify chính handover)

```
[refetch Alpha ALPHA_483USDT 2026-08-16] quote_vol=$234,378 base_vol=5,469,671
  → KHỚP $234K report (diff < 0.01%)
```

**Verdict F3:** con số $234K TÁI TẠO CHÍNH XÁC từ bapi ALPHA_483USDT.

- Nếu handover 17/08 lấy từ chính bapi ALPHA_483USDT → sanity "$234K khớp sổ ✓" trong án Alpha là **VÒNG TRÒN (A khớp A)**, **KHÔNG phải 2 nguồn độc lập**.
- Kết luận "vol_alpha GUA tin cậy" ở `_gua_refresh_20260818.md` line 85 **phải rút xuống ABSTAIN** cho đến khi có nguồn độc lập (ngoài bapi ALPHA_483) confirm giá + volume.
- **Nhãn evidence cho ANALYSIS gỡ:** "khớp sổ 18/08" tự-confirm, không đáng làm bằng chứng identity.

---

## [F4] SWEEP UNIVERSE fw-137 — ratio px_alpha / px_perp

**Date probe:** 2026-08-17. **Trọng tài:** ratio px_alpha / px_perp, độc lập với lookup broken. Flag ngoài [0.8, 1.25] = nghi collision.

### Tổng kết

| Bucket | Count | Ghi chú |
|---|---:|---|
| Total tokens (alpha_map) | 137 | |
| **OK** (ratio ∈ [0.8, 1.25]) | **81** | Alpha ≈ Perp — coi như same-token |
| **OUT of band** | **2** | Nghi collision (chi tiết dưới) |
| no-alpha (empty klines) | 52 | Alpha bapi empty — nhiều là delisted alpha |
| no-perp | 2 | Chinese-name tokens 我踏马来了, 龙虾 (no futures) |

### GUA trong sweep

`GUA` → `ALPHA_483` → Alpha $0.042731 / Perp $0.042810 = **ratio 0.998** → **OK band** (KHÔNG bị flag ở F4 vì ①③ khớp nhau; ② Gate ngoài F4).

### OUT-of-band (2 hit)

| symbol | alphaId | px_alpha | px_perp | ratio | ghi chú |
|---|---|---:|---:|---:|---|
| `1000000BOB` | ALPHA_473 | $0.00382 | $0.01783 | **0.214** | Symbol prefix "1000000" → likely SCALING multiplier bất đồng (perp = 1M-BOB unit vs alpha = plain BOB) — NOT collision |
| `VELVET` | ALPHA_267 | $0.72786 | $0.57760 | **1.260** | Chỉ 26% cao — biên spread rộng, có thể segmentation. Cần nhìn thêm ngày để phân biệt collision vs segment |

### no-alpha 52 (khó gọi collision, chỉ là data gap)

Bao gồm: 0G, 1000CHEEMS, ALLO, AT, BANANAS31, BANK, BARD, BMT, BREV, C, CGPT, COOKIE, EDEN, ENSO, ERA, F, FF, GENIUS, GIGGLE, HAEDAL, HEI, ... — nhiều là alpha token đã delist hoặc bapi endpoint đơn giản không trả kline cho lookup này.

### Verdict F4

- **Ratio-check độc lập cho GUA = OK** (không phát hiện collision Alpha ↔ Perp trên bapi + fapi).
- GUA-Gate anomaly chỉ lộ khi tam giác 3-vế (F2), không lộ trong sweep 2-vế F4.
- **2 nghi khác (BOB scaling, VELVET spread)** = separate follow-up, không blocking GUA.
- **N con nhiễm:** không phát hiện thêm bằng ratio-check trên tập fw-137 ngày 08-17. GUA là **ca đặc biệt** vì bằng chứng bất đồng nằm ở vế thứ ba (Gate), không phải ratio Alpha/Perp.

---

## [F5] SOẠN 2 PATH — CHƯA CHẠY (chờ contract + operator chọn)

### Path A — TRÙNG contract (kỳ vọng theo bằng chứng F1-F4 hiện tại)

**Điều kiện kích:** operator niêm contract GUA canonical = `0xa5c8e1513b6a08334b479fe4d71f1253259469be` (trùng u50 + Alpha + Gate metadata).

**Hành động:**
1. **GIỮ DATA vol_alpha** trong CASE_GUA.xlsx (không quarantine chuỗi Alpha) — Alpha bapi ALPHA_483 = contract-verified SUPERFORTUNE, khớp perp.
2. **MỞ ÁN "giá-tách Gate"** — điều tra 3 giả thuyết H1/H2/H3 (metadata sai / wrapped multiplier / segmentation cực đoan) qua:
   - Check deposit/withdraw GUA 2 venue: onchain trace nạp/rút GUA từ Alpha wallet (Binance BSC) vs Gate wallet — cùng contract có chuyển được?
   - Fetch orderbook Gate GUA_USDT + Alpha ALPHA_483 cùng snapshot: bid/ask depth, size step → có thể lộ multiplier ẩn
   - Kiểm chain khác: Gate `wallet/currency_chains?currency=GUA` chỉ trả BSC (đã có), Alpha token list chainId=56 → xác nhận không tồn tại "GUA phiên bản khác chain"
3. **RÚT nhãn "khớp sổ ✓" trong án Alpha** (F3 vòng tròn) — thay bằng "chưa có nguồn độc lập verify vol_alpha".
4. **KHÔNG revert cột 51-52 CASE_GUA.xlsx** — Gate quote_vol vẫn ghi lại (dữ liệu Gate đo thật, kể cả có tách giá) nhưng đánh dấu **"[SPOT-EXT-GATE-PRICE-ANOMALY]"** trong EVENTS row phù hợp để nhắc downstream không tự tin.
5. **GIỮ TRIA-Bybit** trong evidence L-52-draft (identity khớp, không đụng).

**File sẽ đụng (chỉ khi operator chốt Path A):**
- `docs/reports/_gua_gate_backfill_20260819.md` — thêm section "GIÁ-TÁCH GATE anomaly", tuyến kết luận "Gate = van xả" phải viết lại (Gate ước theo px_Gate ≠ px_ta thấy trên Alpha/Perp — số USD tính có thể sai 4.5×)
- `docs/reports/_gua_refresh_20260818.md` — line 85 rút "vol_alpha tin cậy", ghi "khớp sổ = vòng tròn, chưa có nguồn độc lập"
- `docs/case_files/CASE_GUA.xlsx` — thêm EVENTS row `2026-08-19 · GATE_PRICE_ANOMALY_4.5x`
- md5 backup ĐÃ có tại `/tmp/gua_forensics_20260819/`

### Path B — KHÁC contract (không kỳ vọng — nhưng vẫn soạn)

**Điều kiện kích:** operator niêm contract GUA canonical ≠ `0xa5c8e15...469be` (ví dụ contract khác trên BSC hay chain khác).

**Hành động (quarantine mở rộng 4 bước cũ + 2 tầng thêm):**
1. **Restore cols 51-52 CASE_GUA.xlsx** từ backup `scratch/CASE_GUA_bak_pre_gate_20260819.xlsx` (md5 `08a1b86208ee4424094d99812f39425a`) — xóa Gate quote_vol + xóa EVENTS rows 46-47 (GATE_SPIKE_5X + GATE_BASELINE).
2. **Gỡ / đánh dấu FALSE-VENUE chuỗi vol_alpha GUA** — vì Alpha ALPHA_483 khớp contract "0xa5c8e15..." = SUPERFORTUNE (nếu operator contract KHÁC → Alpha cũng không phải GUA-thật) → tất cả rows vol_alpha trong DAILY (col ~35) đánh dấu FALSE-VENUE.
3. **Revert Alpha status → `fullyDelisted-ABSTAIN`** (vì lookup broken, Alpha nguồn tin cậy sụp).
4. **Patch reports viện dẫn:**
   - `docs/reports/_gua_refresh_20260818.md` — line 83, 85, 98 (tất cả reference Alpha)
   - `docs/reports/_gua_gate_backfill_20260819.md` — toàn bộ Gate section
   - `proposals/lessons_pending_batch_20260818.md` §D.1 (nếu có Alpha-GUA ref) — bỏ dòng GUA, giữ TRIA-Bybit
5. **EVENTS trace 2 tầng vào CASE_GUA.xlsx:**
   - Tầng 1: `FALSE_VENUE_GATE` (Gate GUA_USDT = SUPERFORTUNE `0xa5c8e15...`, KHÁC contract canonical operator = `0x??`)
   - Tầng 2: `FALSE_VENUE_ALPHA` (Alpha ALPHA_483 = SUPERFORTUNE `0xa5c8e15...`, cùng contract = also KHÁC canonical operator)
6. **Regen `alpha_id_map.json`** với contract canonical mới (task `_task_write_alpha_config_*.py` với u50_universe.csv sửa bsc_address GUA).

**File sẽ đụng (chỉ khi operator chốt Path B) + md5 backup TẤT CẢ ở /tmp:**
| File | md5 hiện tại |
|---|---|
| `docs/case_files/CASE_GUA.xlsx` | `9c984a52cd6e6e71730bf724b3a70932` |
| `docs/reports/_gua_refresh_20260818.md` | `dedfff525db3bbc40208961bb099f1ce` |
| `docs/reports/_gua_gate_backfill_20260819.md` | `9b9e0e25b354aefbae37ee5f09b8fe3e` |
| `data/config/alpha_id_map.json` | `57d385638c17ab1597a56928a2c3c663` |
| `D:\Check onchain fresh wallets\u50_universe.csv` | (chưa backup — sẽ add nếu B kích) |
| (VPS) `data/raw/spot_klines_1d/**` binance_alpha rows sym=GUA | (không backup local; VPS rollback riêng) |

### Bảng so sánh Path A vs Path B

|  | Path A (trùng contract) | Path B (khác contract) |
|---|---|---|
| Kỳ vọng theo bằng chứng F1-F4 | **CAO** (contract 3-nơi bit-equal) | Thấp |
| Data-loss | Không (chỉ đánh nhãn anomaly Gate) | Có (revert cols 51-52, quarantine vol_alpha, revert Alpha status) |
| Reports patch | 3 nơi (add anomaly section) | 3-4 nơi (rewrite toàn bộ luồng vol_alpha + Gate) |
| EVENTS append | 1 row (PRICE_ANOMALY) | 2 rows (FALSE_VENUE_GATE + FALSE_VENUE_ALPHA) |
| Regen alpha_id_map | KHÔNG | CÓ (u50 fix trước, sau đó rebuild) |

**KHÔNG chạy Path nào cho đến khi operator: (i) niêm contract, (ii) chọn path.**

---

## [F6] GUARD proposal — schema v2.1-ext (chờ ký cùng)

### Đề xuất bổ sung 2 trường vào `data/config/` universe

Universe file (nếu là `u50_universe.csv` hoặc file kế thừa) thêm cột:

| trường | ý nghĩa | cách điền | ai điền |
|---|---|---|---|
| `alpha_id` | alphaId canonical trên Binance Alpha (ví dụ `ALPHA_483`) | resolve từ contract 1 lần, operator NIÊM | operator |
| `contract_canonical` | contract address canonical trên chain gốc (đã chuẩn hóa lowercase, tokenized chain-suffix) | operator NIÊM 1 lần từ nguồn ngoài (dự án gốc / etherscan verified) | operator |

**Format ví dụ:**
```csv
symbol,futures_base,cg_id,bsc_address,alpha_id,contract_canonical,market_cap,cap_source
GUA,GUA,superfortune,0xa5c8e15...469be,ALPHA_483,bsc:0xa5c8e15...469be,1878437,cg
```

### Collector assert (chặn cứng TRƯỚC mọi collect)

`collect_alpha_daily.py` + `collect_gate_daily.py` (nếu build sau) THÊM Step-0 check:

```python
def _assert_contract(sym: str, universe_row: dict, api_metadata: dict) -> None:
    """Fail-loud nếu contract API khác canonical operator niêm."""
    canon = universe_row["contract_canonical"].split(":")[-1].lower()  # bsc:0x... → 0x...
    api_ct = (api_metadata.get("contractAddress") or "").lower()
    if canon != api_ct:
        raise SystemExit(
            f"CONTRACT_MISMATCH sym={sym} canonical={canon[:12]}... api={api_ct[:12]}... "
            f"— refuse to collect (schema v2.1-ext L-52 guard)"
        )
```

Cross-ref:
- `alpha_id` guard: assert `alpha_map[sym] == universe_row["alpha_id"]` trước _bapi_get
- Gate/Bybit metadata: fetch `chains[]` array, assert BSC entry contract == canonical
- Wallet chain != BSC: **refuse** (v2.1-ext scope BSC-only, cross-chain issue open)

### Nhật ký thiếu ngày này (chỉ vì án GUA lộ)

- Step-0 L-51-draft (identity check trước dùng data) **PHẢI code-hóa** — không thể chỉ probe adhoc mỗi lần nghi.
- Step-2 mirror test (đã ghi nợ) refactor để chạy **full-sample variance**, không chỉ 3 first ticks (probe cũ `_probe_taker_feasibility_20260819.py` chỉ sample 3).
- Hết match-bằng-symbol trong mọi collector — TẤT CẢ collector phải deref qua `contract_canonical` trước gọi API.

### Đề xuất "ai ký"

- Operator NIÊM `contract_canonical` cho **fw-137** current (one-off, ~1 giờ nếu có tool paste từ CoinGecko API bulk)
- Sau ký: `_task_write_alpha_config_20260819_v2.py` rebuild alpha_id_map với assert; commit atomic (cùng schema v2.1-ext).

---

## KẾT LUẬN (raw, không verdict)

1. **Lookup chain contract-verified TẠI MAP CREATION** (u50.bsc_address == Alpha.contractAddress bit-equal cả 3 nơi), nhưng runtime lookup key = symbol string → không có guard chống edit tay hay universe.csv sai contract.

2. **Contract bit-equal 3 nơi:** u50 `0xa5c8e15...469be` = Alpha ALPHA_483 contract = Gate GUA chains[0].addr. → Nếu operator niêm contract KHÁC, cả u50 + Alpha + Gate đều sai đồng bộ.

3. **Tam giác giá F2 (3 ngày 15-17/08):**
   - Alpha ≈ Perp ≈ **$0.042** ①③ khớp
   - Gate = **$0.19** ② tách 4.5×
   - Contract 3 nơi bit-equal → giá tách KHÔNG do collision contract, mà là **anomaly bên trong Gate pair GUA_USDT** (metadata/wrapping/segmentation).

4. **F3 vòng tròn:** $234K "khớp sổ" trong án Alpha 18/08 = **A khớp A** (bapi ALPHA_483 tự-confirm). Sanity đó **VÔ HIỆU**. Vol_alpha GUA cần nguồn độc lập mới verify được.

5. **F4 sweep fw-137:** 81/137 OK (ratio Alpha/Perp ∈ [0.8, 1.25]). GUA KHÔNG bị flag (ratio 1.00 vì Alpha khớp Perp). Chỉ 2 khác trong sweep: `1000000BOB` (scaling multiplier), `VELVET` (spread 26%). **Không phát hiện thêm collision.**

6. **Path A (trùng contract) là kịch bản kỳ vọng bằng chứng hiện tại** — Path B chỉ kích nếu operator niêm contract KHÁC bit-equal.

7. **F6 propose:** thêm `alpha_id` + `contract_canonical` vào universe schema v2.1-ext + collector assert Step-0. Cần operator ký cùng cấu trúc.

## CHỜ OPERATOR

- **① Niêm contract canonical GUA** (từ nguồn ngoài data pipeline mình: CoinGecko / dự án gốc / etherscan verified)
- **② Chọn Path A hoặc Path B** dựa contract niêm
- **③ Ký F6 schema v2.1-ext** proposal (hoặc yêu cầu điều chỉnh)

**DỪNG F1-F6.** KHÔNG restore/patch/sửa file nào tới khi ① + ② rõ ràng.

---

## [F7] Gate isolated-market confirmed — 19/08/2026

**Trigger:** sau A0 SEAL PASS 3/3 bit-equal (Path A cleared), operator yêu cầu xác nhận anomaly Gate ($0.19 vs Alpha/Perp $0.042). Probe read-only 3 endpoint.

### F7.1 — flags Gate `/api/v4/spot/currencies/GUA`

```
currency         : GUA
name             : SUPERFORTUNE
delisted         : False
trade_disabled   : False
withdraw_disabled: False       ← rút được
deposit_disabled : True        ← NẠP ĐÓNG ← smoking gun
chain            : BSC
chains[0]        : name=BSC, deposit_disabled=True, addr=0xa5c8e1513b...469be (khớp SEAL A0)

pair GUA_USDT   : trade_status=tradable, fee=0.2%, buy_start=2025-11-28
```

### F7.2 — orderbook depth ±2%

```
best_bid = 0.19781   best_ask = 0.20027   mid = 0.19904   spread = 1.236%

±2% window [0.195059, 0.203021]:
  bid side: 8 levels · $198.81
  ask side: 2 levels · $16.24        ← ask side gần cạn
  ─────────────────────────────
  TỔNG    : $215.05
```

Ai ném $300 market-buy đã chạy sạch ask side ±2%. Pool trapped $200 depth quanh $0.19.

### F7.3 — 20 trades gần nhất

```
time span : 13.6 phút (2026-08-19 07:23:31 → 07:37:04 UTC)
n_trades  : 20 · Σ notional = $468.89
size range: $1.21 → $99.95 (median ~$14)
side mix  : 11 sell / 9 buy (balanced micro-flow)
price band: $0.19953 → $0.20426 (range 2.4%)
```

Micro-flow trên pool cô lập. Extrapolate ~$2K/hour = ~$50K/day worst case, khớp candlestick daily $10-22K.

### F7 verdict

- **`gate[ISOLATED-DEPOSIT-DISABLED]`** — nhãn vĩnh viễn cho GUA_USDT trên Gate
- Giá tách 4.5× vs Alpha/Perp **giải thích được**: `deposit_disabled=TRUE` → pool GUA trên Gate KHÔNG refill được → cắt arb-bridge → premium cấu trúc, không phải data lỗi, không phải wrong-token
- Vol Gate $10-22K/day = **internal churn pool trapped**, KHÔNG là băng-thông xả kho
- **Luật L-52 vế đường-hàng-thông:** pair tồn tại ∧ deposit đóng = van vẽ trên giấy → EXCLUDE khỏi bandwidth vĩnh viễn
- 3 nguồn giá canonical còn lại (Alpha + Perp khớp bit-equal contract, cùng $0.042) — số truthful

### F7 actions

- CASE_GUA EVENTS row 49: `GATE_ISOLATED_DEPOSIT_DISABLED` (closed)
- CASE_GUA DAILY col52 rename 48 rows: `gate` → `gate[ISOLATED-DEPOSIT-DISABLED]` (provenance giữ số, đổi nhãn)
- CASE_GUA CASE r22-23: note "Bandwidth EXCLUDE flag" + luật L-52
- `_gua_gate_backfill_20260819.md` §E.4 Doctrine #10 revert: **Alpha-only 7.8 tháng canonical**, kịch bản 5-7 tháng (đã gồm Gate) WITHDRAWN.
