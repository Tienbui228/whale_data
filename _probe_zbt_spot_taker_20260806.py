"""Verify: ZBTUSDT spot klines k[10]/k[7] cho ra taker% hợp lệ.
Phân biệt k[9] (base tokens) vs k[10] (quote USDT) — root cause của ABSTAIN cũ.
"""
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

url = "https://api.binance.com/api/v3/klines?symbol=ZBTUSDT&interval=1d&limit=10"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())

from datetime import datetime, timezone
print(f"{'date':<12} {'k[5] base_vol':>16} {'k[7] quote_vol$':>16} {'k[9]/k[7]%':>12} {'k[10]/k[7]%':>13} {'k[10]$':>14}")
print("-" * 85)
for k in data[-10:]:
    d    = datetime.fromtimestamp(int(k[0])//1000, tz=timezone.utc).strftime("%Y-%m-%d")
    bv   = float(k[5])   # base volume (tokens)
    qv   = float(k[7])   # quote volume (USDT)
    tb_b = float(k[9])   # taker buy BASE (tokens)  ← WRONG unit vs qv
    tb_q = float(k[10])  # taker buy QUOTE (USDT)   ← CORRECT unit vs qv
    wrong  = tb_b / qv * 100 if qv else 0  # tokens/USDT → nonsense
    right  = tb_q / qv * 100 if qv else 0  # USDT/USDT   → valid %
    print(f"  {d}  {bv:>16,.0f}  {qv:>16,.0f}  {wrong:>11.1f}%  {right:>12.1f}%  {tb_q:>14,.0f}")

print()
print("Kết luận:")
print("  k[9]/k[7] = base_tokens / quote_USDT → đơn vị lệch → có thể >100% hoặc vô nghĩa")
print("  k[10]/k[7] = takerBuyQuote(USDT) / quoteVol(USDT) → hợp lệ, luôn [0,100]%")
print("  → spot_collector.py dùng k[10] là đúng, probe ZBT cũ dùng k[9] = bug")
print("[DONE]")
