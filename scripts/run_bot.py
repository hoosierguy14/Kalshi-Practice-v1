"""
Main entry point for the Kalshi trading bot.

This script:
1. Connects to Kalshi (demo or prod)
2. Checks your balance and positions
3. Scans for BTC markets
4. Runs the strategy to find trade opportunities
5. Executes trades (with confirmation in cautious mode)
6. Repeats on a timer

Usage:
    python scripts/run_bot.py              # Run in demo mode (default)
    python scripts/run_bot.py --env prod   # Run in production (real money!)
    python scripts/run_bot.py --dry-run    # Scan markets but don't place orders
"""

import argparse
import logging
import sys
import time

# Add project root to path so imports work when running as a script
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from src.client import KalshiClient, KalshiAPIError
from src.markets import find_btc_markets
from src.portfolio import get_balance, get_positions, get_exchange_status
from src.strategy import SimpleStrategy
from src.trading import place_order
from src.utils import setup_logging, format_price, format_pnl

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Kalshi BTC Trading Bot")
    parser.add_argument(
        "--env",
        choices=["demo", "prod"],
        default=None,
        help="Override the environment (default: uses KALSHI_ENV from .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan for opportunities but don't place any orders",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle and exit (don't loop)",
    )
    return parser.parse_args()


def print_banner(env: str, dry_run: bool) -> None:
    """Print a startup banner so you know what mode you're in."""
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("=" * 60)
    logger.info("  Kalshi BTC Trading Bot")
    logger.info("  Environment: %s", env.upper())
    logger.info("  Mode: %s", mode)
    logger.info("=" * 60)

    if env == "prod" and not dry_run:
        logger.warning("*** PRODUCTION MODE — REAL MONEY AT RISK ***")


def run_cycle(client: KalshiClient, strategy: SimpleStrategy, dry_run: bool) -> None:
    """
    Run one trading cycle:
    1. Check exchange status
    2. Get balance and positions
    3. Find BTC markets
    4. Run strategy
    5. Execute trades
    """
    # Step 1: Is the exchange open?
    try:
        status = get_exchange_status(client)
        if not status.get("trading_active", False):
            logger.info("Exchange is not active. Waiting...")
            return
    except KalshiAPIError as e:
        logger.error("Failed to check exchange status: %s", e)
        return

    # Step 2: Check your balance and positions
    try:
        balance = get_balance(client)
        positions = get_positions(client)
    except KalshiAPIError as e:
        logger.error("Failed to get portfolio data: %s", e)
        return

    logger.info("Balance: $%.2f available | Positions: %d open",
                balance.available_dollars, len(positions))

    for pos in positions:
        logger.info("  Position: %s | %s x%d @ %s | PnL: %s",
                     pos.ticker, pos.side, pos.count,
                     format_price(pos.avg_price), format_pnl(pos.realized_pnl))

    # Step 3: Find open BTC markets
    try:
        markets = find_btc_markets(client, status="open")
    except KalshiAPIError as e:
        logger.error("Failed to fetch markets: %s", e)
        return

    if not markets:
        logger.info("No open BTC markets found.")
        return

    logger.info("Found %d open BTC markets", len(markets))

    # Step 4: Run strategy to get trade signals
    signals = strategy.evaluate(client, markets, balance, positions)

    if not signals:
        logger.info("No trade opportunities found this cycle.")
        return

    # Step 5: Execute trades
    for signal in signals:
        logger.info(
            "Signal: %s %d %s on %s @ %s — %s",
            signal.action, signal.count, signal.side,
            signal.ticker, format_price(signal.price), signal.reason,
        )

        if dry_run:
            logger.info("  [DRY RUN] Would place order, but skipping.")
            continue

        try:
            order = place_order(
                client=client,
                ticker=signal.ticker,
                side=signal.side,
                action=signal.action,
                count=signal.count,
                order_type="limit",
                yes_price=signal.price if signal.side == "yes" else None,
                no_price=signal.price if signal.side == "no" else None,
            )
            logger.info("  Order placed: %s (status=%s)", order.order_id, order.status)
        except KalshiAPIError as e:
            logger.error("  Failed to place order: %s", e)


def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging()

    # Override environment if specified via CLI
    if args.env:
        settings.ENV = args.env
        settings.BASE_URL = settings.BASE_URLS[args.env]

    print_banner(settings.ENV, args.dry_run)

    # Validate configuration
    if not settings.API_KEY_ID:
        logger.error(
            "KALSHI_API_KEY_ID is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    # Initialize client and strategy
    try:
        client = KalshiClient()
    except FileNotFoundError as e:
        logger.error("Setup error: %s", e)
        sys.exit(1)

    strategy = SimpleStrategy()

    # Run the bot
    if args.once:
        run_cycle(client, strategy, args.dry_run)
    else:
        logger.info("Starting trading loop (interval: %ds). Press Ctrl+C to stop.",
                     settings.POLL_INTERVAL_SECONDS)
        try:
            while True:
                run_cycle(client, strategy, args.dry_run)
                logger.info("Sleeping %ds until next cycle...", settings.POLL_INTERVAL_SECONDS)
                time.sleep(settings.POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user. Goodbye!")


if __name__ == "__main__":
    main()
