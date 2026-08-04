# PROBE: Alpha Dead Code Investigation — 2026-08-03
Run at: 2026-08-04 01:03 UTC

## PHẦN 2: u50_universe BSC-only — spot listing scan

u50_universe.csv: 137 rows
Cols: ['symbol', 'futures_base', 'cg_id', 'bsc_address', 'market_cap', 'cap_source']
Has bsc_address column: YES (all 137 rows have it)

### 2.4 Spot listing scan — toàn bộ 137 u50 symbols
API: GET api.binance.com/api/v3/klines (cùng URL mà _probe_alpha_taker.py dùng)

| symbol       | status          |
|--------------|-----------------|
| FFUSDT       | OK(0.5420)      |
| BTWUSDT      | NO_SPOT         |
| VELVETUSDT   | NO_SPOT         |
| BUSDT        | NO_SPOT         |
| TAGUSDT      | NO_SPOT         |
| XPINUSDT     | NO_SPOT         |
| HOLOUSDT     | OK(0.4897)      |
| UAIUSDT      | NO_SPOT         |
| ZBTUSDT      | OK(0.4825)      |
| ZAMAUSDT     | OK(0.4658)      |
| GENIUSUSDT   | OK(0.5204)      |
| 1000CHEEMSUSDT | OK(0.4948)      |
| AKEUSDT      | NO_SPOT         |
| OUSDT        | NO_SPOT         |
| DATAIPUSDT   | NO_SPOT         |
| SOONUSDT     | NO_SPOT         |
| MYXUSDT      | NO_SPOT         |
| RAVEUSDT     | NO_SPOT         |
| BANANAS31USDT | OK(0.3901)      |
| BASUSDT      | NO_SPOT         |
| ALLOUSDT     | OK(0.4983)      |
| BILLUSDT     | NO_SPOT         |
| COAIUSDT     | NO_SPOT         |
| CAPUSDT      | NO_SPOT         |
| USELESSUSDT  | NO_SPOT         |
| RIVERUSDT    | NO_SPOT         |
| AIOTUSDT     | NO_SPOT         |
| CYSUSDT      | NO_SPOT         |
| CROSSUSDT    | NO_SPOT         |
| BRUSDT       | NO_SPOT         |
| LABUSDT      | NO_SPOT         |
| AGTUSDT      | NO_SPOT         |
| TOSHIUSDT    | NO_SPOT         |
| IDOLUSDT     | NO_SPOT         |
| GIGGLEUSDT   | OK(0.4934)      |
| JCTUSDT      | NO_SPOT         |
| ONUSDT       | NO_SPOT         |
| OPENUSDT     | OK(0.4939)      |
| EDENUSDT     | OK(0.4242)      |
| BARDUSDT     | OK(0.5827)      |
| ZESTUSDT     | NO_SPOT         |
| KGENUSDT     | NO_SPOT         |
| FOLKSUSDT    | NO_SPOT         |
| SQDUSDT      | NO_SPOT         |
| HOMEUSDT     | OK(0.4810)      |
| SPACEUSDT    | NO_SPOT         |
| HUMAUSDT     | OK(0.5019)      |
| PROVEUSDT    | OK(0.4670)      |
| IRYSUSDT     | NO_SPOT         |
| ATUSDT       | OK(0.3989)      |
| GWEIUSDT     | NO_SPOT         |
| XANUSDT      | NO_SPOT         |
| 0GUSDT       | OK(0.4499)      |
| COLLECTUSDT  | NO_SPOT         |
| GRVTUSDT     | NO_SPOT         |
| SKYAIUSDT    | NO_SPOT         |
| SAHARAUSDT   | OK(0.4846)      |
| BSBUSDT      | NO_SPOT         |
| BLESSUSDT    | NO_SPOT         |
| ROBOUSDT     | OK(0.5041)      |
| ACUUSDT      | NO_SPOT         |
| MERLUSDT     | NO_SPOT         |
| HYPERUSDT    | OK(0.5466)      |
| SIRENUSDT    | NO_SPOT         |
| SLXUSDT      | NO_SPOT         |
| BANKUSDT     | OK(0.4805)      |
| B2USDT       | NO_SPOT         |
| NAORISUSDT   | NO_SPOT         |
| 龙虾USDT       | EMPTY           |
| ENSOUSDT     | OK(0.5493)      |
| POWERUSDT    | NO_SPOT         |
| TRIAUSDT     | NO_SPOT         |
| CARVUSDT     | NO_SPOT         |
| OPGUSDT      | OK(0.4178)      |
| BASEDUSDT    | NO_SPOT         |
| SIGNUSDT     | OK(0.4953)      |
| BREVUSDT     | OK(0.4475)      |
| CGPTUSDT     | OK(0.4993)      |
| XNYUSDT      | NO_SPOT         |
| INXUSDT      | NO_SPOT         |
| YBUSDT       | OK(0.4710)      |
| CLOUSDT      | NO_SPOT         |
| TACUSDT      | NO_SPOT         |
| SOPHUSDT     | OK(0.3856)      |
| TUTUSDT      | OK(0.5676)      |
| TAIKOUSDT    | NO_SPOT         |
| BLUAIUSDT    | NO_SPOT         |
| BULLAUSDT    | NO_SPOT         |
| AINUSDT      | NO_SPOT         |
| MIRAUSDT     | OK(0.3731)      |
| PLAYUSDT     | NO_SPOT         |
| FUSDT        | OK(0.5257)      |
| MUBARAKUSDT  | OK(0.4980)      |
| 1000000BOBUSDT | NO_SPOT         |
| AIOUSDT      | NO_SPOT         |
| STBLUSDT     | NO_SPOT         |
| ERAUSDT      | OK(0.5635)      |
| TAUSDT       | NO_SPOT         |
| INUSDT       | NO_SPOT         |
| ORDERUSDT    | NO_SPOT         |
| ZKCUSDT      | OK(0.4823)      |
| TSTUSDT      | OK(0.5375)      |
| DOODUSDT     | NO_SPOT         |
| TAKEUSDT     | NO_SPOT         |
| LAUSDT       | OK(0.4614)      |
| 4USDT        | NO_SPOT         |
| ZKPUSDT      | OK(0.4371)      |
| KOMAUSDT     | NO_SPOT         |
| OPNUSDT      | OK(0.4531)      |
| NEWTUSDT     | OK(0.5022)      |
| CUSDT        | OK(0.5550)      |
| 我踏马来了USDT    | EMPTY           |
| STOUSDT      | OK(0.4728)      |
| MITOUSDT     | OK(0.4762)      |
| TRADOORUSDT  | NO_SPOT         |
| LYNUSDT      | NO_SPOT         |
| RESOLVUSDT   | OK(0.4777)      |
| HANAUSDT     | NO_SPOT         |
| FIGHTUSDT    | NO_SPOT         |
| TURTLEUSDT   | OK(0.4237)      |
| AIAUSDT      | NO_SPOT         |
| LIGHTUSDT    | NO_SPOT         |
| COOKIEUSDT   | OK(0.4745)      |
| EVAAUSDT     | NO_SPOT         |
| PARTIUSDT    | OK(0.4600)      |
| PUMPBTCUSDT  | NO_SPOT         |
| BTRUSDT      | NO_SPOT         |
| ARIAUSDT     | NO_SPOT         |
| FHEUSDT      | NO_SPOT         |
| SHELLUSDT    | OK(0.4575)      |
| HEMIUSDT     | OK(0.4539)      |
| TOWNSUSDT    | OK(0.5021)      |
| BMTUSDT      | OK(0.4971)      |
| HAEDALUSDT   | OK(0.5155)      |
| ESPORTSUSDT  | NO_SPOT         |
| GUAUSDT      | NO_SPOT         |
| PTBUSDT      | NO_SPOT         |

