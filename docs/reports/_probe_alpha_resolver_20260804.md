# PROBE: Alpha Resolver — token-list + u50 full coverage
Run: 2026-08-04 01:21 UTC

## Bước 1: Token-list endpoint

URL: `https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list`
Status: 200
Total Alpha tokens returned: 659
Sample keys: ['tokenId', 'chainId', 'chainIconUrl', 'chainName', 'contractAddress', 'name', 'symbol', 'iconUrl', 'price', 'percentChange24h']
Sample entry: {"tokenId": "589101E2C2545522E6D174AFFBB544AE", "chainId": "56", "chainIconUrl": "https://bin.bnbstatic.com/image/admin_mgs_image_upload/20250228/d0216ce4-a3e9-4bda-8937-4a6aa943ccf2.png", "chainName": "BSC", "contractAddress": "0x46f2564e0fa8248d15125e7e54173cfbdef91be7", "name": "GRVT", "symbol": 

BSC tokens (chainId=56) with contractAddress: 485

## Bước 2: u50_universe join → alpha_id resolver

u50_universe: 137 symbols

| symbol     | bsc_address                                   | alpha_id      | status |
|------------|-----------------------------------------------|---------------|----------|
| FF         | 0xac23b90a79504865d52b49b327328411a23d4db2    | ALPHA_398     | OK |
| BTW        | 0x444045b0ee1ee319a660a5e3d604ca0ffa35acaa    | ALPHA_778     | OK |
| VELVET     | 0x8b194370825e37b33373e74a41009161808c1488    | ALPHA_267     | OK |
| B          | 0x6bdcce4a559076e37755a78ce0c06214e59e4444    | ALPHA_197     | OK |
| TAG        | 0x208bf3e7da9639f1eaefa2de78c23396b0682025    | ALPHA_233     | OK |
| XPIN       | 0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6    | ALPHA_334     | OK |
| HOLO       | 0x1a5d7e4c3a7f940b240b7357a4bfed30d17f9497    | ALPHA_369     | OK |
| UAI        | 0x3e5d4f8aee0d9b3082d5f6da5d6e225d17ba9ea0    | ALPHA_461     | OK |
| ZBT        | 0xfab99fcf605fd8f4593edb70a43ba56542777777    | ALPHA_435     | OK |
| ZAMA       | 0x6907a5986c4950bdaf2f81828ec0737ce787519f    | ALPHA_658     | OK |
| GENIUS     | 0x1f12b85aac097e43aa1555b2881e98a51090e9a6    | ALPHA_887     | OK |
| 1000CHEEMS | 0x0df0587216a4a1bb7d5082fdc491d93d2dd4b413    | ALPHA_2       | OK |
| AKE        | 0x2c3a8ee94ddd97244a93bc48298f97d2c412f7db    | ALPHA_331     | OK |
| O          | 0x500a02a20b0b0a3f3efccfc0559543f5743bd1c4    | ALPHA_991     | OK |
| DATAIP     | 0xa37eded373c5cdf88644db7c6b89f222e756afb2    | ALPHA_1011    | OK |
| SOON       | 0xb9e1fd5a02d3a33b25a14d661414e6ed6954a721    | ALPHA_199     | OK |
| MYX        | 0xd82544bf0dfe8385ef8fa34d67e6e4940cc63e16    | ALPHA_171     | OK |
| RAVE       | 0x97693439ea2f0ecdeb9135881e49f354656a911c    | ALPHA_497     | OK |
| BANANAS31  | 0x3d4f0513e8a29669b960f9dbca61861548a9a760    | ALPHA_21      | OK |
| BAS        | 0x0f0df6cb17ee5e883eddfef9153fc6036bdb4e37    | ALPHA_328     | OK |
| ALLO       | 0xcce5f304fd043d6a4e8ccb5376a4a4fb583b98d5    | ALPHA_467     | OK |
| BILL       | 0xdf24f8c21cb404b3031a450d8e049d6e39fc1fa5    | ALPHA_953     | OK |
| COAI       | 0x0a8d6c86e1bce73fe4d0bd531e1a567306836ea5    | ALPHA_391     | OK |
| CAP        | 0x99991c6aabba5a096f24f250b73580f5179b9999    | ALPHA_1005    | OK |
| USELESS    | 0xba38b3c706f7a515ff7c8db04daa0a134ec46d2b    | ALPHA_295     | OK |
| RIVER      | 0xda7ad9dea9397cffddae2f8a052b82f1484252b3    | ALPHA_381     | OK |
| AIOT       | 0x55ad16bd573b3365f43a9daeb0cc66a73821b4a5    | ALPHA_158     | OK |
| CYS        | 0x0c69199c1562233640e0db5ce2c399a88eb507c7    | ALPHA_495     | OK |
| CROSS      | 0x6bf62ca91e397b5a7d1d6bce97d9092065d7a510    | ALPHA_259     | OK |
| BR         | 0xff7d6a96ae471bbcd7713af9cb1feeb16cf56b41    | ALPHA_118     | OK |
| LAB        | 0x7ec43cf65f1663f820427c62a5780b8f2e25593a    | ALPHA_428     | OK |
| AGT        | 0x5dbde81fce337ff4bcaaee4ca3466c00aecae274    | ALPHA_191     | OK |
| TOSHI      | 0x6a2608dabe09bc1128eec7275b92dfb939d5db3f    | ALPHA_303     | OK |
| IDOL       | 0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07    | ALPHA_223     | OK |
| GIGGLE     | 0x20d6015660b3fe52e6690a889b5c51f69902ce0e    | ALPHA_410     | OK |
| JCT        | 0xea37a8de1de2d9d10772eeb569e28bfa5cb17707    | ALPHA_466     | OK |
| ON         | 0x0e4f6209ed984b21edea43ace6e09559ed051d48    | ALPHA_444     | OK |
| OPEN       | 0xa227cc36938f0c9e09ce0e64dfab226cad739447    | ALPHA_362     | OK |
| EDEN       | 0x235b6fe22b4642ada16d311855c49ce7de260841    | ALPHA_400     | OK |
| BARD       | 0xd23a186a78c0b3b805505e5f8ea4083295ef9f3a    | ALPHA_379     | OK |
| ZEST       | 0x5506599c722389a60580b5213ea1da60d64754a1    | ALPHA_970     | OK |
| KGEN       | 0xf3d5b4c34ed623478cc5141861776e6cf7ae3a1e    | ALPHA_414     | OK |
| FOLKS      | 0xff7f8f301f7a706e3cfd3d2275f5dc0b9ee8009b    | ALPHA_462     | OK |
| SQD        | 0xe50e3d1a46070444f44df911359033f2937fcc13    | ALPHA_209     | OK |
| HOME       | 0x4bfaa776991e85e5f8b1255461cbbd216cfc714f    | ALPHA_221     | OK |
| SPACE      | 0x87acfa3fd7a6e0d48677d070644d76905c2bdc00    | ALPHA_606     | OK |
| HUMA       | 0x92516e0ddf1ddbf7fab1b79cac26689fdc5ba8e6    | ALPHA_201     | OK |
| PROVE      | 0x7ddf164cecfddd0f992299d033b5a11279a15929    | ALPHA_310     | OK |
| IRYS       | 0x91152b4ef635403efbae860edd0f8c321d7c035d    | ALPHA_479     | OK |
| AT         | 0x9be61a38725b265bc3eb7bfdf17afdfc9d26c130    | ALPHA_443     | OK |
| GWEI       | 0x30117e4bc17d7b044194b76a38365c53b72f7d49    | ALPHA_588     | OK |
| XAN        | 0x7427bd9542e64d1ac207a540cfce194b7390a07f    | ALPHA_399     | OK |
| 0G         | 0x4b948d64de1f71fcd12fb586f4c776421a35b3ee    | ALPHA_388     | OK |
| COLLECT    | 0x4b3d30992f003c8167699735f5ab2831b2a087d3    | ALPHA_506     | OK |
| GRVT       | 0x46f2564e0fa8248d15125e7e54173cfbdef91be7    | ALPHA_1067    | OK |
| SKYAI      | 0x92aa03137385f18539301349dcfc9ebc923ffb10    | ALPHA_154     | OK |
| SAHARA     | 0xfdffb411c4a70aa7c95d5c981a6fb4da867e1111    | ALPHA_247     | OK |
| BSB        | 0x595deaad1eb5476ff1e649fdb7efc36f1e4679cc    | ALPHA_790     | OK |
| BLESS      | 0x7c8217517ed4711fe2deccdfeffe8d906b9ae11f    | ALPHA_389     | OK |
| ROBO       | 0x475cbf5919608e0c6af00e7bf87fab83bf3ef6e2    | ALPHA_769     | OK |
| ACU        | 0x6ef2ffb38d64afe18ce782da280b300e358cfeaf    | ALPHA_587     | OK |
| MERL       | 0xa0c56a8c0692bd10b3fa8f8ba79cf5332b7107f9    | ALPHA_195     | OK |
| HYPER      | 0xc9d23ed2adb0f551369946bd377f8644ce1ca5c4    | ALPHA_152     | OK |
| SIREN      | 0x997a58129890bbda032231a52ed1ddc845fc18e1    | ALPHA_102     | OK |
| SLX        | 0x02bcc4c181b83a8c0a342bc003389cbecb4bc54d    | ALPHA_978     | OK |
| BANK       | 0x3aee7602b612de36088f3ffed8c8f10e86ebf2bf    | ALPHA_146     | OK |
| B2         | 0x783c3f003f172c6ac5ac700218a357d2d66ee2a2    | ALPHA_162     | OK |
| NAORIS     | 0x1b379a79c91a540b2bcd612b4d713f31de1b80cc    | ALPHA_301     | OK |
| 龙虾         | 0xeccbb861c0dda7efd964010085488b69317e4444    | ALPHA_772     | OK |
| ENSO       | 0xfeb339236d25d3e415f280189bc7c2fbab6ae9ef    | ALPHA_427     | OK |
| POWER      | 0x9dc44ae5be187eca9e2a67e33f27a4c91cea1223    | ALPHA_487     | OK |
| TRIA       | 0xb0b92de23baa85fb06208277e925ced53edab482    | ALPHA_669     | OK |
| CARV       | 0xc08cd26474722ce93f4d0c34d16201461c10aa8c    | ALPHA_241     | OK |
| OPG        | 0x5feccd17c393caf1001d18164236a37e731fcb9d    | ALPHA_931     | OK |
| BASED      | 0x1d28d989f9e3ccb8b15d0cec601734514f958e4d    | ALPHA_837     | OK |
| SIGN       | 0x868fced65edbf0056c4163515dd840e9f287a4c3    | ALPHA_159     | OK |
| BREV       | 0x086f405146ce90135750bbec9a063a8b20a8bffb    | ALPHA_510     | OK |
| CGPT       | 0x9840652dc04fb9db2c43853633f0f62be6f00f98    | ALPHA_13      | OK |
| XNY        | 0xe3225e11cab122f1a126a28997788e5230838ab9    | ALPHA_289     | OK |
| INX        | 0x45f55b46689402583073ff227b6ac20520052a24    | ALPHA_638     | OK |
| YB         | 0xfb93ee8152dd0a0e6f4b49c66c06d800cf1db72d    | ALPHA_430     | OK |
| CLO        | 0x81d3a238b02827f62b9f390f947d36d4a5bf89d2    | ALPHA_429     | OK |
| TAC        | 0x1219c409fabe2c27bd0d1a565daeed9bd9f271de    | ALPHA_277     | OK |
| SOPH       | 0x31dba3c96481fde3cd81c2aaf51f2d8bf618c742    | ALPHA_204     | OK |
| TUT        | 0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3    | ALPHA_117     | OK |
| TAIKO      | 0x30c60b20c25b2810ca524810467a0c342294fc61    | ALPHA_207     | OK |
| BLUAI      | 0xed9ae3def8d6f052971bb8b6d1975ff267cf9aad    | ALPHA_438     | OK |
| BULLA      | 0x595e21b20e78674f8a64c1566a20b2b316bc3511    | ALPHA_240     | OK |
| AIN        | 0x9558a9254890b2a8b057a789f413631b9084f4a3    | ALPHA_260     | OK |
| MIRA       | 0x7839fbfd09dae4d0f15bfb36b8f16f7898fbe684    | ALPHA_393     | OK |
| PLAY       | 0xf86089b30f30285d492b0527c37b9c2225bfcf8c    | ALPHA_300     | OK |
| F          | 0xc9ccbd76c2353e593cc975f13295e8289d04d3bb    | ALPHA_228     | OK |
| MUBARAK    | 0x5c85d6c6825ab4032337f11ee92a72df936b46f6    | ALPHA_116     | OK |
| 1000000BOB | 0x52b5fb4b0f6572b8c44d0251cc224513ac5eb7e7    | ALPHA_473     | OK |
| AIO        | 0x81a7da4074b8e0ed51bea40f9dcbdf4d9d4832b4    | ALPHA_361     | OK |
| STBL       | 0x8dedf84656fa932157e27c060d8613824e7979e3    | ALPHA_376     | OK |
| ERA        | 0x00312400303d02c323295f6e8b7309bc30fb6bce    | ALPHA_280     | OK |
| TA         | 0x539ae81a166e5e80aed211731563e549c411b140    | ALPHA_285     | OK |
| IN         | 0x61fac5f038515572d6f42d4bcb6b581642753d50    | ALPHA_312     | OK |
| ORDER      | 0x4e200fe2f3efb977d5fd9c430a41531fb04d97b8    | ALPHA_279     | OK |
| ZKC        | 0x15247e6e23d3923a853ccf15940a20ccdf16e94a    | ALPHA_374     | OK |
| TST        | 0x86bb94ddd16efc8bc58e6b056e8df71d9e666429    | ALPHA_87      | OK |
| DOOD       | 0x722294f6c97102fb0ddb5b907c8d16bdeab3f6d9    | ALPHA_177     | OK |
| TAKE       | 0xe747e54783ba3f77a8e5251a3cba19ebe9c0e197    | ALPHA_337     | OK |
| LA         | 0x389ad4bb96d0d6ee5b6ef0efaf4b7db0ba2e02a0    | ALPHA_212     | OK |
| 4          | 0x0a43fc31a73013089df59194872ecae4cae14444    | ALPHA_407     | OK |
| ZKP        | 0xd89b7dd376e671c124352267516bef1c2cc231a3    | ALPHA_504     | OK |
| KOMA       | 0xd5eaaac47bd1993d661bc087e15dfb079a7f3c19    | ALPHA_1       | OK |
| OPN        | 0x7977bf3e7e0c954d12cdca3e013adaf57e0b06e0    | ALPHA_797     | OK |
| NEWT       | 0xb8a677e6d805c8d743e6f14c8bc9c19305b5defc    | ALPHA_244     | OK |
| C          | 0xc32cc70741c3a8433dcbcb5ade071c299b55ffc8    | ALPHA_275     | OK |
| 我踏马来了      | 0xc51a9250795c0186a6fb4a7d20a90330651e4444    | ALPHA_521     | OK |
| STO        | 0xdaf1695c41327b61b9b9965ac6a5843a3198cf07    | ALPHA_138     | OK |
| MITO       | 0x8e1e6bf7e13c400269987b65ab2b5724b016caef    | ALPHA_342     | OK |
| TRADOOR    | 0x9123400446a56176eb1b6be9ee5cf703e409f492    | ALPHA_356     | OK |
| LYN        | 0x302dfaf2cdbe51a18d97186a7384e87cf599877d    | ALPHA_412     | OK |
| RESOLV     | 0xda6cef7f667d992a60eb823ab215493aa0c6b360    | ALPHA_222     | OK |
| HANA       | 0x6261963ebe9ff014aad10ecc3b0238d4d04e8353    | ALPHA_394     | OK |
| FIGHT      | 0xb2d97c4ed2d0ef452654f5cab3da3735b5e6f3ab    | ALPHA_604     | OK |
| TURTLE     | 0x66fd8de541c0594b4dccdfc13bf3a390e50d3afd    | ALPHA_440     | OK |
| AIA        | 0x53ec33cd4fa46b9eced9ca3f6db626c5ffcd55cc    | ALPHA_496     | OK |
| LIGHT      | 0x477c2c0459004e3354ba427fa285d7c053203c0e    | ALPHA_396     | OK |
| COOKIE     | 0xc0041ef357b183448b235a8ea73ce4e4ec8c265f    | ALPHA_33      | OK |
| EVAA       | 0xaa036928c9c0df07d525b55ea8ee690bb5a628c1    | ALPHA_409     | OK |
| PARTI      | 0x59264f02d301281f3393e1385c0aefd446eb0f00    | ALPHA_127     | OK |
| PUMPBTC    | 0xb7c0007ab75350c582d5eab1862b872b5cf53f0c    | ALPHA_131     | OK |
| BTR        | 0xfed13d0c40790220fbde712987079eda1ed75c51    | ALPHA_340     | OK |
| ARIA       | 0x5d3a12c42e5372b2cc3264ab3cdcf660a1555238    | ALPHA_332     | OK |
| FHE        | 0xd55c9fb62e176a8eb6968f32958fefdd0962727e    | ALPHA_140     | OK |
| SHELL      | 0xf2c88757f8d03634671208935974b60a2a28bdb3    | ALPHA_97      | OK |
| HEMI       | 0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b    | ALPHA_343     | OK |
| TOWNS      | 0x00000000bca93b25a6694ca3d2109d545988b13b    | ALPHA_308     | OK |
| BMT        | 0x7d814b9ed370ec0a502edc3267393bf62d891b62    | ALPHA_115     | OK |
| HAEDAL     | 0x3d9be0ac1001cd81c32464276d863d2ffdca4967    | ALPHA_161     | OK |
| ESPORTS    | 0xf39e4b21c84e737df08e2c3b32541d856f508e48    | ALPHA_283     | OK |
| GUA        | 0xa5c8e1513b6a08334b479fe4d71f1253259469be    | ALPHA_483     | OK |
| PTB        | 0x95c9b514566fbd224dc2037f5914eb8ab91c9201    | ALPHA_352     | OK |

**OK (alpha_id found): 137**
**FAIL (no match): 0**


## Bước 3: CALIB_ALPHA 12/12 verification

| symbol | CALIB_expected | resolver_got | match |
|--------|----------------|--------------|-------|
| AKE    | ALPHA_331      | ALPHA_331    | ✓ |
| BANK   | ALPHA_146      | ALPHA_146    | ✓ |
| BAS    | ALPHA_328      | ALPHA_328    | ✓ |
| BASED  | ALPHA_837      | ALPHA_837    | ✓ |
| BTW    | ALPHA_778      | ALPHA_778    | ✓ |
| BULLA  | ALPHA_240      | ALPHA_240    | ✓ |
| CLO    | ALPHA_429      | ALPHA_429    | ✓ |
| ESPORTS | ALPHA_283      | ALPHA_283    | ✓ |
| IDOL   | ALPHA_223      | ALPHA_223    | ✓ |
| POWER  | ALPHA_487      | ALPHA_487    | ✓ |
| TAG    | ALPHA_233      | ALPHA_233    | ✓ |
| TUT    | ALPHA_117      | ALPHA_117    | ✓ |

Match: 12/12 — PASS ✓
→ CALIB_ALPHA dict có thể retire (resolver tự động thay thế)

## Bước 4: Klines depth check (earliest date)

| symbol | alpha_id | earliest_date | n_candles | latest_date |
|--------|----------|---------------|-----------|-------------|
| BLUAI | ALPHA_438 | 2025-10-21 | 288 | 2026-08-04 |
| IDOL | ALPHA_223 | 2025-06-11 | 420 | 2026-08-04 |
| TAG | ALPHA_233 | 2025-06-18 | 413 | 2026-08-04 |

## Summary

- Token-list endpoint: **OK**
- BSC tokens indexed: 485
- u50_universe coverage: 137/137 resolved
- CALIB_ALPHA verify: 12/12
- FAIL (no alpha listing): 0 — []

### Resolver dict (toàn bộ)

```python
ALPHA_ID_MAP = {
    "0G": "ALPHA_388",
    "1000000BOB": "ALPHA_473",
    "1000CHEEMS": "ALPHA_2",
    "4": "ALPHA_407",
    "ACU": "ALPHA_587",
    "AGT": "ALPHA_191",
    "AIA": "ALPHA_496",
    "AIN": "ALPHA_260",
    "AIO": "ALPHA_361",
    "AIOT": "ALPHA_158",
    "AKE": "ALPHA_331",
    "ALLO": "ALPHA_467",
    "ARIA": "ALPHA_332",
    "AT": "ALPHA_443",
    "B": "ALPHA_197",
    "B2": "ALPHA_162",
    "BANANAS31": "ALPHA_21",
    "BANK": "ALPHA_146",
    "BARD": "ALPHA_379",
    "BAS": "ALPHA_328",
    "BASED": "ALPHA_837",
    "BILL": "ALPHA_953",
    "BLESS": "ALPHA_389",
    "BLUAI": "ALPHA_438",
    "BMT": "ALPHA_115",
    "BR": "ALPHA_118",
    "BREV": "ALPHA_510",
    "BSB": "ALPHA_790",
    "BTR": "ALPHA_340",
    "BTW": "ALPHA_778",
    "BULLA": "ALPHA_240",
    "C": "ALPHA_275",
    "CAP": "ALPHA_1005",
    "CARV": "ALPHA_241",
    "CGPT": "ALPHA_13",
    "CLO": "ALPHA_429",
    "COAI": "ALPHA_391",
    "COLLECT": "ALPHA_506",
    "COOKIE": "ALPHA_33",
    "CROSS": "ALPHA_259",
    "CYS": "ALPHA_495",
    "DATAIP": "ALPHA_1011",
    "DOOD": "ALPHA_177",
    "EDEN": "ALPHA_400",
    "ENSO": "ALPHA_427",
    "ERA": "ALPHA_280",
    "ESPORTS": "ALPHA_283",
    "EVAA": "ALPHA_409",
    "F": "ALPHA_228",
    "FF": "ALPHA_398",
    "FHE": "ALPHA_140",
    "FIGHT": "ALPHA_604",
    "FOLKS": "ALPHA_462",
    "GENIUS": "ALPHA_887",
    "GIGGLE": "ALPHA_410",
    "GRVT": "ALPHA_1067",
    "GUA": "ALPHA_483",
    "GWEI": "ALPHA_588",
    "HAEDAL": "ALPHA_161",
    "HANA": "ALPHA_394",
    "HEMI": "ALPHA_343",
    "HOLO": "ALPHA_369",
    "HOME": "ALPHA_221",
    "HUMA": "ALPHA_201",
    "HYPER": "ALPHA_152",
    "IDOL": "ALPHA_223",
    "IN": "ALPHA_312",
    "INX": "ALPHA_638",
    "IRYS": "ALPHA_479",
    "JCT": "ALPHA_466",
    "KGEN": "ALPHA_414",
    "KOMA": "ALPHA_1",
    "LA": "ALPHA_212",
    "LAB": "ALPHA_428",
    "LIGHT": "ALPHA_396",
    "LYN": "ALPHA_412",
    "MERL": "ALPHA_195",
    "MIRA": "ALPHA_393",
    "MITO": "ALPHA_342",
    "MUBARAK": "ALPHA_116",
    "MYX": "ALPHA_171",
    "NAORIS": "ALPHA_301",
    "NEWT": "ALPHA_244",
    "O": "ALPHA_991",
    "ON": "ALPHA_444",
    "OPEN": "ALPHA_362",
    "OPG": "ALPHA_931",
    "OPN": "ALPHA_797",
    "ORDER": "ALPHA_279",
    "PARTI": "ALPHA_127",
    "PLAY": "ALPHA_300",
    "POWER": "ALPHA_487",
    "PROVE": "ALPHA_310",
    "PTB": "ALPHA_352",
    "PUMPBTC": "ALPHA_131",
    "RAVE": "ALPHA_497",
    "RESOLV": "ALPHA_222",
    "RIVER": "ALPHA_381",
    "ROBO": "ALPHA_769",
    "SAHARA": "ALPHA_247",
    "SHELL": "ALPHA_97",
    "SIGN": "ALPHA_159",
    "SIREN": "ALPHA_102",
    "SKYAI": "ALPHA_154",
    "SLX": "ALPHA_978",
    "SOON": "ALPHA_199",
    "SOPH": "ALPHA_204",
    "SPACE": "ALPHA_606",
    "SQD": "ALPHA_209",
    "STBL": "ALPHA_376",
    "STO": "ALPHA_138",
    "TA": "ALPHA_285",
    "TAC": "ALPHA_277",
    "TAG": "ALPHA_233",
    "TAIKO": "ALPHA_207",
    "TAKE": "ALPHA_337",
    "TOSHI": "ALPHA_303",
    "TOWNS": "ALPHA_308",
    "TRADOOR": "ALPHA_356",
    "TRIA": "ALPHA_669",
    "TST": "ALPHA_87",
    "TURTLE": "ALPHA_440",
    "TUT": "ALPHA_117",
    "UAI": "ALPHA_461",
    "USELESS": "ALPHA_295",
    "VELVET": "ALPHA_267",
    "XAN": "ALPHA_399",
    "XNY": "ALPHA_289",
    "XPIN": "ALPHA_334",
    "YB": "ALPHA_430",
    "ZAMA": "ALPHA_658",
    "ZBT": "ALPHA_435",
    "ZEST": "ALPHA_970",
    "ZKC": "ALPHA_374",
    "ZKP": "ALPHA_504",
    "我踏马来了": "ALPHA_521",
    "龙虾": "ALPHA_772",
}
```