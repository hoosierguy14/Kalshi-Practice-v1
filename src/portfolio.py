"""
Portfolio and position tracking.

This module lets you check:
- Your account balance (how much cash you have)
- Your open positions (what contracts you currently hold)
- The exchange status (is Kalshi up and running?)
"""

import logging
from dataclasses import dataclass

from src.client import KalshiClient

logger = logging.getLogger(__name__)


@dataclass
class Balance:
    """Your Kalshi account balance."""

    available_balance: int  # Cash available to trade (in cents)
    total_balance: int      # Total balance including funds locked in positions

    @property
    def available_dollars(self) -> float:
        """Balance available for trading, in dollars."""
        return self.available_balance / 100

    @property
    def total_dollars(self) -> float:
        """Total balance, in dollars."""
        return self.total_balance / 100


@dataclass
class Position:
    """A position you hold in a market."""

    ticker: str
    market_title: str
    side: str              # "yes" or "no"
    count: int             # Number of contracts you hold
    avg_price: int         # Average price you paid (in cents)
    market_value: int      # Current value based on market price (in cents)
    realized_pnl: int      # Profit/loss from closed trades (in cents)


def get_balance(client: KalshiClient) -> Balance:
    """
    Get your current account balance.

    Args:
        client: An authenticated KalshiClient.

    Returns:
        A Balance object.
    """
    data = client.get("/portfolio/balance")

    balance = Balance(
        available_balance=data.get("balance", 0),
        total_balance=data.get("portfolio_value", data.get("balance", 0)),
    )

    logger.info("Balance: $%.2f available, $%.2f total",
                balance.available_dollars, balance.total_dollars)
    return balance


def get_positions(client: KalshiClient) -> list[Position]:
    """
    Get all your current open positions.

    A position means you currently hold contracts in a market.
    For example, if you bought 5 "Yes" contracts on BTC > $95k,
    that would show up as one position here.

    Args:
        client: An authenticated KalshiClient.

    Returns:
        List of Position objects.
    """
    data = client.get("/portfolio/positions")

    positions = []
    for p in data.get("market_positions", []):
        positions.append(Position(
            ticker=p.get("ticker", ""),
            market_title=p.get("market_title", ""),
            side="yes" if p.get("yes_count", 0) > 0 else "no",
            count=p.get("yes_count", 0) or p.get("no_count", 0),
            avg_price=p.get("avg_price", 0),
            market_value=p.get("market_value", 0),
            realized_pnl=p.get("realized_pnl", 0),
        ))

    logger.info("Found %d open positions", len(positions))
    return positions


def get_exchange_status(client: KalshiClient) -> dict:
    """
    Check if the Kalshi exchange is currently operational.

    Returns:
        Dictionary with exchange status info (e.g., {"trading_active": True}).
    """
    data = client.get("/exchange/status")
    is_active = data.get("trading_active", False)
    logger.info("Exchange status: trading_active=%s", is_active)
    return data
