#!/usr/bin/env python3
"""
pool_inventory_dexscreener.py — bước 1 nghiên cứu pool (15/09/2026)

Lấy inventory pool DEX trên BSC cho 15 case token từ DexScreener (free, không credit).
Output:
  pool_inventory_<YYYYMMDD_HHMM>.csv   — mỗi pair BSC của mỗi token (1 hàng/pair)
  pool_inventory_top_<...>.csv         — 1 hàng/token: pair thanh khoản lớn nhất + tổng vol/liq
Cột SYMBOL_MATCH: baseToken.symbol trên DexScreener có khớp ticker mình gửi không
(chặn lỗi gán nhầm địa chỉ kiểu L-38). MISMATCH => KHÔNG dùng hàng đó, hỏi lại.

Chạy: python3 pool_inventory_dexscreener.py
Phụ thuộc: requests (pip install requests --break-system-packages)
"""
import csv, sys, time, datetime as dt
import requests

TOKENS = [
    ("BANK",  "0x46ddcc662a045770ce1e264819542c9617547777"),
    ("TUT",   "0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3"),
    ("AKE",   "0x2c3a8ee94ddd97244a93bc48298f97d2c412f7db"),
    ("BTW",   "0x444045b0ee1ee319a660a5e3d604ca0ffa35acaa"),
    ("CYS",   "0x0c69199c1562233640e0db5ce2c399a88eb507c7"),
    ("BTR",   "0xfed13d0c40790220fbde712987079eda1ed75c51"),
    ("CAP",   "0x99991c6aabba5a096f24f250b73580f5179b9999"),
    ("ON",    "0x0e4f6209ed984b21edea43ace6e09559ed051d48"),
    ("APR",   "0x299ad4299da5b2b93fba4c96967b040c7f611099"),
    ("HEMI",  "0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b"),
    ("BULLA", "0x595e21b20e78674f8a64c1566a20b2b316bc3511"),
    ("PROM",  "0xaf53d56ff99f1322515e54fdde93ff8b3b7dafd5"),
    ("龙虾",   "0xeccbb861c0dda7efd964010085488b69317e4444"),
    ("UAI",   "0x3e5d4f8aee0d9b3082d5f6da5d6e225d17ba9ea0"),
    ("SOPH",  "0x31dba3c96481fde3cd81c2aaf51f2d8bf618c742"),
]
CHAIN = "bsc"
URL = "https://api.dexscreener.com/latest/dex/tokens/{}"

PAIR_COLS = ["ticker", "token_address", "SYMBOL_MATCH", "ds_base_symbol", "pair_address",
             "dex", "version_labels", "quote_symbol", "quote_address", "liquidity_usd",
             "vol_h24_usd", "vol_h6_usd", "txns_h24_buys", "txns_h24_sells", "price_usd",
             "fdv_usd", "mcap_usd", "pair_created_utc", "url"]


def fetch(addr):
    for attempt in range(3):
        try:
            r = requests.get(URL.format(addr), timeout=20)
            if r.status_code == 429:
                time.sleep(5); continue
            r.raise_for_status()
            return r.json().get("pairs") or []
        except Exception as e:
            print(f"  retry {attempt+1}: {e}", file=sys.stderr); time.sleep(2)
    return None


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0


def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M")
    pair_rows, top_rows = [], []
    for ticker, addr in TOKENS:
        print(f"{ticker} {addr}")
        pairs = fetch(addr)
        if pairs is None:
            top_rows.append({"ticker": ticker, "token_address": addr, "status": "FETCH_FAIL"}); continue
        pairs = [p for p in pairs if p.get("chainId") == CHAIN
                 and p.get("baseToken", {}).get("address", "").lower() == addr.lower()]
        if not pairs:
            top_rows.append({"ticker": ticker, "token_address": addr, "status": "NO_BSC_PAIR"}); continue
        pairs.sort(key=lambda p: f((p.get("liquidity") or {}).get("usd")), reverse=True)
        tot_liq = sum(f((p.get("liquidity") or {}).get("usd")) for p in pairs)
        tot_vol = sum(f((p.get("volume") or {}).get("h24")) for p in pairs)
        for p in pairs:
            sym = p.get("baseToken", {}).get("symbol", "")
            created = p.get("pairCreatedAt")
            pair_rows.append({
                "ticker": ticker, "token_address": addr,
                "SYMBOL_MATCH": "OK" if sym.upper() == ticker.upper() else "MISMATCH",
                "ds_base_symbol": sym, "pair_address": p.get("pairAddress"),
                "dex": p.get("dexId"), "version_labels": "|".join(p.get("labels") or []),
                "quote_symbol": p.get("quoteToken", {}).get("symbol"),
                "quote_address": p.get("quoteToken", {}).get("address"),
                "liquidity_usd": f((p.get("liquidity") or {}).get("usd")),
                "vol_h24_usd": f((p.get("volume") or {}).get("h24")),
                "vol_h6_usd": f((p.get("volume") or {}).get("h6")),
                "txns_h24_buys": ((p.get("txns") or {}).get("h24") or {}).get("buys"),
                "txns_h24_sells": ((p.get("txns") or {}).get("h24") or {}).get("sells"),
                "price_usd": p.get("priceUsd"), "fdv_usd": p.get("fdv"), "mcap_usd": p.get("marketCap"),
                "pair_created_utc": dt.datetime.fromtimestamp(created / 1000, dt.timezone.utc).isoformat()
                                    if created else "", "url": p.get("url"),
            })
        t = pairs[0]
        top_rows.append({
            "ticker": ticker, "token_address": addr, "status": "OK",
            "n_pairs": len(pairs),
            "top_pair_address": t.get("pairAddress"), "top_dex": t.get("dexId"),
            "top_version": "|".join(t.get("labels") or []),
            "top_quote": t.get("quoteToken", {}).get("symbol"),
            "top_liq_usd": f((t.get("liquidity") or {}).get("usd")),
            "total_liq_usd": tot_liq, "total_vol_h24_usd": tot_vol,
            "mcap_usd": t.get("marketCap"), "fdv_usd": t.get("fdv"),
            "liq_over_mcap": (tot_liq / f(t.get("marketCap"))) if f(t.get("marketCap")) else "",
            "SYMBOL_MATCH": "OK" if t.get("baseToken", {}).get("symbol", "").upper() == ticker.upper()
                            else "MISMATCH",
        })
        time.sleep(0.4)

    p1 = f"pool_inventory_{stamp}.csv"
    with open(p1, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=PAIR_COLS); w.writeheader(); w.writerows(pair_rows)
    top_cols = ["ticker", "token_address", "status", "n_pairs", "top_pair_address", "top_dex",
                "top_version", "top_quote", "top_liq_usd", "total_liq_usd", "total_vol_h24_usd",
                "mcap_usd", "fdv_usd", "liq_over_mcap", "SYMBOL_MATCH"]
    p2 = f"pool_inventory_top_{stamp}.csv"
    with open(p2, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=top_cols, extrasaction="ignore"); w.writeheader(); w.writerows(top_rows)
    print(f"\nwrote {p1} ({len(pair_rows)} pairs) and {p2} ({len(top_rows)} tokens)")
    print("Kiểm tra cột SYMBOL_MATCH trước khi dùng; MISMATCH = hỏi lại địa chỉ.")


if __name__ == "__main__":
    main()
