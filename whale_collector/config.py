from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
_data_override = os.getenv("WHALE_DATA_DIR")
DATA_DIR = Path(_data_override) / "data" if _data_override else ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
META_DIR = DATA_DIR / "_meta"
LOGS_DIR = DATA_DIR / "logs"

BINANCE_FUTURES_BASE: str = "https://fapi.binance.com"
BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")

COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")

# Rate limiting — padded well under Binance 2400/min hard limit
RATE_LIMIT_WEIGHT_PER_MIN: int = 2000
SEMAPHORE_SIZE: int = 10

# Universe bounds — only tokens with MC < 500M (excludes large caps per thesis scope)
MAX_MC_USD: int = 500_000_000
MIN_MC_USD: int = 5_000_000
UNIVERSE_TOP_N: int = 300

# Storage
COMPRESSION: str = "zstd"
COMPRESSION_LEVEL: int = 3
SCHEMA_VERSION: int = 1

# Pagination limits (Binance maximums)
KLINE_LIMIT: int = 500
OI_LIMIT: int = 500
RATIO_LIMIT: int = 500
FUNDING_LIMIT: int = 1000

# Assumed retention in days (will be probed at runtime)
ASSUMED_RETENTION_DAYS: int = 30

# Symbols permanently excluded from collection.
# BUSDT: deprecated/delisted by Binance.
# FRAXUSDT, SAFEUSDT, SKRUSDT: low liquidity; audit detected API drift or
# consistently empty responses on ratio/OI endpoints.
EXCLUDED_SYMBOLS: frozenset[str] = frozenset({
    "BUSDT",
    "FRAXUSDT",
    "SAFEUSDT",
    "SKRUSDT",
})

MASTER_PATH = DATA_DIR / "config" / "universe_master.csv"
FRESHWATCH_PATH = DATA_DIR / "config" / "freshwatch_symbols.txt"

ENDPOINT_WEIGHTS: dict[str, int] = {
    "klines_500": 2,
    "klines_1000": 5,
    "openInterestHist": 1,
    "topLongShortPositionRatio": 1,
    "topLongShortAccountRatio": 1,
    "globalLongShortAccountRatio": 1,
    "takerlongshortRatio": 1,
    "fundingRate": 1,
    "exchangeInfo": 1,
}
