"""
Order placement and management.

This module handles buying and selling contracts on Kalshi:
- Place limit and market orders
- Cancel open orders
- List your current orders
"""

import logging
from dataclasses import dataclass

from src.client import KalshiClient

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """Represents a Kalshi order."""

    order_id: str
    ticker: str
    side: str          # "yes" or "no"
    action: str        # "buy" or "sell"
    type: str          # "limit" or "market"
    price: int | None  # Price in cents (for limit orders)
    count: int         # Number of contracts
    status: str        # "resting", "executed", "canceled", etc.
    created_time: str


def place_order(
    client: KalshiClient,
    ticker: str,
    side: str,
    action: str = "buy",
    count: int = 1,
    order_type: str = "limit",
    yes_price: int | None = None,
    no_price: int | None = None,
) -> Order:
    """
    Place an order on a Kalshi market.

    Args:
        client: An authenticated KalshiClient.
        ticker: Market ticker (e.g., "KXBTC-25FEB17-T1800-B95500").
        side: Which side to trade — "yes" or "no".
        action: "buy" or "sell".
        count: Number of contracts (default 1).
        order_type: "limit" (specify a price) or "market" (take best available).
        yes_price: Your limit price in cents for a Yes contract (1-99).
        no_price: Your limit price in cents for a No contract (1-99).

    Returns:
        The created Order object.

    Example:
        # Buy 2 Yes contracts at 45 cents each
        order = place_order(client, "KXBTC-...", side="yes", count=2, yes_price=45)
        # This costs 2 * $0.45 = $0.90
        # If it settles Yes, you get 2 * $1.00 = $2.00 (profit = $1.10)
        # If it settles No, you lose your $0.90
    """
    payload: dict = {
        "ticker": ticker,
        "action": action,
        "side": side,
        "count": count,
        "type": order_type,
    }

    if yes_price is not None:
        payload["yes_price"] = yes_price
    if no_price is not None:
        payload["no_price"] = no_price

    logger.info(
        "Placing order: %s %d %s on %s at price=%s (type=%s)",
        action, count, side, ticker, yes_price or no_price, order_type,
    )

    data = client.post("/portfolio/orders", json=payload)
    order_data = data.get("order", data)
    order = _parse_order(order_data)

    logger.info("Order placed successfully: %s", order.order_id)
    return order


def cancel_order(client: KalshiClient, order_id: str) -> None:
    """
    Cancel a resting (open) order.

    Args:
        client: An authenticated KalshiClient.
        order_id: The ID of the order to cancel.
    """
    logger.info("Canceling order: %s", order_id)
    client.delete(f"/portfolio/orders/{order_id}")
    logger.info("Order canceled: %s", order_id)


def list_orders(
    client: KalshiClient,
    ticker: str | None = None,
    status: str | None = None,
) -> list[Order]:
    """
    List your orders, optionally filtered.

    Args:
        client: An authenticated KalshiClient.
        ticker: Filter by market ticker.
        status: Filter by status ("resting", "executed", "canceled").

    Returns:
        List of Order objects.
    """
    params: dict = {}
    if ticker:
        params["ticker"] = ticker
    if status:
        params["status"] = status

    data = client.get("/portfolio/orders", params=params)
    orders = [_parse_order(o) for o in data.get("orders", [])]

    logger.info("Fetched %d orders", len(orders))
    return orders


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_order(data: dict) -> Order:
    """Convert raw API response dict into an Order dataclass."""
    return Order(
        order_id=data.get("order_id", ""),
        ticker=data.get("ticker", ""),
        side=data.get("side", ""),
        action=data.get("action", ""),
        type=data.get("type", ""),
        price=data.get("yes_price") or data.get("no_price"),
        count=data.get("count", 0),
        status=data.get("status", ""),
        created_time=data.get("created_time", ""),
    )
