#!/usr/bin/env python3
"""PROBE K2+K5: IDOL — BscScan wallet trace.

K2: Tim 13 vi cum Z1 (nhan IDOL 27/07-02/08 tu staging wallets)
    -> check outbound tu 02/08 den nay -> redeposit? = thesis CONFIRMED
K5: Gate wallet 0x0d0707 — inflows thang 7 + subsequent path

IDOL contract BSC: 0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07
Output: docs/reports/_probe_idol_k2_k5_20260804.md
"""
import io, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE = Path(r"D:\Data back test\whale_data")
OUT   = WHALE / "docs" / "reports" / "_probe_idol_k2_k5_20260804.md"

IDOL_CONTRACT = "0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07"
BSCSCAN_BASE  = "https://api.bscscan.com/api"
IDOL_DECIMALS = 18
MIN_TOKENS    = 20_000_000  # 20M IDOL threshold for Z1 candidate

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def ts_to_block(ts_utc: str) -> int:
    """Rough BSC block from date YYYY-MM-DD. BSC ≈ 3s/block, genesis 2020-08-29."""
    epoch = datetime(2020, 8, 29, tzinfo=timezone.utc)
    t = datetime.strptime(ts_utc, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int((t - epoch).days * 28800)

def bsc_get(params: dict, pause: float = 0.3) -> dict | None:
    time.sleep(pause)
    url = f"{BSCSCAN_BASE}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        emit(f"  [FETCH ERROR] {e}")
        return None

def safe_amt(tx) -> float:
    try: return int(tx.get("value","0")) / 10**IDOL_DECIMALS
    except: return 0.0

emit("# PROBE K2+K5: IDOL — BscScan Wallet Trace")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"Contract: {IDOL_CONTRACT}")
emit("")

# ─── K2-A: Fetch large IDOL inflows 25/07→02/08 ──────────────────────────────
emit("## K2-A — Large IDOL Inflows 25/07→02/08 (Z1 candidate search)")
emit("")

SB_IN = ts_to_block("2026-07-25")
EB_IN = ts_to_block("2026-08-03")
emit(f"- Block range: {SB_IN:,} -> {EB_IN:,}")

all_tx = []
page = 1
while page <= 20:
    params = {
        "module": "account", "action": "tokentx",
        "contractaddress": IDOL_CONTRACT,
        "startblock": SB_IN, "endblock": EB_IN,
        "page": page, "offset": 1000, "sort": "asc",
    }
    d = bsc_get(params, pause=0.5)
    if not d or d.get("status") != "1":
        emit(f"- Page {page}: {d.get('message','err') if d else 'no resp'} — stop")
        break
    txs = d.get("result", [])
    all_tx.extend(txs)
    emit(f"- Page {page}: {len(txs)} transfers (total so far: {len(all_tx)})")
    if len(txs) < 1000: break
    page += 1

emit(f"- Total transfers in window: {len(all_tx)}")
emit("")

# Index large inflows by receiver
large_in: dict[str, dict] = {}
for tx in all_tx:
    amt = safe_amt(tx)
    if amt < MIN_TOKENS: continue
    to = tx.get("to","").lower()
    if to not in large_in:
        large_in[to] = {"total": 0.0, "txs": []}
    large_in[to]["total"] += amt
    ts = int(tx.get("timeStamp", 0))
    large_in[to]["txs"].append({
        "dt": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M"),
        "from": tx.get("from","").lower(),
        "amt_M": amt / 1e6,
        "hash": tx.get("hash","")[:20] + "...",
    })

ranked = sorted(large_in.items(), key=lambda x: x[1]["total"], reverse=True)

emit("## K2-B — Vi nhan >=20M IDOL (Z1 candidates, top 20)")
emit("")
emit("| rank | address | total_in_M | n_tx | first_dt | last_dt |")
emit("|------|---------|-----------|------|----------|---------|")

z1_addrs = []
for i, (addr, info) in enumerate(ranked[:20], 1):
    txs = sorted(info["txs"], key=lambda x: x["dt"])
    emit(f"| {i} | `{addr}` | {info['total']/1e6:.1f}M | {len(txs)} | {txs[0]['dt']} | {txs[-1]['dt']} |")
    z1_addrs.append(addr)

emit("")
emit(f"- Z1 candidates (>=20M): {len(large_in)}")
emit(f"- Top senders to Z1:")
# Show what wallets sent to these Z1 addresses
from_counts: dict[str, float] = {}
for tx in all_tx:
    amt = safe_amt(tx)
    to = tx.get("to","").lower()
    if to in large_in:
        frm = tx.get("from","").lower()
        from_counts[frm] = from_counts.get(frm, 0.0) + amt
top_senders = sorted(from_counts.items(), key=lambda x: x[1], reverse=True)[:10]
for addr, total in top_senders:
    emit(f"  - `{addr}`: {total/1e6:.1f}M IDOL sent to Z1 wallets")
emit("")

# ─── K2-C: Outbound từ Z1 sau 02/08 (thesis test) ────────────────────────────
emit("## K2-C — Outbound tu Z1 wallets sau 02/08 (thesis test)")
emit("")
emit("Redeposit len san/Alpha custody = thesis FLIP-BY-DESIGN CONFIRMED")
emit("")

SB_OUT = ts_to_block("2026-08-02")
EB_OUT = ts_to_block("2026-08-05")

# Known Binance/exchange BSC hot wallets
EXCHANGE_LABELS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance-HW1",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance-HW2",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance-HW3",
    "0x1ab4973a48dc892cd9971ece8e01dcc7688f8f23": "Binance-HW4",
    "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance-BSC-HW5",
    "0xa29b548056c3fd0f68bad9d4829ec4e66f22f796": "Binance-Alpha-Custody",
    "0xe2fc31f816a9b511ab5ddf72af1e2d8bbf1e8b58": "Binance-BSC-HW6",
}

