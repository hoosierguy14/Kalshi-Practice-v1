"""
Configuration settings for the Kalshi trading bot.

Loads values from environment variables (.env file) and provides
sensible defaults for things like API URLs and trading limits.
"""

import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Kalshi API credentials
# ---------------------------------------------------------------------------
API_KEY_ID: str = os.getenv("KALSHI_API_KEY_ID", "")
PRIVATE_KEY_PATH: str = os.getenv("KALSHI_PRIVATE_KEY_PATH", "./keys/kalshi_private_key.pem")

# ---------------------------------------------------------------------------
# Environment: "demo" or "prod"
# ---------------------------------------------------------------------------
ENV: str = os.getenv("KALSHI_ENV", "demo").lower()

# Base URLs — the bot picks the right one based on ENV
BASE_URLS: dict[str, str] = {
    "demo": "https://demo-api.kalshi.co/trade-api/v2",
    "prod": "https://trading-api.kalshi.com/trade-api/v2",
}

BASE_URL: str = BASE_URLS.get(ENV, BASE_URLS["demo"])

# ---------------------------------------------------------------------------
# Trading parameters (safe defaults for beginners)
# ---------------------------------------------------------------------------

# Maximum number of contracts to hold at once across all positions
MAX_POSITION_SIZE: int = int(os.getenv("MAX_POSITION_SIZE", "10"))

# Maximum amount (in cents) to spend on a single order
# Kalshi prices are in cents: 50 = $0.50
MAX_ORDER_COST_CENTS: int = int(os.getenv("MAX_ORDER_COST_CENTS", "500"))

# Stop trading if portfolio drops below this balance (in cents)
MIN_BALANCE_CENTS: int = int(os.getenv("MIN_BALANCE_CENTS", "1000"))

# How often to check for new trading opportunities (seconds)
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
MAX_REQUESTS_PER_SECOND: int = 10
RATE_LIMIT_BACKOFF_BASE: float = 2.0  # exponential backoff base (seconds)
RATE_LIMIT_MAX_RETRIES: int = 5

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
