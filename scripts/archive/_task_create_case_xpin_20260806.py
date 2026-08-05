# _task_create_case_xpin_20260806.py
# Tao CASE_XPIN.xlsx day du: CASE, DAILY (328 rows), EVENTS, TRIGGERS, OUTCOME, MM_PROFILE, UNLOCK
# Data: fapi API + XPIN_result.txt hardcoded + freshwatch hardcoded
# Schema DAILY = CASE_BANK (40 cols, 2-row header)

import urllib.request, json, time, os
from datetime import datetime, timezone, timedelta
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = r"D:\Data back test\whale_data\docs\case_files\CASE_XPIN.xlsx"

def p(s): print(str(s).encode('ascii','replace').decode('ascii'))

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if i<retries-1: time.sleep(2)
            else: return {"_error": str(e)}

# ─── Hardcoded: XPIN_result.txt funding daily agg (2026, May-Jul) ───
FUND_HIST = {
    "2026-05-03": (0.000171,0.000085,0.000234),
    "2026-05-04": (0.000322,0.000125,0.000457),
    "2026-05-05": (0.000073,0.000050,0.000167),
    "2026-05-06": (0.000138,0.000050,0.000312),
    "2026-05-07": (0.000179,0.000050,0.000472),
    "2026-05-08": (0.000260,0.000050,0.000634),
    "2026-05-09": (0.000262,0.000050,0.000712),
    "2026-05-10": (0.000144,0.000050,0.000426),
    "2026-05-11": (0.000050,0.000050,0.000050),
    "2026-05-12": (0.000237,0.000050,0.000499),
    "2026-05-13": (0.000226,0.000050,0.000394),
    "2026-05-14": (0.000050,0.000050,0.000050),
    "2026-05-15": (0.000065,0.000050,0.000097),
    "2026-05-16": (0.000050,0.000050,0.000050),
    "2026-05-17": (0.000050,0.000050,0.000050),
    "2026-05-18": (0.000050,0.000050,0.000050),
    "2026-05-19": (0.000050,0.000050,0.000050),
    "2026-05-20": (0.000050,0.000050,0.000050),
    "2026-05-21": (0.000050,0.000050,0.000050),
    "2026-05-22": (0.000050,0.000050,0.000050),
    "2026-05-23": (0.000050,0.000050,0.000050),
    "2026-05-24": (0.000050,0.000050,0.000050),
    "2026-05-25": (0.000050,0.000050,0.000050),
    "2026-05-26": (0.000050,0.000050,0.000050),
    "2026-05-27": (0.000050,0.000050,0.000050),
    "2026-05-28": (0.000050,0.000050,0.000050),
    "2026-05-29": (0.000050,0.000050,0.000050),
    "2026-05-30": (0.000050,0.000050,0.000050),
    "2026-05-31": (0.000050,0.000050,0.000050),
    "2026-06-01": (0.000050,0.000050,0.000050),
    "2026-06-02": (0.000157,0.000050,0.000467),
    "2026-06-03": (0.000050,0.000050,0.000050),
    "2026-06-04": (0.000050,0.000050,0.000050),
    "2026-06-05": (0.000050,0.000050,0.000052),
    "2026-06-06": (0.000050,0.000050,0.000050),
    "2026-06-07": (0.000050,0.000050,0.000050),
    "2026-06-08": (0.000050,0.000050,0.000050),
    "2026-06-09": (0.000096,0.000050,0.000329),
    "2026-06-10": (0.000050,0.000050,0.000050),
    "2026-06-11": (0.000059,0.000050,0.000091),
    "2026-06-12": (0.000055,0.000050,0.000082),
    "2026-06-13": (0.000081,0.000050,0.000237),
    "2026-06-14": (0.000050,0.000050,0.000050),
    "2026-06-15": (0.000050,0.000050,0.000050),
    "2026-06-16": (0.000050,0.000050,0.000050),
    "2026-06-17": (0.000104,0.000050,0.000293),
    "2026-06-18": (0.000068,0.000050,0.000089),
    "2026-06-19": (0.000283,0.000143,0.000451),
    "2026-06-20": (0.000167,0.000050,0.000424),
    "2026-06-21": (0.000065,0.000050,0.000099),
    "2026-06-22": (0.000090,0.000050,0.000177),
    "2026-06-23": (0.000066,0.000050,0.000147),
    "2026-06-24": (0.000148,0.000050,0.000298),
    "2026-06-25": (0.000099,0.000050,0.000212),
    "2026-06-26": (0.000177,0.000050,0.000395),
    "2026-06-27": (0.000298,0.000050,0.000673),
    "2026-06-28": (0.000121,0.000050,0.000325),
    "2026-06-29": (0.000169,0.000050,0.000338),
    "2026-06-30": (0.000154,0.000050,0.000272),
    "2026-07-01": (0.000160,0.000050,0.000242),
    "2026-07-02": (0.000051,0.000050,0.000055),
    "2026-07-03": (0.000192,0.000050,0.000439),
    "2026-07-04": (0.000226,0.000050,0.000445),
    "2026-07-05": (0.000118,0.000050,0.000452),
    "2026-07-06": (0.000055,0.000050,0.000080),
    "2026-07-07": (0.000099,0.000050,0.000344),
    "2026-07-08": (0.000142,0.000050,0.000361),
    "2026-07-09": (0.000057,0.000050,0.000093),
    "2026-07-10": (0.000364,0.000086,0.000938),
    "2026-07-11": (0.000484,0.000281,0.000654),
    "2026-07-12": (0.000094,0.000050,0.000312),
    "2026-07-13": (0.000050,0.000050,0.000050),
    "2026-07-14": (0.000050,0.000050,0.000050),
    "2026-07-15": (0.000050,0.000050,0.000050),
    "2026-07-16": (0.000050,0.000050,0.000050),
    "2026-07-17": (0.000052,0.000050,0.000061),
    "2026-07-18": (0.000067,0.000050,0.000141),
    "2026-07-19": (0.000050,0.000050,0.000050),
    "2026-07-20": (0.000050,0.000050,0.000050),
    "2026-07-21": (0.000050,0.000050,0.000050),
    "2026-07-22": (0.000060,0.000050,0.000110),
    "2026-07-23": (0.000078,0.000050,0.000120),
    "2026-07-24": (0.000054,0.000050,0.000073),
    "2026-07-25": (0.000071,0.000050,0.000112),
}

