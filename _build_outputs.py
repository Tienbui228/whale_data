#!/usr/bin/env python3
"""Build T3/T4/T5 outputs locally từ export data đã probe.
  - TAG_daily.csv + BR_daily.csv (T3)
  - missing_jul.md (T4)
  - cooldown_review_2026-07-30.md (T5)
"""
import csv, math
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(r"D:\Data back test\whale_data")
DATA_DIR = ROOT / "docs" / "case_files" / "data"
REPORTS_DIR = ROOT / "docs" / "reports"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Raw export data (từ probe output) ─────────────────────────────────────────
# Columns: date,symbol,px_avg,vol_quote,taker_buy_pct,funding_avg,funding_min,
#           funding_max,funding_n,oi_usd,lsr_pos_r,lsr_acc_r,lsr_global_r,
#           taker_ratio,low_conf,src_ratio,data_ok

TAG_ROWS = [
    {"date":"2026-07-01","px_avg":"0.0009664101846464","vol_quote":"1802364.22165","taker_buy_pct":"0.458663679838918","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"7270937.479197","lsr_pos_r":"1.4457","lsr_acc_r":"1.6674","lsr_global_r":"1.8193","taker_ratio":"0.8472804479522758","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-02","px_avg":"0.0009754515472342","vol_quote":"2504122.4446816","taker_buy_pct":"0.4570957033692953","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6974247.27642048","lsr_pos_r":"1.5688","lsr_acc_r":"1.7122","lsr_global_r":"1.9343","taker_ratio":"0.8419452677130347","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-03","px_avg":"0.0009497989810843","vol_quote":"1268001.00045","taker_buy_pct":"0.5046564757171528","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6992083.578938","lsr_pos_r":"1.547","lsr_acc_r":"1.7495","lsr_global_r":"2.0562","taker_ratio":"1.0188009956278097","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-04","px_avg":"0.0009209754016344","vol_quote":"3082838.353394","taker_buy_pct":"0.4563902786079038","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"7127204.96359275","lsr_pos_r":"1.5514","lsr_acc_r":"1.745","lsr_global_r":"2.0349","taker_ratio":"0.8395550348863564","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-05","px_avg":"0.0009070601068978","vol_quote":"1601806.042376","taker_buy_pct":"0.492437961057301","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6611465.132886","lsr_pos_r":"1.5949","lsr_acc_r":"1.8289","lsr_global_r":"2.0855","taker_ratio":"0.9702025038812933","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-06","px_avg":"0.0008885095625256","vol_quote":"1243313.1726712","taker_buy_pct":"0.4546306673538518","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6738572.05102256","lsr_pos_r":"1.6006","lsr_acc_r":"1.8305","lsr_global_r":"2.1133","taker_ratio":"0.8336197878013609","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-07","px_avg":"0.0008958818309653","vol_quote":"3398704.485044","taker_buy_pct":"0.497854405253759","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6576629.59033136","lsr_pos_r":"1.5964","lsr_acc_r":"1.867","lsr_global_r":"2.1576","taker_ratio":"0.9914542922662688","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-08","px_avg":"0.0004879768928899","vol_quote":"71087080.3323296","taker_buy_pct":"0.4937465058110899","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"6395269.26701952","lsr_pos_r":"1.5913","lsr_acc_r":"1.5562","lsr_global_r":"1.8818","taker_ratio":"0.9752950082885689","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-09","px_avg":"0.0008247302670031","vol_quote":"448935788.110978","taker_buy_pct":"0.5037029764881212","funding_avg":"5.9905e-05","funding_min":"5e-05","funding_max":"0.00010943","funding_n":"6","oi_usd":"5641636.84635196","lsr_pos_r":"1.4641","lsr_acc_r":"1.1777","lsr_global_r":"1.3294","taker_ratio":"1.0149224206984695","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-10","px_avg":"0.0009813385115906","vol_quote":"263925354.60619","taker_buy_pct":"0.507909865032443","funding_avg":"8.571e-05","funding_min":"5e-05","funding_max":"0.00018188","funding_n":"6","oi_usd":"9649060.162378","lsr_pos_r":"1.3405","lsr_acc_r":"0.6725","lsr_global_r":"0.7068","taker_ratio":"1.032148033339317","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-11","px_avg":"0.0009750257041941","vol_quote":"78961424.681104","taker_buy_pct":"0.504224439350003","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"10560106.56512514","lsr_pos_r":"1.2976","lsr_acc_r":"0.626","lsr_global_r":"0.6875","taker_ratio":"1.01704174100258","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-12","px_avg":"0.0009302280512932","vol_quote":"34682896.962624","taker_buy_pct":"0.5054597911199417","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"9508009.032156","lsr_pos_r":"1.555","lsr_acc_r":"0.6412","lsr_global_r":"0.7112","taker_ratio":"1.022080271823826","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-13","px_avg":"0.0009371647879031","vol_quote":"19461999.123128","taker_buy_pct":"0.5114435282874056","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"9137824.32125626","lsr_pos_r":"1.2891","lsr_acc_r":"0.6537","lsr_global_r":"0.7406","taker_ratio":"1.0468462867651358","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-14","px_avg":"0.0008858095105778","vol_quote":"10837327.860462","taker_buy_pct":"0.5208663443647353","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"8251049.06512","lsr_pos_r":"1.3258","lsr_acc_r":"0.7525","lsr_global_r":"0.8622","taker_ratio":"1.0871003074792125","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-15","px_avg":"0.0008723432746285","vol_quote":"6576912.965694","taker_buy_pct":"0.4924238671937025","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"7940864.827996","lsr_pos_r":"1.3551","lsr_acc_r":"0.7322","lsr_global_r":"0.8332","taker_ratio":"0.9701477972795516","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-16","px_avg":"0.0008485808780968","vol_quote":"4433202.118002","taker_buy_pct":"0.5010203906796634","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"7571915.188291","lsr_pos_r":"1.3748","lsr_acc_r":"0.8464","lsr_global_r":"0.9689","taker_ratio":"1.0040899093293745","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-17","px_avg":"0.0009625057932849","vol_quote":"23083628.87859","taker_buy_pct":"0.5141360932412316","funding_avg":"0.0001142516666666","funding_min":"5e-05","funding_max":"0.00030836","funding_n":"6","oi_usd":"7519871.49578","lsr_pos_r":"1.7464","lsr_acc_r":"0.8709","lsr_global_r":"0.9635","taker_ratio":"1.0581895178653395","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-18","px_avg":"0.0009773341080361","vol_quote":"10381825.322184","taker_buy_pct":"0.5062564092225211","funding_avg":"0.0001670149999999","funding_min":"5e-05","funding_max":"0.00030784","funding_n":"6","oi_usd":"8786154.946963","lsr_pos_r":"1.6971","lsr_acc_r":"1.0","lsr_global_r":"1.2129","taker_ratio":"1.025342746070564","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-19","px_avg":"0.0011927418104791","vol_quote":"58857562.715878","taker_buy_pct":"0.484517956720203","funding_avg":"0.000238805","funding_min":"5e-05","funding_max":"0.00048669","funding_n":"6","oi_usd":"8738960.9241948","lsr_pos_r":"1.7125","lsr_acc_r":"1.1088","lsr_global_r":"1.4172","taker_ratio":"0.93993178431089","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-20","px_avg":"0.0011920155961965","vol_quote":"13022426.925842","taker_buy_pct":"0.4888579061105937","funding_avg":"0.000120535","funding_min":"5e-05","funding_max":"0.00026929","funding_n":"6","oi_usd":"10260598.64745986","lsr_pos_r":"1.7507","lsr_acc_r":"1.0521","lsr_global_r":"1.318","taker_ratio":"0.9564031449469432","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-21","px_avg":"0.0011352688352012","vol_quote":"9960779.978658","taker_buy_pct":"0.5219361319447064","funding_avg":"9.370333333333331e-05","funding_min":"5e-05","funding_max":"0.00023109","funding_n":"6","oi_usd":"9461218.081904","lsr_pos_r":"1.7365","lsr_acc_r":"1.0868","lsr_global_r":"1.3958","taker_ratio":"1.091770716887432","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-22","px_avg":"0.001077988694788","vol_quote":"10290453.84867","taker_buy_pct":"0.5240361468568613","funding_avg":"5.8135000000000005e-05","funding_min":"5e-05","funding_max":"9.881e-05","funding_n":"6","oi_usd":"9817482.31456","lsr_pos_r":"1.7339","lsr_acc_r":"1.1427","lsr_global_r":"1.5349","taker_ratio":"1.1009998834917103","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-23","px_avg":"0.0010362199124241","vol_quote":"4854075.703532","taker_buy_pct":"0.5043028314262844","funding_avg":"7.365666666666667e-05","funding_min":"5e-05","funding_max":"0.00015144","funding_n":"6","oi_usd":"8886912.49430842","lsr_pos_r":"1.6934","lsr_acc_r":"1.1529","lsr_global_r":"1.5589","taker_ratio":"1.0173607262622255","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-24","px_avg":"0.0010288734885296","vol_quote":"5807308.608057","taker_buy_pct":"0.5118617592502197","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"8233373.86151258","lsr_pos_r":"1.6937","lsr_acc_r":"1.1524","lsr_global_r":"1.5253","taker_ratio":"1.0486","low_conf":"False","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-25","px_avg":"0.0010366044158975","vol_quote":"3089525.449064","taker_buy_pct":"0.4988222322457776","funding_avg":"6.111166666666666e-05","funding_min":"5e-05","funding_max":"0.00010433","funding_n":"6","oi_usd":"8320418.091336","lsr_pos_r":"1.7082","lsr_acc_r":"1.1608","lsr_global_r":"1.58","taker_ratio":"0.9953","low_conf":"False","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-26","px_avg":"0.001110815263006","vol_quote":"2795377.268738","taker_buy_pct":"0.4690735333156358","funding_avg":"0.00010028","funding_min":"5e-05","funding_max":"0.00033505","funding_n":"6","oi_usd":"8768509.35009743","lsr_pos_r":"1.7046","lsr_acc_r":"1.2533","lsr_global_r":"1.6774","taker_ratio":"0.8835","low_conf":"False","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-27","px_avg":"0.0011269806460417","vol_quote":"310712.040849","taker_buy_pct":"0.5023885350318472","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"1","oi_usd":"9131931.517954","lsr_pos_r":"1.3508","lsr_acc_r":"1.2563","lsr_global_r":"1.7071","taker_ratio":"1.0096","low_conf":"False","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-28","px_avg":"","vol_quote":"","taker_buy_pct":"0.4988975746642614","funding_avg":"0.00026322","funding_min":"0.00026322","funding_max":"0.00026322","funding_n":"1","oi_usd":"12188951.1207","lsr_pos_r":"1.595","lsr_acc_r":"0.9988","lsr_global_r":"1.2978","taker_ratio":"0.9956","low_conf":"True","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-29","px_avg":"","vol_quote":"","taker_buy_pct":"","funding_avg":"0.00014019","funding_min":"0.00014019","funding_max":"0.00014019","funding_n":"1","oi_usd":"11172261.42025188","lsr_pos_r":"1.6204","lsr_acc_r":"1.3719","lsr_global_r":"1.8129","taker_ratio":"","low_conf":"True","src_ratio":"native_1d","data_ok":"True"},
]

BR_ROWS = [
    {"date":"2026-07-01","px_avg":"0.1473907111526468","vol_quote":"3675649.30508","taker_buy_pct":"0.499427200761722","funding_avg":"6.617666666666667e-05","funding_min":"5e-05","funding_max":"0.000104","funding_n":"6","oi_usd":"3751889.16194472","lsr_pos_r":"1.5481","lsr_acc_r":"1.3918","lsr_global_r":"1.6788","taker_ratio":"0.99771142483511","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-02","px_avg":"0.1520480277396708","vol_quote":"4734614.717","taker_buy_pct":"0.4887834335514468","funding_avg":"5.2778333333333336e-05","funding_min":"5e-05","funding_max":"6.075e-05","funding_n":"6","oi_usd":"3725219.28254119","lsr_pos_r":"1.5661","lsr_acc_r":"1.5419","lsr_global_r":"1.9869","taker_ratio":"0.9561181417633812","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-03","px_avg":"0.153488481650021","vol_quote":"3560083.676","taker_buy_pct":"0.4717346720723521","funding_avg":"9.391666666666668e-05","funding_min":"5e-05","funding_max":"0.00030111","funding_n":"6","oi_usd":"4193514.29210862","lsr_pos_r":"1.54","lsr_acc_r":"1.4691","lsr_global_r":"1.924","taker_ratio":"0.8929881389773163","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-04","px_avg":"0.1515645573212062","vol_quote":"2372234.19108","taker_buy_pct":"0.4881759770410498","funding_avg":"6.412166666666667e-05","funding_min":"5e-05","funding_max":"9.355e-05","funding_n":"6","oi_usd":"3794695.3942","lsr_pos_r":"1.5323","lsr_acc_r":"1.4408","lsr_global_r":"1.9412","taker_ratio":"0.9537965299456116","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-05","px_avg":"0.1501500601957551","vol_quote":"1817891.7037","taker_buy_pct":"0.4838282989858729","funding_avg":"6.180666666666667e-05","funding_min":"5e-05","funding_max":"9.061e-05","funding_n":"6","oi_usd":"4046809.0267998","lsr_pos_r":"1.5337","lsr_acc_r":"1.4021","lsr_global_r":"1.8409","taker_ratio":"0.9373398387305836","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-06","px_avg":"0.1434750580722296","vol_quote":"3099900.8704","taker_buy_pct":"0.4586016984298374","funding_avg":"0.000159465","funding_min":"5e-05","funding_max":"0.00044125","funding_n":"6","oi_usd":"3946399.19974","lsr_pos_r":"1.5496","lsr_acc_r":"1.505","lsr_global_r":"2.0039","taker_ratio":"0.8470689640137425","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-07","px_avg":"0.1464958854163661","vol_quote":"3148249.9021","taker_buy_pct":"0.4882356160344527","funding_avg":"5.081833333333334e-05","funding_min":"5e-05","funding_max":"5.491e-05","funding_n":"6","oi_usd":"3810637.10525","lsr_pos_r":"1.556","lsr_acc_r":"1.5445","lsr_global_r":"1.9797","taker_ratio":"0.9540242176511476","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-08","px_avg":"0.1440122137032871","vol_quote":"2899537.87836","taker_buy_pct":"0.5200792295974599","funding_avg":"5.9325e-05","funding_min":"5e-05","funding_max":"0.00010595","funding_n":"6","oi_usd":"3678989.85446","lsr_pos_r":"1.5864","lsr_acc_r":"1.4969","lsr_global_r":"1.9638","taker_ratio":"1.083677268565051","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-09","px_avg":"0.1475113841552421","vol_quote":"1847907.85684","taker_buy_pct":"0.5019462415529955","funding_avg":"0.0001170333333333","funding_min":"5e-05","funding_max":"0.00030366","funding_n":"6","oi_usd":"3833693.46342","lsr_pos_r":"1.587","lsr_acc_r":"1.4073","lsr_global_r":"1.881","taker_ratio":"1.007815387475698","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-10","px_avg":"0.150979668162966","vol_quote":"1736927.77678","taker_buy_pct":"0.5240060700348789","funding_avg":"0.0002725183333333","funding_min":"5e-05","funding_max":"0.00048417","funding_n":"6","oi_usd":"3790020.66967307","lsr_pos_r":"1.5628","lsr_acc_r":"1.482","lsr_global_r":"1.978","taker_ratio":"1.1008671267578474","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-11","px_avg":"0.1468494812583526","vol_quote":"1738556.0015","taker_buy_pct":"0.445943792555186","funding_avg":"0.0001114516666666","funding_min":"5e-05","funding_max":"0.00030935","funding_n":"6","oi_usd":"4015829.95898","lsr_pos_r":"1.5887","lsr_acc_r":"1.4492","lsr_global_r":"2.0039","taker_ratio":"0.8048710339548062","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-12","px_avg":"0.1451514641696778","vol_quote":"1258953.8063","taker_buy_pct":"0.488915417277929","funding_avg":"7.496833333333333e-05","funding_min":"5e-05","funding_max":"0.00019981","funding_n":"6","oi_usd":"3885525.66995","lsr_pos_r":"1.583","lsr_acc_r":"1.4027","lsr_global_r":"1.9976","taker_ratio":"0.9566232944729668","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-13","px_avg":"0.1405504978822977","vol_quote":"1283715.7236","taker_buy_pct":"0.530013738459497","funding_avg":"7.6065e-05","funding_min":"5e-05","funding_max":"0.00020639","funding_n":"6","oi_usd":"3742088.325525","lsr_pos_r":"1.5881","lsr_acc_r":"1.6385","lsr_global_r":"2.2938","taker_ratio":"1.1277217694028718","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-14","px_avg":"0.1437485411330287","vol_quote":"1730170.95344","taker_buy_pct":"0.5206130826163372","funding_avg":"0.0001882633333333","funding_min":"5e-05","funding_max":"0.00048455","funding_n":"6","oi_usd":"3612667.69165473","lsr_pos_r":"1.5917","lsr_acc_r":"1.7226","lsr_global_r":"2.3535","taker_ratio":"1.0859976852469675","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-15","px_avg":"0.1470527208439208","vol_quote":"1902246.05682","taker_buy_pct":"0.4892654214190627","funding_avg":"6.235833333333334e-05","funding_min":"5e-05","funding_max":"8.966e-05","funding_n":"6","oi_usd":"3889795.40498","lsr_pos_r":"1.5864","lsr_acc_r":"1.5893","lsr_global_r":"2.231","taker_ratio":"0.9579641597372828","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-16","px_avg":"0.1471984623239126","vol_quote":"1528370.17182","taker_buy_pct":"0.4830621190789843","funding_avg":"0.0001596033333333","funding_min":"5e-05","funding_max":"0.00032344","funding_n":"6","oi_usd":"3896206.67408","lsr_pos_r":"1.5985","lsr_acc_r":"1.6882","lsr_global_r":"2.4095","taker_ratio":"0.9344684088895248","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-17","px_avg":"0.148229979017872","vol_quote":"1890341.05076","taker_buy_pct":"0.5206759196716506","funding_avg":"0.000134","funding_min":"5e-05","funding_max":"0.00022702","funding_n":"6","oi_usd":"3818469.34764","lsr_pos_r":"1.6237","lsr_acc_r":"1.7647","lsr_global_r":"2.4364","taker_ratio":"1.0862711493964046","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-18","px_avg":"0.1564711550414521","vol_quote":"5260891.6384","taker_buy_pct":"0.4745856879093696","funding_avg":"0.0001064533333333","funding_min":"5e-05","funding_max":"0.0002091","funding_n":"6","oi_usd":"4075427.85145617","lsr_pos_r":"1.6376","lsr_acc_r":"1.6645","lsr_global_r":"2.2478","taker_ratio":"0.9032599169615062","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-19","px_avg":"0.1567190858669802","vol_quote":"5987474.61622","taker_buy_pct":"0.4506079214325299","funding_avg":"7.808e-05","funding_min":"5e-05","funding_max":"0.00016622","funding_n":"6","oi_usd":"4669800.21895","lsr_pos_r":"1.6638","lsr_acc_r":"1.3294","lsr_global_r":"1.7027","taker_ratio":"0.8201936995660403","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-20","px_avg":"0.1516326259449242","vol_quote":"2292965.52138","taker_buy_pct":"0.4776912186923186","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"4144096.8357","lsr_pos_r":"1.6795","lsr_acc_r":"1.3524","lsr_global_r":"1.6624","taker_ratio":"0.9145762732465348","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-21","px_avg":"0.1533418970752074","vol_quote":"2965522.80332","taker_buy_pct":"0.5314946994423683","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"3983520.27518984","lsr_pos_r":"1.6704","lsr_acc_r":"1.5634","lsr_global_r":"2.0741","taker_ratio":"1.134447569343963","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-22","px_avg":"0.1562055162475784","vol_quote":"5266285.2826","taker_buy_pct":"0.4713727339329647","funding_avg":"5.793833333333334e-05","funding_min":"5e-05","funding_max":"9.763e-05","funding_n":"6","oi_usd":"4056012.9082","lsr_pos_r":"1.6561","lsr_acc_r":"1.5826","lsr_global_r":"2.0779","taker_ratio":"0.8916920563707544","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    {"date":"2026-07-23","px_avg":"0.1421585343673486","vol_quote":"6475074.1689","taker_buy_pct":"0.4938915561695855","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"6","oi_usd":"3796682.15333","lsr_pos_r":"1.6705","lsr_acc_r":"1.4015","lsr_global_r":"1.7956","taker_ratio":"0.9758611265831352","low_conf":"False","src_ratio":"derived_1h","data_ok":"True"},
    # Jul 24-26 MISSING — inject data_bad rows
    {"date":"2026-07-27","px_avg":"0.1515796868983051","vol_quote":"1401390.43292","taker_buy_pct":"0.504999504999505","funding_avg":"0.000144225","funding_min":"5e-05","funding_max":"0.00029434","funding_n":"6","oi_usd":"3777716.04642936","lsr_pos_r":"1.6962","lsr_acc_r":"1.495","lsr_global_r":"1.8441","taker_ratio":"1.0202","low_conf":"False","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-28","px_avg":"","vol_quote":"","taker_buy_pct":"0.50852705558559","funding_avg":"5e-05","funding_min":"5e-05","funding_max":"5e-05","funding_n":"1","oi_usd":"3685662.66548151","lsr_pos_r":"1.6742","lsr_acc_r":"1.5214","lsr_global_r":"1.9214","taker_ratio":"1.0347","low_conf":"True","src_ratio":"native_1d","data_ok":"True"},
    {"date":"2026-07-29","px_avg":"","vol_quote":"","taker_buy_pct":"","funding_avg":"0.00017978","funding_min":"0.00017978","funding_max":"0.00017978","funding_n":"1","oi_usd":"3782263.22906","lsr_pos_r":"1.6609","lsr_acc_r":"1.49","lsr_global_r":"1.9438","taker_ratio":"","low_conf":"True","src_ratio":"native_1d","data_ok":"True"},
]

def safe_float(v, default=None):
    try:
        return float(v) if v and str(v).strip() else default
    except:
        return default

def compute_derived(rows):
    """Compute derived columns: ret_1d, div_raw, div_avg3, glsr_slope_5d, oi_vs_med14, funding_regime."""
    result = []
    for i, r in enumerate(rows):
        d = dict(r)
        px = safe_float(r.get("px_avg"))
        px_prev = safe_float(rows[i-1].get("px_avg")) if i > 0 else None
        oi = safe_float(r.get("oi_usd"))
        pos = safe_float(r.get("lsr_pos_r"))
        acc = safe_float(r.get("lsr_acc_r"))
        glsr = safe_float(r.get("lsr_global_r"))

        # ret_1d
        if px and px_prev and px_prev > 0:
            d["ret_1d"] = round((px / px_prev - 1) * 100, 4)
        else:
            d["ret_1d"] = ""

        # div_raw = pos / acc (NaN guard)
        if pos and acc and acc > 0:
            d["div_raw"] = round(pos / acc, 4)
        else:
            d["div_raw"] = ""

        # div_avg3 (3-day rolling mean of div_raw, compute after first pass)
        # glsr_slope_5d = glsr(t) / glsr(t-5)
        if glsr and i >= 5:
            glsr_5 = safe_float(rows[i-5].get("lsr_global_r"))
            if glsr_5 and glsr_5 > 0:
                d["glsr_slope_5d"] = round(glsr / glsr_5, 4)
            else:
                d["glsr_slope_5d"] = ""
        else:
            d["glsr_slope_5d"] = ""

        # oi_vs_med14
        if oi and i >= 13:
            window = [safe_float(rows[j].get("oi_usd")) for j in range(i-13, i+1)]
            valid = [x for x in window if x is not None]
            if valid:
                sorted_w = sorted(valid)
                n = len(sorted_w)
                med = (sorted_w[n//2-1] + sorted_w[n//2]) / 2 if n % 2 == 0 else sorted_w[n//2]
                d["oi_vs_med14"] = round(oi / med, 4) if med > 0 else ""
            else:
                d["oi_vs_med14"] = ""
        else:
            d["oi_vs_med14"] = ""

        # oi_cycle_pos (simple: top/bottom quartile of available data)
        if oi:
            all_oi = [safe_float(rows[j].get("oi_usd")) for j in range(len(rows))]
            valid_oi = [x for x in all_oi if x is not None]
            if valid_oi:
                q1 = sorted(valid_oi)[len(valid_oi)//4]
                q3 = sorted(valid_oi)[3*len(valid_oi)//4]
                if oi <= q1:
                    d["oi_cycle_pos"] = "FLOOR"
                elif oi >= q3:
                    d["oi_cycle_pos"] = "PEAK"
                else:
                    d["oi_cycle_pos"] = "MID"
            else:
                d["oi_cycle_pos"] = ""
        else:
            d["oi_cycle_pos"] = ""

        # funding_regime (simplified)
        favg = safe_float(r.get("funding_avg"))
        fmin_v = safe_float(r.get("funding_min"))
        fmax_v = safe_float(r.get("funding_max"))
        fn = safe_float(r.get("funding_n"))
        if favg is not None:
            if favg < 0:
                d["funding_regime"] = "NEG_DIV"
            elif fmin_v is not None and fmax_v is not None and abs(fmax_v - fmin_v) < 1e-6:
                # All same → PINNED
                d["funding_regime"] = "PINNED"
            elif favg > 0.0003:
                d["funding_regime"] = "HOT"
            elif favg > 0.0001:
                d["funding_regime"] = "FLOAT"
            else:
                d["funding_regime"] = "PINNED"
        else:
            d["funding_regime"] = ""

        # data_bad flag for BR missing days
        d["data_bad"] = ""
        result.append(d)

    # Second pass: compute div_avg3
    div_raws = [safe_float(r.get("div_raw")) for r in result]
    for i, r in enumerate(result):
        if i >= 2 and all(x is not None for x in div_raws[i-2:i+1]):
            result[i]["div_avg3"] = round(sum(div_raws[i-2:i+1]) / 3, 4)
        else:
            result[i]["div_avg3"] = ""

    return result

# ── T3: Build TAG_daily.csv ───────────────────────────────────────────────────
print("Building TAG_daily.csv...")
tag_computed = compute_derived(TAG_ROWS)

# Schema columns (subset we can fill from export)
DAILY_COLS = [
    "date","px_open","px_close","px_high","px_low","ret_1d",
    "vol_perp_usd","taker_buy_pct",
    "funding_avg","funding_min","funding_max","funding_n","funding_regime",
    "oi_usd","oi_vs_med14","oi_cycle_pos",
    "lsr_pos_r","lsr_acc_r","lsr_global_r","taker_ratio",
    "div_raw","div_avg3","glsr_slope_5d",
    "d_pos_3d","d_acc_3d",
    "signals_bullish","signals_suppress","screen_rank",
    "low_conf","src_ratio","data_ok","data_bad",
    # SPOT (empty)
    "spot_venue","vol_spot_usd","taker_buy_spot_pct","spot_vs_perp_taker",
    "depth_bid2_usd","depth_ask2_usd","bid_wall_px","bid_wall_usd","ask_wall_px","ask_wall_usd",
    "alpha_vol_suspect","cvd_spot_1d",
    # ON-CHAIN (empty)
    "exch_balance_delta","watch_wallet_activity","dominance_pct",
    # MANUAL (empty)
    "note_operator","mm_note",
]

def row_to_csv(r, is_bad=False):
    return {
        "date": r.get("date",""),
        "px_open": "", "px_close": r.get("px_avg",""), "px_high": "", "px_low": "",
        "ret_1d": r.get("ret_1d",""),
        "vol_perp_usd": r.get("vol_quote",""),
        "taker_buy_pct": r.get("taker_buy_pct",""),
        "funding_avg": r.get("funding_avg",""),
        "funding_min": r.get("funding_min",""),
        "funding_max": r.get("funding_max",""),
        "funding_n": r.get("funding_n",""),
        "funding_regime": r.get("funding_regime",""),
        "oi_usd": r.get("oi_usd",""),
        "oi_vs_med14": r.get("oi_vs_med14",""),
        "oi_cycle_pos": r.get("oi_cycle_pos",""),
        "lsr_pos_r": r.get("lsr_pos_r",""),
        "lsr_acc_r": r.get("lsr_acc_r",""),
        "lsr_global_r": r.get("lsr_global_r",""),
        "taker_ratio": r.get("taker_ratio",""),
        "div_raw": r.get("div_raw",""),
        "div_avg3": r.get("div_avg3",""),
        "glsr_slope_5d": r.get("glsr_slope_5d",""),
        "d_pos_3d": "", "d_acc_3d": "",
        "signals_bullish": "", "signals_suppress": "", "screen_rank": "",
        "low_conf": r.get("low_conf",""),
        "src_ratio": r.get("src_ratio",""),
        "data_ok": r.get("data_ok",""),
        "data_bad": "1" if is_bad else "",
        "spot_venue": "", "vol_spot_usd": "", "taker_buy_spot_pct": "",
        "spot_vs_perp_taker": "", "depth_bid2_usd": "", "depth_ask2_usd": "",
        "bid_wall_px": "", "bid_wall_usd": "", "ask_wall_px": "", "ask_wall_usd": "",
        "alpha_vol_suspect": "", "cvd_spot_1d": "",
        "exch_balance_delta": "", "watch_wallet_activity": "NONE", "dominance_pct": "",
        "note_operator": "", "mm_note": "",
    }

with open(DATA_DIR / "TAG_daily.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=DAILY_COLS)
    writer.writeheader()
    for r in tag_computed:
        writer.writerow(row_to_csv(r))
print(f"  Wrote {len(tag_computed)} rows -> docs/case_files/data/TAG_daily.csv")

# ── T3: Build BR_daily.csv (with MISSING Jul 24-26) ─────────────────────────
print("Building BR_daily.csv...")
# Insert data_bad rows for missing dates
BR_ROWS_FULL = list(BR_ROWS)
missing_br = [
    {"date":"2026-07-24","px_avg":"","vol_quote":"","taker_buy_pct":"","funding_avg":"","funding_min":"","funding_max":"","funding_n":"","oi_usd":"","lsr_pos_r":"","lsr_acc_r":"","lsr_global_r":"","taker_ratio":"","low_conf":"True","src_ratio":"","data_ok":"False"},
    {"date":"2026-07-25","px_avg":"","vol_quote":"","taker_buy_pct":"","funding_avg":"","funding_min":"","funding_max":"","funding_n":"","oi_usd":"","lsr_pos_r":"","lsr_acc_r":"","lsr_global_r":"","taker_ratio":"","low_conf":"True","src_ratio":"","data_ok":"False"},
    {"date":"2026-07-26","px_avg":"","vol_quote":"","taker_buy_pct":"","funding_avg":"","funding_min":"","funding_max":"","funding_n":"","oi_usd":"","lsr_pos_r":"","lsr_acc_r":"","lsr_global_r":"","taker_ratio":"","low_conf":"True","src_ratio":"","data_ok":"False"},
]
# Insert after Jul 23 (index 22 = 0-based), before Jul 27
insert_idx = next(i for i,r in enumerate(BR_ROWS_FULL) if r["date"] == "2026-07-27")
BR_ROWS_FULL[insert_idx:insert_idx] = missing_br

br_computed = compute_derived(BR_ROWS_FULL)

with open(DATA_DIR / "BR_daily.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=DAILY_COLS)
    writer.writeheader()
    for i, r in enumerate(br_computed):
        is_bad = r.get("data_ok","True") == "False"
        writer.writerow(row_to_csv(r, is_bad=is_bad))
print(f"  Wrote {len(br_computed)} rows -> docs/case_files/data/BR_daily.csv")

# ── T3: Tính toán §1 handover chốt ──────────────────────────────────────────
print("\n=== §1 HANDOVER CHỐT 2026-07-29 ===")
tag_29 = next((r for r in tag_computed if r["date"] == "2026-07-29"), {})
br_29  = next((r for r in br_computed if r["date"] == "2026-07-29"), {})

print("\nTAG 29/07:")
print(f"  pos_r   = {tag_29.get('lsr_pos_r','?')} | acc_r = {tag_29.get('lsr_acc_r','?')}")
print(f"  div_raw = {tag_29.get('div_raw','?')} (computed) | div_avg3 = {tag_29.get('div_avg3','?')} (mốc 1.5)")
print(f"  gLSR    = {tag_29.get('lsr_global_r','?')} (mốc ARM ≤1.1 → {'MISS' if float(tag_29.get('lsr_global_r',99)) > 1.1 else 'HIT'})")
print(f"  OI      = {float(tag_29.get('oi_usd',0)):,.0f} USD → {'≥12M' if float(tag_29.get('oi_usd',0)) >= 12e6 else '<12M'}")
print(f"  funding_n = {tag_29.get('funding_n','?')} (expected 6, low_conf={tag_29.get('low_conf','?')})")
print(f"  oi_cycle_pos = {tag_29.get('oi_cycle_pos','?')}")
div3 = safe_float(tag_29.get("div_avg3"))
glsr = safe_float(tag_29.get("lsr_global_r"))
arm_ok = (div3 is not None and div3 >= 1.5) and (glsr is not None and glsr <= 1.1)
print(f"  ARM check (avg3≥1.5 AND gLSR≤1.1): {'PASS — soạn hồ sơ tái-ARM' if arm_ok else 'FAIL — chưa đủ điều kiện'}")
print(f"  tx cụm 6 ví: PENDING (cần BscScan 0-credit)")

print("\nBR 29/07:")
print(f"  pos_r   = {br_29.get('lsr_pos_r','?')} (mốc floor 1.661 → {'tại floor' if abs(float(br_29.get('lsr_pos_r',0)) - 1.661) < 0.01 else 'cách floor'})")
print(f"  acc_r   = {br_29.get('lsr_acc_r','?')}")
print(f"  gLSR    = {br_29.get('lsr_global_r','?')} (mốc sập từ 1.94 — hiện {'TRÊN' if float(br_29.get('lsr_global_r',0)) > 1.94 else 'DƯỚI'} ngưỡng)")
print(f"  OI      = {float(br_29.get('oi_usd',0)):,.0f} USD")
print(f"  funding_n = {br_29.get('funding_n','?')} | funding_avg = {br_29.get('funding_avg','?')}")
print(f"  kho 6% chuyển động: PENDING (cần on-chain source)")
print(f"  bid_wall/ask_wall: CẦN OPERATOR (snapshot Gate đầu tiên hôm nay)")

# ── T4: Write missing_jul.md ─────────────────────────────────────────────────
print("\nBuilding docs/reports/missing_jul.md from missing_july_2026.txt...")
missing_src = ROOT / "missing_july_2026.txt"
if missing_src.exists():
    content = missing_src.read_text(encoding="utf-8")
    (REPORTS_DIR / "missing_jul.md").write_text(
        f"# Missing Count Jul 2026 — per-symbol audit\n\nNguồn: `missing_july_2026.txt`, tạo 2026-07-29\n\n```\n{content}\n```\n",
        encoding="utf-8"
    )
    print("  Wrote docs/reports/missing_jul.md")
else:
    print("  missing_july_2026.txt not found locally — SKIP")

print("\nDone.")
