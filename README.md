# Kalshi Practice Bot v1

A Python trading bot for [Kalshi](https://kalshi.com) Bitcoin (BTC) prediction markets.

## What This Does

This bot automatically scans Kalshi's BTC prediction markets and places trades based on a simple value strategy. It looks for contracts where the price is "cheap" relative to its potential payout.

**Example:** If a "Bitcoin above $95,000 at 5pm?" contract is selling for $0.30 (30 cents), and it settles at $1.00 if Bitcoin is indeed above $95k, that's a potential 3.3x return.

## Setup

### 1. Prerequisites

- Python 3.10 or newer
- A [Kalshi account](https://kalshi.com) (verified)
- API keys from Kalshi (Profile Settings > API Keys)

### 2. Install

```bash
git clone https://github.com/hoosierguy14/Kalshi-Practice-v1.git
cd Kalshi-Practice-v1

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your Kalshi API credentials:

```
KALSHI_API_KEY_ID=your-key-id-here
KALSHI_PRIVATE_KEY_PATH=./keys/kalshi_private_key.pem
KALSHI_ENV=demo
```

Place your private key `.pem` file in the `keys/` directory.

### 4. Run

```bash
# Dry run first (scans markets but doesn't trade)
python scripts/run_bot.py --dry-run

# Run one cycle against demo
python scripts/run_bot.py --once

# Run continuously
python scripts/run_bot.py

# Run against production (real money — be careful!)
python scripts/run_bot.py --env prod
```

## Project Structure

```
src/
  auth.py       - RSA-PSS authentication (signs every API request)
  client.py     - HTTP client with retry logic
  markets.py    - Find and inspect BTC markets
  trading.py    - Place and cancel orders
  portfolio.py  - Check balance and positions
  strategy.py   - Trading logic (decides what to buy)
  utils.py      - Helper functions
scripts/
  run_bot.py    - Main entry point
config/
  settings.py   - Configuration (loaded from .env)
tests/
  test_*.py     - Unit tests
```

## Running Tests

```bash
pytest tests/ -v
```

## Safety Notes

- **Always start with the demo environment** — it uses fake money
- **Never commit your `.env` file or private keys** — they're in `.gitignore`
- The default strategy has conservative limits (small positions, low max spend)
- You can adjust limits in `.env` or `config/settings.py`