# ─── Hardcoded: OI daily from XPIN_result.txt (Jun 26 - Jul 25, 2026) ───
OI_HIST = {
    "2026-06-26":8277058,"2026-06-27":8439152,"2026-06-28":8533654,
    "2026-06-29":8302159,"2026-06-30":7853960,"2026-07-01":8896763,
    "2026-07-02":9107413,"2026-07-03":8892560,"2026-07-04":9154375,
    "2026-07-05":9231099,"2026-07-06":8855875,"2026-07-07":8562424,
    "2026-07-08":9465050,"2026-07-09":9628268,"2026-07-10":10006503,
    "2026-07-11":14879303,"2026-07-12":15646180,"2026-07-13":14101974,
    "2026-07-14":11937391,"2026-07-15":10953097,"2026-07-16":11638578,
    "2026-07-17":10945325,"2026-07-18":11099168,"2026-07-19":12176390,
    "2026-07-20":12396717,"2026-07-21":12377489,"2026-07-22":12639691,
    "2026-07-23":12311744,"2026-07-24":12045717,"2026-07-25":12119802,
}

# ─── Hardcoded: LSR from XPIN_result.txt (Jun 25 - Jul 25, 2026) ───
# (pos_r, acc_r, global_r, taker_ratio)
LSR_HIST = {
    "2026-06-25":(None,None,None,0.8823),
    "2026-06-26":(1.7501,1.4679,1.6076,0.9312),
    "2026-06-27":(1.7705,1.5113,1.6247,0.9969),
    "2026-06-28":(1.6908,1.6652,1.7322,0.8099),
    "2026-06-29":(1.7120,1.5913,1.6624,0.7792),
    "2026-06-30":(1.7122,1.5700,1.6838,0.9731),
    "2026-07-01":(1.6907,1.5387,1.6518,0.9222),
    "2026-07-02":(1.8547,1.7405,1.8474,0.8774),
    "2026-07-03":(1.9213,1.7678,1.9087,0.8725),
    "2026-07-04":(1.9348,1.8281,1.9718,0.9516),
    "2026-07-05":(1.9393,1.8019,1.9317,0.7564),
    "2026-07-06":(1.9520,1.8011,1.9189,0.7878),
    "2026-07-07":(1.9415,1.7624,1.8313,0.9381),
    "2026-07-08":(1.9285,1.6788,1.7832,0.8887),
    "2026-07-09":(1.9451,1.4925,1.6448,0.8660),
    "2026-07-10":(1.9658,1.5381,1.7064,1.0088),
    "2026-07-11":(1.7994,0.8947,0.9516,1.0224),
    "2026-07-12":(1.9527,1.1057,1.1772,0.9877),
    "2026-07-13":(1.9579,1.1427,1.2060,0.9253),
    "2026-07-14":(2.0424,1.3148,1.3084,0.9264),
    "2026-07-15":(2.0647,1.1473,1.1427,0.9863),
    "2026-07-16":(2.0757,1.1124,1.0292,0.9662),
    "2026-07-17":(2.3590,1.1290,1.0272,1.0257),
    "2026-07-18":(2.3656,1.2237,1.2432,0.8143),
    "2026-07-19":(2.2368,1.1482,1.0816,1.0660),
    "2026-07-20":(1.9870,1.1386,1.1119,0.9639),
    "2026-07-21":(1.9501,1.2041,1.2134,1.0456),
    "2026-07-22":(1.9472,1.0280,1.0020,1.0911),
    "2026-07-23":(1.9509,1.1151,1.1209,0.9356),
    "2026-07-24":(1.9791,1.1039,1.0982,0.9903),
    "2026-07-25":(2.0002,1.1240,1.1678,None),
}

# ─── Hardcoded: VPS freshwatch Aug 01-04 ───
# schema: px_avg, vol_perp, taker, f_avg, f_min, f_max, f_n, oi, pos_r, acc_r, glsr, taker_ratio, data_bad
FW = {
    "2026-08-01":(0.0015395,1335386,0.5038,0.0002521,5e-5,0.00049419,6,11951087,2.0046,2.0193,2.1939,1.0153,0),
    "2026-08-02":(0.0015261,1669407,0.4428,0.0003055,5e-5,0.00058334,6,12162495,1.8030,1.9394,2.2165,0.7947,0),
    "2026-08-03":(0.0015482,3294343,0.5012,0.0001882,5.536e-5,0.00043335,6,11920802,1.7966,1.9603,2.2031,1.0049,0),
    "2026-08-04":(0.0015325,1435218,0.5095,9.423e-5,5e-5,0.00031539,6,12069070,1.8217,1.8902,2.1348,1.0389,0),
}