emit("| wallet | out_amt_M | out_date | to_addr | label | verdict |")
emit("|--------|----------|----------|---------|-------|---------|")

redeposit_n = 0
holding_n   = 0

for addr in z1_addrs[:15]:  # check top 15
    params = {
        "module": "account", "action": "tokentx",
        "contractaddress": IDOL_CONTRACT,
        "address": addr,
        "startblock": SB_OUT, "endblock": EB_OUT,
        "page": 1, "offset": 100, "sort": "asc",
    }
    d = bsc_get(params, pause=0.35)
    raw = d.get("result", []) if (d and d.get("status") == "1") else []
    outbound = [t for t in raw if t.get("from","").lower() == addr]

    if not outbound:
        emit(f"| `{addr[:42]}` | 0 | — | — | — | **Sent=0 HOLDING** |")
        holding_n += 1
        continue

    for tx in outbound:
        amt     = safe_amt(tx)
        to_addr = tx.get("to","").lower()
        label   = EXCHANGE_LABELS.get(to_addr, "unknown")
        ts      = int(tx.get("timeStamp", 0))
        dt      = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        verdict = "REDEPOSIT" if label != "unknown" else "OUT-unknown"
        if verdict == "REDEPOSIT": redeposit_n += 1
        emit(f"| `{addr[:42]}` | {amt/1e6:.1f}M | {dt} | `{to_addr[:20]}...` | {label} | **{verdict}** |")

emit("")
emit(f"- Holding (Sent=0 post-02/08): {holding_n}")
emit(f"- Redeposit to exchange: {redeposit_n}")
emit(f"- Out-unknown: {len(z1_addrs[:15]) - holding_n - redeposit_n}")
emit("")
if redeposit_n > 0:
    emit("**=> THESIS FLIP-BY-DESIGN: CONFIRMED (K2 redeposit found)**")
else:
    emit("**=> K2 INCONCLUSIVE** — no redeposit in window, wallets holding or sent elsewhere")
emit("")

# ─── K5: Gate wallet 0x0d0707 trace ─────────────────────────────────────────
emit("## K5 — Gate Wallet 0x0d0707 Trace")
emit("")
GATE_PREFIX = "0x0d0707"
emit(f"Search: IDOL txs full July-Aug, filter addresses starting with {GATE_PREFIX}")
emit("")

SB_GATE = ts_to_block("2026-07-01")
EB_GATE = ts_to_block("2026-08-05")

gate_data: dict[str, dict] = {}
page = 1
while page <= 5:
    params = {
        "module": "account", "action": "tokentx",
        "contractaddress": IDOL_CONTRACT,
        "startblock": SB_GATE, "endblock": EB_GATE,
        "page": page, "offset": 1000, "sort": "asc",
    }
    d = bsc_get(params, pause=0.5)
    if not d or d.get("status") != "1":
        break
    txs = d.get("result", [])
    for tx in txs:
        for field in ["from", "to"]:
            a = tx.get(field, "").lower()
            if a.startswith(GATE_PREFIX):
                if a not in gate_data:
                    gate_data[a] = {"in": 0.0, "out": 0.0, "txs": []}
                amt = safe_amt(tx)
                ts  = int(tx.get("timeStamp", 0))
                dt  = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                if field == "to":
                    gate_data[a]["in"] += amt
                else:
                    gate_data[a]["out"] += amt
                gate_data[a]["txs"].append({
                    "dt": dt, "dir": "IN" if field == "to" else "OUT",
                    "amt_M": amt / 1e6,
                    "counterpart": tx.get("from" if field=="to" else "to","").lower(),
                    "hash": tx.get("hash","")[:20] + "...",
                })
    if len(txs) < 1000: break
    page += 1

emit(f"- Addresses matching {GATE_PREFIX}*: {len(gate_data)}")
emit("")

if gate_data:
    for addr, info in gate_data.items():
        emit(f"### Gate: `{addr}`")
        emit(f"- Total IN:  {info['in']/1e6:.2f}M IDOL")
        emit(f"- Total OUT: {info['out']/1e6:.2f}M IDOL")
        emit(f"- Net remaining: {(info['in']-info['out'])/1e6:.2f}M")
        emit("")
        emit("| dir | date | amt_M | counterpart | hash |")
        emit("|-----|------|-------|------------|------|")
        for t in sorted(info["txs"], key=lambda x: x["dt"])[:30]:
            emit(f"| {t['dir']} | {t['dt']} | {t['amt_M']:.2f}M | `{t['counterpart'][:20]}...` | `{t['hash']}` |")
        emit("")
else:
    emit(f"- **0 addresses found with prefix {GATE_PREFIX}**")
    emit(f"  => 0x0d0707 co the la viet tat; can operator cung cap full address tu EVENTS E2")
    emit("")

# ─── Summary ──────────────────────────────────────────────────────────────────
emit("## K2+K5 — Verdict")
emit("")
emit("| item | result |")
emit("|------|--------|")
emit(f"| Z1 wallets found (>=20M receiver 25/07-02/08) | {len(large_in)} |")
emit(f"| Checked for outbound post-02/08 | {min(15, len(z1_addrs))} |")
emit(f"| Still holding (Sent=0) | {holding_n} |")
emit(f"| Redeposit to exchange | {redeposit_n} |")
emit(f"| Gate wallet 0x0d0707 found | {'YES x' + str(len(gate_data)) if gate_data else 'NO — need full addr from E2'} |")
emit(f"| Thesis FLIP-BY-DESIGN (K2) | {'CONFIRMED' if redeposit_n > 0 else 'INCONCLUSIVE'} |")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")