### 2.4 Summary
- OK (spot có taker hợp lệ): 51
- NO_SPOT (400 — không có Binance spot): 84
- BSC_BROKEN (taker ratio >0.9985): 0
- EMPTY/ZERO_VOL: 2

**Nhóm CẦN alpha endpoint phủ (no_spot):** 84 tokens
Danh sách no_spot: ['BTW', 'VELVET', 'B', 'TAG', 'XPIN', 'UAI', 'AKE', 'O', 'DATAIP', 'SOON', 'MYX', 'RAVE', 'BAS', 'BILL', 'COAI', 'CAP', 'USELESS', 'RIVER', 'AIOT', 'CYS', 'CROSS', 'BR', 'LAB', 'AGT', 'TOSHI', 'IDOL', 'JCT', 'ON', 'ZEST', 'KGEN']...
**BSC_BROKEN = 0** → alpha_bsc_symbols.txt sẽ RỖNG nếu generate từ u50

## PHẦN 3: bapi/defi endpoint discovery

### 3.1: IDOL one-off endpoint confirm
URL: https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_223USDT&interval=1d&limit=2
Status: 200
Response shape: dict with keys=['code', 'message', 'messageDetail', 'data', 'success']
data[] count: 2
Sample entry[0]: ["1785715200000", "0.02314917", "0.02466018", "0.01550000", "0.01762105", "294021864.90000000", "1785801599999", "5297410.45724258", "31824", "294021864.90000000", "5297410.45724258", "0"]