# ─── Fetch klines ───
p("Fetching fapi klines...")
url = "https://fapi.binance.com/fapi/v1/klines?symbol=XPINUSDT&interval=1d&limit=1000"
raw = fetch(url)
bars = []
if isinstance(raw, list):
    for b in raw:
        ts_ms = b[0]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        o,h,l,c = float(b[1]),float(b[2]),float(b[3]),float(b[4])
        vol = float(b[7])
        tk = float(b[10])/float(b[7]) if float(b[7])>0 else None  # taker buy vol / total vol
        bars.append({"date":d,"o":o,"h":h,"l":l,"c":c,"vol":vol,"taker":tk})
    p(f"  klines: {len(bars)} bars ({bars[0]['date']} -> {bars[-1]['date']})")
else:
    p(f"  ERROR: {raw}")

# ─── Fetch funding intervals → daily agg ───
p("Fetching funding intervals...")
url_f = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=XPINUSDT&limit=1000"
raw_f = fetch(url_f)
fund_api = {}  # date → list of rates
if isinstance(raw_f, list):
    for r in raw_f:
        ts_ms = r["fundingTime"]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        rate = float(r["fundingRate"])
        if d not in fund_api: fund_api[d] = []
        fund_api[d].append(rate)
    # aggregate
    fund_api_agg = {}
    for d, rates in fund_api.items():
        fund_api_agg[d] = (sum(rates)/len(rates), min(rates), max(rates), len(rates))
    p(f"  funding: {len(fund_api_agg)} days ({min(fund_api_agg)} -> {max(fund_api_agg)})")
else:
    fund_api_agg = {}
    p("  ERROR funding")

# merge fund: API takes priority for dates it covers, else FUND_HIST
FUND_ALL = {}
FUND_ALL.update(FUND_HIST)  # historical first
for d, v in fund_api_agg.items():
    FUND_ALL[d] = v  # API overrides (more recent/accurate)

# ─── Fetch OI history (30d) ───
p("Fetching OI history...")
url_oi = "https://fapi.binance.com/futures/data/openInterestHist?symbol=XPINUSDT&period=1d&limit=90"
raw_oi = fetch(url_oi)
oi_api = {}
if isinstance(raw_oi, list):
    for r in raw_oi:
        ts_ms = r["timestamp"]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        oi_api[d] = float(r["sumOpenInterestValue"])
    p(f"  OI: {len(oi_api)} bars ({min(oi_api)} -> {max(oi_api)})")
else:
    p(f"  ERROR OI")

OI_ALL = {}
OI_ALL.update(OI_HIST)
OI_ALL.update(oi_api)

# ─── Fetch gLSR+pos_r (30d) ───
p("Fetching LSR...")
LSR_API = {}
for endpoint, key in [
    ("https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=XPINUSDT&period=1d&limit=90", "pos"),
    ("https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=XPINUSDT&period=1d&limit=90", "acc"),
    ("https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=XPINUSDT&period=1d&limit=90", "glsr"),
]:
    raw_l = fetch(endpoint)
    if isinstance(raw_l, list):
        for r in raw_l:
            ts_ms = r["timestamp"]
            dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
            d = dt.strftime("%Y-%m-%d")
            if d not in LSR_API: LSR_API[d] = {}
            LSR_API[d][key] = float(r["longShortRatio"])
        p(f"  {key}: {len(raw_l)} bars")
    else:
        p(f"  {key} ERROR")

# taker ratio (takerBuySellVolumeRatio)
raw_tr = fetch("https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=XPINUSDT&period=1d&limit=90")
if isinstance(raw_tr, list):
    for r in raw_tr:
        ts_ms = r["timestamp"]
        dt = datetime.fromtimestamp(ts_ms/1000, tz=timezone.utc)
        d = dt.strftime("%Y-%m-%d")
        if d not in LSR_API: LSR_API[d] = {}
        LSR_API[d]["tr"] = float(r["buySellRatio"])

# merge LSR: HIST first, API overrides
LSR_ALL = {}
for d, (pr, ar, gr, tr) in LSR_HIST.items():
    LSR_ALL[d] = {"pos":pr, "acc":ar, "glsr":gr, "tr":tr}
for d, v in LSR_API.items():
    if d not in LSR_ALL: LSR_ALL[d] = {}
    LSR_ALL[d].update(v)

# ─── Build DAILY rows ───
p("Building DAILY rows...")
rows = []
prev_px = None
for b in bars:
    d = b["date"]
    px = b["c"]
    ret = (px/prev_px - 1) if (prev_px and prev_px>0) else None
    prev_px = px

    # funding
    if d in FW:
        fw = FW[d]
        f_avg,f_min,f_max,f_n = fw[3],fw[4],fw[5],fw[6]
        oi = fw[7]
        pos_r,acc_r,glsr = fw[8],fw[9],fw[10]
        taker_r = fw[11]
        data_bad = fw[12]
        px_use = fw[0]
        vol_use = fw[1]
        taker_use = fw[2]
    else:
        px_use = px
        vol_use = b["vol"]
        taker_use = b["taker"]
        fd = FUND_ALL.get(d)
        if fd:
            f_avg,f_min,f_max = fd[0],fd[1],fd[2]
            f_n = fd[3] if len(fd)>3 else 6
        else:
            f_avg=f_min=f_max=None; f_n=None
        oi = OI_ALL.get(d)
        lsr_d = LSR_ALL.get(d,{})
        pos_r = lsr_d.get("pos")
        acc_r = lsr_d.get("acc")
        glsr = lsr_d.get("glsr")
        taker_r = lsr_d.get("tr")
        data_bad = 0

    # Aug 05 partial
    if d == "2026-08-05":
        data_bad = 1
        if not f_n: f_n = None

    # derived
    div_raw = round(pos_r/acc_r,4) if (pos_r and acc_r and acc_r>0) else None

    # funding regime
    def fund_regime(avg, mn):
        if avg is None: return None
        if avg <= 5.5e-5 and mn <= 5.1e-5: return "pin"
        if avg <= 1.5e-4: return "low"
        if avg >= 4e-4: return "spike"
        return "volatile"
    regime = fund_regime(f_avg, f_min)

    rows.append({
        "date": d,
        "px_avg": round(px_use,8),
        "ret_1d": round(ret,5) if ret else None,
        "vol_perp_usd": round(vol_use,0) if vol_use else None,
        "taker_buy_pct": round(taker_use,5) if taker_use else None,
        "f_avg": f_avg,
        "f_min": f_min,
        "f_max": f_max,
        "f_n": f_n,
        "funding_regime": regime,
        "pin_streak": None,  # compute after
        "oi_usd": round(oi,0) if oi else None,
        "oi_vs_med14": None,  # compute after
        "oi_cycle_pos": None,
        "lsr_pos_r": pos_r,
        "lsr_acc_r": acc_r,
        "lsr_global_r": glsr,
        "div_raw": div_raw,
        "div_avg3": None,
        "glsr_slope_5d": None,
        "d_pos_3d": None,
        "d_acc_3d": None,
        "signals_bullish": None,
        "signals_suppress": None,
        "screen_rank": None,
        "data_bad": data_bad,
    })

