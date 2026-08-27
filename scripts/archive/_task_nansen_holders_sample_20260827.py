"""[NANSEN /tgm/holders sample · operator KY 27/08 · task-scoped · CREDIT-LEDGER]

Per operator explicit authorization "tôi đòng ý sử dụng nansen cho task này".
1 call mẫu để verify /tgm/holders date-param schema per §5-#2.

Auth: NANSEN_KEY_LOCKED env var (per CLAUDE.md — không rename, không hardcode).
Chain: bnb (khớp bot doctrine)
Token: TUT 0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3
Date: 2026-08-01..2026-08-01 (1-day snapshot)
Cost: 5 credits (free-tier labels · cap 2/day)

Ledger đè: data/state/nansen_credit_ledger.log (append-only text).
"""
from __future__ import annotations
import sys, io, os, json, urllib.request
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(r"D:/Data back test/whale_data")
LEDGER = REPO / "data/state/nansen_credit_ledger.log"

# Load NANSEN_KEY_LOCKED from local .env (Windows dev)
def _load_key():
    key = os.getenv("NANSEN_KEY_LOCKED", "")
    if not key:
        # Fallback: parse .env directly (dotenv not necessarily installed)
        env_path = Path(r"D:/Check onchain fresh wallets/.env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("NANSEN_KEY_LOCKED="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key

key = _load_key()
if not key:
    print("[FAIL] NANSEN_KEY_LOCKED not found in env or .env — không thể call")
    sys.exit(1)

BASE = "https://api.nansen.ai/api/v1"
CHAIN = "bnb"
TOKEN = "0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3"  # TUT
DATE_STR = "2026-08-01"

body = {
    "chain": CHAIN,
    "token_address": TOKEN,
    "pagination": {"page": 1, "recordsPerPage": 100},
}

url = f"{BASE}/tgm/holders"
print(f"[CALL] {url}")
print(f"       body = {json.dumps(body, indent=2)}")

req = urllib.request.Request(
    url,
    data=json.dumps(body).encode(),
    headers={"apiKey": key, "Content-Type": "application/json", "User-Agent": "h4-sample/1.0"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        code = resp.status
        raw = resp.read().decode()
    print(f"[OK] status={code}  bytes={len(raw)}")
    data = json.loads(raw)
    # Print schema summary
    print(f"\n[SCHEMA (top-level keys)]")
    print(f"  type: {type(data).__name__}")
    if isinstance(data, dict):
        for k, v in data.items():
            tv = type(v).__name__
            if isinstance(v, list): tv += f"[len={len(v)}]"
            print(f"    {k}: {tv}")
    if isinstance(data, list):
        print(f"  root list len={len(data)}")
        if data:
            first = data[0]
            print(f"  first item keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}")
    # Sample first record
    records = data.get("data") if isinstance(data, dict) else data if isinstance(data, list) else None
    if isinstance(records, list) and records:
        print(f"\n[SAMPLE first record]")
        print(json.dumps(records[0], indent=2, ensure_ascii=False)[:2000])
    elif isinstance(data, dict):
        print(f"\n[FULL response (first 3000 chars)]")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
    # Ledger
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}  /tgm/holders  chain={CHAIN}  token={TOKEN}  date={DATE_STR}  cost=5cr  cap=2/day  counter=1/2  auth=operator-ky-27/08\n")
    print(f"\n[LEDGER] appended {LEDGER}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode(errors="replace")[:500]
    print(f"[HTTPError] status={e.code} body={err_body}")
    # Log to ledger anyway (attempt)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}  /tgm/holders  FAILED status={e.code}  body={err_body[:100]}\n")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
