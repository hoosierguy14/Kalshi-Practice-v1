# CLAUDE.md — Kalshi Practice Bot v1

## Project Overview

This is a Python-based trading bot for [Kalshi](https://kalshi.com), a CFTC-regulated prediction market exchange. The bot is designed to automatically trade Bitcoin (BTC) futures/prediction contracts on Kalshi, including hourly, daily, and 15-minute crypto contracts.

Kalshi prediction markets use binary Yes/No contracts — you buy a position on whether an event will occur (e.g., "Bitcoin above $95,000 at 5pm EST?"). Each contract pays out $1 if the outcome is Yes, $0 if No.

## Repository Status

This repository is in early development. The project structure below describes the intended architecture.

## Intended Project Structure

```
Kalshi-Practice-v1/
├── CLAUDE.md              # This file — project guide for AI assistants
├── README.md              # User-facing documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules
├── config/
│   └── settings.py        # Configuration (API URLs, trading params)
├── src/
│   ├── __init__.py
│   ├── auth.py            # RSA-PSS authentication logic
│   ├── client.py          # Kalshi API client wrapper
│   ├── markets.py         # Market discovery and data retrieval
│   ├── trading.py         # Order placement and management
│   ├── strategy.py        # Trading strategy logic
│   ├── portfolio.py       # Portfolio and position tracking
│   └── utils.py           # Shared utilities
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_markets.py
│   ├── test_trading.py
│   └── test_strategy.py
└── scripts/
    ├── run_bot.py          # Main entry point
    └── backtest.py         # Backtesting harness
```

## Kalshi API Reference

### Base URLs

| Environment | URL |
|---|---|
| **Production** | `https://trading-api.kalshi.com/trade-api/v2` |
| **Demo** | `https://demo-api.kalshi.co/trade-api/v2` |

**Always develop and test against the demo environment first.**

### Authentication — RSA-PSS Signing

Kalshi uses RSA-PSS signatures (not bearer tokens) for API authentication. Every request must include three headers:

| Header | Description |
|---|---|
| `KALSHI-ACCESS-KEY` | Your API key ID |
| `KALSHI-ACCESS-TIMESTAMP` | Request timestamp in milliseconds |
| `KALSHI-ACCESS-SIGNATURE` | RSA-PSS signature (base64-encoded) |

**Signing process:**
1. Get current timestamp in milliseconds as a string
2. Construct the message: `timestamp_str + http_method + path` (strip query params from path)
3. Sign with RSA-PSS using SHA-256, MGF1(SHA-256), salt_length=DIGEST_LENGTH
4. Base64-encode the signature

**Example signing function (Python):**
```python
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64

def sign_pss_text(private_key, message: str) -> str:
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")
```

### Key API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| Markets | GET | `/markets` | List/search markets |
| Markets | GET | `/markets/{ticker}` | Get market details |
| Markets | GET | `/markets/{ticker}/orderbook` | Get order book |
| Trading | POST | `/portfolio/orders` | Place an order |
| Trading | DELETE | `/portfolio/orders/{order_id}` | Cancel an order |
| Trading | GET | `/portfolio/orders` | List your orders |
| Portfolio | GET | `/portfolio/balance` | Get account balance |
| Portfolio | GET | `/portfolio/positions` | Get open positions |
| Exchange | GET | `/exchange/status` | Exchange status |

### Bitcoin Market Tickers

| Ticker | Description |
|---|---|
| `KXBTCMAXY` | How high will Bitcoin get this year? |
| `KXBTCMINY` | How low will Bitcoin fall this year? |
| Hourly tickers | Bitcoin price at specific times (e.g., "BTC at 5pm EST?") |
| 15-min tickers | Ultra-short 15-minute BTC price contracts |

Use the `/markets` endpoint with `series_ticker` or category filters to discover available BTC contracts.

### Rate Limits

- Exceeding rate limits returns HTTP 429
- Implement exponential backoff on 429 responses
- REST latency is typically 50–200ms
- WebSocket feeds are available for real-time data with lower latency

## Development Conventions

### Language and Dependencies

- **Language:** Python 3.10+
- **Key libraries:**
  - `cryptography` — RSA-PSS signing for API auth
  - `requests` or `httpx` — HTTP client
  - `websockets` — For real-time market data (optional)
  - `python-dotenv` — Environment variable management
  - `pytest` — Testing framework
- **Optional SDK:** `kalshi-python` (v2.x on PyPI) wraps authentication automatically

### Environment Variables

Store secrets in a `.env` file (never commit this):

```
KALSHI_API_KEY_ID=your-key-id-here
KALSHI_PRIVATE_KEY_PATH=./keys/kalshi_private_key.pem
KALSHI_ENV=demo          # "demo" or "prod"
```

### Code Style

- Follow PEP 8
- Use type hints on all function signatures
- Use `logging` module (not `print`) for operational output
- Keep modules focused — one responsibility per file

### Testing

- Run tests with: `pytest tests/`
- Use the demo API environment for integration tests
- Mock API calls in unit tests using `unittest.mock` or `responses`
- Never use real API keys in tests

### Git Workflow

- Feature branches off `main`
- Descriptive commit messages: `feat: add order placement` / `fix: handle 429 rate limit`
- Never commit `.env`, private keys, or credentials
- The `.gitignore` should exclude: `.env`, `*.pem`, `__pycache__/`, `.pytest_cache/`, `venv/`

## Important Warnings

1. **Always start with the demo environment** (`demo-api.kalshi.co`) — real money is at stake in production
2. **Never commit private keys or API credentials** — use `.env` and `.gitignore`
3. **Implement rate limiting** — respect Kalshi's API limits to avoid bans
4. **Handle errors gracefully** — network failures, expired signatures, insufficient balance
5. **Kalshi is a regulated exchange** — all trading activity is subject to CFTC oversight and Kalshi's terms of service
6. **Risk management** — always implement position limits and loss limits in your strategy

## Quick Start (once code exists)

```bash
# 1. Set up virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API key ID and private key path

# 4. Run tests against demo
KALSHI_ENV=demo pytest tests/

# 5. Start the bot (demo mode)
python scripts/run_bot.py --env demo
```

## Resources

- [Kalshi API Docs](https://docs.kalshi.com/welcome)
- [Kalshi API Keys Setup](https://docs.kalshi.com/getting_started/api_keys)
- [kalshi-python SDK on PyPI](https://pypi.org/project/kalshi-python/)
- [Kalshi BTC Markets](https://kalshi.com/category/crypto/btc)
- [Kalshi Help Center — API](https://help.kalshi.com/kalshi-api)