# compute pin_streak, oi_vs_med14, div_avg3
PIN = 5e-5; EPS = 5e-6
streak = 0
for r in rows:
    fa = r["f_avg"]; fmn = r["f_min"]
    if fa is not None and fa <= PIN+EPS and fmn is not None and fmn >= PIN-EPS:
        streak += 1
    else:
        streak = 0
    r["pin_streak"] = streak if fa is not None else None

# oi_vs_med14
pxs = [r["oi_usd"] for r in rows]
for i, r in enumerate(rows):
    if r["oi_usd"] is None: continue
    window = [pxs[j] for j in range(max(0,i-13),i+1) if pxs[j] is not None]
    if len(window) >= 7:
        sorted_w = sorted(window)
        med = sorted_w[len(sorted_w)//2]
        r["oi_vs_med14"] = round(r["oi_usd"]/med,3) if med>0 else None

# div_avg3
divs = [r["div_raw"] for r in rows]
for i, r in enumerate(rows):
    window = [divs[j] for j in range(max(0,i-2),i+1) if divs[j] is not None]
    if len(window)>=2: r["div_avg3"] = round(sum(window)/len(window),3)

# glsr_slope_5d
glsrs = [r["lsr_global_r"] for r in rows]
for i, r in enumerate(rows):
    if i<4: continue
    window = [(glsrs[j] if glsrs[j] else None) for j in range(i-4,i+1)]
    valid = [v for v in window if v is not None]
    if len(valid)>=3:
        slope = (valid[-1]-valid[0])/(len(valid)-1)
        r["glsr_slope_5d"] = round(slope,5)

# d_pos_3d, d_acc_3d
pos_rs = [r["lsr_pos_r"] for r in rows]
acc_rs = [r["lsr_acc_r"] for r in rows]
for i, r in enumerate(rows):
    if i<3: continue
    if pos_rs[i] and pos_rs[i-3]:
        r["d_pos_3d"] = round(pos_rs[i]-pos_rs[i-3],4)
    if acc_rs[i] and acc_rs[i-3]:
        r["d_acc_3d"] = round(acc_rs[i]-acc_rs[i-3],4)

p(f"DAILY: {len(rows)} rows ({rows[0]['date']} -> {rows[-1]['date']})")

# ─── Build workbook ───
wb = openpyxl.Workbook()

# ── Colors ──
GOLD = PatternFill("solid", fgColor="FFD700")
GREEN = PatternFill("solid", fgColor="C6EFCE")
RED = PatternFill("solid", fgColor="FFC7CE")
ORANGE = PatternFill("solid", fgColor="FFEB9C")
BLUE = PatternFill("solid", fgColor="DDEBF7")
GREY = PatternFill("solid", fgColor="D9D9D9")
THIN = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

def hdr_font(bold=True, sz=10): return Font(bold=bold, size=sz)
def centre(ws, row, col, val, fill=None, font=None):
    c = ws.cell(row=row, column=col, value=val)
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    if fill: c.fill = fill
    if font: c.font = font
    return c

# ════════════════════════════════════════════
# SHEET: DAILY
# ════════════════════════════════════════════
ws_d = wb.active; ws_d.title = "DAILY"

PERP_COLS = [
    "date","px_avg","ret_1d","vol_perp_usd","taker_buy_pct",
    "f_avg","f_min","f_max","f_n","funding_regime","pin_streak",
    "oi_usd","oi_vs_med14","oi_cycle_pos",
    "lsr_pos_r","lsr_acc_r","lsr_global_r","div_raw","div_avg3",
    "glsr_slope_5d","d_pos_3d","d_acc_3d",
    "signals_bullish","signals_suppress","screen_rank","data_bad"
]
SPOT_COLS = [
    "spot_venue","vol_spot_usd","taker_spot_pct",
    "depth_bid2_usd","depth_ask2_usd",
    "bid_wall_px","bid_wall_usd","ask_wall_px","ask_wall_usd","alpha_suspect"
]
ONCHAIN_COLS = ["exch_balance_delta","wallet_activity","dominance_pct"]
MANUAL_COLS = ["note_operator","mm_note"]

ALL_COLS = PERP_COLS + SPOT_COLS + ONCHAIN_COLS + MANUAL_COLS
p_end = len(PERP_COLS)
s_end = p_end + len(SPOT_COLS)
o_end = s_end + len(ONCHAIN_COLS)
m_end = o_end + len(MANUAL_COLS)

# Row 1: section labels
ws_d.merge_cells(start_row=1, start_column=1, end_row=1, end_column=p_end)
centre(ws_d,1,1,"PERP (may)", GREY, hdr_font())
ws_d.merge_cells(start_row=1, start_column=p_end+1, end_row=1, end_column=s_end)
centre(ws_d,1,p_end+1,"SPOT/ALPHA (may)", GREY, hdr_font())
ws_d.merge_cells(start_row=1, start_column=s_end+1, end_row=1, end_column=o_end)
centre(ws_d,1,s_end+1,"ON-CHAIN (ban tu dong)", GREY, hdr_font())
ws_d.merge_cells(start_row=1, start_column=o_end+1, end_row=1, end_column=m_end)
centre(ws_d,1,o_end+1,"MANUAL (operator)", GREY, hdr_font())

# Row 2: column names
for ci, name in enumerate(ALL_COLS, start=1):
    c = ws_d.cell(row=2, column=ci, value=name)
    c.font = hdr_font()
    c.alignment = Alignment(horizontal='center', wrap_text=True)
    c.fill = BLUE

ws_d.row_dimensions[1].height = 18
ws_d.row_dimensions[2].height = 28

# Data rows starting row 3
for ri, r in enumerate(rows, start=3):
    row_bad = r.get("data_bad")
    # write perp cols
    for ci, col in enumerate(PERP_COLS, start=1):
        val = r.get(col)
        cell = ws_d.cell(row=ri, column=ci, value=val)
        cell.alignment = Alignment(horizontal='center')
        if col == "date": cell.alignment = Alignment(horizontal='left')
        # format numbers
        if col == "px_avg" and val: cell.number_format = '0.0000000'
        if col in ("ret_1d","taker_buy_pct","div_raw","div_avg3") and val is not None:
            cell.number_format = '0.000'
        if col in ("f_avg","f_min","f_max") and val is not None:
            cell.number_format = '0.000000'
        if col in ("vol_perp_usd","oi_usd") and val is not None:
            cell.number_format = '#,##0'

    # spot cols (mostly empty)
    spot_venue_val = "Alpha_ALPHA334+BSC_DEX" if r["date"] >= "2026-01-27" else "BSC_DEX_only"
    ws_d.cell(row=ri, column=p_end+1, value=spot_venue_val)
    # remaining spot empty for now (vol_spot only latest)
    if r["date"] == "2026-08-05":
        ws_d.cell(row=ri, column=p_end+2, value=290000)  # Alpha 24h from probe

    # row coloring
    if r["date"] in ("2026-07-11",):  # failed ignition
        for ci in range(1, p_end+1):
            ws_d.cell(row=ri, column=ci).fill = ORANGE
    elif r["date"] in ("2026-10-16","2026-10-17","2026-10-23"):
        pass  # Oct 2025 pump — no fill (already represented)
    if row_bad:
        ws_d.cell(row=ri, column=1).fill = RED

# Freeze row 1+2, column A
ws_d.freeze_panes = "B3"

# Column widths
ws_d.column_dimensions["A"].width = 11
for i in range(2, m_end+1):
    ws_d.column_dimensions[get_column_letter(i)].width = 10

# ════════════════════════════════════════════
# SHEET: CASE
# ════════════════════════════════════════════
ws_c = wb.create_sheet("CASE")
ws_c.column_dimensions["A"].width = 28
ws_c.column_dimensions["B"].width = 55

case_data = [
    ("token", "XPIN"),
    ("full_name", "XPIN Network (BSC meme/utility)"),
    ("chain", "BSC"),
    ("contract", "0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6"),
    ("coingecko_id", "xpin-network"),
    ("alpha_id", "ALPHA_334"),
    ("venue_perp", "Binance FAPI XPINUSDT"),
    ("venue_spot", "NONE (no Binance spot) — BSC DEX PancakeSwap V3 0.01% main pool"),
    ("venue_alpha", "Binance Alpha ALPHA_334 (listed ~2026-01-27)"),
    ("archetype", "LOAI_A_CANDIDATE — perp-first, PIN discipline, sustained pos_r>2 (chua on-chain confirm)"),
    ("state", "WATCH — post-failed-ignition holding (06/08/2026)"),
    ("thesis_1line", "3 ignition attempts: Oct 2025 (OK), Dec 2025 (partial), Jul 2026 (FAIL). Div <1 = crowd > top traders."),
    ("perp_launch", "2025-09-12 08:00 UTC"),
    ("perp_age_days", 326),
    ("alpha_listing", "~2026-01-27"),
    ("total_supply", 100_000_000_000),
    ("circulating_alpha", 48_074_534_161),
    ("circulating_pct", "48.07%"),
    ("holders_alpha", 69318),
    ("px_current", 0.001555),
    ("mc_est_usd", 74_515_929),
    ("fdv_usd", 155_500_000),
    ("T0_ignition", "N/A — no clean T0 (Jul 11 attempt FAILED, not counted as T0)"),
    ("main_campaign_ok", "2025-10-16 to 2025-10-26 (OI +74% in 1d, ATH ~$0.01032)"),
    ("atH_px", 0.010318),
    ("atH_date", "~2025-10-23 (intraday H from klines)"),
    ("px_vs_ath_now", "-85% (px 0.00155 vs ATH 0.01032)"),
    ("build_VWAP_est", "PENDING — no clean T0 for current campaign"),
    ("OI_latest", 11_611_000),
    ("OI_peak", 15_646_180),
    ("OI_floor_30d", 8_562_000),
    ("gLSR_latest", 2.243),
    ("gLSR_status", "PEAK 30d — BEARISH signal (crowd all-in)"),
    ("pos_r_latest", 1.865),
    ("acc_r_latest", 2.019),
    ("div_raw_latest", 0.924),
    ("div_status", "NEUTRAL/B — acc_r > pos_r (accounts more long than top traders)"),
    ("funding_regime", "OSCILLATING — Aug 2-5 f_avg 0.0002-0.0006, not stable PIN"),
    ("pin_pct_historical", "70.6% (353/500 intervals)"),
    ("pin_streak_max", "105 intervals = 17.5 days (2026-05-15 to 2026-06-02)"),
    ("taker_absorption", "79% days neutral (44-50.5%). No FOMO on any ignition attempt."),
    ("P8_taker_detect", "ABSTAIN — no kho_vol_ratio data without on-chain"),
    ("spot_perp_ratio", "BSC DEX only ~$286K/day (negligible vs perp)"),
    ("venue_top", "Binance FAPI XPINUSDT (price discovery)"),
    ("ignition_cond_1", "gLSR reset <1.2 (currently 2.243 — NOT MET)"),
    ("ignition_cond_2", "div >1.5 (currently 0.924 — NOT MET)"),
    ("ignition_cond_3", "stable PIN >=7d (currently streak=0 — NOT MET)"),
    ("ignition_cond_4", "OI build signal (OI flat — NOT MET)"),
    ("next_ignition_est", "ABSTAIN (min 4-6 weeks if reset starts now)"),
    ("O1_unlock_schedule", "PENDING OPERATOR (BscScan vesting)"),
    ("O2_kho_wallet", "PENDING OPERATOR (BscScan top holders + tx)"),
    ("O3_exchange_balance", "PENDING OPERATOR (Nansen LOCKED / BscScan)"),
    ("O4_bitmart_vol", "PENDING verify ($1.1B suspicious — likely wash)"),
]

for ri, (k, v) in enumerate(case_data, start=1):
    ws_c.cell(row=ri, column=1, value=k).font = Font(bold=True, size=9)
    ws_c.cell(row=ri, column=2, value=v)
    ws_c.row_dimensions[ri].height = 14

# ════════════════════════════════════════════
# SHEET: EVENTS
# ════════════════════════════════════════════
ws_e = wb.create_sheet("EVENTS")
ev_headers = ["date","event_type","px_open","px_high","px_low","px_close","vol_perp_usd","taker_pct","oi_delta","note"]
for ci, h in enumerate(ev_headers, 1):
    c = ws_e.cell(row=1, column=ci, value=h)
    c.font = hdr_font(); c.fill = BLUE

events = [
    ("2025-09-12","LAUNCH","0.00131","0.00249","0.00131","0.00172","95,977,068","47.8%","—","Perp launch day. Sell bias immediate (47.8%)."),
    ("2025-09-14","BAIT_PROBE","?","?","?","0.00159","391,993,821","48.1%","—","16x avg vol, 93% range. Crowd dump, not FOMO."),
    ("2025-10-03","RESCUE_PROBE","?","?","?","0.00100","129,813,493","47.5%","—","5.4x vol, 66% range. px at $0.001 — bottom probe."),
    ("2025-10-16","CAMPAIGN1_IGNITION","0.00114","?","?","0.00285","614,332,097","50.4%","+? (no OI hist)","REAL ignition. +150% net. Vol 25.5x avg."),
    ("2025-10-17","CAMPAIGN1_CONT","0.00285","?","?","0.00369","745,012,418","51.4%","—","+29.7%. Vol 30.9x."),
    ("2025-10-19","CAMPAIGN1_MARKUP","?","?","?","0.00441","392,093,372","51.7%","—","+26.1%. Continued markup."),
    ("2025-10-22","CAMPAIGN1_MARKUP2","?","?","?","0.00499","235,428,920","50.9%","—","$0.005 touched."),
    ("2025-10-23","CAMPAIGN1_ATH","?","0.01032","?","0.00860","1,037,805,445","51.0%","—","ATH day. 43x avg vol. range 112%. Intraday H=$0.01032."),
    ("2025-10-24","CAMPAIGN1_EXIT","?","?","?","0.00807","272,794,440","50.5%","—","Distribution phase. Vol still 11x avg."),
    ("2025-11-04","CAMPAIGN1_COLLAPSE","?","?","?","0.00456","56,280,345","48.7%","—","px drop to $0.00456. Post-campaign unwind."),
    ("2025-11-18","SELL_SIDE","?","?","?","0.00285","6,169,028","38.9%","—","Taker 38.9% = heavy sell. Vol minimal."),
    ("2025-12-21","CAMPAIGN2_IGNITION","?","?","?","0.00261","106,694,784","48.9%","—","Mini campaign 2. 4.4x avg. +48.5%."),
    ("2025-12-22","CAMPAIGN2_CONT","?","?","?","0.00292","148,352,367","49.9%","—","Continuation. 6.2x avg. Then declined."),
    ("2026-03-25","CAPITULATION","?","?","?","0.00117","?","39.6%","—","Taker 39.6% — heavy sell. Bottom proximity."),
    ("2026-04-07","APRIL_BOUNCE","?","?","?","0.00125","16,079,502","48.3%","—","Bounce from $0.001 floor. Vol 6.7x avg."),
    ("2026-07-10","IGNITION3_BUILD","0.00149","0.00190","0.00146","0.00188","33,353,935","50.2%","OI $9.6M→$10.0M","Build-up day. OI +4%."),
    ("2026-07-11","IGNITION3_FAIL","0.00188","0.00225","0.00165","0.00197","207,302,334","50.6%","OI $10.0M→$14.9M (+49%)","FAILED IGNITION. 9x avg vol but taker 50.6% neutral = no crowd bid. Net +4.3% only."),
    ("2026-07-12","POST_FAIL_DUMP","0.00197","0.00213","0.00183","0.00191","32,019,150","49.7%","OI $15.6M (peak)","OI peaked, then unwind started."),
    ("2026-07-17","HIGH_POS_R","?","?","?","0.00155","3,291,790","50.7%","OI $10.9M","pos_r=2.359 peak 30d. Strong Structure A but ignition failed."),
    ("2026-07-29","DIV_BREAK","?","?","?","0.00151","2,031,064","53.1%","OI $11.7M","div crosses below 1.5 (div=1.101) — structure weakening."),
    ("2026-07-31","DIV_INVERT","?","?","?","0.00154","2,413,990","53.5%","OI $11.3M","div=0.991 — inverted. acc_r > pos_r for first time. gLSR=2.017."),
    ("2026-08-05","LATEST","0.00152","0.00156","0.00151","0.00156","567,000","56.4%","OI $11.6M","gLSR=2.243 peak 30d. div=0.924. data_bad=1 (partial day)."),
]

for ri, ev in enumerate(events, start=2):
    for ci, val in enumerate(ev, start=1):
        ws_e.cell(row=ri, column=ci, value=val)
    if "IGNITION3_FAIL" in ev[1]: ws_e.row_dimensions[ri].fill = RED
    if "CAMPAIGN1" in ev[1]:
        for ci in range(1,len(ev_headers)+1):
            ws_e.cell(row=ri, column=ci).fill = GREEN

for ci in range(1,11):
    ws_e.column_dimensions[get_column_letter(ci)].width = 16
ws_e.column_dimensions["J"].width = 55

# ════════════════════════════════════════════
# SHEET: TRIGGERS
# ════════════════════════════════════════════
ws_t = wb.create_sheet("TRIGGERS")
ws_t.merge_cells("A1:E1")
ws_t.cell(1,1,"C. CHOT THEO DOI — doc moi ngay sau nen dong").font = hdr_font()
for ci,h in enumerate(["#","chot","dieu_kien","nghia_khi_bat","trang_thai_hom_nay"],1):
    c = ws_t.cell(row=2,column=ci,value=h); c.font = hdr_font(); c.fill = BLUE

triggers = [
    (1,"NEXT_IGNITION_SETUP","gLSR <1.2 AND div >1.5 AND stable_PIN >=7d AND OI build signal","Ignition window open","NOT MET (0/4 conditions) — 06/08/2026"),
    (2,"DIV_RECOVERY","div_raw > 1.5 sustained >=3 ngay","Top traders leading again — pre-ignition","FAIL (div=0.92 and declining)"),
    (3,"gLSR_RESET","gLSR < 1.2 sustained >=3 ngay","Crowd shorts rebuilt — fuel available","FAIL (gLSR=2.243, peak)"),
    (4,"FUND_RESTABLE","f_avg <= 5.5e-5 AND f_min=5e-5 >=7 intervals liên tiếp","PIN regime restored","FAIL (oscillating 0.0002-0.0006)"),
    (5,"OI_BUILD","OI increase >20% from floor $8.56M trong 5 ngay","MM loading perp longs","FAIL (OI flat $11-12M)"),
    (6,"BITMART_VOL_VERIFY","Confirm BitMart $1.1B/day = wash or real","Venue map locked","PENDING OPERATOR"),
]
for ri, tr in enumerate(triggers, start=3):
    for ci, v in enumerate(tr, start=1):
        ws_t.cell(row=ri, column=ci, value=v)

ws_t.column_dimensions["B"].width = 25; ws_t.column_dimensions["C"].width = 45
ws_t.column_dimensions["D"].width = 30; ws_t.column_dimensions["E"].width = 45

# ════════════════════════════════════════════
# SHEET: OUTCOME
# ════════════════════════════════════════════
ws_o = wb.create_sheet("OUTCOME")
outcome_cols = ["moc","ngay_han","px_actual","ret_vs_T0","ret_vs_exit_VWAP","verdict","note"]
for ci,h in enumerate(outcome_cols,1):
    c = ws_o.cell(row=1,column=ci,value=h); c.font=hdr_font(); c.fill=BLUE

outcome_data = [
    ("T0_campaign1","2025-10-16","0.00114","—","—","BASE","Ignition day Campaign 1"),
    ("T+7_c1","2025-10-23","0.00860","+654%","—","RESOLVED_UP","ATH day"),
    ("T+30_c1","2025-11-15","~0.00310","~+172%","—","PENDING LOOKUP","Approx. from XPIN_result.txt"),
    ("T0_campaign2","2025-12-21","0.00175","—","—","BASE","Mini campaign 2"),
    ("T+30_c2","2026-01-20","~0.00240","~+37%","—","PENDING LOOKUP","Approx."),
    ("Jul11_failed","2026-07-11","0.00197","—","—","FAIL (not counted)","Ignition attempt failed"),
    ("T+30_jul11","2026-08-10","PENDING","PENDING","PENDING","PENDING","If Jul11 was T0 (disputed)"),
    ("exit_VWAP_c1","2025-10-24~26","~0.00815","—","—","REFERENCE","Approx. distribution VWAP"),
    ("atH_px","2025-10-23","0.010318 (intraday)","—","—","REFERENCE","Highest intraday"),
]
for ri, od in enumerate(outcome_data, start=2):
    for ci, v in enumerate(od, start=1):
        ws_o.cell(row=ri, column=ci, value=v)

for ci in range(1,8):
    ws_o.column_dimensions[get_column_letter(ci)].width = 20
ws_o.column_dimensions["G"].width = 40

# ════════════════════════════════════════════
# SHEET: MM_PROFILE
# ════════════════════════════════════════════
ws_m = wb.create_sheet("MM_PROFILE")
ws_m.column_dimensions["A"].width = 30; ws_m.column_dimensions["B"].width = 65

mm_data = [
    ("mm_id","unknown-XPIN"),
    ("archetype","LOAI_A_CANDIDATE (chua on-chain confirm) — perp-first, BSC token"),
    ("fingerprint_1_funding","PIN 70.6% historical. Max streak 17.5d (May-Jun 2026). Stable cost hold."),
    ("fingerprint_2_structure","pos_r >1.9 sustained Jul 2025-Jul 2026 = strong perp long. Peak pos_r=2.359 (17/07)."),
    ("fingerprint_3_div_collapse","div 2.089 (17/07) -> 0.924 (05/08) in 19 days = top traders not adding, accounts piling in."),
    ("fingerprint_4_glsr","gLSR 0.952 (Jul 11 pump day) -> 2.243 (Aug 05) in 25 days = all retail FOMO in after fail."),
    ("fingerprint_5_taker","79% neutral days (44-50.5%). Oct 2025 pump: 50-52% (MM absorbing sells). Jul 2026 fail: 50.6% neutral."),
    ("fingerprint_6_bait_pattern","Sep 2025: dump. Oct 2025: real pump 43x. Dec 2025: mini 6x. Jul 2026: fail 9x. Declining effectiveness."),
    ("campaign_1_verdict","Oct 16-26, 2025: SUCCESS. OI +74% in 1d. ATH $0.01032. Distribution complete by Oct 26."),
    ("campaign_2_verdict","Dec 21-22, 2025: PARTIAL. Vol 6x but smaller scale. px peak $0.00292 vs ATH $0.01032."),
    ("campaign_3_verdict","Jul 10-11, 2026: FAIL. 9x vol but taker neutral — no crowd FOMO. OI +49% then dump. Net +4.3% close."),
    ("current_posture","HOLD/REDUCE? — div <1, gLSR peak, funding unstable. Distribution geometry active."),
    ("risk_bull","Tight band (12%) + funding can restabilize → new ignition in 4-8 weeks if MM decides"),
    ("risk_bear","MM already exited via BitMart/CEX wash + BSC DEX → zombie coin. gLSR 2.24 = trapped retail."),
    ("on_chain_PENDING","Top wallet addresses, exchange balance delta, vesting schedule — all PENDING OPERATOR"),
    ("L10_sources","Perp: Binance FAPI. OI/LSR: Binance FAPI. Funding: Binance FAPI. Spot: BSC DEX GeckoTerminal. On-chain: PENDING."),
]
for ri, (k, v) in enumerate(mm_data, start=1):
    ws_m.cell(row=ri, column=1, value=k).font = Font(bold=True, size=9)
    ws_m.cell(row=ri, column=2, value=v)
    ws_m.row_dimensions[ri].height = 22

# ════════════════════════════════════════════
# SHEET: UNLOCK
# ════════════════════════════════════════════
ws_u = wb.create_sheet("UNLOCK")
ws_u.column_dimensions["A"].width = 28; ws_u.column_dimensions["B"].width = 55

unlock_data = [
    ("total_supply","100,000,000,000 (100B)"),
    ("circulating_alpha","48,074,534,161 (48.07%)"),
    ("circulating_coingecko","~100B (CoinGecko MC=FDV=$154.9M — nghi data inconsistency)"),
    ("circulating_note","Dung Alpha: 48.07B. CG: ABSTAIN (mau thuan noi bo)."),
    ("holders","69,318 (Alpha 06/08/2026)"),
    ("vesting_schedule","PENDING OPERATOR (BscScan contract)"),
    ("cliff_dates","PENDING"),
    ("next_unlock_est","UNKNOWN — PENDING on-chain"),
    ("mu_unlock_applicable","UNKNOWN — can Loai A (insider locked) hoac Loai C (tu mua thi truong)"),
    ("L12_exempt","ABSTAIN — chua biet archetype chinh xac"),
    ("kho_size_est","PENDING OPERATOR"),
    ("kho_val_at_campaign1","PENDING (chua co kho size va exit VWAP chinh xac)"),
    ("kho_vol_ratio","ABSTAIN — chua co on-chain"),
    ("dex_liq_snapshot","PancakeSwap V3 0.01%: liq=$948K, vol24h=$286K (05/08/2026, GeckoTerminal)"),
    ("alpha_liq","$958K (05/08/2026, Binance Alpha)"),
    ("O1_vesting","PENDING OPERATOR"),
    ("O2_top_wallets","PENDING OPERATOR"),
    ("O3_exch_balance","PENDING OPERATOR (Nansen LOCKED / BscScan export)"),
    ("O4_bitmart","PENDING verify (wash or real?)"),
]
for ri, (k, v) in enumerate(unlock_data, start=1):
    ws_u.cell(row=ri, column=1, value=k).font = Font(bold=True, size=9)
    ws_u.cell(row=ri, column=2, value=v)
    ws_u.row_dimensions[ri].height = 16

# ─── Save ───
wb.save(OUT)
p(f"\nDONE -> {OUT}")
p(f"DAILY: {len(rows)} rows")
p(f"Sheets: {[s.title for s in wb.worksheets]}")