### 3.3: Path discovery — cùng prefix alpha-trade/

| path                                               | status | response_shape |
|----------------------------------------------------|--------|--------------------|
| /bapi/defi/v1/public/alpha-trade/token-list        | 404 | {"message":"No message available","timestamp":1785805463313, |
| /bapi/defi/v1/public/alpha-trade/tokens            | 404 | {"path":"/v1/public/alpha-trade/tokens","status":404,"messag |
| /bapi/defi/v1/public/alpha-trade/symbol-list       | 404 | {"message":"No message available","timestamp":1785805464281, |
| /bapi/defi/v1/public/alpha-trade/symbols           | 404 | {"path":"/v1/public/alpha-trade/symbols","status":404,"messa |
| /bapi/defi/v1/public/alpha-trade/config            | 404 | {"error":"Not Found","timestamp":1785805465267,"message":"No |
| /bapi/defi/v1/public/alpha-trade/info              | 404 | {"message":"No message available","timestamp":1785805465741, |
| /bapi/defi/v1/public/alpha-trade/tickers           | 404 | {"path":"/v1/public/alpha-trade/tickers","status":404,"messa |
| /bapi/defi/v1/public/alpha-trade/list              | 404 | {"status":404,"path":"/v1/public/alpha-trade/list","error":" |
| /bapi/defi/v1/public/alpha-trade/allTokens         | 404 | {"status":404,"path":"/v1/public/alpha-trade/allTokens","err |
| /bapi/defi/v1/public/alpha-trade/market            | 404 | {"error":"Not Found","timestamp":1785805467669,"message":"No |

**Không tìm thấy token-list endpoint** → ghi CẦN OPERATOR (DevTools Binance Alpha)

### 3.3b: Confirm WAF block — bapi/alpha/v1
URL: https://www.binance.com/bapi/alpha/v1/public/alpha-trade/token-list
Status: 403 — WAF blocked (expected)
Body: <html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
</body>
</html>


### 3.2: CALIB_ALPHA 12 entries (from _calib_alpha_daily.py)

| symbol | alpha_id | cách sinh |
|--------|----------|-----------|
| AKE | ALPHA_331 | tay (12 calib case — user-provided) |
| CLO | ALPHA_429 | tay (12 calib case — user-provided) |
| ESPORTS | ALPHA_283 | tay (12 calib case — user-provided) |
| BTW | ALPHA_778 | tay (12 calib case — user-provided) |
| POWER | ALPHA_487 | tay (12 calib case — user-provided) |
| BASED | ALPHA_837 | tay (12 calib case — user-provided) |
| BAS | ALPHA_328 | tay (12 calib case — user-provided) |
| TAG | ALPHA_233 | tay (12 calib case — user-provided) |
| IDOL | ALPHA_223 | tay (12 calib case — user-provided) |
| TUT | ALPHA_117 | tay (12 calib case — user-provided) |
| BULLA | ALPHA_240 | tay (12 calib case — user-provided) |
| BANK | ALPHA_146 | tay (12 calib case — user-provided) |

File: `D:\Check onchain fresh wallets\_calib_alpha_daily.py` (tồn tại)
Ngày sinh: không có timestamp trong file, infer từ 12 calib case set (≈07/2026)

## SUMMARY ĐỂ OPERATOR PHÂN NHÁNH

### PHẦN 1 — Fetch path thật
- `collect_alpha_spot.py` gọi: `api.binance.com/api/v3/klines` (standard Binance spot)
- **KHÔNG** gọi `bapi/defi/v1/public/alpha-trade/klines`
- Venue tag = `binance_spot_bsc` (label trong parquet)
- → **NHÁNH B** (gọi spot thường, không phải alpha thật)

### PHẦN 2 — Universe 118 (u50_universe.csv = 137 rows)
- Tổng: 137 BSC symbols có bsc_address
- NO_SPOT (cần alpha endpoint phủ): 84
- OK spot (đã có collect_spot_daily phủ): 51
- BSC_BROKEN: 0 (alpha_bsc_symbols.txt = RỖNG)

### PHẦN 3 — Resolver
- CALIB_ALPHA: 12 entries tay, file `_calib_alpha_daily.py`
- klines endpoint: `/bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_NNN USDT`
- token-list endpoint: → xem kết quả path discovery ở trên
