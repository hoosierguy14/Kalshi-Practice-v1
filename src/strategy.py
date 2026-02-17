"""
Trading strategy logic.

This module decides WHEN and WHAT to trade. It looks at available markets,
analyzes the order book, and generates trade signals.

The starter strategy is simple:
- Look for BTC markets where the Yes price is "cheap" (below a threshold)
- Only trade if the order book has enough liquidity
- Respect position size and balance limits

You can customize or replace this strategy as you learn more.
"""

import logging
from dataclasses import dataclass

from config import settings
from src.client import KalshiClient
from src.markets import Market, get_orderbook
from src.portfolio import Balance, Position

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """
    A recommendation to place a trade.

    The strategy generates these; the bot decides whether to execute them.
    """

    ticker: str
    side: str          # "yes" or "no"
    action: str        # "buy" or "sell"
    price: int         # Price in cents
    count: int         # Number of contracts
    reason: str        # Why this trade was suggested


class SimpleStrategy:
    """
    A simple value-based trading strategy for BTC prediction markets.

    How it works:
    1. Scans open BTC markets for "cheap" Yes or No contracts
    2. "Cheap" means the ask price is below a configurable threshold
       (e.g., buy Yes contracts priced at 30 cents — if they settle Yes,
       you profit 70 cents per contract)
    3. Only suggests trades if you have enough balance
    4. Limits total position size to avoid overexposure
    """

    def __init__(
        self,
        max_price_cents: int = 40,
        min_price_cents: int = 5,
        contracts_per_trade: int = 1,
    ):
        """
        Args:
            max_price_cents: Only buy contracts priced below this (in cents).
                             Lower = cheaper but less likely to pay out.
            min_price_cents: Skip contracts priced below this (too risky).
            contracts_per_trade: How many contracts to buy per signal.
        """
        self.max_price_cents = max_price_cents
        self.min_price_cents = min_price_cents
        self.contracts_per_trade = contracts_per_trade

    def evaluate(
        self,
        client: KalshiClient,
        markets: list[Market],
        balance: Balance,
        positions: list[Position],
    ) -> list[TradeSignal]:
        """
        Evaluate markets and return trade signals.

        Args:
            client: An authenticated KalshiClient (needed for order book data).
            markets: List of open markets to consider.
            balance: Your current account balance.
            positions: Your current open positions.

        Returns:
            List of TradeSignal recommendations (may be empty).
        """
        signals: list[TradeSignal] = []

        # Safety check: don't trade if balance is too low
        if balance.available_balance < settings.MIN_BALANCE_CENTS:
            logger.warning(
                "Balance too low ($%.2f < $%.2f minimum). Skipping.",
                balance.available_dollars,
                settings.MIN_BALANCE_CENTS / 100,
            )
            return signals

        # Safety check: don't exceed max position size
        total_position_count = sum(p.count for p in positions)
        if total_position_count >= settings.MAX_POSITION_SIZE:
            logger.warning(
                "At max position size (%d/%d). Skipping.",
                total_position_count,
                settings.MAX_POSITION_SIZE,
            )
            return signals

        # Check which tickers we already have positions in
        held_tickers = {p.ticker for p in positions}

        for market in markets:
            # Skip markets we already hold
            if market.ticker in held_tickers:
                continue

            # Skip non-open markets
            if market.status != "open":
                continue

            signal = self._evaluate_market(client, market)
            if signal:
                # Make sure we can afford it
                cost = signal.price * signal.count
                if cost <= balance.available_balance and cost <= settings.MAX_ORDER_COST_CENTS:
                    signals.append(signal)
                else:
                    logger.debug("Skipping %s — cost %d exceeds limits", market.ticker, cost)

        logger.info("Strategy generated %d trade signals from %d markets",
                     len(signals), len(markets))
        return signals

    def _evaluate_market(self, client: KalshiClient, market: Market) -> TradeSignal | None:
        """
        Evaluate a single market for trading opportunity.

        Looks at the current Yes ask price. If it's in our target range,
        we generate a buy signal.
        """
        # Check if the Yes side is cheap enough
        yes_ask = market.yes_ask
        if yes_ask is not None and self.min_price_cents <= yes_ask <= self.max_price_cents:
            return TradeSignal(
                ticker=market.ticker,
                side="yes",
                action="buy",
                price=yes_ask,
                count=self.contracts_per_trade,
                reason=f"Yes ask at {yes_ask}c is below {self.max_price_cents}c threshold",
            )

        # Check if the No side is cheap enough
        no_ask = market.no_ask
        if no_ask is not None and self.min_price_cents <= no_ask <= self.max_price_cents:
            return TradeSignal(
                ticker=market.ticker,
                side="no",
                action="buy",
                price=no_ask,
                count=self.contracts_per_trade,
                reason=f"No ask at {no_ask}c is below {self.max_price_cents}c threshold",
            )

        return None
